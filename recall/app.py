from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Callable

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from recall.api.routes import router
from recall.config import AppSettings, FRONTEND_DIST_DIR, ensure_data_dirs
from recall.db.database import init_db
from recall.services.core.engine import Engine


def _is_safe_frontend_path(root_dir: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root_dir)
    except ValueError:
        return False
    return True


def _mount_frontend(app: FastAPI, frontend_dist_dir: Path) -> None:
    frontend_dist_dir = frontend_dist_dir.resolve()
    if not frontend_dist_dir.exists():
        return

    assets_dir = frontend_dist_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    index_file = frontend_dist_dir / "index.html"
    if not index_file.is_file():
        return

    @app.get("/", include_in_schema=False)
    def frontend_index() -> FileResponse:
        return FileResponse(index_file)

    @app.get("/{frontend_path:path}", include_in_schema=False)
    def frontend_fallback(frontend_path: str) -> FileResponse:
        if frontend_path == "api" or frontend_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")

        requested_file = (frontend_dist_dir / frontend_path).resolve()
        if _is_safe_frontend_path(frontend_dist_dir, requested_file) and requested_file.is_file():
            return FileResponse(requested_file)

        return FileResponse(index_file)


def create_app(
    *,
    ensure_data_dirs_fn: Callable[[], None] = ensure_data_dirs,
    init_db_fn: Callable[[], None] = init_db,
    engine_factory: Callable[[], Engine] = Engine,
    frontend_dist_dir: Path | None = FRONTEND_DIST_DIR,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        ensure_data_dirs_fn()
        init_db_fn()
        engine = engine_factory()
        app.state.engine = engine
        await engine.start()
        try:
            yield
        finally:
            await engine.stop()

    app = FastAPI(title="Recall API", lifespan=lifespan)
    app.include_router(router)

    @app.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    if frontend_dist_dir is not None:
        _mount_frontend(app, frontend_dist_dir)

    return app


app = create_app()


if __name__ == "__main__":
    settings = AppSettings()
    app = create_app(frontend_dist_dir=settings.frontend_dist if settings.serve_frontend else None)
    uvicorn.run(app, host=settings.host, port=settings.port, reload=settings.reload)
