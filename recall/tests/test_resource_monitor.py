import asyncio
import os
import types
from pathlib import Path
from unittest.mock import patch

from recall.db.database import init_db
from recall.db.setting import set_setting
from unittest.mock import MagicMock

from recall.services.monitor.resource_monitor import (
    ResourceMonitor,
    _sample_cpu_usage,
    _sample_gpu_usage,
    _sample_gpu_usage_nvml,
    _sample_gpu_usage_cli,
)


class EventBusSpy:
    def __init__(self) -> None:
        self.events: list[object] = []

    async def publish(self, event: object) -> None:
        self.events.append(event)


def test_resource_monitor_publishes_when_resource_available() -> None:
    async def scenario() -> None:
        event_bus = EventBusSpy()
        monitor = ResourceMonitor(
            event_bus,
            cpu_threshold=70.0,
            gpu_threshold=60.0,
            cpu_usage_sampler=lambda: 21.5,
            gpu_usage_sampler=lambda: 12.3,
        )
        published = await monitor.check_and_publish_once()

        assert published is True
        assert len(event_bus.events) == 1
        event_payload = event_bus.events[0].payload
        assert event_payload["cpu_usage"] == 21.5
        assert event_payload["gpu_usage"] == 12.3

    asyncio.run(scenario())


def test_resource_monitor_skips_when_resource_busy() -> None:
    async def scenario() -> None:
        event_bus = EventBusSpy()
        monitor = ResourceMonitor(
            event_bus,
            cpu_threshold=30.0,
            gpu_threshold=40.0,
            cpu_usage_sampler=lambda: 55.0,
            gpu_usage_sampler=lambda: 10.0,
        )
        published = await monitor.check_and_publish_once()

        assert published is False
        assert event_bus.events == []

    asyncio.run(scenario())


def test_resource_monitor_reads_thresholds_from_settings(tmp_path: Path) -> None:
    async def scenario() -> None:
        db_path = tmp_path / "recall.db"
        init_db(db_path)
        set_setting("CPU_USAGE_THRESHOLD", "33", db_path)
        set_setting("GPU_USAGE_THRESHOLD", "44", db_path)

        event_bus = EventBusSpy()
        monitor = ResourceMonitor(
            event_bus,
            db_path=db_path,
            cpu_threshold=99.0,
            gpu_threshold=99.0,
            cpu_usage_sampler=lambda: 32.0,
            gpu_usage_sampler=lambda: 43.0,
        )
        snapshot = monitor.sample_once()
        assert snapshot.cpu_threshold == 33.0
        assert snapshot.gpu_threshold == 44.0

        published = await monitor.check_and_publish_once()
        assert published is True
        assert len(event_bus.events) == 1

    asyncio.run(scenario())


def test_sample_cpu_usage_falls_back_to_psutil_on_windows() -> None:
    fake_psutil = types.ModuleType("psutil")
    fake_psutil.cpu_percent = lambda interval=None: 42.5

    def fake_getloadavg():
        raise OSError("not supported on Windows")

    with patch.object(os, "getloadavg", fake_getloadavg, create=True), \
         patch.dict("sys.modules", {"psutil": fake_psutil}):
        result = _sample_cpu_usage()

    assert result == 42.5


def test_sample_cpu_usage_returns_zero_without_psutil() -> None:
    def fake_getloadavg():
        raise OSError("not supported on Windows")

    with patch.object(os, "getloadavg", fake_getloadavg, create=True), \
         patch.dict("sys.modules", {"psutil": None}):
        result = _sample_cpu_usage()

    assert result == 0.0


def test_sample_gpu_usage_nvml_returns_value_when_pynvml_available() -> None:
    fake_pynvml = types.ModuleType("pynvml")
    fake_pynvml.nvmlInit = lambda: None
    fake_handle = MagicMock()
    fake_pynvml.nvmlDeviceGetHandleByIndex = lambda idx: fake_handle
    fake_util = MagicMock()
    fake_util.gpu = 55.0
    fake_pynvml.nvmlDeviceGetUtilizationRates = lambda h: fake_util

    with patch.dict("sys.modules", {"pynvml": fake_pynvml}):
        result = _sample_gpu_usage_nvml()

    assert result == 55.0


def test_sample_gpu_usage_nvml_returns_none_without_pynvml() -> None:
    with patch.dict("sys.modules", {"pynvml": None}):
        result = _sample_gpu_usage_nvml()

    assert result is None


def test_sample_gpu_usage_prefers_nvml_over_cli() -> None:
    fake_pynvml = types.ModuleType("pynvml")
    fake_pynvml.nvmlInit = lambda: None
    fake_handle = MagicMock()
    fake_pynvml.nvmlDeviceGetHandleByIndex = lambda idx: fake_handle
    fake_util = MagicMock()
    fake_util.gpu = 30.0
    fake_pynvml.nvmlDeviceGetUtilizationRates = lambda h: fake_util

    with patch.dict("sys.modules", {"pynvml": fake_pynvml}):
        result = _sample_gpu_usage()

    assert result == 30.0
