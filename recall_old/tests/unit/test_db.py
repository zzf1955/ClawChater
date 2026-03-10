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


class TestSummaryOperations:
    """摘要操作测试"""

    def test_insert_summary(self, initialized_db):
        """测试插入摘要"""
        sid = initialized_db.insert_summary(
            start_time="2024-01-01T10:00:00",
            end_time="2024-01-01T10:30:00",
            summary="用户在写代码",
            activity_type="work"
        )
        assert sid > 0

    def test_get_summaries_empty(self, initialized_db):
        """测试空数据时返回空列表"""
        result = initialized_db.get_summaries(hours=24)
        assert result == []

    def test_get_summaries_returns_recent(self, initialized_db):
        """测试按时间范围查询摘要"""
        # 插入一条"最近"的摘要（用 datetime('now') 附近的时间）
        now = datetime.now()
        start = now.replace(minute=0, second=0).isoformat()
        end = now.isoformat()
        initialized_db.insert_summary(start, end, "最近的活动", "work")

        # 插入一条很久以前的摘要
        initialized_db.insert_summary(
            "2020-01-01T00:00:00", "2020-01-01T00:30:00",
            "很久以前的活动", "other"
        )

        result = initialized_db.get_summaries(hours=1)
        assert len(result) == 1
        assert result[0]['summary'] == "最近的活动"

    def test_get_latest_summary_empty(self, initialized_db):
        """测试空数据时 get_latest_summary 返回 None"""
        result = initialized_db.get_latest_summary()
        assert result is None

    def test_get_latest_summary(self, initialized_db):
        """测试获取最新摘要"""
        initialized_db.insert_summary(
            "2024-01-01T10:00:00", "2024-01-01T10:30:00",
            "第一条", "work"
        )
        initialized_db.insert_summary(
            "2024-01-01T11:00:00", "2024-01-01T11:30:00",
            "第二条", "entertainment"
        )

        result = initialized_db.get_latest_summary()
        assert result is not None
        assert result['summary'] == "第二条"
        assert result['activity_type'] == "entertainment"

    def test_insert_summary_without_activity_type(self, initialized_db):
        """测试不传 activity_type 时插入成功"""
        sid = initialized_db.insert_summary(
            "2024-01-01T10:00:00", "2024-01-01T10:30:00",
            "无分类摘要"
        )
        assert sid > 0
        result = initialized_db.get_latest_summary()
        assert result['activity_type'] is None

    def test_init_db_creates_summaries_table(self, initialized_db):
        """测试 init_db 创建 summaries 表"""
        with initialized_db.get_connection() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t['name'] for t in tables]
            assert 'summaries' in table_names

    def test_get_summary_by_id(self, initialized_db):
        """测试按 ID 获取单条总结"""
        sid = initialized_db.insert_summary(
            "2024-01-01T10:00:00", "2024-01-01T10:30:00",
            "测试摘要", "work"
        )
        result = initialized_db.get_summary_by_id(sid)
        assert result is not None
        assert result['id'] == sid
        assert result['summary'] == "测试摘要"

    def test_get_summary_by_id_not_found(self, initialized_db):
        """测试获取不存在的总结返回 None"""
        result = initialized_db.get_summary_by_id(99999)
        assert result is None

    def test_get_summaries_by_time_range(self, initialized_db):
        """测试按时间范围获取总结"""
        # 插入几条不同时间的总结
        initialized_db.insert_summary(
            "2024-01-01T09:00:00", "2024-01-01T09:30:00",
            "早上的活动", "work"
        )
        initialized_db.insert_summary(
            "2024-01-01T10:00:00", "2024-01-01T10:30:00",
            "上午的活动", "work"
        )
        initialized_db.insert_summary(
            "2024-01-01T14:00:00", "2024-01-01T14:30:00",
            "下午的活动", "work"
        )

        # 查询 9:00-11:00 范围内的总结
        results = initialized_db.get_summaries_by_time_range(
            "2024-01-01T09:00:00", "2024-01-01T11:00:00"
        )
        assert len(results) == 2

    def test_get_summary_list_by_time_range(self, initialized_db):
        """测试获取总结列表（不含内容）"""
        initialized_db.insert_summary(
            "2024-01-01T10:00:00", "2024-01-01T10:30:00",
            "测试摘要内容", "work"
        )
        results = initialized_db.get_summary_list_by_time_range(
            "2024-01-01T09:00:00", "2024-01-01T11:00:00"
        )
        assert len(results) == 1
        # 确保不包含 summary 字段
        assert 'summary' not in results[0]
        assert 'id' in results[0]
        assert 'start_time' in results[0]
        assert 'end_time' in results[0]


