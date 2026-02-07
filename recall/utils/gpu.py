"""GPU监控模块"""
import logging

log = logging.getLogger(__name__)

_nvml_initialized = False
_has_nvidia = False

def _init_nvml():
    """初始化NVML"""
    global _nvml_initialized, _has_nvidia
    if _nvml_initialized:
        return _has_nvidia

    _nvml_initialized = True
    try:
        import pynvml
        pynvml.nvmlInit()
        _has_nvidia = True
        log.info("NVML初始化成功")
    except Exception as e:
        _has_nvidia = False
        log.warning(f"NVML初始化失败: {e}")
    return _has_nvidia


def get_gpu_usage() -> float:
    """获取GPU使用率 (0-100)，无GPU返回0"""
    if not _init_nvml():
        return 0.0

    try:
        import pynvml
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        return float(util.gpu)
    except Exception as e:
        log.error(f"获取GPU使用率失败: {e}")
        return 0.0


def is_gpu_idle(threshold: float = 30.0) -> bool:
    """检查GPU是否空闲"""
    usage = get_gpu_usage()
    return usage < threshold
