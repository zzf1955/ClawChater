"""IncomingWatcher: monitor a syncthing incoming directory for new screenshots.

Discovers .jpg files with matching .json sidecar metadata, imports them into
the database, and moves the image to the standard screenshots directory.
"""
from __future__ import annotations

import asyncio
import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from recall.config import DATA_DIR, SCREENSHOTS_DIR
from recall.db.screenshot import insert_screenshot

_logger = logging.getLogger(__name__)

_POLL_INTERVAL = 3.0


class IncomingWatcher:
    def __init__(
        self,
        incoming_dir: Path,
        screenshots_dir: Path = SCREENSHOTS_DIR,
        data_dir: Path = DATA_DIR,
        poll_interval: float = _POLL_INTERVAL,
        insert_record: Callable[..., int] = insert_screenshot,
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self._incoming_dir = incoming_dir
        self._screenshots_dir = screenshots_dir
        self._data_dir = data_dir
        self._poll_interval = poll_interval
        self._insert_record = insert_record
        self._running = False

    def _list_ready_files(self) -> list[Path]:
        """Return .jpg files that have a matching .json sidecar."""
        if not self._incoming_dir.is_dir():
            return []
        result = []
        for jpg_path in sorted(self._incoming_dir.glob("*.jpg")):
            json_path = jpg_path.with_suffix(".json")
            if json_path.is_file():
                result.append(jpg_path)
        return result

    def _read_sidecar(self, json_path: Path) -> dict | None:
        try:
            text = json_path.read_text(encoding="utf-8")
            return json.loads(text)
        except Exception:
            self._logger.warning("failed to read sidecar %s", json_path, exc_info=True)
            return None

    def _import_one(self, jpg_path: Path) -> int | None:
        json_path = jpg_path.with_suffix(".json")
        metadata = self._read_sidecar(json_path)
        if metadata is None:
            self._logger.warning("skipping %s: no valid sidecar", jpg_path.name)
            return None

        captured_at = metadata.get("captured_at")
        if not captured_at:
            captured_at = datetime.now(timezone.utc).isoformat()

        try:
            dt = datetime.fromisoformat(captured_at)
        except (ValueError, TypeError):
            dt = datetime.now(timezone.utc)
            captured_at = dt.isoformat()

        day_bucket = dt.strftime("%Y-%m-%d")
        hour_bucket = dt.strftime("%H")

        device_id = metadata.get("device_id", "unknown")
        dest_dir = self._screenshots_dir / day_bucket / hour_bucket
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_filename = f"{device_id}_{jpg_path.stem.split('_', 1)[-1]}.jpg"
        dest_path = dest_dir / dest_filename

        relative_path = (Path("screenshots") / day_bucket / hour_bucket / dest_filename).as_posix()

        # Insert DB record before moving file so a failed insert doesn't orphan the file.
        try:
            screenshot_id = self._insert_record(
                captured_at=captured_at,
                file_path=relative_path,
                ocr_status="pending",
                window_title=metadata.get("window_title"),
                process_name=metadata.get("process_name"),
                phash=metadata.get("phash"),
            )
        except Exception:
            self._logger.exception("failed to insert record for %s", jpg_path)
            return None

        shutil.move(str(jpg_path), str(dest_path))

        # Clean up sidecar
        try:
            json_path.unlink()
        except OSError:
            pass

        self._logger.info(
            "imported screenshot_id=%s device=%s path=%s",
            screenshot_id, device_id, relative_path,
        )
        return screenshot_id

    def import_pending(self) -> list[int]:
        """Import all ready files. Returns list of inserted screenshot IDs."""
        ready = self._list_ready_files()
        if not ready:
            return []

        ids = []
        for jpg_path in ready:
            sid = self._import_one(jpg_path)
            if sid is not None:
                ids.append(sid)
        return ids

    async def run(self) -> None:
        self._running = True
        self._logger.info("incoming watcher started dir=%s", self._incoming_dir)
        while self._running:
            try:
                imported = self.import_pending()
                if imported:
                    self._logger.info("imported %d screenshots", len(imported))
            except Exception:
                self._logger.exception("incoming watcher poll error")
            await asyncio.sleep(self._poll_interval)

    def stop(self) -> None:
        self._running = False
        self._logger.info("incoming watcher stopped")
