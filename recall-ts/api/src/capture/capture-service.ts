import { createHash, randomUUID } from 'node:crypto';
import { existsSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { isAbsolute, join, relative, resolve, sep } from 'node:path';

import { CaptureCompletedEvent, CaptureRequestEvent } from '../events/app-events.js';
import { AppEvents } from '../events/app-events.js';
import { EventBus } from '../events/event-bus.js';
import { ConfigService } from '../config/config-service.js';
import { ScreenshotRepository } from '../db/repositories/screenshot-repository.js';

export interface CaptureServiceOptions {
  eventBus: EventBus<AppEvents>;
  configService: ConfigService;
  screenshotRepository: ScreenshotRepository;
  runtimeRootDir: string;
}

export class CaptureService {
  private readonly unsubscribe: () => void;

  constructor(private readonly options: CaptureServiceOptions) {
    this.unsubscribe = this.options.eventBus.on('capture.requested', (payload) => {
      this.capture(payload);
    });
  }

  capture(request: CaptureRequestEvent): CaptureCompletedEvent {
    const captureDate = new Date(request.timestamp);
    const { dateSegment, hourSegment } = buildStorageSegments(captureDate);
    const screenshotDir = resolveScreenshotDir(this.options.configService, this.options.runtimeRootDir);
    const placeholderPath = `pending:${randomUUID()}`;
    const screenshotId = this.options.screenshotRepository.create({
      filePath: placeholderPath,
      timestamp: request.timestamp,
      ocrStatus: 'pending',
      windowTitle: request.frame.windowTitle,
      processName: request.frame.processName
    });

    const absoluteFilePath = join(screenshotDir, dateSegment, hourSegment, `${screenshotId}.jpg`);
    const fileBuffer = Buffer.from(request.frame.image);
    const phash = createPseudoPhash(fileBuffer);

    try {
      mkdirSync(join(screenshotDir, dateSegment, hourSegment), { recursive: true });
      writeFileSync(absoluteFilePath, fileBuffer);

      const storedFilePath = toStoredFilePath(absoluteFilePath, this.options.runtimeRootDir);
      this.options.screenshotRepository.updateCaptureArtifact(screenshotId, {
        filePath: storedFilePath,
        phash
      });

      const completedEvent: CaptureCompletedEvent = {
        screenshotId,
        filePath: storedFilePath,
        timestamp: request.timestamp,
        phash,
        windowTitle: request.frame.windowTitle ?? null,
        processName: request.frame.processName ?? null,
        reason: request.reason,
        changeScore: request.changeScore
      };
      this.options.eventBus.emit('capture.completed', completedEvent);
      return completedEvent;
    } catch (error) {
      this.options.screenshotRepository.deleteById(screenshotId);
      if (existsSync(absoluteFilePath)) {
        rmSync(absoluteFilePath, { force: true });
      }
      throw error;
    }
  }

  close(): void {
    this.unsubscribe();
  }
}

function resolveScreenshotDir(configService: ConfigService, runtimeRootDir: string): string {
  const configuredPath = configService.get('SCREENSHOT_DIR', './screenshots');
  if (typeof configuredPath !== 'string' || configuredPath.length === 0) {
    return resolve(runtimeRootDir, 'screenshots');
  }

  return isAbsolute(configuredPath) ? configuredPath : resolve(runtimeRootDir, configuredPath);
}

function buildStorageSegments(captureDate: Date): { dateSegment: string; hourSegment: string } {
  const year = captureDate.getFullYear();
  const month = padTwoDigits(captureDate.getMonth() + 1);
  const day = padTwoDigits(captureDate.getDate());
  const hour = padTwoDigits(captureDate.getHours());

  return {
    dateSegment: `${year}-${month}-${day}`,
    hourSegment: hour
  };
}

function createPseudoPhash(image: Uint8Array): string {
  return createHash('sha1').update(image).digest('hex').slice(0, 16);
}

function toStoredFilePath(absoluteFilePath: string, runtimeRootDir: string): string {
  const relativePath = relative(runtimeRootDir, absoluteFilePath);
  if (relativePath.length > 0 && !relativePath.startsWith('..') && !isAbsolute(relativePath)) {
    return relativePath.split(sep).join('/');
  }

  return absoluteFilePath.split(sep).join('/');
}

function padTwoDigits(value: number): string {
  return String(value).padStart(2, '0');
}
