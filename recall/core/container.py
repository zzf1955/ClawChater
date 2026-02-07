"""依赖注入容器 - 管理所有服务实例的生命周期"""
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from db import Database
    from message_queue import MessageQueue
    from llm import LLMService
    from memory.text_memory import TextMemory
    from memory.vector_memory import VectorMemory
    from memory.summarizer import ActivitySummarizer
    from memory.extractor import MemoryExtractor


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

    @property
    def text_memory(self) -> "TextMemory":
        """获取文本记忆实例"""
        if 'text_memory' not in self._instances:
            from memory.text_memory import TextMemory
            filepath = self.config.data_dir / "memory.md"
            self._instances['text_memory'] = TextMemory(filepath)
        return self._instances['text_memory']

    @property
    def vector_memory(self) -> "VectorMemory":
        """获取向量记忆实例"""
        if 'vector_memory' not in self._instances:
            from memory.vector_memory import VectorMemory
            chroma_dir = self.config.data_dir / "chroma"
            self._instances['vector_memory'] = VectorMemory(chroma_dir)
        return self._instances['vector_memory']

    @property
    def summarizer(self) -> "ActivitySummarizer":
        """获取活动总结器实例"""
        if 'summarizer' not in self._instances:
            from memory.summarizer import ActivitySummarizer
            summaries_dir = self.config.data_dir / "summaries" / "hourly"
            self._instances['summarizer'] = ActivitySummarizer(summaries_dir)
        return self._instances['summarizer']

    @property
    def extractor(self) -> "MemoryExtractor":
        """获取记忆提取器实例"""
        if 'extractor' not in self._instances:
            from memory.extractor import MemoryExtractor
            self._instances['extractor'] = MemoryExtractor(
                text_memory=self.text_memory,
                vector_memory=self.vector_memory
            )
        return self._instances['extractor']

    @property
    def message_queue(self) -> "MessageQueue":
        """获取消息队列实例"""
        if 'message_queue' not in self._instances:
            from message_queue import MessageQueue
            self._instances['message_queue'] = MessageQueue(self.database)
        return self._instances['message_queue']

    @property
    def llm_service(self) -> "LLMService":
        """获取LLM服务实例"""
        if 'llm_service' not in self._instances:
            from llm import LLMService
            self._instances['llm_service'] = LLMService(
                text_memory=self.text_memory,
                vector_memory=self.vector_memory,
                summarizer=self.summarizer
            )
        return self._instances['llm_service']

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
