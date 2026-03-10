from __future__ import annotations

from collections import defaultdict
import logging
from threading import RLock
from typing import Awaitable, Callable

from recall.services.core.events import BaseEvent, Event

Handler = Callable[[Event], Awaitable[None]]

class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[type[BaseEvent], list[Handler]] = defaultdict(list)
        self._lock = RLock()
        self._logger = logging.getLogger(__name__)

    def subscribe(self, event_type: type[BaseEvent], handler: Handler) -> bool:
        with self._lock:
            handlers = self._subscribers[event_type]
            if handler in handlers:
                self._logger.debug("skip duplicate subscriber for %s", event_type.__name__)
                return False

            handlers.append(handler)
            self._logger.debug("registered handler for %s; total=%d", event_type.__name__, len(handlers))
            return True

    def subscriber_count(self, event_type: type[BaseEvent] | None = None) -> int:
        with self._lock:
            if event_type is None:
                return sum(len(handlers) for handlers in self._subscribers.values())
            return len(self._subscribers[event_type])

    async def publish(self, event: Event) -> None:
        with self._lock:
            handlers = tuple(self._subscribers[type(event)])

        for handler in handlers:
            try:
                await handler(event)
            except Exception:
                self._logger.exception("event handler crashed for %s", event.name)
