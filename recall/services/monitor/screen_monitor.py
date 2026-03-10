from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Callable

from recall.db.setting import get_setting
from recall.services.core.events import ScreenChangeEvent


def hamming_distance_hex(left: str, right: str) -> int:
    if len(left) != len(right):
        return max(len(left), len(right)) * 4
    return sum((int(a, 16) ^ int(b, 16)).bit_count() for a, b in zip(left, right))


class ScreenMonitor:
    def __init__(
        self,
        event_bus,
        interval_seconds: float = 3.0,
        change_threshold: int = 5,
        hash_provider: Callable[[], str | None] | None = None,
        sleep_fn: Callable[[float], asyncio.Future] = asyncio.sleep,
        *,
        db_path: Path | None = None,
        setting_reader: Callable[..., str | None] = get_setting,
    ) -> None:
        self._event_bus = event_bus
        self._interval_seconds = interval_seconds
        self._change_threshold = change_threshold
        self._default_interval_seconds = max(0.1, float(interval_seconds))
        self._default_change_threshold = max(1, int(change_threshold))
        self._hash_provider = hash_provider or (lambda: None)
        self._sleep_fn = sleep_fn
        self._db_path = db_path
        self._setting_reader = setting_reader
        self._running = False
        self._last_hash: str | None = None
        self.reload_config()

    def _read_setting(self, key: str) -> str | None:
        try:
            return self._setting_reader(key, db_path=self._db_path)
        except TypeError:
            return self._setting_reader(key)
        except Exception:
            return None

    @staticmethod
    def _parse_positive_float(raw: str | None, default: float) -> float:
        if raw is None:
            return default
        try:
            value = float(raw)
        except ValueError:
            return default
        return value if value > 0 else default

    @staticmethod
    def _parse_positive_int(raw: str | None, default: int) -> int:
        if raw is None:
            return default
        try:
            value = int(raw)
        except ValueError:
            return default
        return value if value > 0 else default

    def reload_config(self) -> None:
        self._interval_seconds = self._parse_positive_float(
            self._read_setting("SCREEN_CHECK_INTERVAL"),
            self._default_interval_seconds,
        )
        self._change_threshold = self._parse_positive_int(
            self._read_setting("CHANGE_THRESHOLD"),
            self._default_change_threshold,
        )

    async def sample_once(self) -> bool:
        current_hash = self._hash_provider()
        if not current_hash:
            return False

        if self._last_hash is None:
            self._last_hash = current_hash
            return False

        changed = hamming_distance_hex(self._last_hash, current_hash) >= self._change_threshold
        self._last_hash = current_hash

        if changed:
            await self._event_bus.publish(ScreenChangeEvent())
            return True
        return False

    async def run(self) -> None:
        self._running = True
        while self._running:
            self.reload_config()
            await self._sleep_fn(self._interval_seconds)
            await self.sample_once()

    def stop(self) -> None:
        self._running = False
