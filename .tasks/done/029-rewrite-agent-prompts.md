---
id: "029"
title: "重写双 Agent Prompt + 废弃 intents 机制"
priority: high
depends_on: ["027", "028"]
module: openclaw
branch: main
estimated_scope: medium
---

## 背景

新架构下，Thinking Agent 和 Chat Agent 的交互方式完全改变：
- Thinking Agent：持久 session，通过 `sessions_send` 向 Chat Agent 发指令，管理 facts.json
- Chat Agent：收到用户消息 + Thinking 注入的指令，根据指令回复
- 废弃 intents.json 机制，facts.json 改由 Thinking Agent 管理

## 技术方案

### 重写：`~/.openclaw/workspace-thinking/AGENTS.md`

新 prompt 要点：
- **持久 session**：你有持续的记忆，不需要每次重新了解上下文
- **双触发模式**：
  - Cron 触发：获取 OCR 数据分析，有趣时通过 `sessions_send` 向 Chat Agent 发指令
  - 用户消息触发：收到用户消息，分析后通过 `sessions_send` 向 Chat Agent 发指令
- **指令格式**：自然语言指令，告诉 Chat Agent 如何回复用户
  - 例："用户在抱怨加班，关心一下他，语气轻松随意"
  - 例："用户在看美食视频，好奇地问他在看什么好吃的"
  - 例："用户问了一个普通问题，正常回答即可，不需要特别指导"
- **facts.json 管理**：用 write 工具维护 `~/.openclaw/workspace/facts.json`，记录用户偏好、习惯等
- **sessions_send 用法**：
  ```
  sessions_send(agentId: "chat", label: "main", message: "指令内容", timeoutSeconds: 0)
  ```
- **不再写 intents.json**

### 重写：`~/.openclaw/workspace-chat/AGENTS.md`

新 prompt 要点：
- **你是用户的聊天伙伴**，轻松随意，像发微信
- **你会收到来自内部系统的指导消息**（Agent-to-agent message），按照指导的方向回复用户
- **不要提及你收到了指导**，自然地融入对话
- **如果没有指导消息**，根据聊天上下文自由回复
- **不再读写 intents.json 和 facts.json**
- 保留原有的语气规则（短句、表情适度、不说"我注意到你的屏幕上..."）

### 废弃 intents.json

- 不需要修改代码（intents.json 是 Agent 通过 read/write 工具操作的文件，不是代码逻辑）
- 删除 `~/.openclaw/workspace/intents.json` 文件
- 从两个 AGENTS.md 中移除所有 intents 相关内容

### facts.json 改由 Thinking Agent 管理

- 保留 `~/.openclaw/workspace/facts.json` 文件
- Thinking Agent 的 AGENTS.md 中说明如何维护 facts
- Chat Agent 的 AGENTS.md 中移除 facts 相关内容

### Cron 触发 Chat Agent 的方式

Thinking Agent 在 Cron 模式下发现有趣内容时：
1. 通过 `sessions_send` 向 Chat session 注入指令
2. 然后用 `cron` 工具创建一次性任务触发 Chat Agent（保持现有方式）
3. Chat Agent 被触发后，session 中已有指令，据此主动发消息

## 验收标准

- [ ] Thinking Agent prompt 完整覆盖双触发模式
- [ ] Chat Agent prompt 正确处理 A2A 指令消息
- [ ] facts.json 由 Thinking Agent 维护
- [ ] intents.json 不再被任何 Agent 使用
- [ ] Cron 触发的主动聊天流程正常工作
- [ ] 用户消息触发的指令注入流程正常工作

## 测试要求

- [ ] 手动测试：Cron 触发 → Thinking 分析 → sessions_send 指令 → Chat 主动聊天
- [ ] 手动测试：用户发消息 → Thinking 分析 → sessions_send 指令 → Chat 回复
- [ ] 手动测试：Chat Agent 回复中不暴露指令来源

---
completed_by: w-7d3e
completed_at: 2026-02-09T13:30:00Z
commit: (prompt-only, runtime config files in ~/.openclaw/)
files_changed:
  - ~/.openclaw/workspace-thinking/AGENTS.md (rewritten - dual trigger, sessions_send, no intents)
  - ~/.openclaw/workspace-chat/AGENTS.md (rewritten - A2A guidance, no intents/facts)
test_result: "prompt files updated, manual testing required"
---
