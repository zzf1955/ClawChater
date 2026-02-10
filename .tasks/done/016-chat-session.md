---
id: "016"
title: "实现 Chat Session — Telegram 双向聊天与事实提取"
priority: high
depends_on: ["014"]
module: openclaw
branch: feature/dual-session-chat
estimated_scope: medium
---

## 背景

OpenClaw 的 Telegram Bot 已有接收消息和调用 Agent 回复的完整代码框架。
需要：
1. 确保 Telegram DM 双向聊天能跑通
2. 配置 Chat Agent 的 system prompt，使其能读取 intents.json 并与用户自然聊天
3. Chat Agent 在对话中提取事实，写入 facts.json

## 技术方案

### 1. 验证 Telegram 双向聊天

确认 OpenClaw 配置中 Telegram 相关设置正确：
- `plugins.entries.telegram.enabled: true`（已配置）
- Bot token 正确
- 用户 allowlist 包含 8168126294
- auto-reply 已启用

手动在 Telegram 给 bot 发消息，验证能收到回复。

### 2. 配置 Agent System Prompt

在 agent workspace 的 AGENT.md 或 OpenClaw 配置中添加指令：

```markdown
## 意图处理
每次收到触发消息时，用 read 工具读取 intents.json。
如果有 status: "pending" 的意图，自然地融入对话中。
不要机械地逐条询问，而是像朋友一样聊天。

## 事实记录
当用户分享了新信息（计划、偏好、事实），用 read 工具读取 facts.json，
追加新事实后用 write 工具写回。每条事实关联对应的 intent ID。

## 对话风格
- 像朋友一样自然聊天，不要像问卷调查
- 一次只聊一个话题
- 如果用户不想聊某个话题，标记该 intent 为 expired
```

### 3. 处理 Hook 触发的主动对话

当 Screen Agent 触发 Chat Session 时（通过 hooks），Chat Agent 需要：
1. 读取 intents.json 中的 pending 意图
2. 选择最合适的意图发起对话
3. 将已发起的意图标记为 delivered

Hook 触发消息格式：
```
有新的屏幕观察，请查看 intents.json 中的待处理意图，
选择合适的话题和用户聊天。
```

## 验收标准

- [ ] Telegram DM 双向聊天跑通（用户发消息 → agent 回复）
- [ ] Agent system prompt 包含意图处理和事实记录指令
- [ ] Agent 能读取 intents.json 并自然发起对话
- [ ] Agent 能将用户分享的信息写入 facts.json
- [ ] Hook 触发的主动对话正常工作

## 测试要求

- [ ] 手动在 Telegram 发消息验证双向聊天
- [ ] 手动触发 hook 验证主动对话
- [ ] 验证 facts.json 在对话后被正确更新
- [ ] 验证 intents.json 中意图状态被正确更新

---
completed_by: w-7e3b
completed_at: 2026-02-08T16:30:00+08:00
commit: c3cd917 (workspace repo)
files_changed:
  - ~/.openclaw/workspace/AGENTS.md
  - ~/.openclaw/openclaw.json (已验证配置正确，无需修改)
test_result: "配置验证通过; 集成测试需 OpenClaw 运行环境"
notes: |
  - AGENTS.md 添加了 Screen Agent Protocol 章节（意图处理 + 事实记录）
  - Telegram 配置已验证：enabled, allowlist, bot token, proxy 均正确
  - PROTOCOL.md 不在 workspace 自动加载列表中，指令已合并到 AGENTS.md
  - 集成测试（Telegram DM、hook 触发）需要启动 OpenClaw 后手动验证
---
