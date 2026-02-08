# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 项目愿景

ClawChater 是一个**能看到你在做什么的聊天 bot**。通过持续观察用户屏幕（PC + 手机），理解用户当前活动，然后通过 Telegram 主动和用户聊天。手机端尤其重要——它能捕捉到生活中的细节。

## 系统架构

两个模块协作，数据单向流动：

```
Recall (:5000) ──HTTP API──▶ OpenClaw (:18789)
截图+OCR+存储                 Thinking Agent (分析决策)
(PC + Android)                Chat Agent (Telegram 聊天)
```

**当前状态**：Recall + OpenClaw 双模块架构。Thinking Agent 每 5 分钟通过 Cron 拉取 OCR 数据分析，有趣时触发 Chat Agent 在 Telegram 上聊天。

## 模块速查

| 模块 | 语言 | 启动命令 | 端口 |
|------|------|----------|------|
| recall | Python 3.11 (conda: `recall`) | `python main.py` | 5000 |
| openclaw | TypeScript (Node ≥22.12) | `pnpm start` | 18789 |

## 常用命令

### Recall
```bash
conda run -n recall python main.py          # PC 端启动

pytest tests/ -v                             # 全部测试
pytest tests/unit/ -v                        # 单元测试
pytest tests/unit/test_db.py -v              # 单个文件

# 前端
npm run dev --prefix "D:/BaiduSyncdisk/Desktop/ClawChater/recall/web/frontend"
npm run build --prefix "D:/BaiduSyncdisk/Desktop/ClawChater/recall/web/frontend"

# Android 编译
cmd //c "cd /d D:\\BaiduSyncdisk\\Desktop\\ClawChater\\recall\\android\\RecallMobile && gradlew.bat assembleDebug"
```

### OpenClaw
```bash
pnpm install && pnpm build                   # 安装 + 构建
pnpm dev                                     # 开发模式
pnpm test                                    # vitest 并行测试
pnpm check                                   # 类型检查 + oxlint + oxfmt
```

## 架构要点

### Recall — 数据采集层（PC + Android）
协调者模式：`RecallApp`（app.py）统一管理截图、OCR、托盘、窗口、Web 服务。所有核心模块支持**依赖注入**（构造函数参数），同时保留全局实例兼容旧代码。

- **截图**：像素差异检测 + 强制间隔 + 感知哈希（phash）去重
- **OCR**：RapidOCR + GPU 加速，GPU 空闲时（<30%）批量处理
- **存储**：SQLite（`data/recall.db`），截图按 `screenshots/YYYY-MM-DD/HH/HHMMSS.jpg` 存放，OCR 文本为同名 `.txt`
- **配置**：数据库热更新（`settings` 表）
- **Web**：Flask REST API（:5000）+ Vue 3 前端
- **移动端**：Android 原生应用，用于捕捉手机端的生活细节

关键约束：cuDNN 路径必须在 `import onnxruntime` **之前**加入 PATH。

### OpenClaw — 智能分析 + 消息投递层
分层架构：CLI（Commander.js）→ Gateway（WebSocket/HTTP）→ Agent → Channels（渠道插件）。

**双 Agent 架构**：
- **Thinking Agent**（Haiku）：后台观察者，每 5 分钟被 Cron 唤醒，从 Recall API 拉取 OCR 数据分析用户活动，有趣时写入 intent 触发 Chat Agent
- **Chat Agent**（Sonnet）：用户面对面的聊天伙伴，读取 intent 后以朋友口吻在 Telegram 上发起聊天，从用户回复中提取 facts

**共享数据**：`~/.openclaw/workspace/` 下的 `intents.json`（Thinking→Chat）和 `facts.json`（Chat→Thinking）

当前渠道：**Telegram**（@zzf1955_bot）。

OpenClaw 开发规范见 `openclaw/AGENTS.md`：
- 严格 TypeScript（ESM），import 必须带 `.js` 后缀
- Oxlint + Oxfmt 格式化，提交前跑 `pnpm check`
- 文件控制在 ~700 行以内
- 提交用 `scripts/committer "<msg>" <file...>`

## 环境

- **平台**：Windows，Claude Code 的 Bash 工具运行在 Git Bash（不要用 PowerShell 包装）
- **路径**：用 `/` 或 `\\\\`，npm 用 `--prefix`，.bat 文件用 `cmd //c`
- **GPU**：RTX 4060，CUDA 12.x + cuDNN 9.x
- **网络代理**：`http://127.0.0.1:7897`
- **Android SDK**：`C:\Users\ZZF\AppData\Local\Android\Sdk`

## 子模块文档

- `recall/CLAUDE.md` — Recall 开发流程、skills、规范
- `openclaw/AGENTS.md` — OpenClaw 贡献者指南、PR 流程、发布流程
- `recall/doc/framework.md` — Recall 架构设计文档

## 多 Agent 协作

本项目使用基于文件的任务系统协调多个 Claude Code 会话并行开发。

### Skills

| 命令 | 角色 | 说明 |
|------|------|------|
| `/planner` | Plan Agent | 需求澄清 → 技术方案 → 任务拆解（需要用户参与） |
| `/worker` | Worker Agent | 自主领取任务 → 开发 → 测试 → 完成 |
| `/status` | — | 查看任务看板 |

### 任务目录

```
.tasks/
├── backlog/    # 待领取的任务
├── wip/        # 进行中（按 worker-id 分子目录）
└── done/       # 已完成的任务
```

### 任务文件

每个任务是一个 `.md` 文件，包含 YAML front matter（id、priority、depends_on、module、branch、estimated_scope）和正文（背景、技术方案、验收标准、测试要求）。详见 `.claude/skills/planner/SKILL.md`。

### 工作流程

1. 用户在一个终端运行 `/planner`，描述需求 → Plan Agent 澄清、设计、创建任务文件
2. 用户开新终端运行 `/worker` → Worker Agent 自动扫描、领取、开发、测试、完成
3. 可同时开多个 `/worker` 终端并行开发不同任务
4. 随时运行 `/status` 查看进度
