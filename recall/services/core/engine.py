from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any, Awaitable, Callable, Protocol

from recall.config import DB_PATH, INCOMING_DIR
from recall.services.capture import CaptureService
from recall.services.incoming_watcher import IncomingWatcher
from recall.services.core.event_bus import EventBus
from recall.services.core.events import BaseEvent, ConfigUpdatedEvent, ForceCaptureEvent, ResourceAvailableEvent, ScreenChangeEvent
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
        capture_service: CaptureService | None = None,
        ocr_worker: OCRWorker | None = None,
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self.event_bus = event_bus or EventBus()
        self.ocr_worker = ocr_worker or OCRWorker()
        self.capture_service = capture_service or CaptureService()
        self._capture_handler = capture_handler

        self.screen_monitor = screen_monitor or ScreenMonitor(
            self.event_bus,
            hash_provider=self.capture_service.current_screen_hash,
            db_path=DB_PATH,
        )
        self.time_monitor = time_monitor or TimeMonitor(self.event_bus, db_path=DB_PATH)
        self.resource_monitor = resource_monitor or ResourceMonitor(self.event_bus, db_path=DB_PATH)
        self._monitors: list[Monitor] = [self.screen_monitor, self.time_monitor, self.resource_monitor]

        if INCOMING_DIR is not None:
            self.incoming_watcher: IncomingWatcher | None = IncomingWatcher(incoming_dir=INCOMING_DIR)
            self._monitors.append(self.incoming_watcher)
            self._logger.info("incoming watcher enabled dir=%s", INCOMING_DIR)
        else:
            self.incoming_watcher = None
        self._tasks: list[asyncio.Task] = []
        self._running = False
        self._register_handlers()

    def _register_handlers(self) -> None:
        self.event_bus.subscribe(ScreenChangeEvent, self._handle_capture)
        self.event_bus.subscribe(ForceCaptureEvent, self._handle_capture)
        self.event_bus.subscribe(ResourceAvailableEvent, self._handle_resource_available)
        self.event_bus.subscribe(ConfigUpdatedEvent, self._handle_config_updated)

    def _reload_monitor_configs(self) -> None:
        for monitor in (self.screen_monitor, self.time_monitor):
            reload_config = getattr(monitor, "reload_config", None)
            if callable(reload_config):
                reload_config()

    async def _handle_capture(self, event: ScreenChangeEvent | ForceCaptureEvent) -> None:
        self._logger.info("capture trigger received event=%s payload=%s", event.name, event.payload)
        if self._capture_handler is not None:
            result = self._capture_handler()
            if inspect.isawaitable(result):
                await result
            self._logger.debug("capture handler finished via injected handler event=%s", event.name)
        else:
            trigger = "screen_change" if isinstance(event, ScreenChangeEvent) else "force_capture"
            capture_result = self.capture_service.capture(trigger=trigger)
            self._logger.info(
                "capture completed event=%s screenshot_id=%s path=%s phash=%s",
                event.name,
                capture_result.screenshot_id,
                capture_result.file_path,
                capture_result.phash,
            )

        reset_timer = getattr(self.time_monitor, "reset_timer", None)
        if callable(reset_timer):
            reset_timer()
            self._logger.debug("time monitor reset after capture event=%s", event.name)

    async def _handle_resource_available(self, event: ResourceAvailableEvent) -> None:
        self._logger.info("resource_available received payload=%s", event.payload)
        result = await self.ocr_worker.run_once()
        self._logger.info(
            "ocr batch done total=%s done=%s error=%s",
            result.get("total", 0),
            result.get("done", 0),
            result.get("error", 0),
        )

    async def _handle_config_updated(self, event: ConfigUpdatedEvent) -> None:
        self._logger.info("config_updated received payload=%s", event.payload)
        self._reload_monitor_configs()
        self._logger.debug("monitor configs reloaded")

    def register_handler(
        self,
        event_type: type[BaseEvent],
        handler: Callable[[BaseEvent], Awaitable[None]],
    ) -> bool:
        return self.event_bus.subscribe(event_type, handler)

    async def trigger(self, event: BaseEvent) -> None:
        self._logger.debug("manual trigger event=%s payload=%s", event.name, event.payload)
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
            self._logger.debug("engine start skipped: already running")
            return

        self._running = True
        self._reload_monitor_configs()
        self._tasks = [
            asyncio.create_task(monitor.run())
            for monitor in self._monitors
        ]
        self._logger.info("engine started monitors=%d", len(self._monitors))

    async def stop(self) -> None:
        if not self._running:
            self._logger.debug("engine stop skipped: not running")
            return

        self._running = False
        for monitor in self._monitors:
            monitor.stop()

        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        self._logger.info("engine stopped")
