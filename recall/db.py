"""数据库模块 - SQLite存储截图元数据

重构说明：
- Database 类：支持依赖注入，可指定数据库路径
- 模块级函数：向后兼容层，使用默认数据库实例
"""
import sqlite3
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

log = logging.getLogger(__name__)

# 默认数据库路径（向后兼容）
DB_PATH = Path(__file__).parent / "data" / "recall.db"


class Database:
    """数据库操作类 - 支持依赖注入"""

    def __init__(self, db_path: Path = None):
        """
        初始化数据库

        Args:
            db_path: 数据库文件路径，默认为 data/recall.db
        """
        self.db_path = db_path or DB_PATH

    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS screenshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    timestamp DATETIME NOT NULL,
                    phash TEXT,
                    ocr_text TEXT,
                    ocr_status TEXT DEFAULT 'pending',
                    group_id INTEGER,
                    window_title TEXT,
                    process_name TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time DATETIME,
                    end_time DATETIME,
                    screenshot_count INTEGER DEFAULT 0,
                    merged_text TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_screenshots_timestamp ON screenshots(timestamp);
                CREATE INDEX IF NOT EXISTS idx_screenshots_ocr_status ON screenshots(ocr_status);
                CREATE INDEX IF NOT EXISTS idx_screenshots_group_id ON screenshots(group_id);
                CREATE INDEX IF NOT EXISTS idx_screenshots_phash ON screenshots(phash);

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

            log.info(f"数据库初始化完成: {self.db_path}")

    # ============ 截图相关方法 ============

    def add_screenshot(self, path: str, timestamp: datetime, phash: str = None,
                       window_title: str = None, process_name: str = None) -> int:
        """添加截图记录，返回ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO screenshots (path, timestamp, phash, window_title, process_name)
                   VALUES (?, ?, ?, ?, ?)""",
                (path, timestamp.isoformat(), phash, window_title, process_name)
            )
            return cursor.lastrowid

    def add_screenshot_with_ocr(self, path: str, timestamp: datetime, phash: str = None,
                                ocr_text: str = None, ocr_status: str = 'pending',
                                window_title: str = None, process_name: str = None) -> int:
        """添加截图记录(包含OCR结果)"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO screenshots
                (path, timestamp, phash, ocr_text, ocr_status, window_title, process_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (path, timestamp.isoformat(), phash, ocr_text, ocr_status,
                  window_title, process_name))
            return cursor.lastrowid

    def screenshot_exists(self, path: str) -> bool:
        """检查截图是否已存在"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM screenshots WHERE path = ?", (path,)
            ).fetchone()
            return row is not None

    def get_pending_ocr(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取待OCR的截图"""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT id, path FROM screenshots WHERE ocr_status = 'pending' ORDER BY id LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(row) for row in rows]

    def update_ocr_result(self, screenshot_id: int, ocr_text: str, status: str = 'done'):
        """更新OCR结果"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE screenshots SET ocr_text = ?, ocr_status = ? WHERE id = ?",
                (ocr_text, status, screenshot_id)
            )

    def get_recent_phash(self, hours: int = 1) -> List[Dict[str, Any]]:
        """获取最近N小时的截图哈希"""
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT id, path, phash, timestamp, group_id
                FROM screenshots
                WHERE timestamp > datetime('now', ? || ' hours')
                AND phash IS NOT NULL
                ORDER BY timestamp DESC
            """, (f"-{hours}",)).fetchall()
            return [dict(row) for row in rows]

    def update_group(self, screenshot_id: int, group_id: int):
        """更新截图的分组"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE screenshots SET group_id = ? WHERE id = ?",
                (group_id, screenshot_id)
            )

    def create_group(self, start_time: datetime, end_time: datetime) -> int:
        """创建新分组"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO groups (start_time, end_time) VALUES (?, ?)",
                (start_time.isoformat(), end_time.isoformat())
            )
            return cursor.lastrowid

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM screenshots").fetchone()[0]
            pending = conn.execute(
                "SELECT COUNT(*) FROM screenshots WHERE ocr_status = 'pending'"
            ).fetchone()[0]
            done = conn.execute(
                "SELECT COUNT(*) FROM screenshots WHERE ocr_status = 'done'"
            ).fetchone()[0]
            groups = conn.execute("SELECT COUNT(*) FROM groups").fetchone()[0]
            return {
                "total_screenshots": total,
                "pending_ocr": pending,
                "done_ocr": done,
                "groups": groups
            }

    # ============ 配置存储相关方法 ============

    def get_setting(self, key: str, default=None):
        """获取单个配置值"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
            if row:
                return json.loads(row['value'])
            return default

    def set_setting(self, key: str, value):
        """设置单个配置值"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO settings (key, value, updated_at)
                VALUES (?, ?, datetime('now'))
                ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = datetime('now')
            """, (key, json.dumps(value), json.dumps(value)))

    def get_all_settings(self) -> Dict[str, Any]:
        """获取所有配置"""
        with self.get_connection() as conn:
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
            return {row['key']: json.loads(row['value']) for row in rows}

    def set_all_settings(self, settings: Dict[str, Any]):
        """批量设置配置"""
        with self.get_connection() as conn:
            for key, value in settings.items():
                conn.execute("""
                    INSERT INTO settings (key, value, updated_at)
                    VALUES (?, ?, datetime('now'))
                    ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = datetime('now')
                """, (key, json.dumps(value), json.dumps(value)))


