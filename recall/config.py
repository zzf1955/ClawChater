from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
DB_PATH = DATA_DIR / "recall.db"


@dataclass(frozen=True)
class AppSettings:
    host: str = os.getenv("RECALL_HOST", "127.0.0.1")
    port: int = int(os.getenv("RECALL_PORT", "8000"))
    reload: bool = os.getenv("RECALL_RELOAD", "0") == "1"


def ensure_data_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
