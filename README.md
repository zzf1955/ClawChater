# ClawChater — 能看到你在做什么的聊天 Bot

通过持续观察用户屏幕（PC + 手机），理解用户当前活动，然后通过 Telegram 主动和用户聊天。

## 迁移收口（task009）

- 旧新架构映射、迁移步骤、切换与回滚清单：`doc/migration-closeout.md`
- 数据迁移脚本：`scripts/migrate_recall_old_db.py`
- 当前策略：`recall/` 为主线，`recall_old/` 归档保留（只读）

### 核心问题

当前 AI Agent 的研究大量聚焦于大语言模型（LLM）本身的推理能力，但在实际应用中，**Agent 表现的上限往往不取决于 LLM 有多强，而取决于它能获取多少关于用户的上下文信息**。一个拥有完整用户行为画像的普通模型，远比一个对用户一无所知的顶级模型更有用。

### 核心思路

本项目构建了一个**多平台用户行为感知系统**，通过持续、被动地采集用户在 PC 和移动端的屏幕活动，结合 OCR 文本提取和记忆系统，为 AI Agent 构建丰富的用户上下文，再通过消息通道与用户主动交互。

系统由三部分组成：
- **Recall（数据采集层）**：在 PC 端和 Android 端持续截图 + OCR，构建用户活动的时间线数据库
- **Screen Agent（智能分析层）**：基于 LLM 分析采集到的屏幕数据，判断用户当前状态并决策是否主动交互
- **OpenClaw（消息投递层）**：多渠道消息网关（WeChat / Telegram / WhatsApp 等），将 Agent 的消息送达用户

### 为什么要多平台

信息采集的全面性是整个系统的关键。用户的行为不局限于电脑——手机端承载了大量碎片化但高价值的生活场景信息：

| 平台 | 能捕捉到的信息 | 价值 |
|------|---------------|------|
| PC 端 | 工作内容、代码编写、文档阅读、网页浏览 | 深度工作行为 |
| 移动端 | 即时通讯、社交媒体、地图导航、购物、日程 | 生活习惯与社交行为 |

单一平台的 Agent 只能看到用户生活的一个切面；**PC + 移动端的融合采集**才能构建出完整的用户行为画像，从而让 Agent 的判断和交互真正有意义。

### 为什么必须开源

屏幕级的持续数据采集天然与用户隐私高度敏感。微软 Windows Recall 功能就是前车之鉴——它在本地持续截图并建立可搜索的活动记录，功能设计与本项目高度相似，但因隐私争议在发布前被迫搁置重做。核心矛盾在于：**AI Agent 越智能，就越需要大面积、持续性的用户数据；而这种级别的数据采集，用户不可能信任一个闭源的黑盒系统。**

闭源产品无法自证清白——用户无从验证数据是否真的只存在本地、是否被上传、是否被用于训练。因此，这类"AI + 大规模个人信息采集"的系统，几乎只能由开源社区来推动：

- **数据完全本地化**：截图、OCR 文本、记忆数据库全部存储在用户设备上，不经过任何云端
- **代码可审计**：任何人都可以检查数据流向，确认没有隐蔽的上传行为
- **用户完全控制**：采集频率、存储策略、数据保留时长均可自行配置和修改

本项目的 Recall 模块采用纯本地架构（SQLite + 本地文件系统），LLM 分析仅发送 OCR 文本摘要而非原始截图，从设计上最小化隐私风险。开源是这类系统获得用户信任的唯一路径。

### 应用场景

本系统的核心架构（多平台采集 → AI 分析 → 主动交互）是通用的，可以灵活适配不同场景：

| 场景 | 说明 | PC 端作用 | 移动端作用 |
|------|------|----------|-----------|
| **学习行为分析** | 分析学生在线学习的专注度、分心频率、学习节奏 | 捕捉网课/文档阅读行为 | 捕捉学习间隙的手机使用（刷社交媒体等） |
| **学习监督助手** | 发现学生走神或长时间未学习时，主动发送提醒和鼓励 | 监测是否在学习相关应用 | 监测是否在娱乐应用停留过久 |
| **远程办公效率监测** | 分析工作节奏，久坐提醒，工作效率报告 | 工作内容和工具使用分析 | 休息时间和通勤行为 |
| **老年人数字关怀** | 检测操作困难或疑似诈骗页面，通知家属 | 电脑操作困难检测 | 手机诈骗/异常转账预警 |

当前原型以**学习行为分析与监督**为主要演示场景，但场景可按需替换。

---

## 系统架构

```
Recall (:5000) ──HTTP API──▶ OpenClaw (:18789)
截图+OCR+存储                 Thinking Agent (分析决策)
(PC + Android)                Chat Agent (Telegram 聊天)
```

两个模块协作，数据单向流动：

- **Recall** 负责截图采集、OCR 文字提取、数据存储
- **OpenClaw** 负责智能分析和 Telegram 消息投递

### 双 Agent 架构

OpenClaw 内部运行两个 AI Agent：

