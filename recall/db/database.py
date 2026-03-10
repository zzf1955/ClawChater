from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from recall import config

DEFAULT_SETTINGS: tuple[tuple[str, str], ...] = (
    ("SCREEN_CHECK_INTERVAL", "3"),
    ("CHANGE_THRESHOLD", "5"),
    ("OCR_BATCH_SIZE", "10"),
    ("GPU_USAGE_THRESHOLD", "70"),
    ("CPU_USAGE_THRESHOLD", "80"),
    ("FORCE_INTERVAL", "30"),
)


def resolve_db_path(db_path: Path | None = None) -> Path:
    return db_path if db_path is not None else config.DB_PATH


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(resolve_db_path(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Path | None = None) -> None:
    resolved_db_path = resolve_db_path(db_path)
    if db_path is None:
        config.ensure_data_dirs()
    else:
        resolved_db_path.parent.mkdir(parents=True, exist_ok=True)

    schema_path = Path(__file__).resolve().parent / "schema.sql"
    schema = schema_path.read_text(encoding="utf-8")

    with db_session(resolved_db_path) as conn:
        conn.executescript(schema)
        conn.executemany(
            """
            INSERT OR IGNORE INTO settings(key, value)
            VALUES (?, ?)
            """,
            list(DEFAULT_SETTINGS),
        )
