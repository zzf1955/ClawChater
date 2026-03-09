import assert from 'node:assert/strict';
import test from 'node:test';

import { buildServer } from '../src/server.js';

test('GET /health should return status ok', async () => {
  const app = buildServer();

  const response = await app.inject({
    method: 'GET',
    url: '/health'
  });

  assert.equal(response.statusCode, 200);

  const payload = response.json();
  assert.equal(payload.status, 'ok');
  assert.ok(typeof payload.timestamp === 'string');

  await app.close();
});
