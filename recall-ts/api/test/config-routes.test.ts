import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import test from 'node:test';

import { createAppContext } from '../src/app-context.js';
import { buildServer } from '../src/server.js';

test('config routes return merged settings and persist runtime overrides', async () => {
  const tempDir = mkdtempSync(join(tmpdir(), 'recall-ts-config-routes-'));
  const staticConfigPath = join(tempDir, 'config.json');
  const dbPath = join(tempDir, 'recall.db');

  writeFileSync(
    staticConfigPath,
    JSON.stringify(
      {
        DB_PATH: dbPath,
        OCR_BATCH_SIZE: 8,
        CHANGE_THRESHOLD: 0.5
      },
      null,
      2
    ),
    'utf-8'
  );

  const context = createAppContext({ staticConfigPath });
  const app = buildServer({ context });

  try {
    const initialResponse = await app.inject({
      method: 'GET',
      url: '/config'
    });

    assert.equal(initialResponse.statusCode, 200);
    assert.equal(initialResponse.json().settings.OCR_BATCH_SIZE, 8);

    const updateResponse = await app.inject({
      method: 'POST',
      url: '/config',
      payload: {
        OCR_BATCH_SIZE: 16,
        CHANGE_THRESHOLD: 0.92
      }
    });

    assert.equal(updateResponse.statusCode, 200);
    assert.equal(updateResponse.json().settings.OCR_BATCH_SIZE, 16);
    assert.equal(updateResponse.json().settings.CHANGE_THRESHOLD, 0.92);
  } finally {
    await app.close();
    context.close();
  }

  const restartedContext = createAppContext({ staticConfigPath });
  try {
    assert.equal(restartedContext.configService.get('OCR_BATCH_SIZE'), 16);
    assert.equal(restartedContext.configService.get('CHANGE_THRESHOLD'), 0.92);
  } finally {
    restartedContext.close();
    rmSync(tempDir, { recursive: true, force: true });
  }
});
