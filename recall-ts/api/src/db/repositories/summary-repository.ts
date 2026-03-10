import { DatabaseConnection } from '../database.js';

export interface CreateSummaryInput {
  startTime: string;
  endTime: string;
  summary: string;
  activityType?: string;
}

export interface SummaryRecord {
  id: number;
  start_time: string;
  end_time: string;
  summary: string;
  activity_type: string | null;
  created_at: string;
}

export class SummaryRepository {
  constructor(private readonly db: DatabaseConnection) {}

  create(input: CreateSummaryInput): number {
    this.db.run(
      `
        INSERT INTO summaries(start_time, end_time, summary, activity_type)
        VALUES (?, ?, ?, ?);
      `,
      input.startTime,
      input.endTime,
      input.summary,
      input.activityType ?? null
    );

    const row = this.db.get<{ id: number }>('SELECT last_insert_rowid() AS id;');
    if (!row) {
      throw new Error('Failed to retrieve inserted summary id');
    }

    return row.id;
  }

  listRecent(hours = 24): SummaryRecord[] {
    return this.db.all<SummaryRecord>(
      `
        SELECT id, start_time, end_time, summary, activity_type, created_at
        FROM summaries
        WHERE start_time > datetime('now', ? || ' hours')
        ORDER BY start_time DESC;
      `,
      `-${hours}`
    );
  }
}
