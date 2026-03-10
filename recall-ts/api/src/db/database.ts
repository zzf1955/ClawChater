import { mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { DatabaseSync } from 'node:sqlite';

type SqlValue = string | number | bigint | Uint8Array | null;

export interface DatabaseConnectionOptions {
  dbPath: string;
}

export class DatabaseConnection {
  readonly dbPath: string;
  private readonly db: DatabaseSync;

  constructor(options: DatabaseConnectionOptions) {
    this.dbPath = resolve(options.dbPath);
    mkdirSync(dirname(this.dbPath), { recursive: true });

    this.db = new DatabaseSync(this.dbPath);
    this.db.exec('PRAGMA journal_mode = WAL;');
    this.db.exec('PRAGMA foreign_keys = ON;');
  }

  exec(sql: string): void {
    this.db.exec(sql);
  }

  run(sql: string, ...params: SqlValue[]): void {
    this.db.prepare(sql).run(...params);
  }

  get<T>(sql: string, ...params: SqlValue[]): T | undefined {
    return this.db.prepare(sql).get(...params) as T | undefined;
  }

  all<T>(sql: string, ...params: SqlValue[]): T[] {
    return this.db.prepare(sql).all(...params) as T[];
  }

  close(): void {
    this.db.close();
  }
}
