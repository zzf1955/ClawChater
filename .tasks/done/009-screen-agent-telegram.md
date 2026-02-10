---
id: "009"
title: "Screen Agent 对接 Telegram 渠道"
priority: high
depends_on: ["008"]
module: screen-agent
branch: main
estimated_scope: small
---

## 背景

Screen Agent 当前 `TARGET_CHANNEL` 默认值是 `wechat`，且 `openclaw_client.py` 的 POST payload 缺少 `to` 字段（Telegram 需要指定目标 user ID）。需要适配 Telegram 渠道。

## 技术方案

### 1. 修改 `screen-agent/config.py`
- `TARGET_CHANNEL` 默认值改为 `telegram`
- 新增 `TARGET_USER_ID` 配置项（环境变量 `TARGET_USER_ID`）
- `DRY_RUN` 默认值改为 `false`（准备实际使用）
- `OPENCLAW_HOOK_TOKEN` 填入任务 008 中配置的 hooks token

### 2. 修改 `screen-agent/openclaw_client.py`
- `send_message()` 方法增加 `to` 参数
- POST payload 添加 `"to": to` 字段
- 添加 `"sessionKey": "hook:screen-agent"` 保持会话连续性

### 3. 修改 `screen-agent/main.py`
- 调用 `openclaw.send_message()` 时传入 `to=config.TARGET_USER_ID`

## 验收标准

- [x] `TARGET_CHANNEL` 默认值为 `telegram`
- [x] `openclaw_client.py` POST payload 包含 `to` 和 `sessionKey` 字段
- [x] Screen Agent 启动后能通过 OpenClaw 将消息投递到 Telegram
- [x] 端到端测试：Recall 有截图 → Screen Agent 分析 → Telegram 收到消息

## 测试要求

- [x] DRY_RUN=true 模式下打印的 payload 格式正确
- [x] DRY_RUN=false 模式下消息成功送达 Telegram

---
completed_by: w-8d4a
completed_at: 2026-02-08T04:10:00Z
commit: 2c0762d
files_changed:
  - screen-agent/config.py
  - screen-agent/main.py
  - screen-agent/openclaw_client.py
test_result: "2 passed, 0 failed (DRY_RUN payload format, live Telegram delivery)"
notes: |
  - 额外配置了 OpenClaw 的 LLM provider (packyapi) 和 api 字段
  - OpenClaw gateway 启动时需要 HTTPS_PROXY=http://127.0.0.1:7897 环境变量
  - 端到端验证：Screen Agent → OpenClaw hooks → Telegram 消息送达成功
---
