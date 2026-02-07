"""抽象接口定义 - 使用 Protocol 实现结构化子类型"""
from typing import Protocol, Optional, Dict, List, Any, runtime_checkable
from datetime import datetime
from pathlib import Path


@runtime_checkable
class IDatabase(Protocol):
    """数据库接口"""

    def init_db(self) -> None:
        """初始化数据库表"""
        ...

    def add_screenshot(self, path: str, timestamp: datetime,
                       phash: str = None, window_title: str = None,
                       process_name: str = None) -> int:
        """添加截图记录，返回ID"""
        ...

    def screenshot_exists(self, path: str) -> bool:
        """检查截图是否已存在"""
        ...

    def get_pending_ocr(self, limit: int = 10) -> List[Dict]:
        """获取待OCR处理的截图"""
        ...

    def update_ocr_result(self, screenshot_id: int, ocr_text: str,
                          status: str = 'done') -> None:
        """更新OCR结果"""
        ...

    def get_setting(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        ...

    def set_setting(self, key: str, value: Any) -> None:
        """设置配置项"""
        ...


@runtime_checkable
class IConfig(Protocol):
    """配置接口"""

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        ...

    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        ...

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        ...
