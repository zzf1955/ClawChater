"""pytest 全局 fixtures"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

# 确保项目根目录在 path 中
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============ 数据目录 Fixtures ============

@pytest.fixture
def temp_data_dir(tmp_path):
    """创建临时数据目录"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def temp_screenshot_dir(tmp_path):
    """创建临时截图目录"""
    screenshot_dir = tmp_path / "screenshots"
    screenshot_dir.mkdir()
    return screenshot_dir


# ============ 容器 Fixtures ============

@pytest.fixture
def test_config(temp_data_dir, temp_screenshot_dir):
    """测试用应用配置"""
    from core.container import AppConfig
    return AppConfig(
        data_dir=temp_data_dir,
        screenshot_dir=temp_screenshot_dir,
        web_port=5001  # 使用不同端口避免冲突
    )


@pytest.fixture
def test_container(test_config):
    """测试用容器，使用临时目录"""
    from core.container import Container, set_container, reset_container
    container = Container(test_config)
    set_container(container)
    yield container
    reset_container()


# ============ 数据库 Fixtures ============

@pytest.fixture
def initialized_db(test_container):
    """初始化的临时数据库"""
    db = test_container.database
    db.init_db()
    return db


# ============ 配置 Fixtures ============

@pytest.fixture
def mock_config():
    """Mock 配置，返回测试默认值"""
    return {
        'SCREENSHOT_DIR': 'test_screenshots',
        'CHANGE_THRESHOLD': 0.8,
        'FORCE_CAPTURE_INTERVAL': 300,
        'MIN_CAPTURE_INTERVAL': 10,
        'JPEG_QUALITY': 85,
        'GPU_USAGE_THRESHOLD': 30,
        'OCR_BATCH_SIZE': 10,
        'AI_EXPLORE_INTERVAL': 300,
        'AI_MIN_QUESTION_INTERVAL': 600,
        'AI_ENABLED': True,
    }


# ============ HTTP/LLM Fixtures ============

@pytest.fixture
def mock_httpx_response():
    """Mock httpx 响应"""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": "这是测试回复",
                "tool_calls": []
            }
        }]
    }
    mock_response.raise_for_status = MagicMock()
    return mock_response


@pytest.fixture
def mock_httpx_client(mock_httpx_response):
    """Mock httpx.Client"""
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.return_value = mock_httpx_response
    return mock_client


@pytest.fixture
def mock_llm_api(mock_httpx_client, monkeypatch):
    """Mock LLM API 调用"""
    import httpx
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_httpx_client)
    return mock_httpx_client


# ============ 文件系统 Fixtures ============

@pytest.fixture
def temp_memory_file(temp_data_dir):
    """临时记忆文件"""
    memory_file = temp_data_dir / "memory.md"
    memory_file.write_text(
        "# 用户记忆\n\n## 基本信息\n\n## 偏好\n\n## 重要事项\n",
        encoding="utf-8"
    )
    return memory_file


@pytest.fixture
def temp_summaries_dir(temp_data_dir):
    """临时总结目录"""
    summaries_dir = temp_data_dir / "summaries" / "hourly"
    summaries_dir.mkdir(parents=True)
    return summaries_dir


# ============ 测试数据 Fixtures ============

@pytest.fixture
def sample_screenshot_data():
    """示例截图数据"""
    from datetime import datetime
    return {
        "path": "screenshots/2024-01-01/12/120000.jpg",
        "timestamp": datetime(2024, 1, 1, 12, 0, 0),
        "phash": "a" * 16,
        "window_title": "Test Window",
        "process_name": "test.exe",
        "ocr_text": "测试文本内容"
    }
