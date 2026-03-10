from __future__ import annotations

import asyncio

from recall.services.core.events import ForceCaptureEvent


class TimeMonitor:
    def __init__(self, event_bus, interval_seconds: float = 30.0) -> None:
        self._event_bus = event_bus
        self._interval_seconds = interval_seconds
        self._running = False

    async def run(self) -> None:
        self._running = True
        while self._running:
            await asyncio.sleep(self._interval_seconds)
            await self._event_bus.publish(ForceCaptureEvent())

    def stop(self) -> None:
        self._running = False
