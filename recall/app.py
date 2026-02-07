"""Recall 应用核心 - 整合托盘和GUI (PyWebView + pystray 版本)

重构说明：
- RecallApp 类：协调者角色，组合各个服务
- 业务逻辑已提取到 core/capture.py, ui/tray.py, ui/window.py
"""
import os
import sys
import time
import atexit
import logging
import threading
from pathlib import Path

import config
import db
from ocr_worker import get_worker
from core.capture import CaptureService
from ui.tray import TrayManager
from ui.window import WindowManager

WEB_PORT = 5000

# 路径配置
ROOT_DIR = Path(__file__).parent
LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "recall.log"
PID_FILE = LOG_DIR / "recall.pid"
ICON_FILE = ROOT_DIR / "assets" / "icon.png"

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8'),
    ]
)
log = logging.getLogger(__name__)


class RecallApp:
    """Recall 应用主类 - 协调者"""

    def __init__(self):
        # 服务实例
        self.capture_service: CaptureService = None
        self.tray_manager: TrayManager = None
        self.window_manager: WindowManager = None
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

        # 托盘管理器
        self.tray_manager = TrayManager(icon_file=ICON_FILE)
        self.tray_manager.on_open_window = self._on_open_window
        self.tray_manager.on_toggle_pause = self._on_toggle_pause
        self.tray_manager.on_quit = self._on_quit

        # 窗口管理器
        self.window_manager = WindowManager(
            title="Recall",
            url=f"http://127.0.0.1:{WEB_PORT}",
            width=1200,
            height=800
        )

    def _on_open_window(self):
        """打开窗口回调"""
        self.window_manager.show()

    def _on_toggle_pause(self, paused: bool):
        """切换暂停状态回调"""
        if paused:
            self.capture_service.pause()
        else:
            self.capture_service.resume()

    def _on_quit(self):
        """退出应用回调"""
        log.info("Recall 退出")
        self.running = False

        # 停止各服务
        if self.capture_service:
            self.capture_service.stop()
        if self.ocr_worker:
            self.ocr_worker.stop()
        if self.window_manager:
            self.window_manager.destroy()

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
        log.info(f"Web API: http://127.0.0.1:{WEB_PORT}")

    def _start_web_server(self):
        """启动Web服务器"""
        from web.app import app
        import logging as flask_logging
        flask_logging.getLogger('werkzeug').setLevel(flask_logging.ERROR)
        app.run(host='127.0.0.1', port=WEB_PORT, debug=False, use_reloader=False)

    def run(self):
        """运行应用"""
        self.setup()

        # 设置托盘
        self.tray_manager.setup()

        # 等待 Flask 启动
        time.sleep(1)

        # 创建窗口
        self.window_manager.create()

        # 在单独线程运行托盘
        tray_thread = threading.Thread(target=self.tray_manager.run, daemon=False)
        tray_thread.start()

        # 启动 webview (阻塞，但窗口关闭时只是隐藏)
        WindowManager.start()

        # webview.start() 返回说明所有窗口都被销毁了
        # 等待托盘线程结束
        tray_thread.join()
