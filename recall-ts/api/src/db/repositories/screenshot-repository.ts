import { DatabaseConnection } from '../database.js';

export type OcrStatus = 'pending' | 'done' | 'error';

export interface CreateScreenshotInput {
  filePath: string;
  timestamp: string;
  phash?: string;
  ocrText?: string;
  ocrStatus?: OcrStatus;
  windowTitle?: string;
  processName?: string;
}

export interface ScreenshotRecord {
  id: number;
  file_path: string;
  timestamp: string;
  phash: string | null;
  ocr_text: string | null;
  ocr_status: OcrStatus;
  ocr_error: string | null;
  window_title: string | null;
  process_name: string | null;
  created_at: string;
}

export interface UpdateCaptureArtifactInput {
  filePath: string;
  phash: string;
}

export interface UpdateOcrResultInput {
  ocrText: string | null;
  ocrStatus: OcrStatus;
  ocrError?: string | null;
}

export class ScreenshotRepository {
  constructor(private readonly db: DatabaseConnection) {}

  create(input: CreateScreenshotInput): number {
    this.db.run(
      `
        INSERT INTO screenshots(
          file_path,
          timestamp,
          phash,
          ocr_text,
          ocr_status,
          ocr_error,
          window_title,
          process_name
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
      `,
      input.filePath,
      input.timestamp,
      input.phash ?? null,
      input.ocrText ?? null,
      input.ocrStatus ?? 'pending',
      null,
      input.windowTitle ?? null,
      input.processName ?? null
    );

    const row = this.db.get<{ id: number }>('SELECT last_insert_rowid() AS id;');
    if (!row) {
      throw new Error('Failed to retrieve inserted screenshot id');
    }

    return row.id;
  }

  listPendingOcr(limit = 10): ScreenshotRecord[] {
    return this.db.all<ScreenshotRecord>(
      `
        SELECT id, file_path, timestamp, phash, ocr_text, ocr_status, ocr_error, window_title, process_name, created_at
        FROM screenshots
        WHERE ocr_status = 'pending'
          AND file_path NOT LIKE 'pending:%'
        ORDER BY id ASC
        LIMIT ?;
      `,
      limit
    );
  }

  getById(id: number): ScreenshotRecord | undefined {
    return this.db.get<ScreenshotRecord>(
      `
        SELECT id, file_path, timestamp, phash, ocr_text, ocr_status, ocr_error, window_title, process_name, created_at
        FROM screenshots
        WHERE id = ?;
      `,
      id
    );
  }

  updateOcrResult(id: number, input: UpdateOcrResultInput): void {
    this.db.run(
      `
        UPDATE screenshots
        SET ocr_text = ?, ocr_status = ?, ocr_error = ?
        WHERE id = ?;
      `,
      input.ocrText,
      input.ocrStatus,
      input.ocrError ?? null,
      id
    );
  }

  updateCaptureArtifact(id: number, input: UpdateCaptureArtifactInput): void {
    this.db.run(
      `
        UPDATE screenshots
        SET file_path = ?, phash = ?
        WHERE id = ?;
      `,
      input.filePath,
      input.phash,
      id
    );
  }

  deleteById(id: number): void {
    this.db.run('DELETE FROM screenshots WHERE id = ?;', id);
  }
}
