from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi.testclient import TestClient

import recall.api.routes as routes
import recall.config as config
from recall.app import create_app
from recall.db.database import init_db
from recall.services.capture import CaptureService
from recall.services.core.engine import Engine
from recall.services.core.events import ForceCaptureEvent, ResourceAvailableEvent
from recall.services.ocr_worker import OCRWorker


class BlockingMonitor:
    def __init__(self) -> None:
        self._stopped = asyncio.Event()

    async def run(self) -> None:
        await self._stopped.wait()

    def stop(self) -> None:
        self._stopped.set()


def test_pipeline_trigger_to_capture_to_ocr_to_api_query(tmp_path: Path, monkeypatch) -> None:
    data_dir = tmp_path / "data"
    screenshots_dir = data_dir / "screenshots"
    db_path = data_dir / "recall.db"

    monkeypatch.setattr(config, "DATA_DIR", data_dir)
    monkeypatch.setattr(config, "SCREENSHOTS_DIR", screenshots_dir)
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(routes, "DATA_DIR", data_dir)

    init_db(db_path)

    capture_service = CaptureService(
        screenshots_dir=screenshots_dir,
        data_dir=data_dir,
        screenshot_provider=lambda: b"pipeline-image",
    )

    async def fake_ocr(image_path: Path) -> str:
        return f"ocr:{image_path.name}"

    ocr_worker = OCRWorker(db_path=db_path, data_dir=data_dir, ocr_engine=fake_ocr)
    engine = Engine(
        screen_monitor=BlockingMonitor(),
        time_monitor=BlockingMonitor(),
        resource_monitor=BlockingMonitor(),
        capture_service=capture_service,
        ocr_worker=ocr_worker,
    )

    app = create_app(
        ensure_data_dirs_fn=lambda: None,
        init_db_fn=lambda: init_db(db_path),
        engine_factory=lambda: engine,
    )

    with TestClient(app) as client:
        asyncio.run(engine.trigger(ForceCaptureEvent()))

        pending_response = client.get("/api/screenshots", params={"limit": 10})
        assert pending_response.status_code == 200
        pending_rows = pending_response.json()
        assert len(pending_rows) == 1
        assert pending_rows[0]["ocr_status"] == "pending"

        screenshot_id = pending_rows[0]["id"]

        asyncio.run(engine.trigger(ResourceAvailableEvent()))

        done_detail = client.get(f"/api/screenshots/{screenshot_id}")
        assert done_detail.status_code == 200
        done_row = done_detail.json()
        assert done_row["ocr_status"] == "done"
        assert done_row["ocr_text"].startswith("ocr:")

        image_response = client.get(f"/api/screenshots/{screenshot_id}/image")
        assert image_response.status_code == 200
        assert image_response.content == b"pipeline-image"
