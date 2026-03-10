from __future__ import annotations

import asyncio
from typing import Callable

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
    ) -> None:
        self._event_bus = event_bus
        self._interval_seconds = interval_seconds
        self._change_threshold = change_threshold
        self._hash_provider = hash_provider or (lambda: None)
        self._sleep_fn = sleep_fn
        self._running = False
        self._last_hash: str | None = None

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
            await self._sleep_fn(self._interval_seconds)
            await self.sample_once()

    def stop(self) -> None:
        self._running = False
