import asyncio
from pathlib import Path

from recall.db.database import init_db
from recall.db.screenshot import create_screenshot, list_screenshots_by_status
from recall.db.setting import set_setting
from recall.services.ocr_worker import OCRWorker


def test_ocr_worker_handles_mixed_success_and_failure(tmp_path: Path) -> None:
    async def scenario() -> None:
        db_path = tmp_path / "recall.db"
        data_dir = tmp_path / "data"
        screenshots_dir = data_dir / "screenshots"
        screenshots_dir.mkdir(parents=True)
        init_db(db_path)

        image_1 = screenshots_dir / "1.jpg"
        image_2 = screenshots_dir / "2.jpg"
        image_1.write_bytes(b"image-1")
        image_2.write_bytes(b"image-2")

        first = create_screenshot(
            captured_at="2026-03-10T10:00:00Z",
            file_path="screenshots/1.jpg",
            db_path=db_path,
        )
        second = create_screenshot(
            captured_at="2026-03-10T10:01:00Z",
            file_path="screenshots/2.jpg",
            db_path=db_path,
        )

        async def fake_ocr(path: Path) -> str:
            if path.name == "2.jpg":
                raise RuntimeError("ocr engine crashed")
            return f"text-{path.stem}"

        worker = OCRWorker(db_path=db_path, data_dir=data_dir, batch_size=10, ocr_engine=fake_ocr)
        result = await worker.run_once()

        assert result == {"total": 2, "done": 1, "error": 1}

        done_rows = list_screenshots_by_status("done", db_path=db_path)
        error_rows = list_screenshots_by_status("error", db_path=db_path)
        assert [row["id"] for row in done_rows] == [first["id"]]
        assert [row["id"] for row in error_rows] == [second["id"]]
        assert done_rows[0]["ocr_text"] == "text-1"
        assert error_rows[0]["ocr_text"] is None

    asyncio.run(scenario())


def test_ocr_worker_honors_batch_size_setting(tmp_path: Path) -> None:
    async def scenario() -> None:
        db_path = tmp_path / "recall.db"
        data_dir = tmp_path / "data"
        screenshots_dir = data_dir / "screenshots"
        screenshots_dir.mkdir(parents=True)
        init_db(db_path)
        set_setting("OCR_BATCH_SIZE", "1", db_path)

        image_1 = screenshots_dir / "1.jpg"
        image_2 = screenshots_dir / "2.jpg"
        image_1.write_bytes(b"image-1")
        image_2.write_bytes(b"image-2")

        create_screenshot(
            captured_at="2026-03-10T10:00:00Z",
            file_path="screenshots/1.jpg",
            db_path=db_path,
        )
        create_screenshot(
            captured_at="2026-03-10T10:01:00Z",
            file_path="screenshots/2.jpg",
            db_path=db_path,
        )

        worker = OCRWorker(
            db_path=db_path,
            data_dir=data_dir,
            ocr_engine=lambda path: f"ocr-{path.stem}",
        )
        result = await worker.run_once()

        assert result == {"total": 1, "done": 1, "error": 0}
        pending_rows = list_screenshots_by_status("pending", db_path=db_path)
        assert len(pending_rows) == 1

    asyncio.run(scenario())


def test_ocr_worker_returns_fast_when_no_pending(tmp_path: Path) -> None:
    async def scenario() -> None:
        db_path = tmp_path / "recall.db"
        init_db(db_path)
        called = 0

        def fake_ocr(_: Path) -> str:
            nonlocal called
            called += 1
            return "unused"

        worker = OCRWorker(db_path=db_path, ocr_engine=fake_ocr)
        result = await worker.run_once()

        assert result == {"total": 0, "done": 0, "error": 0}
        assert called == 0

    asyncio.run(scenario())
