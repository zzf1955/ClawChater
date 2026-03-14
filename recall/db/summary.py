from __future__ import annotations

from pathlib import Path
from typing import Any

from recall.db.database import db_session, get_connection
from recall.utils.time_parse import parse_iso8601


def _validate_time_range(start_time: str, end_time: str) -> None:
    if parse_iso8601(start_time) > parse_iso8601(end_time):
        raise ValueError("start_time must be less than or equal to end_time")


def list_summaries(
    start_time: str | None,
    end_time: str | None,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    query = "SELECT * FROM summaries WHERE 1=1"
    params: list[Any] = []
    if start_time:
        query += " AND end_time >= ?"
        params.append(start_time)
    if end_time:
        query += " AND start_time <= ?"
        params.append(end_time)
    query += " ORDER BY start_time DESC"

    with get_connection(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_summary(summary_id: int, db_path: Path | None = None) -> dict[str, Any] | None:
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM summaries WHERE id = ?", (summary_id,)).fetchone()
    return dict(row) if row else None


def create_summary(
    start_time: str,
    end_time: str,
    summary: str,
    activity_type: str | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    _validate_time_range(start_time, end_time)

    with db_session(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO summaries(start_time, end_time, summary, activity_type)
            VALUES (?, ?, ?, ?)
            """,
            (start_time, end_time, summary, activity_type),
        )
        summary_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM summaries WHERE id = ?", (summary_id,)).fetchone()

    return dict(row) if row else {}


def update_summary(
    summary_id: int,
    *,
    start_time: str,
    end_time: str,
    summary: str,
    activity_type: str | None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    _validate_time_range(start_time, end_time)

    with db_session(db_path) as conn:
        cursor = conn.execute(
            """
            UPDATE summaries
            SET start_time = ?, end_time = ?, summary = ?, activity_type = ?
            WHERE id = ?
            """,
            (start_time, end_time, summary, activity_type, summary_id),
        )
        if cursor.rowcount == 0:
            raise LookupError(f"summary not found: {summary_id}")
        row = conn.execute("SELECT * FROM summaries WHERE id = ?", (summary_id,)).fetchone()

    return dict(row) if row else {}


def delete_summary(summary_id: int, db_path: Path | None = None) -> bool:
    with db_session(db_path) as conn:
        cursor = conn.execute("DELETE FROM summaries WHERE id = ?", (summary_id,))
    return cursor.rowcount > 0
