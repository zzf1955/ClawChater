"""Web API 集成测试"""
import pytest
from flask import Flask


class TestWebAPI:
    """Web API 测试"""

    @pytest.fixture
    def client(self, initialized_db, monkeypatch):
        """创建测试客户端"""
        # Mock db 模块使用测试数据库
        import db as db_module
        monkeypatch.setattr(db_module, "_default_db", initialized_db)

        from web.app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_api_status(self, client):
        """测试状态 API"""
        response = client.get('/api/status')
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_screenshots' in data
        assert 'pending_ocr' in data

    def test_api_get_config(self, client):
        """测试获取配置 API"""
        response = client.get('/api/config')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)

    def test_api_screenshots_empty(self, client):
        """测试获取截图列表（空）"""
        response = client.get('/api/screenshots')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_api_ai_messages(self, client, initialized_db):
        """测试获取 AI 消息"""
        # 添加测试消息
        initialized_db.add_ai_message("user", "测试消息")

        response = client.get('/api/ai/messages?since_id=0')
        assert response.status_code == 200
        data = response.get_json()
        assert 'messages' in data
        assert len(data['messages']) >= 1
