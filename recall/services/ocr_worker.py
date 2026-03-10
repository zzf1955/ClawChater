from __future__ import annotations

import inspect
import logging
from pathlib import Path
from typing import Awaitable, Callable

from recall import config
from recall.db.screenshot import list_screenshots_by_status, update_screenshot_ocr
from recall.db.setting import get_setting


OCRCallable = Callable[[Path], str | None | Awaitable[str | None]]


def _default_ocr_engine(image_path: Path) -> str:
    image_path.read_bytes()
    return ""


class OCRWorker:
    def __init__(
        self,
        *,
        db_path: Path | None = None,
        data_dir: Path | None = None,
        batch_size: int | None = None,
        ocr_engine: OCRCallable = _default_ocr_engine,
    ) -> None:
        self._db_path = db_path
        self._data_dir = data_dir or config.DATA_DIR
        self._batch_size = batch_size
        self._ocr_engine = ocr_engine
        self._logger = logging.getLogger(__name__)

    async def run_once(self) -> dict[str, int]:
        batch_size = self._resolve_batch_size()
        pending_rows = list_screenshots_by_status(
            "pending",
            limit=batch_size,
            db_path=self._db_path,
        )
        if not pending_rows:
            return {"total": 0, "done": 0, "error": 0}

        done_count = 0
        error_count = 0
        for row in pending_rows:
            screenshot_id = int(row["id"])
            image_path = self._resolve_image_path(str(row["file_path"]))
            try:
                ocr_text = await self._run_ocr(image_path)
                update_screenshot_ocr(
                    screenshot_id,
                    ocr_text=ocr_text if ocr_text is not None else "",
                    ocr_status="done",
                    db_path=self._db_path,
                )
                done_count += 1
            except Exception:
                self._logger.exception("ocr failed for screenshot_id=%s path=%s", screenshot_id, image_path)
                update_screenshot_ocr(
                    screenshot_id,
                    ocr_text=None,
                    ocr_status="error",
                    db_path=self._db_path,
                )
                error_count += 1

        return {"total": len(pending_rows), "done": done_count, "error": error_count}

    def _resolve_batch_size(self) -> int:
        if self._batch_size is not None:
            return max(self._batch_size, 1)
        raw_batch_size = get_setting("OCR_BATCH_SIZE", db_path=self._db_path)
        try:
            parsed_batch_size = int(raw_batch_size or "10")
        except ValueError:
            parsed_batch_size = 10
        return max(parsed_batch_size, 1)

    def _resolve_image_path(self, file_path: str) -> Path:
        path = Path(file_path)
        if path.is_absolute():
            return path
        return self._data_dir / path

    async def _run_ocr(self, image_path: Path) -> str | None:
        result = self._ocr_engine(image_path)
        if inspect.isawaitable(result):
            return await result
        return result
