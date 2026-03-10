import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import test from 'node:test';

import { createAppContext } from '../src/app-context.js';

test('trigger captures when change score crosses threshold after the throttle window', () => {
  const tempDir = mkdtempSync(join(tmpdir(), 'recall-ts-trigger-threshold-'));
  const context = createAppContext({
    dbPath: join(tempDir, 'recall.db'),
    staticOverrides: {
      CHANGE_THRESHOLD: 0.8,
      MIN_CAPTURE_INTERVAL: 10,
      FORCE_CAPTURE_INTERVAL: 300
    }
  });

  try {
    context.triggerService.evaluate({
      changeScore: 0.1,
      frame: {
        image: Buffer.from('initial'),
        timestamp: '2026-03-09T10:00:00+08:00'
      }
    });

    const decision = context.triggerService.evaluate({
      changeScore: 0.86,
      frame: {
        image: Buffer.from('changed'),
        timestamp: '2026-03-09T10:00:15+08:00'
      }
    });

    assert.equal(decision.shouldCapture, true);
    assert.equal(decision.reason, 'change');
  } finally {
    context.close();
    rmSync(tempDir, { recursive: true, force: true });
  }
});

test('trigger forces capture when the force interval elapses without enough visual change', () => {
  const tempDir = mkdtempSync(join(tmpdir(), 'recall-ts-trigger-force-'));
  const context = createAppContext({
    dbPath: join(tempDir, 'recall.db'),
    staticOverrides: {
      CHANGE_THRESHOLD: 0.9,
      MIN_CAPTURE_INTERVAL: 10,
      FORCE_CAPTURE_INTERVAL: 300
    }
  });

  try {
    context.triggerService.evaluate({
      changeScore: 0.05,
      frame: {
        image: Buffer.from('initial'),
        timestamp: '2026-03-09T10:00:00+08:00'
      }
    });

    const decision = context.triggerService.evaluate({
      changeScore: 0.08,
      frame: {
        image: Buffer.from('force'),
        timestamp: '2026-03-09T10:05:01+08:00'
      }
    });

    assert.equal(decision.shouldCapture, true);
    assert.equal(decision.reason, 'force');
  } finally {
    context.close();
    rmSync(tempDir, { recursive: true, force: true });
  }
});

test('trigger throttles captures inside the minimum capture interval', () => {
  const tempDir = mkdtempSync(join(tmpdir(), 'recall-ts-trigger-throttle-'));
  const context = createAppContext({
    dbPath: join(tempDir, 'recall.db'),
    staticOverrides: {
      CHANGE_THRESHOLD: 0.2,
      MIN_CAPTURE_INTERVAL: 10,
      FORCE_CAPTURE_INTERVAL: 300
    }
  });

  try {
    context.triggerService.evaluate({
      changeScore: 0.4,
      frame: {
        image: Buffer.from('initial'),
        timestamp: '2026-03-09T10:00:00+08:00'
      }
    });

    const decision = context.triggerService.evaluate({
      changeScore: 0.99,
      frame: {
        image: Buffer.from('throttled'),
        timestamp: '2026-03-09T10:00:05+08:00'
      }
    });

    assert.equal(decision.shouldCapture, false);
    assert.equal(decision.skipReason, 'throttled');
  } finally {
    context.close();
    rmSync(tempDir, { recursive: true, force: true });
  }
});
