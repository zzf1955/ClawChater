# Recall 架构设计

## 概述

Recall 采用**分层架构 + 依赖注入**模式，将业务逻辑与 UI 分离，支持单元测试和模块化开发。

**UI 模式**: 纯 Web UI，通过浏览器访问 http://127.0.0.1:5000

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
├── ocr_worker.py              # OCR 处理
│
├── web/                       # Web 层
│   ├── app.py                 # Flask REST API
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
| `ocr_worker.py` | OCR 处理 | db, config |
| `web/app.py` | REST API | db |

## 数据流

```
截图采集流程：
CaptureService → 截图 → 保存文件 → db.add_screenshot() → OCR Worker

配置热更新：
Web API → config.set_all() → db.set_setting() → 各模块 config.get() 读取
```

## 启动方式

```bash
# 启动应用
python main.py

# 访问 Web UI
# http://127.0.0.1:5000
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
