# Recall 架构设计

## 概述

Recall 采用**分层架构 + 依赖注入**模式，将业务逻辑与 UI 分离，支持单元测试和模块化开发。

## 目录结构

```
recall/
├── main.py                    # 应用入口
├── app.py                     # 应用协调者
├── config.py                  # 配置管理
│
├── core/                      # 核心业务层
│   ├── __init__.py
│   ├── interfaces.py          # 抽象接口定义（Protocol）
│   ├── container.py           # 依赖注入容器
│   └── capture.py             # 截图服务
│
├── db.py                      # 数据库层（Database 类）
│
├── llm.py                     # LLM 服务（LLMService 类）
├── message_queue.py           # 消息队列（MessageQueue 类）
├── curious_ai.py              # AI 探索（CuriousAI 类）
│
├── memory/                    # 记忆系统
│   ├── text_memory.py         # 文本记忆（TextMemory 类）
│   ├── vector_memory.py       # 向量记忆（VectorMemory 类）
│   ├── summarizer.py          # 活动总结（ActivitySummarizer 类）
│   └── extractor.py           # 记忆提取（MemoryExtractor 类）
│
├── ui/                        # UI 层
│   ├── tray.py                # 托盘管理（TrayManager 类）
│   └── window.py              # 窗口管理（WindowManager 类）
│
├── web/                       # Web API 层
│   ├── app.py                 # Flask 路由
│   └── frontend/              # Vue 3 前端
│
├── utils/                     # 工具模块
│   ├── similarity.py          # 图片哈希
│   ├── gpu.py                 # GPU 监控
│   └── window.py              # 窗口信息
│
├── tests/                     # 测试模块
│   ├── conftest.py            # pytest fixtures
│   ├── unit/                  # 单元测试
│   └── integration/           # 集成测试
│
└── pyproject.toml             # pytest 配置
```

## 核心设计

### 1. 依赖注入容器

`core/container.py` 管理所有服务实例的生命周期：

```python
from core.container import Container, get_container

# 获取全局容器
container = get_container()

# 获取服务实例（懒加载）
db = container.database
llm = container.llm_service
mq = container.message_queue
```

### 2. 接口定义

`core/interfaces.py` 使用 Protocol 定义抽象接口：

```python
from typing import Protocol

class IDatabase(Protocol):
    def init_db(self) -> None: ...
    def add_screenshot(...) -> int: ...
```

### 3. 模块依赖注入

所有核心模块支持构造函数注入：

```python
# 使用默认全局实例
from db import Database
db = Database()

# 使用自定义路径（测试用）
db = Database(db_path=Path("/tmp/test.db"))
```

### 4. 向后兼容

每个模块保留全局实例，确保旧代码无需修改：

```python
# 旧代码仍然可用
import db
db.init_db()
db.add_screenshot(...)

# 新代码可以使用类
from db import Database
my_db = Database(custom_path)
```

## 模块职责

| 模块 | 职责 | 依赖 |
|------|------|------|
| `core/container.py` | 依赖注入容器 | config |
| `core/capture.py` | 截图采集、差异检测 | db, config |
| `db.py` | 数据库 CRUD | - |
| `llm.py` | LLM API 调用 | config, memory |
| `message_queue.py` | 用户-AI 消息队列 | db |
| `curious_ai.py` | AI 主动探索 | llm, message_queue, memory |
| `memory/*` | 记忆存储和检索 | config |
| `ui/tray.py` | 系统托盘 | - |
| `ui/window.py` | WebView 窗口 | - |
| `web/app.py` | REST API | db, llm, message_queue |

## 数据流

```
截图采集流程：
CaptureService → 截图 → 保存文件 → db.add_screenshot() → OCR Worker

用户对话流程：
Web API → message_queue.user_send() → CuriousAI → LLMService → message_queue.ai_send()

配置热更新：
Web API → config.set_all() → db.set_setting() → 各模块 config.get() 读取
```

## 测试架构

### Fixtures（conftest.py）

```python
@pytest.fixture
def temp_data_dir(tmp_path):
    """临时数据目录"""

@pytest.fixture
def test_container(temp_data_dir):
    """测试用容器"""

@pytest.fixture
def initialized_db(test_container):
    """初始化的临时数据库"""

@pytest.fixture
def mock_llm_api(monkeypatch):
    """Mock LLM API"""
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 只运行单元测试
pytest tests/unit/ -v

# 只运行集成测试
pytest tests/integration/ -v

# 运行特定模块测试
pytest tests/unit/test_db.py -v
```

## 扩展指南

### 添加新服务

1. 在对应目录创建模块（如 `core/new_service.py`）
2. 定义类，构造函数接受依赖参数
3. 在 `core/container.py` 添加属性
4. 创建全局实例（向后兼容）
5. 编写测试

### 添加新测试

1. 在 `tests/unit/` 或 `tests/integration/` 创建 `test_xxx.py`
2. 使用 `conftest.py` 中的 fixtures
3. 运行 `pytest tests/unit/test_xxx.py -v` 验证
