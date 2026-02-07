"""向量记忆库 - ChromaDB存储长期记忆

重构说明：
- VectorMemory 类：支持依赖注入，可指定 ChromaDB 目录
- 全局实例：向后兼容层
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

log = logging.getLogger(__name__)

# 默认 ChromaDB 目录（向后兼容）
CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma"


class VectorMemory:
    """向量记忆库管理"""

    def __init__(self, chroma_dir: Path = None):
        """
        初始化向量记忆库

        Args:
            chroma_dir: ChromaDB 存储目录，默认为 data/chroma
        """
        self.chroma_dir = chroma_dir or CHROMA_DIR
        self._client = None
        self._collection = None

    def _ensure_initialized(self):
        """延迟初始化ChromaDB"""
        if self._client is None:
            try:
                import chromadb
                self.chroma_dir.mkdir(parents=True, exist_ok=True)
                self._client = chromadb.PersistentClient(path=str(self.chroma_dir))
                self._collection = self._client.get_or_create_collection(
                    name="memories",
                    metadata={"hnsw:space": "cosine"}
                )
                log.info(f"ChromaDB初始化完成: {self.chroma_dir}")
            except ImportError:
                log.warning("chromadb未安装，向量记忆功能不可用")
                raise
            except Exception as e:
                log.error(f"ChromaDB初始化失败: {e}")
                raise

    def add(self, text: str, metadata: Optional[Dict] = None) -> str:
        """添加记忆，返回ID"""
        self._ensure_initialized()

        memory_id = str(uuid.uuid4())[:8]
        meta = metadata or {}
        meta["created_at"] = datetime.now().isoformat()

        self._collection.add(
            documents=[text],
            metadatas=[meta],
            ids=[memory_id]
        )
        log.info(f"添加向量记忆 [{memory_id}]: {text[:50]}...")
        return memory_id

    def search(self, query: str, n: int = 5) -> List[Dict[str, Any]]:
        """语义搜索记忆"""
        self._ensure_initialized()

        results = self._collection.query(
            query_texts=[query],
            n_results=n
        )

        memories = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                memory = {
                    "id": results["ids"][0][i] if results["ids"] else None,
                    "text": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results.get("distances") else None
                }
                memories.append(memory)

        return memories

    def delete(self, memory_id: str):
        """删除记忆"""
        self._ensure_initialized()
        self._collection.delete(ids=[memory_id])
        log.info(f"删除向量记忆: {memory_id}")

    def count(self) -> int:
        """获取记忆数量"""
        self._ensure_initialized()
        return self._collection.count()

    def get_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取所有记忆"""
        self._ensure_initialized()
        results = self._collection.get(limit=limit)

        memories = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"]):
                memory = {
                    "id": results["ids"][i] if results["ids"] else None,
                    "text": doc,
                    "metadata": results["metadatas"][i] if results["metadatas"] else {}
                }
                memories.append(memory)

        return memories


# 全局实例（向后兼容，延迟初始化）
vector_memory = VectorMemory()
