from __future__ import annotations

import asyncio

from recall.services.capture import CaptureService
from recall.services.core.event_bus import EventBus
from recall.services.core.events import ForceCaptureEvent, ResourceAvailableEvent, ScreenChangeEvent
from recall.services.monitor.resource_monitor import ResourceMonitor
from recall.services.monitor.screen_monitor import ScreenMonitor
from recall.services.monitor.time_monitor import TimeMonitor
from recall.services.ocr_worker import OCRWorker


class Engine:
    def __init__(self) -> None:
        self.event_bus = EventBus()
        self.ocr_worker = OCRWorker()
        self.capture_service = CaptureService()

        self.screen_monitor = ScreenMonitor(self.event_bus)
        self.time_monitor = TimeMonitor(self.event_bus)
        self.resource_monitor = ResourceMonitor(self.event_bus)

        self._tasks: list[asyncio.Task] = []
        self._register_handlers()

    def _register_handlers(self) -> None:
        self.event_bus.subscribe(ScreenChangeEvent, self._handle_capture)
        self.event_bus.subscribe(ForceCaptureEvent, self._handle_capture)
        self.event_bus.subscribe(ResourceAvailableEvent, self._handle_resource_available)

    async def _handle_capture(self, event: ScreenChangeEvent | ForceCaptureEvent) -> None:
        trigger = "screen_change" if isinstance(event, ScreenChangeEvent) else "force_capture"
        self.capture_service.capture(trigger=trigger)
        self.time_monitor.reset_timer()

    async def _handle_resource_available(self, _event: ResourceAvailableEvent) -> None:
        await self.ocr_worker.run_once()

    async def start(self) -> None:
        self._tasks = [
            asyncio.create_task(self.screen_monitor.run()),
            asyncio.create_task(self.time_monitor.run()),
            asyncio.create_task(self.resource_monitor.run()),
        ]

    async def stop(self) -> None:
        self.screen_monitor.stop()
        self.time_monitor.stop()
        self.resource_monitor.stop()
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
