import { DatabaseConnection } from './database.js';

interface Migration {
  version: number;
  name: string;
  up: (db: DatabaseConnection) => void;
}

const MIGRATIONS: Migration[] = [
  {
    version: 1,
    name: 'create_core_tables',
    up: (db) => {
      db.exec(`
        CREATE TABLE IF NOT EXISTS screenshots (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          file_path TEXT NOT NULL UNIQUE,
          timestamp TEXT NOT NULL,
          phash TEXT,
          ocr_text TEXT,
          ocr_status TEXT NOT NULL DEFAULT 'pending' CHECK (ocr_status IN ('pending', 'done', 'error')),
          ocr_error TEXT,
          window_title TEXT,
          process_name TEXT,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_screenshots_timestamp ON screenshots(timestamp);
        CREATE INDEX IF NOT EXISTS idx_screenshots_ocr_status ON screenshots(ocr_status);
        CREATE INDEX IF NOT EXISTS idx_screenshots_phash ON screenshots(phash);

        CREATE TABLE IF NOT EXISTS summaries (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          start_time TEXT NOT NULL,
          end_time TEXT NOT NULL,
          summary TEXT NOT NULL,
          activity_type TEXT,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_summaries_time ON summaries(start_time, end_time);

        CREATE TABLE IF NOT EXISTS settings (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_settings_updated_at ON settings(updated_at);
      `);
    }
  },
  {
    version: 2,
    name: 'add_screenshot_ocr_error',
    up: (db) => {
      if (!hasColumn(db, 'screenshots', 'ocr_error')) {
        db.exec("ALTER TABLE screenshots ADD COLUMN ocr_error TEXT;");
      }
    }
  }
];

export function runMigrations(db: DatabaseConnection): void {
  db.exec(`
    CREATE TABLE IF NOT EXISTS schema_migrations (
      version INTEGER PRIMARY KEY,
      name TEXT NOT NULL,
      applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
  `);

  const appliedVersions = new Set(
    db
      .all<{ version: number }>('SELECT version FROM schema_migrations ORDER BY version ASC')
      .map((row) => row.version)
  );

  for (const migration of MIGRATIONS) {
    if (appliedVersions.has(migration.version)) {
      continue;
    }

    db.exec('BEGIN;');
    try {
      migration.up(db);
      db.run(
        'INSERT INTO schema_migrations(version, name) VALUES (?, ?);',
        migration.version,
        migration.name
      );
      db.exec('COMMIT;');
    } catch (error) {
      db.exec('ROLLBACK;');
      throw error;
    }
  }
}

function hasColumn(db: DatabaseConnection, tableName: string, columnName: string): boolean {
  return db
    .all<{ name: string }>(`PRAGMA table_info('${tableName}');`)
    .some((column) => column.name === columnName);
}
