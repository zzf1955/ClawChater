import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import test from 'node:test';

import { createAppContext } from '../src/app-context.js';
import { buildServer } from '../src/server.js';

test('GET /health should return status ok', async () => {
  const tempDir = mkdtempSync(join(tmpdir(), 'recall-ts-health-'));
  const context = createAppContext({
    dbPath: join(tempDir, 'recall.db')
  });
  const app = buildServer({ context });

  try {
    const response = await app.inject({
      method: 'GET',
      url: '/health'
    });

    assert.equal(response.statusCode, 200);

    const payload = response.json();
    assert.equal(payload.status, 'ok');
    assert.ok(typeof payload.timestamp === 'string');
    assert.equal(payload.dbPath, context.dbPath);
  } finally {
    await app.close();
    context.close();
    rmSync(tempDir, { recursive: true, force: true });
  }
});
