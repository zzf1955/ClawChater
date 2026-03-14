from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Callable

from recall.db.setting import get_setting
from recall.services.core.events import ScreenChangeEvent
from recall.services.monitor.utils import parse_positive_float, parse_positive_int, read_setting


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
        self._logger = logging.getLogger(__name__)
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

    def reload_config(self) -> None:
        old_interval = self._interval_seconds
        old_threshold = self._change_threshold
        self._interval_seconds = parse_positive_float(
            read_setting("SCREEN_CHECK_INTERVAL", db_path=self._db_path, setting_reader=self._setting_reader),
            self._default_interval_seconds,
        )
        self._change_threshold = parse_positive_int(
            read_setting("CHANGE_THRESHOLD", db_path=self._db_path, setting_reader=self._setting_reader),
            self._default_change_threshold,
        )
        if old_interval != self._interval_seconds or old_threshold != self._change_threshold:
            self._logger.info(
                "screen monitor config updated interval=%.2fs threshold=%d",
                self._interval_seconds,
                self._change_threshold,
            )

    async def sample_once(self) -> bool:
        current_hash = self._hash_provider()
        if not current_hash:
            self._logger.debug("screen sample skipped: hash provider returned empty payload")
            return False

        if self._last_hash is None:
            self._last_hash = current_hash
            self._logger.debug("screen sample initialized baseline hash=%s", current_hash)
            return False

        distance = hamming_distance_hex(self._last_hash, current_hash)
        changed = distance >= self._change_threshold
        self._logger.debug(
            "screen sample distance=%d threshold=%d changed=%s",
            distance,
            self._change_threshold,
            changed,
        )
        self._last_hash = current_hash

        if changed:
            await self._event_bus.publish(ScreenChangeEvent())
            self._logger.info(
                "screen_change published distance=%d threshold=%d",
                distance,
                self._change_threshold,
            )
            return True
        return False

    async def run(self) -> None:
        self._running = True
        self._logger.info("screen monitor started interval=%.2fs threshold=%d", self._interval_seconds, self._change_threshold)
        while self._running:
            self.reload_config()
            await self._sleep_fn(self._interval_seconds)
            await self.sample_once()

    def stop(self) -> None:
        self._running = False
        self._logger.info("screen monitor stopped")
