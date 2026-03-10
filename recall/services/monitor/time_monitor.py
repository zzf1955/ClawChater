from __future__ import annotations

import asyncio
import time
from typing import Callable

from recall.services.core.events import ForceCaptureEvent


class TimeMonitor:
    def __init__(
        self,
        event_bus,
        interval_seconds: float = 30.0,
        now_fn: Callable[[], float] = time.monotonic,
        sleep_fn: Callable[[float], asyncio.Future] = asyncio.sleep,
    ) -> None:
        self._event_bus = event_bus
        self._interval_seconds = interval_seconds
        self._now_fn = now_fn
        self._sleep_fn = sleep_fn
        self._running = False
        self._deadline = self._now_fn() + self._interval_seconds

    def reset_timer(self) -> None:
        self._deadline = self._now_fn() + self._interval_seconds

    async def tick(self) -> bool:
        if self._now_fn() < self._deadline:
            return False
        await self._event_bus.publish(ForceCaptureEvent())
        self.reset_timer()
        return True

    async def run(self) -> None:
        self._running = True
        while self._running:
            await self._sleep_fn(self._interval_seconds)
            await self.tick()

    def stop(self) -> None:
        self._running = False
