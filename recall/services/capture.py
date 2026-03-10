from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from recall.config import DATA_DIR, SCREENSHOTS_DIR
from recall.db.screenshot import insert_screenshot


@dataclass(frozen=True)
class CaptureResult:
    screenshot_id: int
    captured_at: str
    file_path: str
    absolute_path: Path
    phash: str


class CaptureService:
    def __init__(
        self,
        screenshots_dir: Path = SCREENSHOTS_DIR,
        data_dir: Path = DATA_DIR,
        screenshot_provider: Callable[[], bytes] | None = None,
        file_writer: Callable[[Path, bytes], None] | None = None,
        insert_record: Callable[..., int] = insert_screenshot,
    ) -> None:
        self._screenshots_dir = screenshots_dir
        self._data_dir = data_dir
        self._screenshot_provider = screenshot_provider or self._default_screenshot_provider
        self._file_writer = file_writer or self._default_file_writer
        self._insert_record = insert_record

    @staticmethod
    def _default_screenshot_provider() -> bytes:
        return b"RECALL_FAKE_JPEG"

    @staticmethod
    def _default_file_writer(path: Path, payload: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

    @staticmethod
    def _build_phash(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()[:16]

    def capture(self, trigger: str, window_title: str | None = None, process_name: str | None = None) -> CaptureResult:
        captured_at_dt = datetime.now(timezone.utc)
        captured_at = captured_at_dt.isoformat()
        day_bucket = captured_at_dt.strftime("%Y-%m-%d")
        hour_bucket = captured_at_dt.strftime("%H")

        image_bytes = self._screenshot_provider()
        phash = self._build_phash(image_bytes)
        filename = f"{captured_at_dt.strftime('%Y%m%d%H%M%S%f')}.jpg"

        absolute_dir = self._screenshots_dir / day_bucket / hour_bucket
        absolute_path = absolute_dir / filename
        relative_path = (Path("screenshots") / day_bucket / hour_bucket / filename).as_posix()

        self._file_writer(absolute_path, image_bytes)

        try:
            screenshot_id = self._insert_record(
                captured_at=captured_at,
                file_path=relative_path,
                ocr_status="pending",
                window_title=window_title,
                process_name=process_name,
                phash=phash,
            )
        except Exception:
            if absolute_path.exists():
                absolute_path.unlink()
            raise

        return CaptureResult(
            screenshot_id=screenshot_id,
            captured_at=captured_at,
            file_path=relative_path,
            absolute_path=absolute_path,
            phash=phash,
        )


def capture_screen() -> Path:
    result = CaptureService().capture(trigger="manual")
    return result.absolute_path
