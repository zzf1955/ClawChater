import os from 'node:os';

import {
  AppEvents,
  ResourceBusyReason,
  ResourceStatusSnapshot
} from '../events/app-events.js';
import { EventBus } from '../events/event-bus.js';
import { ConfigService } from '../config/config-service.js';

export interface ResourceSample {
  cpuUsage: number;
  gpuUsage: number;
  sampledAt?: string;
}

export interface ResourceSampler {
  sample: () => ResourceSample;
}

export interface ResourceMonitorServiceOptions {
  configService: ConfigService;
  eventBus?: EventBus<AppEvents>;
  sampler?: ResourceSampler;
}

export class ResourceMonitorService {
  private readonly sampler: ResourceSampler;
  private readonly unsubscribeConfigChange: () => void;
  private intervalHandle?: NodeJS.Timeout;
  private snapshot: ResourceStatusSnapshot = {
    cpuUsage: 0,
    gpuUsage: 0,
    state: 'idle',
    busyReasons: [],
    sampledAt: new Date().toISOString()
  };

  constructor(private readonly options: ResourceMonitorServiceOptions) {
    this.sampler = options.sampler ?? new DefaultResourceSampler();
    this.unsubscribeConfigChange = this.options.configService.onDidChange((_, changedKeys) => {
      if (changedKeys.includes('RESOURCE_MONITOR_INTERVAL') && this.intervalHandle) {
        this.stop();
        this.start();
      }
    });
  }

  start(): void {
    if (this.intervalHandle) {
      return;
    }

    const intervalMs = getNumberSetting(this.options.configService, 'RESOURCE_MONITOR_INTERVAL', 5) * 1000;
    this.intervalHandle = setInterval(() => {
      this.sampleNow();
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

  close(): void {
    this.stop();
    this.unsubscribeConfigChange();
  }

  sampleNow(): ResourceStatusSnapshot {
    const nextSnapshot = this.toSnapshot(this.sampler.sample());
    if (!areSnapshotsEquivalent(this.snapshot, nextSnapshot)) {
      this.snapshot = nextSnapshot;
      this.options.eventBus?.emit('resource.status.changed', this.getSnapshot());
    } else {
      this.snapshot = nextSnapshot;
    }

    return this.getSnapshot();
  }

  getSnapshot(): ResourceStatusSnapshot {
    return {
      ...this.snapshot,
      busyReasons: [...this.snapshot.busyReasons]
    };
  }

  isBusy(): boolean {
    return this.snapshot.state === 'busy';
  }

  private toSnapshot(sample: ResourceSample): ResourceStatusSnapshot {
    const cpuUsage = clampUsage(sample.cpuUsage);
    const gpuUsage = clampUsage(sample.gpuUsage);
    const cpuThreshold = getNumberSetting(this.options.configService, 'CPU_USAGE_THRESHOLD', 75);
    const gpuThreshold = getNumberSetting(this.options.configService, 'GPU_USAGE_THRESHOLD', 30);
    const busyReasons: ResourceBusyReason[] = [];

    if (cpuUsage >= cpuThreshold) {
      busyReasons.push('cpu');
    }

    if (gpuUsage >= gpuThreshold) {
      busyReasons.push('gpu');
    }

    return {
      cpuUsage,
      gpuUsage,
      state: busyReasons.length === 0 ? 'idle' : 'busy',
      busyReasons,
      sampledAt: sample.sampledAt ?? new Date().toISOString()
    };
  }
}

interface CpuTimesSnapshot {
  idle: number;
  total: number;
}

class DefaultResourceSampler implements ResourceSampler {
  private previous = readCpuTimes();

  sample(): ResourceSample {
    const current = readCpuTimes();
    const idleDelta = current.idle - this.previous.idle;
    const totalDelta = current.total - this.previous.total;
    this.previous = current;

    const cpuUsage =
      totalDelta <= 0 ? 0 : ((totalDelta - idleDelta) / totalDelta) * 100;

    return {
      cpuUsage,
      gpuUsage: 0,
      sampledAt: new Date().toISOString()
    };
  }
}

function readCpuTimes(): CpuTimesSnapshot {
  return os.cpus().reduce<CpuTimesSnapshot>(
    (accumulator, cpu) => {
      const total = Object.values(cpu.times).reduce((sum, value) => sum + value, 0);
      accumulator.idle += cpu.times.idle;
      accumulator.total += total;
      return accumulator;
    },
    { idle: 0, total: 0 }
  );
}

function clampUsage(value: number): number {
  if (!Number.isFinite(value)) {
    return 0;
  }

  return Math.max(0, Math.min(100, Number(value.toFixed(2))));
}

function getNumberSetting(configService: ConfigService, key: string, fallback: number): number {
  const value = configService.get(key, fallback);
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

function areSnapshotsEquivalent(
  left: ResourceStatusSnapshot,
  right: ResourceStatusSnapshot
): boolean {
  return (
    left.state === right.state &&
    left.cpuUsage === right.cpuUsage &&
    left.gpuUsage === right.gpuUsage &&
    left.busyReasons.join(',') === right.busyReasons.join(',')
  );
}
