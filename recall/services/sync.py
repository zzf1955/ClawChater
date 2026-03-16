from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from recall.config import DATA_DIR, SCREENSHOTS_DIR
from recall.db.screenshot import (
    delete_screenshots_by_ids,
    get_all_file_path_set,
    insert_screenshot,
    list_all_file_paths,
)

logger = logging.getLogger(__name__)

_FILENAME_RE = re.compile(r"^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d+)\.jpg$")


def _parse_captured_at(filename: str) -> str | None:
    m = _FILENAME_RE.match(filename)
    if not m:
        return None
    year, month, day, hour, minute, second, micro = m.groups()
    try:
        dt = datetime(
            int(year), int(month), int(day),
            int(hour), int(minute), int(second),
            int(micro[:6].ljust(6, "0")),
            tzinfo=timezone.utc,
        )
    except ValueError:
        return None
    return dt.isoformat()


def sync_db_with_filesystem() -> dict[str, Any]:
    # Phase 1: find orphan DB records (file missing on disk)
    all_records = list_all_file_paths()
    orphan_ids: list[int] = []
    for record in all_records:
        abs_path = DATA_DIR / record["file_path"]
        if not abs_path.exists():
            orphan_ids.append(record["id"])

    deleted = delete_screenshots_by_ids(orphan_ids)
    logger.info("Sync: deleted %d orphan DB records", deleted)

    # Phase 2: find files on disk not in DB
    existing_paths = get_all_file_path_set()
    imported = 0

    if SCREENSHOTS_DIR.exists():
        for jpg_file in SCREENSHOTS_DIR.rglob("*.jpg"):
            rel_path = jpg_file.relative_to(DATA_DIR).as_posix()
            if rel_path in existing_paths:
                continue

            captured_at = _parse_captured_at(jpg_file.name)
            if captured_at is None:
                logger.warning("Sync: skipping file with unparseable name: %s", jpg_file.name)
                continue

            insert_screenshot(
                captured_at=captured_at,
                file_path=rel_path,
                ocr_status="pending",
            )
            imported += 1

    logger.info("Sync: imported %d new files into DB", imported)

    total_db = len(all_records) - deleted + imported
    total_files = sum(1 for _ in SCREENSHOTS_DIR.rglob("*.jpg")) if SCREENSHOTS_DIR.exists() else 0

    return {
        "deleted": deleted,
        "imported": imported,
        "total_db": total_db,
        "total_files": total_files,
    }
