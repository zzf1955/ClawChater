from __future__ import annotations

import hashlib
import logging
import platform
import subprocess
import tempfile
from io import BytesIO
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from PIL import Image

from recall.config import DATA_DIR, SCREENSHOTS_DIR
from recall.db.screenshot import insert_screenshot

_logger = logging.getLogger(__name__)


def _capture_macos() -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        subprocess.run(
            ["screencapture", "-x", "-t", "jpg", str(temp_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return temp_path.read_bytes()
    except Exception:
        _logger.warning("screencapture failed, using placeholder", exc_info=True)
        return b"RECALL_FAKE_JPEG"
    finally:
        temp_path.unlink(missing_ok=True)


def _capture_windows() -> bytes:
    from PIL import ImageGrab

    try:
        img = ImageGrab.grab()
        buf = BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()
    except Exception:
        _logger.warning("ImageGrab.grab failed, using placeholder", exc_info=True)
        return b"RECALL_FAKE_JPEG"


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
        self._logger = logging.getLogger(__name__)
        self._screenshots_dir = screenshots_dir
        self._data_dir = data_dir
        self._screenshot_provider = screenshot_provider or self._default_screenshot_provider
        self._file_writer = file_writer or self._default_file_writer
        self._insert_record = insert_record

    @staticmethod
    def _default_screenshot_provider() -> bytes:
        system = platform.system()

        if system == "Darwin":
            return _capture_macos()
        if system == "Windows":
            return _capture_windows()

        return b"RECALL_FAKE_JPEG"

    @staticmethod
    def _default_file_writer(path: Path, payload: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

    @staticmethod
    def _build_phash(payload: bytes) -> str:
        try:
            with Image.open(BytesIO(payload)) as image:
                grayscale = image.convert("L").resize((9, 8), Image.Resampling.BILINEAR)
                pixels = list(grayscale.getdata())
        except Exception:
            _logger.warning("PIL open failed, falling back to sha256 hash", exc_info=True)
            return hashlib.sha256(payload).hexdigest()[:16]

        bits = 0
        for row in range(8):
            row_offset = row * 9
            for col in range(8):
                left = pixels[row_offset + col]
                right = pixels[row_offset + col + 1]
                bits = (bits << 1) | int(left > right)

        return f"{bits:016x}"

    def current_screen_hash(self) -> str | None:
        try:
            payload = self._screenshot_provider()
        except Exception:
            self._logger.exception("current_screen_hash failed to get screenshot payload")
            return None
        if not payload:
            self._logger.debug("current_screen_hash got empty payload")
            return None
        return self._build_phash(payload)

    def capture(self, trigger: str, window_title: str | None = None, process_name: str | None = None) -> CaptureResult:
        self._logger.info("capture start trigger=%s", trigger)
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
            self._logger.exception("capture failed trigger=%s path=%s", trigger, absolute_path)
            raise

        self._logger.info(
            "capture success trigger=%s screenshot_id=%s path=%s",
            trigger,
            screenshot_id,
            relative_path,
        )
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
