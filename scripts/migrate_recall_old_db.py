#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from recall.db.database import init_db

VALID_STATUS = {"pending", "done", "error"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate recall_old sqlite db into recall/db/schema.sql layout."
    )
    parser.add_argument("--old-db", type=Path, required=True, help="path to old recall.db")
    parser.add_argument("--new-db", type=Path, help="path to migrated db (optional in dry-run)")
    parser.add_argument("--report", type=Path, help="where to write migration report json")
    parser.add_argument("--sample-size", type=int, default=5, help="sample rows for field checks")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="run migration into temp db and remove it after checks",
    )
    return parser.parse_args()


def normalize_status(status: Any) -> str:
    if isinstance(status, str) and status in VALID_STATUS:
        return status
    return "error"


def normalize_setting_value(raw: str) -> str:
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError:
        return raw

    if decoded is None:
        return ""
    if isinstance(decoded, bool):
        return "true" if decoded else "false"
    if isinstance(decoded, (int, float, str)):
        return str(decoded)
    return json.dumps(decoded, ensure_ascii=True, separators=(",", ":"))


def normalize_file_path(path: str) -> tuple[str, str | None]:
    candidate = Path(path)
    if not candidate.is_absolute():
        return path, None

    parts = candidate.parts
    if "screenshots" in parts:
        idx = parts.index("screenshots")
        return str(Path(*parts[idx:])), None

    return path, f"absolute path kept as-is: {path}"


def fetch_rows(conn: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    return conn.execute(query, params).fetchall()


def migrate(old_db: Path, new_db: Path, sample_size: int) -> dict[str, Any]:
    if not old_db.exists():
        raise FileNotFoundError(f"old db not found: {old_db}")

    init_db(new_db)

    report: dict[str, Any] = {
        "old_db": str(old_db.resolve()),
        "new_db": str(new_db.resolve()),
        "warnings": [],
    }

    with sqlite3.connect(old_db) as src, sqlite3.connect(new_db) as dst:
        src.row_factory = sqlite3.Row
        dst.row_factory = sqlite3.Row

        old_screenshots = fetch_rows(
            src,
            """
            SELECT id, path, timestamp, ocr_text, ocr_status, window_title, process_name, phash
            FROM screenshots
            ORDER BY id ASC
            """,
        )
        old_summaries = fetch_rows(
            src,
            """
            SELECT id, start_time, end_time, summary, activity_type, created_at
            FROM summaries
            ORDER BY id ASC
            """,
        )
        old_settings = fetch_rows(src, "SELECT key, value FROM settings ORDER BY key ASC")

        dst.execute("DELETE FROM screenshots")
        dst.execute("DELETE FROM summaries")
        dst.execute("DELETE FROM settings")

        for row in old_screenshots:
            file_path, warning = normalize_file_path(row["path"])
            if warning:
                report["warnings"].append(warning)
            dst.execute(
                """
                INSERT INTO screenshots(
                    id, captured_at, file_path, ocr_text, ocr_status, window_title, process_name, phash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["id"],
                    row["timestamp"],
                    file_path,
                    row["ocr_text"],
                    normalize_status(row["ocr_status"]),
                    row["window_title"],
                    row["process_name"],
                    row["phash"],
                ),
            )

        for row in old_summaries:
            dst.execute(
                """
                INSERT INTO summaries(id, start_time, end_time, summary, activity_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    row["id"],
                    row["start_time"],
                    row["end_time"],
                    row["summary"],
                    row["activity_type"],
                    row["created_at"],
                ),
            )

        for row in old_settings:
            dst.execute(
                """
                INSERT INTO settings(key, value, updated_at)
                VALUES (?, ?, datetime('now'))
                """,
                (row["key"], normalize_setting_value(row["value"])),
            )

        dst.commit()

        counts = {
            "screenshots": {
                "old": len(old_screenshots),
                "new": dst.execute("SELECT COUNT(*) FROM screenshots").fetchone()[0],
            },
            "summaries": {
                "old": len(old_summaries),
                "new": dst.execute("SELECT COUNT(*) FROM summaries").fetchone()[0],
            },
            "settings": {
                "old": len(old_settings),
                "new": dst.execute("SELECT COUNT(*) FROM settings").fetchone()[0],
            },
        }

        old_status_dist = {
            row[0]: row[1]
            for row in src.execute(
                "SELECT COALESCE(ocr_status, 'NULL') AS status, COUNT(*) FROM screenshots GROUP BY status"
            )
        }
        new_status_dist = {
            row[0]: row[1]
            for row in dst.execute("SELECT ocr_status, COUNT(*) FROM screenshots GROUP BY ocr_status")
        }

        sample_rows = fetch_rows(
            dst,
            """
            SELECT id, captured_at, file_path, ocr_status, window_title, process_name
            FROM screenshots
            ORDER BY id ASC
            LIMIT ?
            """,
            (max(sample_size, 0),),
        )
        sample = [dict(row) for row in sample_rows]

        checksum_old_row = src.execute(
            "SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM screenshots"
        ).fetchone()
        checksum_new_row = dst.execute(
            "SELECT COUNT(*), MIN(captured_at), MAX(captured_at) FROM screenshots"
        ).fetchone()
        checksum_old = tuple(checksum_old_row) if checksum_old_row else (0, None, None)
        checksum_new = tuple(checksum_new_row) if checksum_new_row else (0, None, None)

        report.update(
            {
                "counts": counts,
                "status_distribution": {
                    "old": old_status_dist,
                    "new": new_status_dist,
                },
                "screenshot_time_span": {
                    "old": {
                        "count": checksum_old[0],
                        "min": checksum_old[1],
                        "max": checksum_old[2],
                    },
                    "new": {
                        "count": checksum_new[0],
                        "min": checksum_new[1],
                        "max": checksum_new[2],
                    },
                },
                "sample": sample,
                "consistency": {
                    "counts_match": all(v["old"] == v["new"] for v in counts.values()),
                    "time_span_match": checksum_old == checksum_new,
                },
            }
        )

    return report


def main() -> None:
    args = parse_args()

    if args.dry_run:
        if args.new_db:
            target_db = args.new_db
            target_db.parent.mkdir(parents=True, exist_ok=True)
        else:
            tmpdir = Path(tempfile.mkdtemp(prefix="recall-migration-"))
            target_db = tmpdir / "recall.db"
    else:
        if not args.new_db:
            raise ValueError("--new-db is required without --dry-run")
        target_db = args.new_db
        target_db.parent.mkdir(parents=True, exist_ok=True)

    report = migrate(args.old_db, target_db, args.sample_size)
    report["dry_run"] = bool(args.dry_run)

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.dry_run and not args.new_db and target_db.exists():
        target_db.unlink()
        target_db.parent.rmdir()


if __name__ == "__main__":
    main()
