import { DatabaseConnection } from '../database.js';
import { JsonValue } from '../../types/json.js';

interface SettingRow {
  key: string;
  value: string;
}

function parseJsonValue(raw: string): JsonValue {
  return JSON.parse(raw) as JsonValue;
}

export class SettingsRepository {
  constructor(private readonly db: DatabaseConnection) {}

  getAll(): Record<string, JsonValue> {
    const rows = this.db.all<SettingRow>('SELECT key, value FROM settings;');
    const settings: Record<string, JsonValue> = {};

    for (const row of rows) {
      settings[row.key] = parseJsonValue(row.value);
    }

    return settings;
  }

  get(key: string): JsonValue | undefined {
    const row = this.db.get<SettingRow>('SELECT key, value FROM settings WHERE key = ?;', key);
    if (!row) {
      return undefined;
    }

    return parseJsonValue(row.value);
  }

  set(key: string, value: JsonValue): void {
    const valueAsJson = JSON.stringify(value);
    this.db.run(
      `
        INSERT INTO settings(key, value, updated_at)
        VALUES(?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key)
        DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP;
      `,
      key,
      valueAsJson
    );
  }

  setMany(settings: Record<string, JsonValue>): void {
    const entries = Object.entries(settings);
    if (entries.length === 0) {
      return;
    }

    this.db.exec('BEGIN;');
    try {
      for (const [key, value] of entries) {
        this.set(key, value);
      }
      this.db.exec('COMMIT;');
    } catch (error) {
      this.db.exec('ROLLBACK;');
      throw error;
    }
  }
}
