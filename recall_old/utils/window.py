"""活动窗口信息获取"""
import logging
from typing import Optional, Dict, Any

log = logging.getLogger(__name__)

try:
    import win32gui
    import win32process
    import psutil
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    log.warning("pywin32/psutil 未安装，无法获取活动窗口信息")


def get_active_window() -> Optional[Dict[str, Any]]:
    """获取当前活动窗口信息

    Returns:
        dict: {
            'window_title': 窗口标题,
            'process_name': 进程名,
            'exe_path': 可执行文件路径
        }
        或 None（获取失败时）
    """
    if not HAS_WIN32:
        return None

    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None

        window_title = win32gui.GetWindowText(hwnd)

        # 获取进程信息
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            proc = psutil.Process(pid)
            process_name = proc.name()
            exe_path = proc.exe()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            process_name = None
            exe_path = None

        return {
            'window_title': window_title,
            'process_name': process_name,
            'exe_path': exe_path
        }
    except Exception as e:
        log.debug(f"获取活动窗口失败: {e}")
        return None
