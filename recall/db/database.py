from __future__ import annotations

import sqlite3
from pathlib import Path

from recall.config import DB_PATH, ensure_data_dirs


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    ensure_data_dirs()
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    with get_connection() as conn:
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        conn.executemany(
            """
            INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)
            """,
            [
                ("CHANGE_THRESHOLD", "5"),
                ("OCR_BATCH_SIZE", "10"),
                ("GPU_USAGE_THRESHOLD", "70"),
                ("CPU_USAGE_THRESHOLD", "80"),
                ("FORCE_INTERVAL", "30"),
            ],
        )
        conn.commit()
