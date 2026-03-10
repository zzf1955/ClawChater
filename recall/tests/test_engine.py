import asyncio

from recall.services.core.engine import Engine
from recall.services.core.events import ForceCaptureEvent, ResourceAvailableEvent, ScreenChangeEvent


class BlockingMonitor:
    def __init__(self) -> None:
        self._stopped = asyncio.Event()

    async def run(self) -> None:
        await self._stopped.wait()

    def stop(self) -> None:
        self._stopped.set()


class WorkerSpy:
    def __init__(self) -> None:
        self.calls = 0

    async def run_once(self) -> None:
        self.calls += 1


def test_engine_lifecycle_and_status() -> None:
    async def scenario() -> None:
        monitors = [BlockingMonitor(), BlockingMonitor(), BlockingMonitor()]
        engine = Engine(
            screen_monitor=monitors[0],
            time_monitor=monitors[1],
            resource_monitor=monitors[2],
        )

        await engine.start()
        started_status = engine.get_status()

        assert started_status["running"] is True
        assert started_status["alive_task_count"] == 3

        await engine.stop()
        stopped_status = engine.get_status()

        assert stopped_status["running"] is False
        assert stopped_status["task_count"] == 0
        assert stopped_status["alive_task_count"] == 0

    asyncio.run(scenario())


def test_engine_can_trigger_events() -> None:
    async def scenario() -> None:
        capture_calls = 0
        worker = WorkerSpy()

        def capture_handler() -> None:
            nonlocal capture_calls
            capture_calls += 1

        engine = Engine(
            screen_monitor=BlockingMonitor(),
            time_monitor=BlockingMonitor(),
            resource_monitor=BlockingMonitor(),
            capture_handler=capture_handler,
            ocr_worker=worker,
        )

        await engine.trigger(ScreenChangeEvent())
        await engine.trigger(ForceCaptureEvent())
        await engine.trigger(ResourceAvailableEvent())

        assert capture_calls == 2
        assert worker.calls == 1

    asyncio.run(scenario())


def test_engine_concurrency_smoke_no_task_leak() -> None:
    async def scenario() -> None:
        engine = Engine(
            screen_monitor=BlockingMonitor(),
            time_monitor=BlockingMonitor(),
            resource_monitor=BlockingMonitor(),
        )
        await engine.start()

        await asyncio.gather(*[engine.trigger(ScreenChangeEvent()) for _ in range(50)])

        before_stop = engine.get_status()
        assert before_stop["alive_task_count"] == 3

        await engine.stop()
        after_stop = engine.get_status()
        assert after_stop["alive_task_count"] == 0

    asyncio.run(scenario())
