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

    def test_index_serves_frontend(self, client):
        """测试首页返回 Vue 前端"""
        response = client.get('/')
        assert response.status_code == 200
        # 应该返回 HTML（Vue SPA 或提示信息）
        assert response.content_type.startswith('text/html')

    def test_health_endpoint(self, client):
        """测试健康检查接口"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'
