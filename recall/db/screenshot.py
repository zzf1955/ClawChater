from __future__ import annotations

from pathlib import Path
from typing import Any

from recall.db.database import db_session, get_connection

VALID_OCR_STATUS = {"pending", "done", "error"}


def _validate_status(status: str) -> None:
    if status not in VALID_OCR_STATUS:
        raise ValueError(f"invalid ocr_status: {status}")


def list_screenshots(
    start_time: str | None,
    end_time: str | None,
    limit: int = 100,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    if limit < 1:
        raise ValueError("limit must be greater than 0")

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

    with get_connection(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def list_screenshots_by_status(
    ocr_status: str,
    limit: int = 100,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    _validate_status(ocr_status)
    if limit < 1:
        raise ValueError("limit must be greater than 0")

    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM screenshots
            WHERE ocr_status = ?
            ORDER BY captured_at ASC
            LIMIT ?
            """,
            (ocr_status, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def get_screenshot(screenshot_id: int, db_path: Path | None = None) -> dict[str, Any] | None:
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM screenshots WHERE id = ?", (screenshot_id,)).fetchone()
    return dict(row) if row else None


def create_screenshot(
    captured_at: str,
    file_path: str,
    *,
    ocr_text: str | None = None,
    ocr_status: str = "pending",
    window_title: str | None = None,
    process_name: str | None = None,
    phash: str | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    _validate_status(ocr_status)

    with db_session(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO screenshots(
                captured_at, file_path, ocr_text, ocr_status, window_title, process_name, phash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (captured_at, file_path, ocr_text, ocr_status, window_title, process_name, phash),
        )
        screenshot_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM screenshots WHERE id = ?", (screenshot_id,)).fetchone()

    return dict(row) if row else {}


def update_screenshot_ocr(
    screenshot_id: int,
    *,
    ocr_text: str | None,
    ocr_status: str,
    db_path: Path | None = None,
) -> dict[str, Any]:
    _validate_status(ocr_status)

    with db_session(db_path) as conn:
        cursor = conn.execute(
            """
            UPDATE screenshots
            SET ocr_text = ?, ocr_status = ?
            WHERE id = ?
            """,
            (ocr_text, ocr_status, screenshot_id),
        )
        if cursor.rowcount == 0:
            raise LookupError(f"screenshot not found: {screenshot_id}")
        row = conn.execute("SELECT * FROM screenshots WHERE id = ?", (screenshot_id,)).fetchone()

    return dict(row) if row else {}


def delete_screenshot(screenshot_id: int, db_path: Path | None = None) -> bool:
    with db_session(db_path) as conn:
        cursor = conn.execute("DELETE FROM screenshots WHERE id = ?", (screenshot_id,))
    return cursor.rowcount > 0
