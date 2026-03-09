import { CaptureFrame, CaptureReason } from '../events/app-events.js';
import { AppEvents } from '../events/app-events.js';
import { EventBus } from '../events/event-bus.js';
import { ConfigService } from '../config/config-service.js';

export interface EvaluateTriggerInput {
  changeScore: number;
  frame: CaptureFrame;
}

export type TriggerSkipReason = 'below_threshold' | 'throttled';

export interface TriggerDecision {
  shouldCapture: boolean;
  reason?: CaptureReason;
  skipReason?: TriggerSkipReason;
  timestamp: string;
  elapsedSinceLastCaptureMs: number | null;
}

export class TriggerService {
  private lastCaptureAtMs?: number;

  constructor(
    private readonly eventBus: EventBus<AppEvents>,
    private readonly configService: ConfigService
  ) {}

  evaluate(input: EvaluateTriggerInput): TriggerDecision {
    const capturedAt = coerceDate(input.frame.timestamp);
    const timestamp = capturedAt.toISOString();
    const elapsedSinceLastCaptureMs =
      this.lastCaptureAtMs === undefined ? null : capturedAt.getTime() - this.lastCaptureAtMs;
    const changeScore = Number.isFinite(input.changeScore) ? input.changeScore : 0;

    if (this.lastCaptureAtMs === undefined) {
      this.lastCaptureAtMs = capturedAt.getTime();
      this.emitCapture('initial', changeScore, timestamp, input.frame);
      return {
        shouldCapture: true,
        reason: 'initial',
        timestamp,
        elapsedSinceLastCaptureMs
      };
    }

    const minCaptureIntervalMs = getNumberSetting(this.configService, 'MIN_CAPTURE_INTERVAL', 10) * 1000;
    if (elapsedSinceLastCaptureMs !== null && elapsedSinceLastCaptureMs < minCaptureIntervalMs) {
      return {
        shouldCapture: false,
        skipReason: 'throttled',
        timestamp,
        elapsedSinceLastCaptureMs
      };
    }

    const changeThreshold = getNumberSetting(this.configService, 'CHANGE_THRESHOLD', 0.8);
    if (changeScore >= changeThreshold) {
      this.lastCaptureAtMs = capturedAt.getTime();
      this.emitCapture('change', changeScore, timestamp, input.frame);
      return {
        shouldCapture: true,
        reason: 'change',
        timestamp,
        elapsedSinceLastCaptureMs
      };
    }

    const forceCaptureIntervalMs =
      getNumberSetting(this.configService, 'FORCE_CAPTURE_INTERVAL', 300) * 1000;
    if (elapsedSinceLastCaptureMs !== null && elapsedSinceLastCaptureMs >= forceCaptureIntervalMs) {
      this.lastCaptureAtMs = capturedAt.getTime();
      this.emitCapture('force', changeScore, timestamp, input.frame);
      return {
        shouldCapture: true,
        reason: 'force',
        timestamp,
        elapsedSinceLastCaptureMs
      };
    }

    return {
      shouldCapture: false,
      skipReason: 'below_threshold',
      timestamp,
      elapsedSinceLastCaptureMs
    };
  }

  private emitCapture(
    reason: CaptureReason,
    changeScore: number,
    timestamp: string,
    frame: CaptureFrame
  ): void {
    this.eventBus.emit('capture.requested', {
      requestedAt: new Date().toISOString(),
      timestamp,
      reason,
      changeScore,
      frame: {
        image: frame.image,
        windowTitle: frame.windowTitle,
        processName: frame.processName
      }
    });
  }
}

function coerceDate(value: Date | string | undefined): Date {
  if (value instanceof Date) {
    return value;
  }

  const resolved = value ? new Date(value) : new Date();
  if (Number.isNaN(resolved.getTime())) {
    throw new Error(`Invalid capture timestamp: ${String(value)}`);
  }

  return resolved;
}

function getNumberSetting(configService: ConfigService, key: string, fallback: number): number {
  const value = configService.get(key, fallback);
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}
