from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Callable

from recall.db.setting import get_setting
from recall.services.core.events import ForceCaptureEvent


class TimeMonitor:
    def __init__(
        self,
        event_bus,
        interval_seconds: float = 30.0,
        now_fn: Callable[[], float] = time.monotonic,
        sleep_fn: Callable[[float], asyncio.Future] = asyncio.sleep,
        *,
        db_path: Path | None = None,
        setting_reader: Callable[..., str | None] = get_setting,
    ) -> None:
        self._event_bus = event_bus
        self._interval_seconds = interval_seconds
        self._default_interval_seconds = max(1.0, float(interval_seconds))
        self._now_fn = now_fn
        self._sleep_fn = sleep_fn
        self._db_path = db_path
        self._setting_reader = setting_reader
        self._running = False
        self._deadline = self._now_fn() + self._interval_seconds
        self.reload_config()

    def reset_timer(self) -> None:
        self._deadline = self._now_fn() + self._interval_seconds

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

    def reload_config(self) -> None:
        updated_interval = self._parse_positive_float(
            self._read_setting("FORCE_INTERVAL"),
            self._default_interval_seconds,
        )
        if updated_interval != self._interval_seconds:
            self._interval_seconds = updated_interval
            self.reset_timer()

    async def tick(self) -> bool:
        if self._now_fn() < self._deadline:
            return False
        await self._event_bus.publish(ForceCaptureEvent())
        self.reset_timer()
        return True

    async def run(self) -> None:
        self._running = True
        while self._running:
            self.reload_config()
            await self._sleep_fn(self._interval_seconds)
            await self.tick()

    def stop(self) -> None:
        self._running = False
