import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import test from 'node:test';

import { createAppContext } from '../src/app-context.js';

test('config service loads static settings and lets DB settings override after restart', () => {
  const tempDir = mkdtempSync(join(tmpdir(), 'recall-ts-config-'));
  const staticConfigPath = join(tempDir, 'config.json');
  const dbPath = join(tempDir, 'recall.db');

  writeFileSync(
    staticConfigPath,
    JSON.stringify(
      {
        DB_PATH: dbPath,
        SCREENSHOT_DIR: './screenshots',
        CHANGE_THRESHOLD: 0.5,
        OCR_BATCH_SIZE: 8
      },
      null,
      2
    ),
    'utf-8'
  );

  const firstRun = createAppContext({ staticConfigPath });
  try {
    assert.equal(firstRun.configService.get('CHANGE_THRESHOLD'), 0.5);
    assert.equal(firstRun.configService.get('OCR_BATCH_SIZE'), 8);

    firstRun.configService.setMany({
      CHANGE_THRESHOLD: 0.92,
      OCR_BATCH_SIZE: 16
    });
  } finally {
    firstRun.close();
  }

  const secondRun = createAppContext({ staticConfigPath });
  try {
    assert.equal(secondRun.configService.get('CHANGE_THRESHOLD'), 0.92);
    assert.equal(secondRun.configService.get('OCR_BATCH_SIZE'), 16);
    assert.equal(secondRun.configService.get('SCREENSHOT_DIR'), './screenshots');
  } finally {
    secondRun.close();
    rmSync(tempDir, { recursive: true, force: true });
  }
});
