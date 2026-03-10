"""依赖注入容器 - 管理所有服务实例的生命周期"""
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from db import Database


@dataclass
class AppConfig:
    """应用配置"""
    data_dir: Path = field(
        default_factory=lambda: Path(__file__).parent.parent / "data"
    )
    screenshot_dir: Path = field(
        default_factory=lambda: Path(__file__).parent.parent / "screenshots"
    )
    web_port: int = 5000


class Container:
    """依赖注入容器 - 懒加载所有服务实例"""

    def __init__(self, config: AppConfig = None):
        self.config = config or AppConfig()
        self._instances: dict = {}

    @property
    def database(self) -> "Database":
        """获取数据库实例"""
        if 'database' not in self._instances:
            from db import Database
            db_path = self.config.data_dir / "recall.db"
            self._instances['database'] = Database(db_path)
        return self._instances['database']

    def reset(self):
        """重置所有实例（用于测试）"""
        self._instances.clear()


# 全局容器实例
_container: Optional[Container] = None


def get_container() -> Container:
    """获取全局容器实例"""
    global _container
    if _container is None:
        _container = Container()
    return _container


def set_container(container: Container) -> None:
    """设置全局容器实例（用于测试）"""
    global _container
    _container = container


def reset_container() -> None:
    """重置全局容器（用于测试）"""
    global _container
    if _container is not None:
        _container.reset()
    _container = None