class TestOCROperations:
    """OCR 操作测试"""

    def test_get_ocr_by_time_range(self, initialized_db):
        """测试按时间范围获取 OCR 数据"""
        # 添加带 OCR 的截图
        initialized_db.add_screenshot_with_ocr(
            path="ocr1.jpg",
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            ocr_text="第一段OCR文本",
            ocr_status="done",
            window_title="窗口1",
            process_name="app1.exe"
        )
        initialized_db.add_screenshot_with_ocr(
            path="ocr2.jpg",
            timestamp=datetime(2024, 1, 1, 10, 30, 0),
            ocr_text="第二段OCR文本",
            ocr_status="done",
            window_title="窗口2",
            process_name="app2.exe"
        )
        # 添加 pending 状态的截图（不应被返回）
        initialized_db.add_screenshot_with_ocr(
            path="ocr3.jpg",
            timestamp=datetime(2024, 1, 1, 10, 15, 0),
            ocr_text="待处理的OCR",
            ocr_status="pending",
            window_title="窗口3",
            process_name="app3.exe"
        )

        results = initialized_db.get_ocr_by_time_range(
            "2024-01-01T09:00:00", "2024-01-01T11:00:00"
        )
        assert len(results) == 2  # 只有 done 状态的
        assert all('ocr_text' in r for r in results)
        assert all('window_title' in r for r in results)
        assert all('process_name' in r for r in results)

    def test_get_ocr_by_time_range_with_limit(self, initialized_db):
        """测试 OCR 查询的 limit 参数"""
        for i in range(5):
            initialized_db.add_screenshot_with_ocr(
                path=f"ocr_limit_{i}.jpg",
                timestamp=datetime(2024, 1, 1, 10, i, 0),
                ocr_text=f"OCR文本{i}",
                ocr_status="done"
            )

        results = initialized_db.get_ocr_by_time_range(
            "2024-01-01T09:00:00", "2024-01-01T11:00:00",
            limit=3
        )
        assert len(results) == 3

    def test_get_screenshot_by_timestamp_exact(self, initialized_db):
        """测试按精确时间戳获取截图"""
        ts = "2024-01-01T10:00:00"
        initialized_db.add_screenshot_with_ocr(
            path="exact_ts.jpg",
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            ocr_text="精确时间戳测试",
            ocr_status="done"
        )

        result = initialized_db.get_screenshot_by_timestamp(ts)
        assert result is not None
        assert result['path'] == "exact_ts.jpg"

    def test_get_screenshot_by_timestamp_nearest(self, initialized_db):
        """测试按时间戳获取最接近的截图"""
        initialized_db.add_screenshot(
            path="nearest1.jpg",
            timestamp=datetime(2024, 1, 1, 10, 0, 0)
        )
        initialized_db.add_screenshot(
            path="nearest2.jpg",
            timestamp=datetime(2024, 1, 1, 10, 30, 0)
        )

        # 查询 10:15，应该返回最接近的
        result = initialized_db.get_screenshot_by_timestamp("2024-01-01T10:15:00")
        assert result is not None
        # 应该返回其中一个
        assert result['path'] in ["nearest1.jpg", "nearest2.jpg"]

    def test_get_screenshot_by_timestamp_empty(self, initialized_db):
        """测试空数据库时返回 None"""
        result = initialized_db.get_screenshot_by_timestamp("2024-01-01T10:00:00")
        assert result is None
