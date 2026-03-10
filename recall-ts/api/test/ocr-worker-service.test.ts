import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import test from 'node:test';

import { createAppContext } from '../src/app-context.js';
import { OcrEngine } from '../src/ocr-worker/ocr-engine.js';

test('ocr worker processes batches and records per-item failures', async () => {
  const tempDir = mkdtempSync(join(tmpdir(), 'recall-ts-ocr-worker-'));
  const screenshotsDir = join(tempDir, 'screenshots', '2026-03-09', '10');
  mkdirSync(screenshotsDir, { recursive: true });

  const seenPaths: string[] = [];
  const engine: OcrEngine = {
    isAvailable: () => true,
    recognize: async ({ absoluteFilePath }) => {
      seenPaths.push(absoluteFilePath);
      if (absoluteFilePath.endsWith('2.jpg')) {
        throw new Error('mock ocr failure');
      }

      return {
        text: `text:${absoluteFilePath.slice(-5)}`
      };
    }
  };

  const context = createAppContext({
    dbPath: join(tempDir, 'recall.db'),
    startServices: false,
    ocrEngine: engine,
    staticOverrides: {
      SCREENSHOT_DIR: './screenshots',
      OCR_BATCH_SIZE: 2
    }
  });

  try {
    const absolutePaths = [
      resolve(tempDir, 'screenshots/2026-03-09/10/1.jpg'),
      resolve(tempDir, 'screenshots/2026-03-09/10/2.jpg'),
      resolve(tempDir, 'screenshots/2026-03-09/10/3.jpg')
    ];
    for (const absolutePath of absolutePaths) {
      writeFileSync(absolutePath, `image:${absolutePath}`, 'utf-8');
      context.screenshotRepository.create({
        filePath: absolutePath,
        timestamp: '2026-03-09T10:00:00.000Z'
      });
    }

    const firstRun = await context.ocrWorker.runNow();
    assert.equal(firstRun.state, 'processed');
    assert.equal(firstRun.fetched, 2);
    assert.equal(firstRun.processed, 1);
    assert.equal(firstRun.failed, 1);

    const firstRecord = context.screenshotRepository.getById(1);
    const secondRecord = context.screenshotRepository.getById(2);
    const thirdRecordBefore = context.screenshotRepository.getById(3);
    assert.equal(firstRecord?.ocr_status, 'done');
    assert.equal(firstRecord?.ocr_text, 'text:1.jpg');
    assert.equal(firstRecord?.ocr_error, null);
    assert.equal(secondRecord?.ocr_status, 'error');
    assert.equal(secondRecord?.ocr_error, 'mock ocr failure');
    assert.equal(thirdRecordBefore?.ocr_status, 'pending');

    const secondRun = await context.ocrWorker.runNow();
    assert.equal(secondRun.processed, 1);
    assert.equal(secondRun.failed, 0);
    assert.equal(context.screenshotRepository.getById(3)?.ocr_status, 'done');
    assert.equal(seenPaths.length, 3);
  } finally {
    await context.ocrWorker.close();
    context.close();
    rmSync(tempDir, { recursive: true, force: true });
  }
});

test('ocr worker leaves pending screenshots untouched while resources are busy', async () => {
  const tempDir = mkdtempSync(join(tmpdir(), 'recall-ts-ocr-worker-busy-'));
  const screenshotsDir = join(tempDir, 'screenshots', '2026-03-09', '11');
  mkdirSync(screenshotsDir, { recursive: true });

  const samplerValues = [
    { cpuUsage: 95, gpuUsage: 10, sampledAt: '2026-03-09T11:00:00.000Z' },
    { cpuUsage: 10, gpuUsage: 10, sampledAt: '2026-03-09T11:00:05.000Z' }
  ];
  let samplerIndex = 0;
  let recognizeCalls = 0;
  const engine: OcrEngine = {
    isAvailable: () => true,
    recognize: async () => {
      recognizeCalls += 1;
      return { text: 'ok' };
    }
  };

  const context = createAppContext({
    dbPath: join(tempDir, 'recall.db'),
    startServices: false,
    ocrEngine: engine,
    resourceSampler: {
      sample: () => samplerValues[Math.min(samplerIndex++, samplerValues.length - 1)]
    },
    staticOverrides: {
      SCREENSHOT_DIR: './screenshots',
      OCR_BATCH_SIZE: 1,
      CPU_USAGE_THRESHOLD: 70
    }
  });

  try {
    const absolutePath = resolve(tempDir, 'screenshots/2026-03-09/11/1.jpg');
    writeFileSync(absolutePath, 'image', 'utf-8');
    context.screenshotRepository.create({
      filePath: absolutePath,
      timestamp: '2026-03-09T11:00:00.000Z'
    });

    context.resourceMonitor.sampleNow();
    const busyRun = await context.ocrWorker.runNow();
    assert.equal(busyRun.state, 'busy');
    assert.equal(recognizeCalls, 0);
    assert.equal(context.screenshotRepository.getById(1)?.ocr_status, 'pending');

    context.resourceMonitor.sampleNow();
    const idleRun = await context.ocrWorker.runNow();
    assert.equal(idleRun.state, 'processed');
    assert.equal(recognizeCalls, 1);
    assert.equal(context.screenshotRepository.getById(1)?.ocr_status, 'done');
  } finally {
    await context.ocrWorker.close();
    context.close();
    rmSync(tempDir, { recursive: true, force: true });
  }
});
