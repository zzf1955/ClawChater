# Screen Watcher — 屏幕观察 AI 助手

一个由三个独立模块组成的系统：后台持续截图 → AI 分析屏幕内容 → 通过聊天软件主动给你发消息。

## 架构总览

```
┌──────────────────┐  HTTP API  ┌──────────────────┐  POST /hooks/agent  ┌──────────────────┐
│  Recall           │ ─────────▶│  Screen Agent     │ ──────────────────▶│  OpenClaw          │
│  截图服务 (Python) │           │  屏幕智能 (Python) │                    │  消息投递 (TS)     │
│  :5000            │           │  独立进程          │                    │  :18789            │
└──────────────────┘           └──────────────────┘                    └──────────────────┘
  截图 + OCR + 存储              浏览数据库 + LLM 分析                     WeChat / Telegram 等
```

## 目录结构

```
screen-watcher/
├── recall/                      # 模块1: 截图采集服务
│   ├── main.py                  # 应用入口（托盘 + GUI）
│   ├── app.py                   # RecallApp 主类（协调者）
│   ├── config.py                # 配置管理（DB 热更新）
│   ├── db.py                    # SQLite 数据库层
│   ├── ocr_worker.py            # 后台 OCR 处理（RapidOCR + GPU）
│   ├── core/
│   │   ├── capture.py           # 截图采集（PIL ImageGrab）
│   │   ├── interfaces.py        # 接口定义
│   │   └── container.py         # 依赖注入
│   ├── memory/
│   │   ├── text_memory.py       # 文本记忆
│   │   ├── vector_memory.py     # 向量记忆
│   │   ├── summarizer.py        # 活动总结
│   │   └── extractor.py         # 信息提取
│   ├── ui/
│   │   ├── tray.py              # 系统托盘
│   │   └── window.py            # PyWebView 窗口
│   ├── web/
│   │   ├── app.py               # Flask REST API (:5000)
│   │   └── frontend/            # Vue 3 前端
│   ├── utils/
│   │   ├── gpu.py               # GPU 监控
│   │   ├── similarity.py        # 图片哈希
│   │   └── window.py            # 活动窗口检测
│   ├── data/                    # SQLite 数据库
│   ├── screenshots/             # 截图存储 (按日期/小时)
│   └── requirements.txt
│
├── screen-agent/                # 模块2: 屏幕智能代理
│   ├── main.py                  # 主循环（拉取→分析→发送）
│   ├── config.py                # 环境变量配置
│   ├── recall_client.py         # Recall API 客户端
│   ├── openclaw_client.py       # OpenClaw Hooks 客户端
│   ├── analyzer.py              # LLM 分析（OCR优先）
│   └── requirements.txt         # httpx
│
├── openclaw/                    # 模块3: 多渠道消息控制平面
│   ├── src/                     # TypeScript 核心代码
│   │   ├── gateway/             # 网关（含 Hooks API）
│   │   ├── channels/            # 渠道插件
│   │   ├── agents/              # AI Agent 运行器
│   │   ├── auto-reply/          # 自动回复
│   │   ├── infra/               # 基础设施（心跳、事件）
│   │   └── ...
│   ├── extensions/              # 渠道扩展（Discord 等）
│   ├── apps/                    # 原生应用（iOS/Android/macOS）
│   └── package.json
│
└── README.md                    # 本文件
```

## 各模块说明

### 模块1: Recall 截图服务

**职责**：纯数据采集层，不含任何 AI 逻辑

**核心功能**：
- 每 0.5 秒检测屏幕变化，变化超过阈值时截图
- GPU 空闲时自动 OCR 提取文字（RapidOCR + CUDA）
- 记录活动窗口标题和进程名
- 提供 REST API 供外部查询

**API 端点**：
| 端点 | 说明 |
|------|------|
| `GET /api/health` | 健康检查 + 统计 |
| `GET /api/recent?since=&limit=50` | 最近截图 OCR 摘要 |
| `GET /api/search?q=关键词&hours=24` | 搜索截图 |
| `GET /api/screenshot/<id>/detail` | 单条截图完整信息 |
| `GET /api/screenshot/<id>/image` | 截图图片（file/base64） |
| `GET /api/activity_summary?hours=1` | 活动统计 |
| `GET /api/screenshots` | 截图列表（分页） |
| `GET /api/status` | 服务状态 |
| `GET /api/config` | 读取配置 |
| `POST /api/config` | 更新配置 |

**数据库表**：`screenshots`
```
id, path, timestamp, phash, ocr_text, ocr_status, group_id, window_title, process_name
```

**启动**：`python main.py`（端口 5000）

---

### 模块2: Screen Agent 屏幕智能代理

**职责**：后台持续浏览截图数据库，通过 LLM 分析用户活动，主动发消息

**工作流程**：
```
1. 每 5 分钟从 Recall 拉取最新截图 OCR 摘要
2. 发送给 LLM 分析（OCR 文本优先，按需取图片）
3. LLM 判断是否需要主动提问
4. 如果需要，通过 OpenClaw Hooks API 发送到 WeChat
```

**配置**（环境变量）：
```bash
RECALL_API_URL=http://127.0.0.1:5000
OPENCLAW_HOOKS_URL=http://127.0.0.1:18789
OPENCLAW_HOOK_TOKEN=your-token
TARGET_CHANNEL=wechat
DRY_RUN=true                    # true=只打印不发送
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://www.packyapi.com/v1
LLM_MODEL=claude-haiku-4-5-20251001
ANALYSIS_INTERVAL=300           # 分析间隔（秒）
QUESTION_COOLDOWN=600           # 提问冷却（秒）
```

**启动**：`python main.py`

---

### 模块3: OpenClaw 消息控制平面

**职责**：接收 Screen Agent 的消息，通过各种聊天渠道投递给用户

**Screen Agent 使用的接口**：
```
POST /hooks/agent
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "你好像在研究 Python，需要帮忙吗？",
  "name": "Screen Agent",
  "channel": "wechat",
  "deliver": true,
  "wakeMode": "now"
}
```

**配置要求**：
```yaml
# ~/.openclaw/config.yaml
hooks:
  enabled: true
  token: "your-secret-token"
```

**支持的渠道**：WeChat, Telegram, WhatsApp, Discord, Slack, Signal, iMessage 等

---

## 快速启动

```bash
# 1. 启动截图服务
cd recall && python main.py

# 2. 安装 Screen Agent 依赖
cd screen-agent && pip install -r requirements.txt

# 3. 启动 Screen Agent（dry-run 模式，只打印不发送）
cd screen-agent && python main.py

# 4.（可选）启动 OpenClaw 并配置 WeChat
cd openclaw && pnpm start
```

## 技术栈

| 模块 | 语言 | 关键依赖 |
|------|------|----------|
| Recall | Python 3.11 | Flask, PIL, RapidOCR, pywin32, SQLite |
| Screen Agent | Python 3.11 | httpx |
| OpenClaw | TypeScript | Node.js ≥22.12, pnpm |

## 开发状态

- [x] Recall 截图服务 — 已完成，API 已测试
- [x] Screen Agent — 已完成，dry-run 模式可用
- [ ] OpenClaw WeChat 配置 — 待配置
- [ ] 端到端联调 — 待 WeChat 配好后测试
