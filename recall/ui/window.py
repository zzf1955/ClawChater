"""窗口管理 - 从 app.py 提取的 WebView 窗口逻辑

职责：
- WebView 窗口创建
- 窗口事件处理
"""
import logging
from typing import Optional, Callable

import webview

log = logging.getLogger(__name__)


class WindowManager:
    """WebView 窗口管理器"""

    def __init__(self, title: str = "Recall", url: str = None,
                 width: int = 1200, height: int = 800):
        """
        初始化窗口管理器

        Args:
            title: 窗口标题
            url: 要加载的 URL
            width: 窗口宽度
            height: 窗口高度
        """
        self.title = title
        self.url = url or "http://127.0.0.1:5000"
        self.width = width
        self.height = height
        self.window: Optional[webview.Window] = None

        # 回调函数
        self.on_closing: Optional[Callable] = None

    def _handle_closing(self):
        """处理窗口关闭事件 - 隐藏而非关闭"""
        if self.on_closing:
            return self.on_closing()
        # 默认行为：隐藏窗口
        if self.window:
            self.window.hide()
        return False  # 返回 False 阻止窗口真正关闭

    def create(self):
        """创建窗口"""
        self.window = webview.create_window(
            self.title,
            self.url,
            width=self.width,
            height=self.height,
            min_size=(800, 600)
        )
        # 绑定窗口关闭事件
        self.window.events.closing += self._handle_closing
        log.info(f"窗口已创建: {self.title}")

    def show(self):
        """显示窗口"""
        if self.window:
            self.window.show()
            self.window.restore()

    def hide(self):
        """隐藏窗口"""
        if self.window:
            self.window.hide()

    def destroy(self):
        """销毁窗口"""
        if self.window:
            self.window.destroy()
            log.info("窗口已销毁")

    @staticmethod
    def start():
        """启动 WebView 事件循环（阻塞）"""
        webview.start()
