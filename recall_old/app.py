"""Recall 应用核心 - 简化版 (纯 Web UI)

重构说明：
- 移除了 PyWebView 桌面窗口和系统托盘
- 只保留后台服务 + Flask Web 服务器
- 通过浏览器访问 http://127.0.0.1:5000
"""
import os
import sys
import atexit
import logging
import threading
from pathlib import Path

import config
import db
from ocr_worker import get_worker
from core.capture import CaptureService

WEB_PORT = 5000

# 路径配置
ROOT_DIR = Path(__file__).parent
LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "recall.log"
PID_FILE = LOG_DIR / "recall.pid"

# 日志配置
_log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
_file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
_file_handler.setFormatter(_log_formatter)
_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(_log_formatter)

_root = logging.getLogger()
_root.setLevel(logging.INFO)
_root.handlers.clear()
_root.addHandler(_file_handler)
_root.addHandler(_stream_handler)
log = logging.getLogger(__name__)


class RecallApp:
    """Recall 应用主类 - 简化版"""

    def __init__(self):
        # 服务实例
        self.capture_service: CaptureService = None
        self.ocr_worker = None

        # 线程
        self.web_thread = None

        # 状态
        self.running = True

    def setup(self):
        """初始化应用"""
        # 写入PID
        PID_FILE.write_text(str(os.getpid()))
        atexit.register(lambda: PID_FILE.unlink() if PID_FILE.exists() else None)

        log.info("=" * 50)
        log.info("Recall 启动")
        log.info(f"PID: {os.getpid()}")

        # 初始化数据库
        db.init_db()

        # 初始化默认配置到数据库
        config.init_defaults()

        # 初始化服务
        self._init_services()

        # 启动后台服务
        self._start_background_services()

    def _init_services(self):
        """初始化各个服务"""
        # 截图服务
        self.capture_service = CaptureService()

    def _start_background_services(self):
        """启动后台服务"""
        # 启动OCR Worker
        self.ocr_worker = get_worker()
        self.ocr_worker.start()

        # 启动截图服务
        self.capture_service.start()

        # 启动Web服务器
        self.web_thread = threading.Thread(target=self._start_web_server, daemon=True)
        self.web_thread.start()
        log.info(f"Web UI: http://127.0.0.1:{WEB_PORT}")

    def _start_web_server(self):
        """启动Web服务器"""
        try:
            from web.app import app
            import logging as flask_logging
            flask_logging.getLogger('werkzeug').setLevel(flask_logging.ERROR)
            log.info(f"Web 服务器启动中 (port={WEB_PORT})...")
            app.run(host='127.0.0.1', port=WEB_PORT, debug=False, use_reloader=False)
        except Exception as e:
            log.error(f"Web 服务器启动失败: {e}", exc_info=True)

    def shutdown(self):
        """关闭应用"""
        log.info("Recall 关闭中...")
        self.running = False

        # 停止各服务
        if self.capture_service:
            self.capture_service.stop()
        if self.ocr_worker:
            self.ocr_worker.stop()

        log.info("Recall 已关闭")

    def run(self):
        """运行应用 (阻塞)"""
        self.setup()

        # 等待 Web 服务器启动
        import time
        time.sleep(1)

        print(f"\n{'='*50}")
        print(f"Recall 已启动")
        print(f"访问地址: http://127.0.0.1:{WEB_PORT}")
        print(f"按 Ctrl+C 退出")
        print(f"{'='*50}\n")

        # 保持主线程运行
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n收到退出信号...")
            self.shutdown()
