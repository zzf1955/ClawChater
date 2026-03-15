from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from recall.db.setting import get_setting
from recall.services.core.events import ResourceAvailableEvent
from recall.services.monitor.utils import read_setting


@dataclass(slots=True)
class ResourceSnapshot:
    cpu_usage: float
    gpu_usage: float
    cpu_threshold: float
    gpu_threshold: float


UsageSampler = Callable[[], float]


def _parse_threshold(raw_value: str | None, default_value: float) -> float:
    if raw_value is None:
        return default_value
    try:
        return float(raw_value)
    except ValueError:
        return default_value


def _sample_cpu_usage() -> float:
    cpu_count = os.cpu_count() or 1
    try:
        one_minute_load = os.getloadavg()[0]
    except OSError:
        try:
            import psutil
            return psutil.cpu_percent(interval=0.5)
        except ImportError:
            return 0.0
    usage = (one_minute_load / cpu_count) * 100
    return max(0.0, min(100.0, usage))


def _sample_gpu_usage_nvml() -> float | None:
    try:
        import pynvml
    except ImportError:
        return None
    try:
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        return float(util.gpu)
    except Exception:
        return None


def _sample_gpu_usage_cli() -> float:
    popen_kwargs: dict = {}
    if sys.platform == "win32":
        popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    try:
        proc = subprocess.Popen(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            **popen_kwargs,
        )
        try:
            output, _ = proc.communicate(timeout=3.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                proc.communicate(timeout=2.0)
            except Exception:
                pass
            return 0.0
    except FileNotFoundError:
        return 0.0
    except Exception:
        return 0.0

    values: list[float] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            values.append(float(line))
        except ValueError:
            continue
    return max(values) if values else 0.0


def _sample_gpu_usage() -> float:
    nvml_result = _sample_gpu_usage_nvml()
    if nvml_result is not None:
        return nvml_result
    return _sample_gpu_usage_cli()


class ResourceMonitor:
    def __init__(
        self,
        event_bus,
        interval_seconds: float = 5.0,
        *,
        db_path: Path | None = None,
        cpu_threshold: float = 80.0,
        gpu_threshold: float = 70.0,
        cpu_usage_sampler: UsageSampler = _sample_cpu_usage,
        gpu_usage_sampler: UsageSampler = _sample_gpu_usage,
    ) -> None:
        self._event_bus = event_bus
        self._interval_seconds = interval_seconds
        self._db_path = db_path
        self._cpu_threshold = cpu_threshold
        self._gpu_threshold = gpu_threshold
        self._cpu_usage_sampler = cpu_usage_sampler
        self._gpu_usage_sampler = gpu_usage_sampler
        self._logger = logging.getLogger(__name__)
        self._running = False
        self._sampling = False

    async def run(self) -> None:
        self._running = True
        self._logger.info("resource monitor started interval=%.2fs", self._interval_seconds)
        while self._running:
            await asyncio.sleep(self._interval_seconds)
            await self.check_and_publish_once()

    async def check_and_publish_once(self) -> bool:
        if self._sampling:
            self._logger.debug("resource sample already in progress, skipping")
            return False
        self._sampling = True
        try:
            snapshot = await asyncio.wait_for(
                asyncio.to_thread(self.sample_once),
                timeout=10.0,
            )
        except asyncio.TimeoutError:
            self._logger.warning("resource sample timed out after 10s, skipping cycle")
            return False
        finally:
            self._sampling = False
        if not self._is_resource_available(snapshot):
            self._logger.info(
                "resource_available skipped: busy cpu=%.2f/%.2f gpu=%.2f/%.2f",
                snapshot.cpu_usage,
                snapshot.cpu_threshold,
                snapshot.gpu_usage,
                snapshot.gpu_threshold,
            )
            return False

        await self._event_bus.publish(
            ResourceAvailableEvent(
                payload={
                    "cpu_usage": round(snapshot.cpu_usage, 2),
                    "gpu_usage": round(snapshot.gpu_usage, 2),
                    "cpu_threshold": snapshot.cpu_threshold,
                    "gpu_threshold": snapshot.gpu_threshold,
                }
            )
        )
        self._logger.info(
            "resource_available published cpu=%.2f gpu=%.2f",
            snapshot.cpu_usage,
            snapshot.gpu_usage,
        )
        return True

    def sample_once(self) -> ResourceSnapshot:
        cpu_threshold = self._read_threshold("CPU_USAGE_THRESHOLD", self._cpu_threshold)
        gpu_threshold = self._read_threshold("GPU_USAGE_THRESHOLD", self._gpu_threshold)
        cpu_usage = self._cpu_usage_sampler()
        gpu_usage = self._gpu_usage_sampler()
        return ResourceSnapshot(
            cpu_usage=cpu_usage,
            gpu_usage=gpu_usage,
            cpu_threshold=cpu_threshold,
            gpu_threshold=gpu_threshold,
        )

    def _read_threshold(self, key: str, default_value: float) -> float:
        raw_value = read_setting(key, db_path=self._db_path)
        return _parse_threshold(raw_value, default_value)

    def _is_resource_available(self, snapshot: ResourceSnapshot) -> bool:
        is_available = (
            snapshot.cpu_usage <= snapshot.cpu_threshold
            and snapshot.gpu_usage <= snapshot.gpu_threshold
        )
        self._logger.debug(
            "resource sample cpu=%.2f gpu=%.2f thresholds cpu=%.2f gpu=%.2f available=%s",
            snapshot.cpu_usage,
            snapshot.gpu_usage,
            snapshot.cpu_threshold,
            snapshot.gpu_threshold,
            is_available,
        )
        return is_available

    def stop(self) -> None:
        self._running = False
        self._logger.info("resource monitor stopped")