| Agent | Session Key | 职责 |
|-------|-------------|------|
| Thinking Agent | `agent:thinking:main` | 后台观察者，每 5 分钟从 Recall 拉取 OCR 数据分析用户活动 |
| Chat Agent | `agent:chat:main` | 用户面对面的聊天伙伴，以朋友口吻在 Telegram 上聊天 |

**工作流程**：
1. Thinking Agent 通过 Heartbeat 定时分析 OCR 数据
2. 发现有趣内容时，向 Chat Agent 发送指导消息
3. Chat Agent 收到指导后，以自然口吻在 Telegram 上与用户聊天
4. 用户回复时，消息先经 Thinking Agent 分析，再由 Chat Agent 回复

## 目录结构

```
ClawChater/
├── recall/                      # 模块1: 数据采集服务
│   ├── main.py                  # 应用入口
│   ├── app.py                   # RecallApp 主类（协调者）
│   ├── config.py                # 配置管理（DB 热更新）
│   ├── db.py                    # SQLite 数据库层
│   ├── ocr_worker.py            # 后台 OCR 处理（RapidOCR + GPU）
│   ├── core/                    # 核心业务（截图、依赖注入）
│   ├── web/                     # Flask REST API + Vue 3 前端
│   ├── utils/                   # GPU 监控、图片哈希、窗口检测
│   ├── android/                 # Android 移动端
│   └── tests/                   # 测试
│
├── openclaw/                    # 模块2: 智能分析 + 消息投递（git submodule）
│   ├── src/                     # TypeScript 核心代码
│   │   ├── gateway/             # 网关（WebSocket/HTTP）
│   │   ├── channels/            # 渠道插件（Telegram）
│   │   ├── agents/              # AI Agent 运行器
│   │   └── ...
│   └── package.json
│
├── .tasks/                      # 任务管理系统
│   ├── backlog/                 # 待领取
│   ├── wip/                     # 进行中
│   └── done/                    # 已完成
│
├── CLAUDE.md                    # Claude Code 开发指导
└── README.md                    # 本文件
```

## 各模块说明

### Recall — 数据采集层

**职责**：纯数据采集，不含 AI 逻辑

**核心功能**：
- 像素差异检测 + 强制间隔截图 + 感知哈希（phash）去重
- GPU 空闲时自动 OCR 提取文字（RapidOCR + CUDA）
- 记录活动窗口标题和进程名
- 提供 REST API 供 OpenClaw 查询
- Web UI 截图浏览和搜索

**API 端点**：

| 端点 | 说明 |
|------|------|
| `GET /api/health` | 健康检查 + 统计 |
| `GET /api/status` | 服务状态 |
| `GET /api/recent?since=&limit=50` | 最近截图 OCR 摘要 |
| `GET /api/search?q=关键词&hours=24` | 搜索截图 |
| `GET /api/screenshots` | 截图列表（分页） |
| `GET /api/screenshot/<id>/detail` | 单条截图完整信息 |
| `GET /api/screenshot/<id>/image` | 截图图片 |
| `GET /api/activity_summary?hours=1` | 活动统计 |
| `GET /api/config` | 读取配置 |
| `POST /api/config` | 更新配置 |
| `POST /api/summaries` | 写入活动摘要 |
| `GET /api/summaries?hours=24` | 查询活动摘要 |

**数据库表**：

| 表 | 用途 |
|----|------|
| `screenshots` | 截图元数据（path, timestamp, phash, ocr_text, window_title, process_name） |
| `groups` | 截图分组 |
| `settings` | 配置存储（热更新） |
| `summaries` | 活动摘要（由 Thinking Agent 写入） |

### OpenClaw — 智能分析 + 消息投递层

**职责**：分析用户活动，通过 Telegram 与用户聊天

**架构**：CLI（Commander.js）→ Gateway（WebSocket/HTTP）→ Agent → Channels

**当前渠道**：Telegram（@zzf1955_bot）

**Agent 间通信**：
- Thinking → Chat：通过 `sessions_send` 工具（`deliver: true, channel: "telegram"`）
- 共享长期记忆：`~/.openclaw/workspace/facts.json`

## 快速启动

```bash
# 1. 启动 Recall 截图服务
cd recall && conda run -n recall python main.py
# 访问 http://127.0.0.1:5000 查看 Web UI

# 2. 启动 OpenClaw Gateway
cd openclaw && pnpm start gateway
```

## 技术栈

| 模块 | 语言 | 关键依赖 |
|------|------|----------|
| Recall | Python 3.11 | Flask, PIL, RapidOCR, SQLite |
| Recall Android | Kotlin | MediaProjection API, Room |
| OpenClaw | TypeScript | Node.js >=22.12, grammY (Telegram) |

## 开发状态

### v1.0 已完成
- [x] Recall 截图服务（PC + Android）
- [x] OCR 文字提取（GPU 加速）
- [x] Web UI 截图浏览
- [x] OpenClaw 双 Agent 架构
- [x] Thinking Agent 定时分析
- [x] Chat Agent Telegram 聊天
- [x] 活动摘要生成与存储
- [x] 用户消息 Thinking 中继

### 后续计划
- [ ] 移动端截图通过 Telegram 中转到 PC
- [ ] 更多渠道支持
