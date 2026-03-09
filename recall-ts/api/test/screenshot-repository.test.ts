import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import test from 'node:test';

import { createAppContext } from '../src/app-context.js';

test('screenshot repository exposes only ready pending OCR items and persists OCR errors', () => {
  const tempDir = mkdtempSync(join(tmpdir(), 'recall-ts-screenshot-repo-'));
  const context = createAppContext({
    dbPath: join(tempDir, 'recall.db'),
    startServices: false
  });

  try {
    const placeholderId = context.screenshotRepository.create({
      filePath: 'pending:123',
      timestamp: '2026-03-09T10:00:00.000Z'
    });
    const readyId = context.screenshotRepository.create({
      filePath: 'screenshots/2026-03-09/10/2.jpg',
      timestamp: '2026-03-09T10:00:01.000Z'
    });

    const pending = context.screenshotRepository.listPendingOcr(10);
    assert.deepEqual(
      pending.map((record) => record.id),
      [readyId]
    );

    context.screenshotRepository.updateOcrResult(readyId, {
      ocrText: null,
      ocrStatus: 'error',
      ocrError: 'mock failure'
    });

    const failedRecord = context.screenshotRepository.getById(readyId);
    const placeholderRecord = context.screenshotRepository.getById(placeholderId);
    assert.equal(failedRecord?.ocr_status, 'error');
    assert.equal(failedRecord?.ocr_error, 'mock failure');
    assert.equal(placeholderRecord?.ocr_status, 'pending');
  } finally {
    context.close();
    rmSync(tempDir, { recursive: true, force: true });
  }
});
