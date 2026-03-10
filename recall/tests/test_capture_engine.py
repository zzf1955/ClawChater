from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import pytest

from recall.db import database, screenshot
from recall.services.capture import CaptureService
from recall.services.core.engine import Engine
from recall.services.core.events import ForceCaptureEvent
from recall.services.monitor.time_monitor import TimeMonitor


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def test_capture_raises_when_screenshot_fails(tmp_path: Path) -> None:
    def bad_provider() -> bytes:
        raise RuntimeError("capture failed")

    service = CaptureService(screenshots_dir=tmp_path / "screenshots", screenshot_provider=bad_provider)

    with pytest.raises(RuntimeError, match="capture failed"):
        service.capture(trigger="force_capture")


def test_capture_raises_when_write_fails(tmp_path: Path) -> None:
    def bad_writer(_path: Path, _payload: bytes) -> None:
        raise OSError("disk full")

    service = CaptureService(screenshots_dir=tmp_path / "screenshots", file_writer=bad_writer)

    with pytest.raises(OSError, match="disk full"):
        service.capture(trigger="force_capture")


def test_capture_rolls_back_file_when_db_insert_fails(tmp_path: Path) -> None:
    created_paths: list[Path] = []

    def tracking_writer(path: Path, payload: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        created_paths.append(path)

    def bad_insert(**_kwargs: object) -> int:
        raise RuntimeError("db insert failed")

    service = CaptureService(
        screenshots_dir=tmp_path / "screenshots",
        file_writer=tracking_writer,
        insert_record=bad_insert,
    )

    with pytest.raises(RuntimeError, match="db insert failed"):
        service.capture(trigger="force_capture")

    assert created_paths
    assert all(not path.exists() for path in created_paths)


def test_engine_force_capture_writes_file_and_db_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "recall.db"
    screenshots_dir = tmp_path / "screenshots"

    monkeypatch.setattr(database, "get_connection", lambda: _connect(db_path))
    monkeypatch.setattr(screenshot, "get_connection", lambda: _connect(db_path))

    database.init_db()

    engine = Engine()
    engine.capture_service = CaptureService(screenshots_dir=screenshots_dir)

    class SpyTimeMonitor(TimeMonitor):
        def __init__(self, event_bus) -> None:
            super().__init__(event_bus, interval_seconds=30.0, now_fn=lambda: 0.0)
            self.reset_calls = 0

        def reset_timer(self) -> None:
            self.reset_calls += 1
            super().reset_timer()

    engine.time_monitor = SpyTimeMonitor(engine.event_bus)

    asyncio.run(engine.event_bus.publish(ForceCaptureEvent()))

    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT file_path, ocr_status FROM screenshots ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert row is not None
    assert row["ocr_status"] == "pending"
    assert row["file_path"].startswith("screenshots/")
    assert (tmp_path / row["file_path"]).exists()
    assert engine.time_monitor.reset_calls == 1
