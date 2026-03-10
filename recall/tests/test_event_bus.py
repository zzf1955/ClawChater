import asyncio

from recall.services.core.event_bus import EventBus
from recall.services.core.events import ScreenChangeEvent


def test_event_dispatch_order() -> None:
    calls: list[str] = []
    bus = EventBus()

    async def first_handler(_event: ScreenChangeEvent) -> None:
        calls.append("first")

    async def second_handler(_event: ScreenChangeEvent) -> None:
        calls.append("second")

    bus.subscribe(ScreenChangeEvent, first_handler)
    bus.subscribe(ScreenChangeEvent, second_handler)

    asyncio.run(bus.publish(ScreenChangeEvent()))

    assert calls == ["first", "second"]


def test_duplicate_subscription_is_ignored() -> None:
    calls: list[str] = []
    bus = EventBus()

    async def handler(_event: ScreenChangeEvent) -> None:
        calls.append("called")

    added_first = bus.subscribe(ScreenChangeEvent, handler)
    added_second = bus.subscribe(ScreenChangeEvent, handler)
    asyncio.run(bus.publish(ScreenChangeEvent()))

    assert added_first is True
    assert added_second is False
    assert calls == ["called"]


def test_handler_exception_isolated() -> None:
    calls: list[str] = []
    bus = EventBus()

    async def broken_handler(_event: ScreenChangeEvent) -> None:
        raise RuntimeError("boom")

    async def healthy_handler(_event: ScreenChangeEvent) -> None:
        calls.append("healthy")

    bus.subscribe(ScreenChangeEvent, broken_handler)
    bus.subscribe(ScreenChangeEvent, healthy_handler)

    asyncio.run(bus.publish(ScreenChangeEvent()))

    assert calls == ["healthy"]