# ============ 向后兼容层 ============
# 以下函数使用默认数据库实例，保持与旧代码的兼容性

_default_db: Optional[Database] = None


def _get_db() -> Database:
    """获取默认数据库实例"""
    global _default_db
    if _default_db is None:
        _default_db = Database()
    return _default_db


@contextmanager
def get_connection():
    """获取数据库连接（向后兼容）"""
    with _get_db().get_connection() as conn:
        yield conn


def init_db():
    """初始化数据库表（向后兼容）"""
    return _get_db().init_db()


def add_screenshot(path: str, timestamp: datetime, phash: str = None,
                   window_title: str = None, process_name: str = None) -> int:
    """添加截图记录（向后兼容）"""
    return _get_db().add_screenshot(path, timestamp, phash, window_title, process_name)


def add_screenshot_with_ocr(path: str, timestamp: datetime, phash: str = None,
                            ocr_text: str = None, ocr_status: str = 'pending',
                            window_title: str = None, process_name: str = None) -> int:
    """添加截图记录(包含OCR结果)（向后兼容）"""
    return _get_db().add_screenshot_with_ocr(
        path, timestamp, phash, ocr_text, ocr_status, window_title, process_name
    )


def screenshot_exists(path: str) -> bool:
    """检查截图是否已存在（向后兼容）"""
    return _get_db().screenshot_exists(path)


def get_pending_ocr(limit: int = 10) -> List[Dict[str, Any]]:
    """获取待OCR的截图（向后兼容）"""
    return _get_db().get_pending_ocr(limit)


def update_ocr_result(screenshot_id: int, ocr_text: str, status: str = 'done'):
    """更新OCR结果（向后兼容）"""
    return _get_db().update_ocr_result(screenshot_id, ocr_text, status)


def get_recent_phash(hours: int = 1) -> List[Dict[str, Any]]:
    """获取最近N小时的截图哈希（向后兼容）"""
    return _get_db().get_recent_phash(hours)


def update_group(screenshot_id: int, group_id: int):
    """更新截图的分组（向后兼容）"""
    return _get_db().update_group(screenshot_id, group_id)


def create_group(start_time: datetime, end_time: datetime) -> int:
    """创建新分组（向后兼容）"""
    return _get_db().create_group(start_time, end_time)


def get_stats() -> Dict[str, Any]:
    """获取统计信息（向后兼容）"""
    return _get_db().get_stats()


def init_settings_table():
    """初始化配置表（向后兼容，已在 init_db 中包含）"""
    pass


def get_setting(key: str, default=None):
    """获取单个配置值（向后兼容）"""
    return _get_db().get_setting(key, default)


def set_setting(key: str, value):
    """设置单个配置值（向后兼容）"""
    return _get_db().set_setting(key, value)


def get_all_settings() -> Dict[str, Any]:
    """获取所有配置（向后兼容）"""
    return _get_db().get_all_settings()


def set_all_settings(settings: Dict[str, Any]):
    """批量设置配置（向后兼容）"""
    return _get_db().set_all_settings(settings)
