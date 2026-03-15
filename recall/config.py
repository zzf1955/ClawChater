from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
LOG_DIR = DATA_DIR / "logs"
LOG_FILE = LOG_DIR / "recall.log"
DB_PATH = DATA_DIR / "recall.db"
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"


def _frontend_dist_from_env() -> Path:
    raw = os.getenv("RECALL_FRONTEND_DIST")
    if raw:
        return Path(raw).expanduser()
    return FRONTEND_DIST_DIR


def _serve_frontend_from_env() -> bool:
    return os.getenv("RECALL_SERVE_FRONTEND", "1") != "0"


def _log_file_from_env() -> Path:
    raw = os.getenv("RECALL_LOG_FILE")
    if raw:
        return Path(raw).expanduser()
    return LOG_FILE


def _log_level_from_env() -> str:
    return os.getenv("RECALL_LOG_LEVEL", "DEBUG").upper()


@dataclass(frozen=True)
class AppSettings:
    host: str = os.getenv("RECALL_HOST", "127.0.0.1")
    port: int = int(os.getenv("RECALL_PORT", "8000"))
    reload: bool = os.getenv("RECALL_RELOAD", "0") == "1"
    frontend_dist: Path = field(default_factory=_frontend_dist_from_env)
    serve_frontend: bool = field(default_factory=_serve_frontend_from_env)
    log_file: Path = field(default_factory=_log_file_from_env)
    log_level: str = field(default_factory=_log_level_from_env)


INCOMING_DIR: Path | None = (
    Path(os.getenv("RECALL_INCOMING_DIR")) if os.getenv("RECALL_INCOMING_DIR") else None
)


def ensure_data_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
