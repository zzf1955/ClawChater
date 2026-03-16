# ClawChater — 多平台用户行为感知 chat bot

通过持续观察用户屏幕（PC + 移动端），采集、识别和结构化用户活动数据，为 AI Agent 构建丰富的用户上下文。

### 核心问题

当前 AI Agent 的研究大量聚焦于大语言模型（LLM）本身的推理能力，但在实际应用中，**Agent 表现的上限往往不取决于 LLM 有多强，而取决于它能获取多少关于用户的上下文信息**。一个拥有完整用户行为画像的普通模型，远比一个对用户一无所知的顶级模型更有用。

### 核心思路

本项目构建了一个**多平台用户行为感知系统**，通过持续、被动地采集用户在 PC 和移动端的屏幕活动，结合 OCR 文本提取和结构化存储，为 AI Agent 构建丰富的用户上下文。

系统采用事件驱动架构，核心模块包括：
- **屏幕监控**：像素差异检测 + 感知哈希（phash）去重，智能捕捉屏幕变化
- **OCR 引擎**：GPU 空闲时自动提取截图中的文字（RapidOCR + CUDA）
- **活动记录**：记录活动窗口标题、进程名，构建用户活动时间线
- **REST API**：提供标准化接口，供上层 AI Agent 查询用户上下文
- **Web UI**：截图浏览、搜索、配置管理

### 为什么要多平台

信息采集的全面性是整个系统的关键。用户的行为不局限于电脑——手机端承载了大量碎片化但高价值的生活场景信息：

| 平台 | 能捕捉到的信息 | 价值 |
|------|---------------|------|
| PC 端 | 工作内容、代码编写、文档阅读、网页浏览 | 深度工作行为 |
| 移动端 | 即时通讯、社交媒体、地图导航、购物、日程 | 生活习惯与社交行为 |

单一平台的 Agent 只能看到用户生活的一个切面；**PC + 移动端的融合采集**才能构建出完整的用户行为画像。

屏幕级数据采集天然涉及隐私，因此本项目采用**纯本地架构**（数据不经过云端）并完全开源，确保代码可审计、数据流向透明。

### 应用场景

本系统的核心架构（多平台采集 → 结构化存储 → API 输出）是通用的，可以灵活适配不同场景：

| 场景 | 说明 |
|------|------|
| **AI Agent 上下文构建** | 为任意 AI Agent 提供实时用户行为数据 |
| **学习行为分析** | 分析在线学习的专注度、分心频率、学习节奏 |
| **远程办公效率监测** | 分析工作节奏，生成效率报告 |
| **个人数字生活记录** | 构建可搜索的个人活动时间线 |

---

## 系统架构

```
┌─────────────────────────────────────────────┐
│              Tentacle Server                │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Screen   │  │  Time    │  │ Resource │  │
│  │ Monitor  │  │ Monitor  │  │ Monitor  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │              │              │        │
│       └──────────┬───┘──────────────┘        │
│                  ▼                           │
│            ┌──────────┐                      │
│            │ EventBus │                      │
│            └────┬─────┘                      │
│                 ▼                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Capture  │  │   OCR    │  │ Incoming │  │
│  │ Service  │  │ Worker   │  │ Watcher  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │              │              │        │
│       └──────────┬───┘──────────────┘        │
│                  ▼                           │
│            ┌──────────┐    ┌──────────┐      │
│            │  SQLite  │    │ FastAPI  │      │
│            │ Database │    │ REST API │      │
│            └──────────┘    └──────────┘      │
└─────────────────────────────────────────────┘
         ▲                        ▲
         │ Syncthing              │ HTTP
    ┌────┴────┐             ┌─────┴─────┐
    │  Slave  │             │  Web UI / │
    │ (远程)   │             │ AI Agent  │
    └─────────┘             └───────────┘
```

**事件驱动**：三个 Monitor 检测变化 → 通过 EventBus 发布事件 → Capture 截图 → OCR 提取文字 → 存入 SQLite → FastAPI 提供查询接口。

## 目录结构

