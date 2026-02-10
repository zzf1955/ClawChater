---
id: "014"
title: "定义双 Session 文件通信协议"
priority: high
depends_on: []
module: openclaw
branch: feature/dual-session-chat
estimated_scope: small
---

## 背景

实现 Telegram 双向聊天需要两个 Agent Session 协作：
- **Thinking Session**（后台）：分析 OCR 数据，生成意图
- **Chat Session**（Telegram DM）：根据意图和用户聊天，提取事实

两个 session 通过 JSON 文件解耦通信，文件存放在共享的 agent workspace 中。

## 技术方案

在 OpenClaw agent workspace（`~/.openclaw/workspace`）下创建通信文件：

### intents.json — Thinking → Chat

```json
{
  "updated_at": "2026-02-08T12:00:00Z",
  "intents": [
    {
      "id": "i-001",
      "created_at": "2026-02-08T12:00:00Z",
      "type": "observation | curiosity | question",
      "content": "用户在浏览日本旅游攻略，似乎在计划旅行",
      "context": "OCR 摘要片段...",
      "status": "pending | delivered | expired"
    }
  ]
}
```

### facts.json — Chat → Thinking

```json
{
  "updated_at": "2026-02-08T12:05:00Z",
  "facts": [
    {
      "id": "f-001",
      "created_at": "2026-02-08T12:05:00Z",
      "source": "user_reply | inference",
      "content": "用户计划下个月去东京旅行，预算 1 万元",
      "related_intent": "i-001"
    }
  ]
}
```

### 文件位置

- `~/.openclaw/workspace/intents.json`
- `~/.openclaw/workspace/facts.json`

### 初始化

创建空的初始文件（intents: [], facts: []）。

## 验收标准

- [ ] intents.json 和 facts.json schema 定义清晰
- [ ] 初始空文件已创建在 workspace 目录
- [ ] 文档说明了字段含义和状态流转

## 测试要求

- [ ] 验证 JSON schema 合法性
- [ ] 验证文件路径可被 OpenClaw agent 的 read/write 工具访问

---
completed_by: w-7e3b
completed_at: 2026-02-08T16:00:00+08:00
commit: d2be642
files_changed:
  - ~/.openclaw/workspace/intents.json
  - ~/.openclaw/workspace/facts.json
  - ~/.openclaw/workspace/PROTOCOL.md
test_result: "JSON 验证通过，文件路径可访问"
---
