import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import test from 'node:test';

import { createAppContext } from '../src/app-context.js';
import { AppEvents, ResourceStatusSnapshot } from '../src/events/app-events.js';
import { EventBus } from '../src/events/event-bus.js';
import { ResourceMonitorService } from '../src/resource-monitor/resource-monitor-service.js';

test('resource monitor reports idle/busy states from CPU and GPU thresholds', () => {
  const tempDir = mkdtempSync(join(tmpdir(), 'recall-ts-resource-'));
  const context = createAppContext({
    dbPath: join(tempDir, 'recall.db'),
    staticOverrides: {
      CPU_USAGE_THRESHOLD: 70,
      GPU_USAGE_THRESHOLD: 30
    }
  });

  const samples = [
    { cpuUsage: 20, gpuUsage: 10, sampledAt: '2026-03-09T10:00:00.000Z' },
    { cpuUsage: 82, gpuUsage: 5, sampledAt: '2026-03-09T10:00:05.000Z' },
    { cpuUsage: 22, gpuUsage: 65, sampledAt: '2026-03-09T10:00:10.000Z' }
  ];
  let sampleIndex = 0;
  const eventBus = new EventBus<AppEvents>();
  const changedEvents: ResourceStatusSnapshot[] = [];
  const unsubscribe = eventBus.on('resource.status.changed', (payload) => {
    changedEvents.push(payload);
  });
  const monitor = new ResourceMonitorService({
    configService: context.configService,
    eventBus,
    sampler: {
      sample: () => samples[sampleIndex++] ?? samples[samples.length - 1]
    }
  });

  try {
    const idleSnapshot = monitor.sampleNow();
    assert.equal(idleSnapshot.state, 'idle');
    assert.deepEqual(idleSnapshot.busyReasons, []);

    const cpuBusySnapshot = monitor.sampleNow();
    assert.equal(cpuBusySnapshot.state, 'busy');
    assert.deepEqual(cpuBusySnapshot.busyReasons, ['cpu']);

    const gpuBusySnapshot = monitor.sampleNow();
    assert.equal(gpuBusySnapshot.state, 'busy');
    assert.deepEqual(gpuBusySnapshot.busyReasons, ['gpu']);
    assert.equal(monitor.isBusy(), true);

    assert.equal(changedEvents.length, 3);
    assert.deepEqual(changedEvents[0].busyReasons, []);
    assert.deepEqual(changedEvents[1].busyReasons, ['cpu']);
    assert.deepEqual(changedEvents[2].busyReasons, ['gpu']);
  } finally {
    unsubscribe();
    monitor.close();
    context.close();
    rmSync(tempDir, { recursive: true, force: true });
  }
});
