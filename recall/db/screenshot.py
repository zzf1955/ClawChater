from __future__ import annotations

from typing import Any

from recall.db.database import get_connection


def list_screenshots(start_time: str | None, end_time: str | None, limit: int = 100) -> list[dict[str, Any]]:
    query = "SELECT * FROM screenshots WHERE 1=1"
    params: list[Any] = []
    if start_time:
        query += " AND captured_at >= ?"
        params.append(start_time)
    if end_time:
        query += " AND captured_at <= ?"
        params.append(end_time)
    query += " ORDER BY captured_at DESC LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_screenshot(screenshot_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM screenshots WHERE id = ?", (screenshot_id,)).fetchone()
    return dict(row) if row else None