```
tentacle/
├── recall/                         # 核心服务
│   ├── app.py                      # FastAPI 应用入口
│   ├── config.py                   # 配置管理
│   ├── slave.py                    # 远程采集客户端（通过 Syncthing 同步）
│   ├── api/
│   │   ├── routes.py               # REST API 端点
│   │   └── schemas.py              # Pydantic 数据模型
│   ├── db/
│   │   ├── database.py             # SQLite 连接管理
│   │   ├── schema.sql              # 数据库建表
│   │   ├── screenshot.py           # 截图表操作
│   │   ├── setting.py              # 配置表操作
│   │   └── summary.py              # 摘要表操作
│   ├── services/
│   │   ├── capture.py              # 跨平台截图（macOS/Windows）
│   │   ├── ocr_engine.py           # RapidOCR 引擎初始化
│   │   ├── ocr_worker.py           # OCR 后台处理
│   │   ├── incoming_watcher.py     # Syncthing 目录监控
│   │   ├── sync.py                 # 数据库-文件系统同步
│   │   ├── core/
│   │   │   ├── engine.py           # 主编排引擎
│   │   │   ├── event_bus.py        # 发布-订阅事件系统
│   │   │   └── events.py           # 事件类型定义
│   │   └── monitor/
│   │       ├── screen_monitor.py   # 屏幕变化检测（phash）
│   │       ├── time_monitor.py     # 定时强制截图
│   │       ├── resource_monitor.py # CPU/GPU 资源监控
│   │       └── utils.py            # 监控工具函数
│   ├── frontend/                   # React + Vite Web UI
│   │   ├── src/
│   │   │   ├── App.tsx
│   │   │   ├── api.ts
│   │   │   └── types.ts
│   │   └── dist/                   # 构建产物（FastAPI 静态服务）
│   ├── utils/
│   │   └── time_parse.py           # ISO8601 解析
│   └── tests/                      # 测试套件
│
├── doc/                            # 项目文档
├── CLAUDE.md                       # Claude Code 开发指导
└── README.md                       # 本文件
```

## API 端点

| 端点 | 说明 |
|------|------|
| `GET /health` | 健康检查 |
| `GET /api/screenshots` | 截图列表（支持时间范围过滤） |
| `GET /api/screenshots/{id}` | 单条截图详情 |
| `GET /api/screenshots/{id}/image` | 截图图片 |
| `GET /api/summaries` | 查询活动摘要 |
| `POST /api/summaries` | 写入活动摘要 |
| `GET /api/config` | 读取配置 |
| `POST /api/config` | 更新配置 |
| `POST /api/sync` | 数据库-文件系统同步 |

## 数据库

SQLite，三张表：

| 表 | 用途 |
|----|------|
| `screenshots` | 截图元数据（路径、时间戳、phash、OCR 文本、窗口标题、进程名） |
| `summaries` | 活动摘要 |
| `settings` | 配置存储（支持热更新） |

## 快速启动

```bash
# 激活 conda 环境
conda activate recall

# 启动服务
python -m recall.app
# 访问 http://127.0.0.1:8000 查看 Web UI

# 开发模式（热重载）
RECALL_RELOAD=1 python -m recall.app
```

### Slave 模式（远程采集）

在远程机器上运行 Slave，通过 Syncthing 将截图同步到主服务器：

```bash
RECALL_DEVICE_ID=my-laptop RECALL_SYNC_DIR=/path/to/sync python -m recall.slave
```

## 配置

通过环境变量或 Web UI 配置：

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `RECALL_HOST` | `127.0.0.1` | 监听地址 |
| `RECALL_PORT` | `8000` | 监听端口 |
| `RECALL_RELOAD` | `0` | 开发模式热重载 |
| `RECALL_LOG_LEVEL` | `DEBUG` | 日志级别 |
| `RECALL_SERVE_FRONTEND` | `1` | 是否提供前端静态文件 |
| `RECALL_INCOMING_DIR` | - | Syncthing 同步目录 |

运行时参数（通过 Web UI 或 API 修改）：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `SCREEN_CHECK_INTERVAL` | `3` | 屏幕检测间隔（秒） |
| `CHANGE_THRESHOLD` | `5` | phash 汉明距离阈值 |
| `OCR_BATCH_SIZE` | `10` | OCR 批处理大小 |
| `GPU_USAGE_THRESHOLD` | `70` | GPU 占用阈值（%） |
| `FORCE_INTERVAL` | `30` | 强制截图间隔（秒） |

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Python 3.11, FastAPI, Uvicorn, SQLite |
| OCR | RapidOCR + ONNX Runtime (GPU 加速) |
| 前端 | React 18, TypeScript, Vite, Tailwind CSS |
| 测试 | pytest, Vitest, Playwright |
| 图像处理 | Pillow, 感知哈希 |
| 系统监控 | psutil, pynvml |
