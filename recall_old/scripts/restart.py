"""启动/重启 Recall 服务"""
import os
import sys
import subprocess
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
LOG_DIR = ROOT_DIR / "logs"
PID_FILE = LOG_DIR / "recall.pid"
MAIN_PY = ROOT_DIR / "main.py"
CONDA_ENV = "recall"


def is_process_running(pid):
    """检查进程是否在运行 (Windows 兼容)"""
    try:
        result = subprocess.run(
            ["tasklist", "/fi", f"PID eq {pid}"],
            capture_output=True,
            text=True,
        )
        return str(pid) in result.stdout
    except Exception:
        return False


def get_running_pid():
    """获取正在运行的进程 PID"""
    if not PID_FILE.exists():
        return None
    try:
        pid = int(PID_FILE.read_text().strip())
        if is_process_running(pid):
            return pid
        return None
    except ValueError:
        return None


def kill_process(pid):
    """终止进程"""
    try:
        subprocess.run(["taskkill", "/pid", str(pid), "/f"], capture_output=True)
        time.sleep(1)
        return True
    except Exception:
        return False


def start_service():
    """启动服务"""
    cmd = f'conda run -n {CONDA_ENV} python "{MAIN_PY}"'

    subprocess.Popen(
        cmd,
        shell=True,
        cwd=ROOT_DIR,
        creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main():
    print("[Recall] 检查现有进程...")

    pid = get_running_pid()
    if pid:
        print(f"[Recall] 发现运行中的进程 PID: {pid}")
        if kill_process(pid):
            print("[Recall] 已终止旧进程")
        if PID_FILE.exists():
            PID_FILE.unlink()
        time.sleep(1)
    else:
        print("[Recall] 没有运行中的进程")

    print("[Recall] 启动服务...")
    start_service()

    # 等待 PID 文件生成
    for _ in range(10):
        time.sleep(0.5)
        if PID_FILE.exists():
            new_pid = PID_FILE.read_text().strip()
            print(f"[Recall] 服务已启动，PID: {new_pid}")
            return

    print("[Recall] 服务已启动（等待 PID 超时）")


if __name__ == "__main__":
    main()
