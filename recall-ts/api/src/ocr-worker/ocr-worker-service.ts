import { readFile } from 'node:fs/promises';
import { isAbsolute, resolve, sep } from 'node:path';

import { ConfigService } from '../config/config-service.js';
import {
  ScreenshotRecord,
  ScreenshotRepository
} from '../db/repositories/screenshot-repository.js';
import { AppEvents } from '../events/app-events.js';
import { EventBus } from '../events/event-bus.js';
import { ResourceMonitorService } from '../resource-monitor/resource-monitor-service.js';
import { OcrEngine, OcrResult, OnnxRuntimeOcrEngine } from './ocr-engine.js';

interface LoggerLike {
  info?: (...args: unknown[]) => void;
  warn?: (...args: unknown[]) => void;
  error?: (...args: unknown[]) => void;
}

export interface OcrWorkerRunResult {
  state: 'disabled' | 'busy' | 'idle' | 'processed';
  fetched: number;
  processed: number;
  failed: number;
}

export interface OcrWorkerServiceOptions {
  configService: ConfigService;
  screenshotRepository: ScreenshotRepository;
  resourceMonitor: ResourceMonitorService;
  runtimeRootDir: string;
  eventBus?: EventBus<AppEvents>;
  engine?: OcrEngine;
  logger?: LoggerLike;
}

export class OcrWorkerService {
  private readonly engine: OcrEngine;
  private readonly logger: LoggerLike;
  private readonly unsubscribers: Array<() => void> = [];
  private intervalHandle?: NodeJS.Timeout;
  private activeRun?: Promise<OcrWorkerRunResult>;
  private rerunRequested = false;

  constructor(private readonly options: OcrWorkerServiceOptions) {
    this.engine =
      options.engine ??
      new OnnxRuntimeOcrEngine(options.configService, options.runtimeRootDir);
    this.logger = options.logger ?? console;
    this.unsubscribers.push(
      this.options.configService.onDidChange((_, changedKeys) => {
        if (changedKeys.includes('OCR_POLL_INTERVAL') && this.intervalHandle) {
          this.stop();
          this.start();
        }

        if (
          changedKeys.some((key) =>
            ['OCR_POLL_INTERVAL', 'OCR_PIPELINE_MODULE', 'OCR_BATCH_SIZE'].includes(key)
          )
        ) {
          this.requestRerun();
        }
      })
    );

    if (this.options.eventBus) {
      this.unsubscribers.push(
        this.options.eventBus.on('capture.completed', () => {
          this.requestRerun();
        })
      );
      this.unsubscribers.push(
        this.options.eventBus.on('resource.status.changed', (snapshot) => {
          if (snapshot.state === 'idle') {
            this.requestRerun();
          }
        })
      );
    }
  }

  start(): void {
    if (this.intervalHandle) {
      return;
    }

    const intervalMs =
      getPositiveIntegerSetting(this.options.configService, 'OCR_POLL_INTERVAL', 5) * 1000;
    this.intervalHandle = setInterval(() => {
      void this.runNow();
    }, Math.max(intervalMs, 1000));

    if (typeof this.intervalHandle.unref === 'function') {
      this.intervalHandle.unref();
    }
  }

  stop(): void {
    if (!this.intervalHandle) {
      return;
    }

    clearInterval(this.intervalHandle);
    this.intervalHandle = undefined;
  }

  async close(): Promise<void> {
    this.stop();
    for (const unsubscribe of this.unsubscribers) {
      unsubscribe();
    }
    this.unsubscribers.length = 0;
    await this.engine.close?.();
  }

  async runNow(): Promise<OcrWorkerRunResult> {
    if (this.activeRun) {
      this.rerunRequested = true;
      return this.activeRun;
    }

    this.activeRun = this.executeRun();
    try {
      return await this.activeRun;
    } finally {
      this.activeRun = undefined;
      if (this.rerunRequested) {
        this.rerunRequested = false;
        queueMicrotask(() => {
          void this.runNow();
        });
      }
    }
  }

  private async executeRun(): Promise<OcrWorkerRunResult> {
    if ((await this.engine.isAvailable?.()) === false) {
      return {
        state: 'disabled',
        fetched: 0,
        processed: 0,
        failed: 0
      };
    }

    if (this.options.resourceMonitor.isBusy()) {
      return {
        state: 'busy',
        fetched: 0,
        processed: 0,
        failed: 0
      };
    }

    const batchSize = getPositiveIntegerSetting(this.options.configService, 'OCR_BATCH_SIZE', 10);
    const pending = this.options.screenshotRepository.listPendingOcr(batchSize);
    if (pending.length === 0) {
      return {
        state: 'idle',
        fetched: 0,
        processed: 0,
        failed: 0
      };
    }

    let processed = 0;
    let failed = 0;

    for (const screenshot of pending) {
      if (this.options.resourceMonitor.isBusy()) {
        this.requestRerun();
        break;
      }

      const outcome = await this.processScreenshot(screenshot);
      if (outcome === 'done') {
        processed += 1;
      } else {
        failed += 1;
      }
    }

    if (!this.options.resourceMonitor.isBusy() && this.options.screenshotRepository.listPendingOcr(1).length > 0) {
      this.requestRerun();
    }

    return {
      state: 'processed',
      fetched: pending.length,
      processed,
      failed
    };
  }

  private async processScreenshot(screenshot: ScreenshotRecord): Promise<'done' | 'error'> {
    try {
      const absoluteFilePath = toAbsoluteFilePath(screenshot.file_path, this.options.runtimeRootDir);
      const image = await readFile(absoluteFilePath);
      const result = await this.engine.recognize({
        screenshot,
        absoluteFilePath,
        image,
        runtimeRootDir: this.options.runtimeRootDir
      });

      this.options.screenshotRepository.updateOcrResult(screenshot.id, {
        ocrText: normalizeResultText(result),
        ocrStatus: 'done',
        ocrError: null
      });
      this.logger.info?.(`OCR processed screenshot ${screenshot.id}`);
      return 'done';
    } catch (error) {
      const message = toErrorMessage(error);
      this.options.screenshotRepository.updateOcrResult(screenshot.id, {
        ocrText: null,
        ocrStatus: 'error',
        ocrError: message
      });
      this.logger.warn?.(`OCR failed for screenshot ${screenshot.id}: ${message}`);
      return 'error';
    }
  }

  private requestRerun(): void {
    this.rerunRequested = true;
    if (!this.activeRun) {
      queueMicrotask(() => {
        void this.runNow();
      });
    }
  }
}

function getPositiveIntegerSetting(
  configService: ConfigService,
  key: string,
  fallback: number
): number {
  const value = configService.get(key, fallback);
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return fallback;
  }

  return Math.max(1, Math.trunc(value));
}

function normalizeResultText(result: OcrResult): string {
  return result.text.trim();
}

function toAbsoluteFilePath(filePath: string, runtimeRootDir: string): string {
  if (isAbsolute(filePath)) {
    return filePath;
  }

  return resolve(runtimeRootDir, filePath.split('/').join(sep));
}

function toErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message.length > 0) {
    return error.message;
  }

  return String(error);
}
