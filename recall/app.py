from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Callable

import uvicorn
from fastapi import FastAPI

from recall.api.routes import router
from recall.config import AppSettings, ensure_data_dirs
from recall.db.database import init_db
from recall.services.core.engine import Engine


def create_app(
    *,
    ensure_data_dirs_fn: Callable[[], None] = ensure_data_dirs,
    init_db_fn: Callable[[], None] = init_db,
    engine_factory: Callable[[], Engine] = Engine,
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

    return app


app = create_app()


if __name__ == "__main__":
    settings = AppSettings()
    uvicorn.run("recall.app:app", host=settings.host, port=settings.port, reload=settings.reload)
