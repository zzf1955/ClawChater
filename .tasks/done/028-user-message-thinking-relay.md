---
id: "028"
title: "用户消息串行触发 Thinking → Chat"
priority: high
depends_on: ["027"]
module: openclaw
branch: main
estimated_scope: large
---

## 背景

当前用户在 Telegram 发消息时，消息直接路由到 Chat Agent。新架构要求：用户消息先发给 Thinking Agent 分析，Thinking Agent 通过 `sessions_send` 向 Chat Agent session 注入指令，然后 Chat Agent 再处理用户消息。串行执行，确保指令是最新的。

## 技术方案

### 核心流程

```
用户消息 → [拦截层] → Thinking Agent (持久 session)
                          │ sessions_send 指令到 Chat session
                          ▼
                      Chat Agent 处理用户消息（session 中已有指令）
                          │
                          ▼
                      回复用户
```

### 新文件：`src/agents/thinking-relay.ts`

```typescript
export async function relayToThinkingAgent(params: {
  userMessage: string;
  chatSessionKey: string;
  config: OpenClawConfig;
}): Promise<void>
```

功能：
1. 构建 Thinking Agent 的 prompt：包含用户消息 + 指示 Thinking Agent 分析并通过 `sessions_send` 向 Chat session 发指令
2. 通过 Gateway `agent` method 触发 Thinking Agent（复用持久 session）
3. 等待 Thinking Agent 完成（`agent.wait`）
4. 设置合理超时（如 30 秒），超时则跳过，让 Chat Agent 直接处理

### 修改：消息处理流程

**拦截点**：`src/auto-reply/reply/dispatch-from-config.ts` 中的 `getReplyFromConfig()` 或 `dispatchReplyFromConfig()`

在调用 `runReplyAgent()` 之前：
1. 检测是否为 Telegram DM（非 group，非 cron 触发）
2. 如果是，调用 `relayToThinkingAgent()`
3. 等待完成后，继续正常的 Chat Agent 流程

**关键约束**：
- 只对 Telegram DM 消息触发 relay，group 消息和 cron 触发的不走这个流程
- Thinking Agent 的 `sessions_send` 使用 `timeoutSeconds: 0`（fire-and-forget），因为我们在代码层等待 Thinking Agent 完成
- 需要确保 Thinking Agent 有 `sessions_send` 工具权限

### 配置要求

`openclaw.json` 中需要：
```json5
{
  tools: {
    agentToAgent: {
      enabled: true,
      allow: [
        { from: "thinking", to: "chat" }
      ]
    }
  }
}
```

### 错误处理

- Thinking Agent 超时：跳过，Chat Agent 正常处理（无指令或用旧指令）
- Thinking Agent 报错：记录日志，Chat Agent 正常处理
- Gateway 不可用：跳过 relay

## 验收标准

- [ ] 用户在 Telegram DM 发消息时，Thinking Agent 先被触发
- [ ] Thinking Agent 完成后，Chat Agent 收到用户消息 + Thinking 注入的指令
- [ ] Chat Agent 的回复基于指令内容
- [ ] Thinking Agent 超时不阻塞 Chat Agent
- [ ] Group 消息不触发 relay
- [ ] Cron 触发的 Chat Agent 不走 relay 流程

## 测试要求

- [ ] 单元测试：`relayToThinkingAgent()` 正常流程
- [ ] 单元测试：超时处理
- [ ] 单元测试：DM vs Group 消息的路由判断
- [ ] 集成测试：完整的 用户消息 → Thinking → Chat → 回复 流程

---
completed_by: w-7d3e
completed_at: 2026-02-09T13:15:00Z
commit: 61e4fd49a
files_changed:
  - openclaw/src/agents/thinking-relay.ts (NEW - relay module)
  - openclaw/src/agents/thinking-relay.test.ts (NEW - 11 tests)
  - openclaw/src/auto-reply/reply/dispatch-from-config.ts (intercept point)
  - openclaw/src/auto-reply/reply/commands-multi-session.ts (lint fix)
  - openclaw/src/auto-reply/reply/commands-multi-session.test.ts (format fix)
  - openclaw/src/auto-reply/reply/session-routing.test.ts (format fix)
  - openclaw/src/config/sessions/multi-session.ts (lint fix)
  - openclaw/src/config/sessions/multi-session.test.ts (lint fix)
  - openclaw/src/cron/isolated-agent/session.ts (format fix)
test_result: "906 passed, 0 failed (77 test files)"
---
