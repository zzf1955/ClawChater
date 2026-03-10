from __future__ import annotations

import asyncio
import inspect
from typing import Any, Awaitable, Callable, Protocol

from recall.services.capture import capture_screen
from recall.services.core.event_bus import EventBus
from recall.services.core.events import Event, ForceCaptureEvent, ResourceAvailableEvent, ScreenChangeEvent
from recall.services.monitor.resource_monitor import ResourceMonitor
from recall.services.monitor.screen_monitor import ScreenMonitor
from recall.services.monitor.time_monitor import TimeMonitor
from recall.services.ocr_worker import OCRWorker


class Monitor(Protocol):
    async def run(self) -> None: ...
    def stop(self) -> None: ...


CaptureHandler = Callable[[], Any]


class Engine:
    def __init__(
        self,
        event_bus: EventBus | None = None,
        screen_monitor: Monitor | None = None,
        time_monitor: Monitor | None = None,
        resource_monitor: Monitor | None = None,
        capture_handler: CaptureHandler | None = None,
        ocr_worker: OCRWorker | None = None,
    ) -> None:
        self.event_bus = event_bus or EventBus()
        self.ocr_worker = ocr_worker or OCRWorker()
        self._capture_handler = capture_handler or capture_screen

        self.screen_monitor = screen_monitor or ScreenMonitor(self.event_bus)
        self.time_monitor = time_monitor or TimeMonitor(self.event_bus)
        self.resource_monitor = resource_monitor or ResourceMonitor(self.event_bus)
        self._monitors = [self.screen_monitor, self.time_monitor, self.resource_monitor]
        self._tasks: list[asyncio.Task] = []
        self._running = False
        self._register_handlers()

    def _register_handlers(self) -> None:
        self.event_bus.subscribe(ScreenChangeEvent, self._handle_capture)
        self.event_bus.subscribe(ForceCaptureEvent, self._handle_capture)
        self.event_bus.subscribe(ResourceAvailableEvent, self._handle_resource_available)

    async def _handle_capture(self, _event: ScreenChangeEvent | ForceCaptureEvent) -> None:
        result = self._capture_handler()
        if inspect.isawaitable(result):
            await result

    async def _handle_resource_available(self, _event: ResourceAvailableEvent) -> None:
        await self.ocr_worker.run_once()

    def register_handler(
        self,
        event_type: type[ScreenChangeEvent | ForceCaptureEvent | ResourceAvailableEvent],
        handler: Callable[[Event], Awaitable[None]],
    ) -> bool:
        return self.event_bus.subscribe(event_type, handler)

    async def trigger(self, event: Event) -> None:
        await self.event_bus.publish(event)

    def get_status(self) -> dict[str, int | bool]:
        alive_tasks = sum(1 for task in self._tasks if not task.done())
        return {
            "running": self._running,
            "task_count": len(self._tasks),
            "alive_task_count": alive_tasks,
            "subscriber_count": self.event_bus.subscriber_count(),
        }

    async def start(self) -> None:
        if self._running:
            return

        self._running = True
        self._tasks = [
            asyncio.create_task(monitor.run())
            for monitor in self._monitors
        ]

    async def stop(self) -> None:
        if not self._running:
            return

        self._running = False
        for monitor in self._monitors:
            monitor.stop()

        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
