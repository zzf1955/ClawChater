from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

import recall.api.routes as routes
import recall.config as config
from recall.app import create_app
from recall.db.database import init_db
from recall.db.screenshot import create_screenshot


class FakeEngine:
    def __init__(self) -> None:
        self.start_calls = 0
        self.stop_calls = 0

    async def start(self) -> None:
        self.start_calls += 1

    async def stop(self) -> None:
        self.stop_calls += 1


def _prepare_paths(tmp_path: Path, monkeypatch) -> tuple[Path, Path]:
    data_dir = tmp_path / "data"
    screenshots_dir = data_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "recall.db"

    monkeypatch.setattr(config, "DATA_DIR", data_dir)
    monkeypatch.setattr(config, "SCREENSHOTS_DIR", screenshots_dir)
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(routes, "DATA_DIR", data_dir)

    init_db(db_path)
    return data_dir, db_path


def test_screenshot_routes_and_image(tmp_path: Path, monkeypatch) -> None:
    data_dir, _ = _prepare_paths(tmp_path, monkeypatch)

    relative_path = "screenshots/2026-03-10/10/sample.jpg"
    image_path = data_dir / relative_path
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(b"fake-jpeg-bytes")

    row = create_screenshot(
        captured_at="2026-03-10T10:00:00Z",
        file_path=relative_path,
        ocr_text="hello",
        ocr_status="done",
    )

    app = create_app(engine_factory=FakeEngine)
    with TestClient(app) as client:
        response = client.get("/api/screenshots", params={"start_time": "2026-03-10T09:00:00Z", "limit": 10})
        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1
        assert payload[0]["id"] == row["id"]

        detail = client.get(f"/api/screenshots/{row['id']}")
        assert detail.status_code == 200
        assert detail.json()["file_path"] == relative_path

        image = client.get(f"/api/screenshots/{row['id']}/image")
        assert image.status_code == 200
        assert image.content == b"fake-jpeg-bytes"


def test_screenshot_route_errors(tmp_path: Path, monkeypatch) -> None:
    _prepare_paths(tmp_path, monkeypatch)

    missing_file_row = create_screenshot(
        captured_at="2026-03-10T10:00:00Z",
        file_path="screenshots/missing.jpg",
    )
    traversal_row = create_screenshot(
        captured_at="2026-03-10T11:00:00Z",
        file_path="../outside.jpg",
    )

    app = create_app(engine_factory=FakeEngine)
    with TestClient(app) as client:
        not_found = client.get("/api/screenshots/99999")
        assert not_found.status_code == 404

        missing_image = client.get(f"/api/screenshots/{missing_file_row['id']}/image")
        assert missing_image.status_code == 404

        traversal = client.get(f"/api/screenshots/{traversal_row['id']}/image")
        assert traversal.status_code == 400

        invalid_range = client.get(
            "/api/screenshots",
            params={
                "start_time": "2026-03-10T12:00:00Z",
                "end_time": "2026-03-10T11:00:00Z",
            },
        )
        assert invalid_range.status_code == 422


def test_summary_and_config_routes(tmp_path: Path, monkeypatch) -> None:
    _prepare_paths(tmp_path, monkeypatch)

    app = create_app(engine_factory=FakeEngine)
    with TestClient(app) as client:
        created = client.post(
            "/api/summaries",
            json={
                "start_time": "2026-03-10T10:00:00Z",
                "end_time": "2026-03-10T11:00:00Z",
                "summary": "focus work",
                "activity_type": "coding",
            },
        )
        assert created.status_code == 201
        created_payload = created.json()
        assert created_payload["summary"] == "focus work"

        listed = client.get(
            "/api/summaries",
            params={"start_time": "2026-03-10T09:00:00Z", "end_time": "2026-03-10T12:00:00Z"},
        )
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        invalid_summary = client.post(
            "/api/summaries",
            json={
                "start_time": "2026-03-10T12:00:00Z",
                "end_time": "2026-03-10T11:00:00Z",
                "summary": "bad range",
            },
        )
        assert invalid_summary.status_code == 422

        config_get = client.get("/api/config")
        assert config_get.status_code == 200
        assert config_get.json()["OCR_BATCH_SIZE"] == "10"

        config_update = client.post("/api/config", json={"OCR_BATCH_SIZE": "20"})
        assert config_update.status_code == 200
        assert config_update.json()["OCR_BATCH_SIZE"] == "20"

        invalid_config = client.post("/api/config", json={"   ": "1"})
        assert invalid_config.status_code == 422


def test_lifespan_hooks_and_idempotency(tmp_path: Path, monkeypatch) -> None:
    _prepare_paths(tmp_path, monkeypatch)

    calls: list[str] = []
    engines: list[FakeEngine] = []

    def ensure_data_dirs_fn() -> None:
        calls.append("ensure")

    def init_db_fn() -> None:
        calls.append("init")
        init_db()

    def engine_factory() -> FakeEngine:
        calls.append("engine")
        engine = FakeEngine()
        engines.append(engine)
        return engine

    app = create_app(
        ensure_data_dirs_fn=ensure_data_dirs_fn,
        init_db_fn=init_db_fn,
        engine_factory=engine_factory,
    )

    with TestClient(app):
        assert calls == ["ensure", "init", "engine"]
        assert engines[0].start_calls == 1
        assert engines[0].stop_calls == 0

    assert engines[0].stop_calls == 1

    with TestClient(app):
        assert calls == ["ensure", "init", "engine", "ensure", "init", "engine"]
        assert engines[1].start_calls == 1
        assert engines[1].stop_calls == 0

    assert engines[1].stop_calls == 1


def test_frontend_static_and_spa_fallback(tmp_path: Path, monkeypatch) -> None:
    _prepare_paths(tmp_path, monkeypatch)

    frontend_dist = tmp_path / "frontend-dist"
    assets_dir = frontend_dist / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    (frontend_dist / "index.html").write_text("<html><body><div id='root'>frontend</div></body></html>", encoding="utf-8")
    (assets_dir / "main.js").write_text("console.log('ok');", encoding="utf-8")

    app = create_app(engine_factory=FakeEngine, frontend_dist_dir=frontend_dist)
    with TestClient(app) as client:
        root_response = client.get("/")
        assert root_response.status_code == 200
        assert "frontend" in root_response.text

        fallback_response = client.get("/screenshots")
        assert fallback_response.status_code == 200
        assert "frontend" in fallback_response.text

        asset_response = client.get("/assets/main.js")
        assert asset_response.status_code == 200
        assert "console.log('ok');" in asset_response.text

        api_response = client.get("/api/config")
        assert api_response.status_code == 200
        assert api_response.json()["OCR_BATCH_SIZE"] == "10"

        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "ok"
