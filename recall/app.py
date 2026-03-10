from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from recall.api.routes import router
from recall.config import AppSettings, ensure_data_dirs
from recall.db.database import init_db
from recall.services.core.engine import Engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_data_dirs()
    init_db()
    engine = Engine()
    app.state.engine = engine
    await engine.start()
    yield
    await engine.stop()


def create_app() -> FastAPI:
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
