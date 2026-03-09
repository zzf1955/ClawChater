import { dirname, isAbsolute, resolve } from 'node:path';

import { CaptureService } from './capture/capture-service.js';
import { ConfigService } from './config/config-service.js';
import { loadStaticConfig } from './config/static-config.js';
import { DatabaseConnection } from './db/database.js';
import { runMigrations } from './db/migrations.js';
import { ScreenshotRepository } from './db/repositories/screenshot-repository.js';
import { SettingsRepository } from './db/repositories/settings-repository.js';
import { SummaryRepository } from './db/repositories/summary-repository.js';
import { AppEvents } from './events/app-events.js';
import { EventBus } from './events/event-bus.js';
import { OcrEngine } from './ocr-worker/ocr-engine.js';
import { OcrWorkerService } from './ocr-worker/ocr-worker-service.js';
import { ResourceMonitorService } from './resource-monitor/resource-monitor-service.js';
import { ResourceSampler } from './resource-monitor/resource-monitor-service.js';
import { TriggerService } from './trigger/trigger-service.js';
import { JsonValue } from './types/json.js';

export interface AppContextOptions {
  dbPath?: string;
  staticConfigPath?: string;
  staticOverrides?: Record<string, JsonValue>;
  startServices?: boolean;
  ocrEngine?: OcrEngine;
  resourceSampler?: ResourceSampler;
}

export interface AppContext {
  readonly db: DatabaseConnection;
  readonly dbPath: string;
  readonly runtimeRootDir: string;
  readonly screenshotRepository: ScreenshotRepository;
  readonly summaryRepository: SummaryRepository;
  readonly settingsRepository: SettingsRepository;
  readonly configService: ConfigService;
  readonly eventBus: EventBus<AppEvents>;
  readonly triggerService: TriggerService;
  readonly captureService: CaptureService;
  readonly resourceMonitor: ResourceMonitorService;
  readonly ocrWorker: OcrWorkerService;
  close: () => void;
}

function resolveRuntimePath(baseDir: string, configuredPath: JsonValue, label: string): string {
  if (typeof configuredPath !== 'string') {
    throw new Error(`${label} in static config must be a string`);
  }

  if (isAbsolute(configuredPath)) {
    return configuredPath;
  }

  return resolve(baseDir, configuredPath);
}

export function createAppContext(options: AppContextOptions = {}): AppContext {
  const loadedStaticConfig = loadStaticConfig(options.staticConfigPath);
  const staticSettings = {
    ...loadedStaticConfig.settings,
    ...(options.staticOverrides ?? {})
  };
  const runtimeRootDir = dirname(loadedStaticConfig.configPath);
  const resolvedDbPath = options.dbPath
    ? resolve(options.dbPath)
    : resolveRuntimePath(runtimeRootDir, staticSettings.DB_PATH, 'DB_PATH');

  const db = new DatabaseConnection({ dbPath: resolvedDbPath });
  runMigrations(db);

  const settingsRepository = new SettingsRepository(db);
  const configService = new ConfigService(staticSettings, settingsRepository);
  configService.load();
  const eventBus = new EventBus<AppEvents>();
  const screenshotRepository = new ScreenshotRepository(db);
  const captureService = new CaptureService({
    eventBus,
    configService,
    screenshotRepository,
    runtimeRootDir
  });
  const triggerService = new TriggerService(eventBus, configService);
  const resourceMonitor = new ResourceMonitorService({
    eventBus,
    configService,
    sampler: options.resourceSampler
  });
  const ocrWorker = new OcrWorkerService({
    configService,
    eventBus,
    screenshotRepository,
    resourceMonitor,
    runtimeRootDir,
    engine: options.ocrEngine
  });

  if (options.startServices !== false) {
    resourceMonitor.start();
    ocrWorker.start();
  }

  let closed = false;

  return {
    db,
    dbPath: db.dbPath,
    runtimeRootDir,
    screenshotRepository,
    summaryRepository: new SummaryRepository(db),
    settingsRepository,
    configService,
    eventBus,
    triggerService,
    captureService,
    resourceMonitor,
    ocrWorker,
    close: () => {
      if (closed) {
        return;
      }

      closed = true;
      void ocrWorker.close();
      resourceMonitor.close();
      captureService.close();
      db.close();
    }
  };
}
