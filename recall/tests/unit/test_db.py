"""数据库模块单元测试"""
import pytest
from datetime import datetime


class TestDatabaseInit:
    """数据库初始化测试"""

    def test_init_db_creates_tables(self, initialized_db):
        """测试 init_db 创建所有必要的表"""
        with initialized_db.get_connection() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t['name'] for t in tables]

            assert 'screenshots' in table_names
            assert 'groups' in table_names
            assert 'settings' in table_names


class TestScreenshotOperations:
    """截图操作测试"""

    def test_add_screenshot(self, initialized_db):
        """测试添加截图"""
        screenshot_id = initialized_db.add_screenshot(
            path="test/path.jpg",
            timestamp=datetime.now(),
            phash="abc123",
            window_title="Test",
            process_name="test.exe"
        )
        assert screenshot_id > 0

    def test_screenshot_exists(self, initialized_db):
        """测试截图存在检查"""
        initialized_db.add_screenshot("unique/path.jpg", datetime.now())

        assert initialized_db.screenshot_exists("unique/path.jpg") is True
        assert initialized_db.screenshot_exists("nonexistent.jpg") is False

    def test_get_pending_ocr(self, initialized_db):
        """测试获取待 OCR 截图"""
        initialized_db.add_screenshot("pending1.jpg", datetime.now())
        initialized_db.add_screenshot("pending2.jpg", datetime.now())

        pending = initialized_db.get_pending_ocr(limit=10)
        assert len(pending) == 2
        assert all(p['path'].startswith('pending') for p in pending)

    def test_update_ocr_result(self, initialized_db):
        """测试更新 OCR 结果"""
        sid = initialized_db.add_screenshot("ocr_test.jpg", datetime.now())
        initialized_db.update_ocr_result(sid, "识别的文字", "done")

        # 验证更新
        with initialized_db.get_connection() as conn:
            row = conn.execute(
                "SELECT ocr_text, ocr_status FROM screenshots WHERE id = ?",
                (sid,)
            ).fetchone()
            assert row['ocr_text'] == "识别的文字"
            assert row['ocr_status'] == "done"


class TestSettingsOperations:
    """配置存储测试"""

    def test_set_and_get_setting(self, initialized_db):
        """测试设置和获取配置"""
        initialized_db.set_setting("TEST_KEY", 123)
        assert initialized_db.get_setting("TEST_KEY") == 123

    def test_get_setting_default(self, initialized_db):
        """测试获取不存在的配置返回默认值"""
        assert initialized_db.get_setting("NONEXISTENT", default="default") == "default"

    def test_set_all_settings(self, initialized_db):
        """测试批量设置配置"""
        settings = {"KEY1": "value1", "KEY2": 42, "KEY3": True}
        initialized_db.set_all_settings(settings)

        result = initialized_db.get_all_settings()
        assert result["KEY1"] == "value1"
        assert result["KEY2"] == 42
        assert result["KEY3"] is True
