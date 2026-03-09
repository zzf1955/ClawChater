import assert from 'node:assert/strict';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import test from 'node:test';

import { createAppContext } from '../src/app-context.js';

test('trigger -> capture persists screenshot files and metadata', () => {
  const tempDir = mkdtempSync(join(tmpdir(), 'recall-ts-capture-'));
  const staticConfigPath = join(tempDir, 'config.json');

  writeFileSync(
    staticConfigPath,
    JSON.stringify(
      {
        DB_PATH: './data/recall.db',
        SCREENSHOT_DIR: './screenshots'
      },
      null,
      2
    ),
    'utf-8'
  );

  const context = createAppContext({ staticConfigPath });
  const image = Buffer.from('fake-jpeg-binary');

  try {
    const decision = context.triggerService.evaluate({
      changeScore: 0.95,
      frame: {
        image,
        timestamp: '2026-03-09T12:34:56+08:00',
        windowTitle: 'Editor',
        processName: 'Code.exe'
      }
    });

    assert.equal(decision.shouldCapture, true);

    const records = context.screenshotRepository.listPendingOcr(10);
    assert.equal(records.length, 1);

    const record = records[0];
    assert.equal(record.ocr_status, 'pending');
    assert.equal(record.window_title, 'Editor');
    assert.equal(record.process_name, 'Code.exe');
    assert.equal(record.timestamp, '2026-03-09T04:34:56.000Z');
    assert.match(record.file_path, /^screenshots\/2026-03-09\/12\/\d+\.jpg$/);
    assert.ok(record.phash);

    const absoluteFilePath = resolve(tempDir, record.file_path);
    assert.equal(existsSync(absoluteFilePath), true);
    assert.equal(readFileSync(absoluteFilePath).equals(image), true);
  } finally {
    context.close();
    rmSync(tempDir, { recursive: true, force: true });
  }
});
