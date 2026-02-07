"""截图服务 - 从 app.py 提取的截图采集逻辑

职责：
- 截图采集
- 像素差异检测
- 截图保存
"""
import time
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, TYPE_CHECKING

import numpy as np
from PIL import ImageGrab, Image

import config
from utils.similarity import compute_phash
from utils.window import get_active_window

if TYPE_CHECKING:
    from db import Database

log = logging.getLogger(__name__)


class CaptureService:
    """截图服务"""

    def __init__(self, database: "Database" = None,
                 screenshot_dir: Path = None):
        """
        初始化截图服务

        Args:
            database: 数据库实例，默认使用全局模块函数
            screenshot_dir: 截图保存目录，默认从 config 读取
        """
        self._database = database
        self._screenshot_dir = screenshot_dir
        self.running = False
        self.paused = False
        self.last_img: Optional[np.ndarray] = None
        self.last_capture_time: float = 0
        self.capture_count: int = 0
        self._thread: Optional[threading.Thread] = None

    @property
    def screenshot_dir(self) -> Path:
        """获取截图目录"""
        if self._screenshot_dir is not None:
            return self._screenshot_dir
        return Path(config.SCREENSHOT_DIR)

    def _add_screenshot(self, path: str, timestamp: datetime, phash: str = None,
                        window_title: str = None, process_name: str = None) -> int:
        """添加截图到数据库"""
        if self._database is not None:
            return self._database.add_screenshot(
                path, timestamp, phash, window_title, process_name
            )
        else:
            import db
            return db.add_screenshot(
                path, timestamp, phash, window_title, process_name
            )

    def get_screenshot_path(self) -> Path:
        """生成截图保存路径"""
        now = datetime.now()
        dir_path = self.screenshot_dir / now.strftime("%Y-%m-%d") / now.strftime("%H")
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path / f"{now.strftime('%H%M%S')}.jpg"

    def capture_screen(self) -> np.ndarray:
        """截取屏幕"""
        screenshot = ImageGrab.grab()
        return np.array(screenshot)

    def calculate_diff(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """计算两张图片的差异比例"""
        if img1.shape != img2.shape:
            return 1.0
        diff = np.abs(img1.astype(np.int16) - img2.astype(np.int16))
        changed_pixels = np.sum(diff > 10)
        total_pixels = img1.size
        return changed_pixels / total_pixels

    def save_screenshot(self, img: np.ndarray, path: Path,
                        window_info: dict = None):
        """保存截图并记录到数据库"""
        timestamp = datetime.now()
        jpeg_quality = config.get('JPEG_QUALITY', 85)
        Image.fromarray(img).save(path, "JPEG", quality=jpeg_quality)
        self.capture_count += 1

        window_str = ""
        if window_info and window_info.get('process_name'):
            window_str = f" [{window_info['process_name']}]"
        log.info(f"截图保存: {path.name}{window_str} (总计: {self.capture_count})")

        try:
            phash = compute_phash(path)
        except Exception as e:
            log.error(f"计算phash失败: {e}")
            phash = None

        try:
            self._add_screenshot(
                str(path), timestamp, phash,
                window_title=window_info.get('window_title') if window_info else None,
                process_name=window_info.get('process_name') if window_info else None
            )
        except Exception as e:
            log.error(f"数据库写入失败: {e}")

    def capture_loop(self):
        """截图主循环 - 支持配置热更新"""
        while self.running:
            try:
                if self.paused:
                    time.sleep(1)
                    continue

                current_img = self.capture_screen()
                current_time = time.time()

                # 从数据库读取配置（支持热更新）
                force_interval = config.get('FORCE_CAPTURE_INTERVAL', 300)
                min_interval = config.get('MIN_CAPTURE_INTERVAL', 10)
                change_threshold = config.get('CHANGE_THRESHOLD', 0.8)

                should_capture = False

                if self.last_img is None:
                    should_capture = True
                elif current_time - self.last_capture_time >= force_interval:
                    should_capture = True
                elif current_time - self.last_capture_time >= min_interval:
                    diff = self.calculate_diff(self.last_img, current_img)
                    if diff > change_threshold:
                        should_capture = True

                if should_capture:
                    path = self.get_screenshot_path()
                    window_info = get_active_window()
                    self.save_screenshot(current_img, path, window_info)
                    self.last_img = current_img
                    self.last_capture_time = current_time

                time.sleep(0.5)

            except Exception as e:
                log.error(f"截图错误: {e}")
                time.sleep(1)

    def start(self):
        """启动截图服务"""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self.capture_loop, daemon=True)
        self._thread.start()
        log.info("截图服务已启动")

    def stop(self):
        """停止截图服务"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)
        log.info("截图服务已停止")

    def pause(self):
        """暂停截图"""
        self.paused = True
        log.info("截图已暂停")

    def resume(self):
        """恢复截图"""
        self.paused = False
        log.info("截图已恢复")
