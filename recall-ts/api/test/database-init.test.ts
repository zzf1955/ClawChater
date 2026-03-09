import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import test from 'node:test';

import { createAppContext } from '../src/app-context.js';

test('db initialization creates required core tables, columns and indexes', () => {
  const tempDir = mkdtempSync(join(tmpdir(), 'recall-ts-db-'));
  const dbPath = join(tempDir, 'recall.db');
  const context = createAppContext({ dbPath });

  try {
    const tables = context.db
      .all<{ name: string }>("SELECT name FROM sqlite_master WHERE type = 'table';")
      .map((table) => table.name);

    for (const requiredTable of ['schema_migrations', 'screenshots', 'summaries', 'settings']) {
      assert.ok(tables.includes(requiredTable), `Missing table: ${requiredTable}`);
    }

    const screenshotColumns = context.db
      .all<{ name: string }>("PRAGMA table_info('screenshots');")
      .map((column) => column.name);
    assert.ok(screenshotColumns.includes('id'));
    assert.ok(screenshotColumns.includes('file_path'));
    assert.ok(screenshotColumns.includes('timestamp'));
    assert.ok(screenshotColumns.includes('phash'));
    assert.ok(screenshotColumns.includes('ocr_text'));
    assert.ok(screenshotColumns.includes('ocr_status'));
    assert.ok(screenshotColumns.includes('ocr_error'));
    assert.ok(screenshotColumns.includes('window_title'));
    assert.ok(screenshotColumns.includes('process_name'));
    assert.ok(screenshotColumns.includes('created_at'));

    const screenshotIndexes = context.db
      .all<{ name: string }>("PRAGMA index_list('screenshots');")
      .map((index) => index.name);
    assert.ok(screenshotIndexes.includes('idx_screenshots_timestamp'));
    assert.ok(screenshotIndexes.includes('idx_screenshots_ocr_status'));

    const summaryColumns = context.db
      .all<{ name: string }>("PRAGMA table_info('summaries');")
      .map((column) => column.name);
    assert.ok(summaryColumns.includes('start_time'));
    assert.ok(summaryColumns.includes('end_time'));
    assert.ok(summaryColumns.includes('summary'));
    assert.ok(summaryColumns.includes('activity_type'));
    assert.ok(summaryColumns.includes('created_at'));

    const settingColumns = context.db
      .all<{ name: string }>("PRAGMA table_info('settings');")
      .map((column) => column.name);
    assert.ok(settingColumns.includes('key'));
    assert.ok(settingColumns.includes('value'));
    assert.ok(settingColumns.includes('updated_at'));
  } finally {
    context.close();
    rmSync(tempDir, { recursive: true, force: true });
  }
});
