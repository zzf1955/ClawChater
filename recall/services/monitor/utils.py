from __future__ import annotations

from pathlib import Path
from typing import Callable

from recall.db.setting import get_setting


def read_setting(
    key: str,
    *,
    db_path: Path | None = None,
    setting_reader: Callable[..., str | None] = get_setting,
) -> str | None:
    if db_path is None and setting_reader is get_setting:
        return None
    try:
        return setting_reader(key, db_path=db_path)
    except TypeError:
        return setting_reader(key)
    except Exception:
        return None


def parse_positive_float(raw: str | None, default: float) -> float:
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def parse_positive_int(raw: str | None, default: int) -> int:
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default
