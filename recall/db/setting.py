from __future__ import annotations

from recall.db.database import get_connection


def get_all_settings() -> dict[str, str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT key, value FROM settings ORDER BY key").fetchall()
    return {row["key"]: row["value"] for row in rows}


def update_settings(payload: dict[str, str]) -> dict[str, str]:
    with get_connection() as conn:
        conn.executemany(
            """
            INSERT INTO settings(key, value, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET
              value = excluded.value,
              updated_at = datetime('now')
            """,
            list(payload.items()),
        )
        conn.commit()
    return get_all_settings()
