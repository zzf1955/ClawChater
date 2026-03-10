from __future__ import annotations

from typing import Any

from recall.db.database import get_connection


def list_summaries(start_time: str | None, end_time: str | None) -> list[dict[str, Any]]:
    query = "SELECT * FROM summaries WHERE 1=1"
    params: list[Any] = []
    if start_time:
        query += " AND end_time >= ?"
        params.append(start_time)
    if end_time:
        query += " AND start_time <= ?"
        params.append(end_time)
    query += " ORDER BY start_time DESC"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def create_summary(start_time: str, end_time: str, summary: str, activity_type: str | None = None) -> dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO summaries(start_time, end_time, summary, activity_type)
            VALUES (?, ?, ?, ?)
            """,
            (start_time, end_time, summary, activity_type),
        )
        summary_id = cursor.lastrowid
        conn.commit()
        row = conn.execute("SELECT * FROM summaries WHERE id = ?", (summary_id,)).fetchone()
    return dict(row)
