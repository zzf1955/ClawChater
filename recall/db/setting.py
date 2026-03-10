from __future__ import annotations

from pathlib import Path

from recall.db.database import db_session, get_connection


def _validate_key(key: str) -> str:
    normalized = key.strip()
    if not normalized:
        raise ValueError("setting key must not be empty")
    return normalized


def get_setting(key: str, db_path: Path | None = None) -> str | None:
    normalized = _validate_key(key)
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (normalized,)).fetchone()
    return row["value"] if row else None


def get_all_settings(db_path: Path | None = None) -> dict[str, str]:
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT key, value FROM settings ORDER BY key").fetchall()
    return {row["key"]: row["value"] for row in rows}


def set_setting(key: str, value: str, db_path: Path | None = None) -> str:
    normalized = _validate_key(key)
    with db_session(db_path) as conn:
        conn.execute(
            """
            INSERT INTO settings(key, value, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET
              value = excluded.value,
              updated_at = datetime('now')
            """,
            (normalized, value),
        )
    return value


def update_settings(payload: dict[str, str], db_path: Path | None = None) -> dict[str, str]:
    if not payload:
        return get_all_settings(db_path)

    normalized_payload = [(_validate_key(key), value) for key, value in payload.items()]
    with db_session(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO settings(key, value, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET
              value = excluded.value,
              updated_at = datetime('now')
            """,
            normalized_payload,
        )
    return get_all_settings(db_path)


def delete_setting(key: str, db_path: Path | None = None) -> bool:
    normalized = _validate_key(key)
    with db_session(db_path) as conn:
        cursor = conn.execute("DELETE FROM settings WHERE key = ?", (normalized,))
    return cursor.rowcount > 0
