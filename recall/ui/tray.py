"""托盘管理 - 从 app.py 提取的系统托盘逻辑

职责：
- 系统托盘图标
- 托盘菜单
- 托盘事件处理
"""
import logging
from pathlib import Path
from typing import Callable, Optional

from PIL import Image, ImageDraw, ImageFont
import pystray

log = logging.getLogger(__name__)

# 默认图标路径
DEFAULT_ICON_FILE = Path(__file__).parent.parent / "assets" / "icon.png"


class TrayManager:
    """系统托盘管理器"""

    def __init__(self, icon_file: Path = None):
        """
        初始化托盘管理器

        Args:
            icon_file: 图标文件路径
        """
        self.icon_file = icon_file or DEFAULT_ICON_FILE
        self.tray_icon: Optional[pystray.Icon] = None
        self.paused = False

        # 回调函数
        self.on_open_window: Optional[Callable] = None
        self.on_toggle_pause: Optional[Callable] = None
        self.on_quit: Optional[Callable] = None

    def create_icon_image(self, paused: bool = False) -> Image.Image:
        """创建托盘图标图像"""
        if self.icon_file.exists():
            img = Image.open(self.icon_file).convert('RGBA')
            img = img.resize((64, 64), Image.Resampling.LANCZOS)
            if paused:
                # 暂停时在右下角添加橙色圆点指示
                draw = ImageDraw.Draw(img)
                draw.ellipse([44, 44, 60, 60], fill=(255, 152, 0, 255))
            return img

        # 回退：动态生成图标
        size = 64
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        fill = (255, 152, 0, 255) if paused else (76, 175, 80, 255)
        draw.ellipse([4, 4, size-4, size-4], fill=fill)
        try:
            font = ImageFont.truetype("arial.ttf", 28)
        except:
            font = ImageFont.load_default()
        draw.text((size//2 - 8, size//2 - 14), "R",
                  fill=(255, 255, 255, 255), font=font)
        return img

    def _handle_open_window(self, icon=None, item=None):
        """处理打开窗口事件"""
        if self.on_open_window:
            self.on_open_window()

    def _handle_toggle_pause(self, icon=None, item=None):
        """处理切换暂停事件"""
        self.paused = not self.paused
        self.update_icon()
        if self.on_toggle_pause:
            self.on_toggle_pause(self.paused)

    def _handle_quit(self, icon=None, item=None):
        """处理退出事件"""
        if self.on_quit:
            self.on_quit()
        self.stop()

    def update_icon(self):
        """更新托盘图标状态"""
        if self.tray_icon:
            self.tray_icon.icon = self.create_icon_image(paused=self.paused)
            self.tray_icon.title = "Recall - 已暂停" if self.paused else "Recall - 运行中"

    def setup(self):
        """设置系统托盘"""
        menu = pystray.Menu(
            pystray.MenuItem("打开控制面板", self._handle_open_window, default=True),
            pystray.MenuItem(
                lambda item: "继续截图" if self.paused else "暂停截图",
                self._handle_toggle_pause
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self._handle_quit)
        )

        self.tray_icon = pystray.Icon(
            "Recall",
            self.create_icon_image(),
            "Recall - 运行中",
            menu
        )

    def run(self):
        """运行托盘（阻塞）"""
        if self.tray_icon:
            self.tray_icon.run()

    def stop(self):
        """停止托盘"""
        if self.tray_icon:
            self.tray_icon.stop()
            log.info("托盘已停止")
