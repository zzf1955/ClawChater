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


class TestSummariesAPI:
    """Summaries API 测试"""

    @pytest.fixture
    def client(self, initialized_db, monkeypatch):
        """创建测试客户端"""
        import db as db_module
        monkeypatch.setattr(db_module, "_default_db", initialized_db)

        from web.app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_post_summary(self, client):
        """测试写入摘要"""
        response = client.post('/api/summaries', json={
            'start_time': '2024-01-01T10:00:00',
            'end_time': '2024-01-01T10:30:00',
            'summary': '用户在写代码',
            'activity_type': 'work'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert 'id' in data
        assert data['id'] > 0

    def test_post_summary_missing_fields(self, client):
        """测试缺少必填字段"""
        response = client.post('/api/summaries', json={
            'start_time': '2024-01-01T10:00:00'
        })
        assert response.status_code == 400

    def test_post_summary_no_body(self, client):
        """测试无 body"""
        response = client.post('/api/summaries',
                               content_type='application/json')
        assert response.status_code == 400

    def test_get_summaries_empty(self, client):
        """测试空数据返回空数组"""
        response = client.get('/api/summaries')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_summaries_with_data(self, client):
        """测试写入后能查询到"""
        from datetime import datetime
        now = datetime.now()
        client.post('/api/summaries', json={
            'start_time': now.replace(minute=0, second=0).isoformat(),
            'end_time': now.isoformat(),
            'summary': '测试摘要',
            'activity_type': 'work'
        })

        response = client.get('/api/summaries?hours=1')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['summary'] == '测试摘要'

    def test_post_summary_without_activity_type(self, client):
        """测试不传 activity_type"""
        response = client.post('/api/summaries', json={
            'start_time': '2024-01-01T10:00:00',
            'end_time': '2024-01-01T10:30:00',
            'summary': '无分类摘要'
        })
        assert response.status_code == 201
