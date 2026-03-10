from __future__ import annotations

import asyncio

from recall.services.monitor.screen_monitor import ScreenMonitor
from recall.services.monitor.time_monitor import TimeMonitor


class FakeEventBus:
    def __init__(self) -> None:
        self.events: list[object] = []

    async def publish(self, event: object) -> None:
        self.events.append(event)


def test_screen_monitor_uses_phash_threshold() -> None:
    event_bus = FakeEventBus()
    hashes = iter(["0" * 16, "0" * 15 + "1", "f" * 16])
    monitor = ScreenMonitor(
        event_bus,
        change_threshold=5,
        hash_provider=lambda: next(hashes, None),
    )

    async def run_check() -> None:
        await monitor.sample_once()
        await monitor.sample_once()
        await monitor.sample_once()

    asyncio.run(run_check())

    assert len(event_bus.events) == 1


def test_time_monitor_triggers_on_interval_and_reset() -> None:
    event_bus = FakeEventBus()

    class Clock:
        def __init__(self) -> None:
            self.value = 100.0

        def now(self) -> float:
            return self.value

    clock = Clock()
    monitor = TimeMonitor(event_bus, interval_seconds=10.0, now_fn=clock.now)

    async def run_check() -> None:
        await monitor.tick()
        clock.value += 10.0
        await monitor.tick()

        clock.value += 9.0
        await monitor.tick()

        monitor.reset_timer()
        clock.value += 9.0
        await monitor.tick()

        clock.value += 1.0
        await monitor.tick()

    asyncio.run(run_check())

    assert len(event_bus.events) == 2
