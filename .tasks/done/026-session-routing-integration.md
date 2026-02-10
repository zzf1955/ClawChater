---
id: "026"
title: "Session 路由集成 + Thinking Agent 衔接"
priority: high
depends_on: ["024", "025"]
module: openclaw
branch: main
estimated_scope: medium
---

## 背景

024 实现了数据模型，025 实现了命令。本任务将多 session 路由集成到消息处理主流程，并确保 Thinking Agent 的主动聊天正确加入当前活跃 session。

## 技术方案

### 修改：`src/config/sessions/session-key.ts`

`resolveSessionKey()` 需要感知多 session 路由：

```typescript
export function resolveSessionKey(scope, ctx, mainKey) {
  const explicit = ctx.SessionKey?.trim();
  if (explicit) return explicit.toLowerCase();

  const raw = deriveSessionKey(scope, ctx);
  if (scope === "global") return raw;

  const isGroup = raw.includes(":group:") || raw.includes(":channel:");
  if (isGroup) {
    return `agent:${DEFAULT_AGENT_ID}:${raw}`;
  }

  // 多 session 路由：查询活跃 session
  // 需要从调用方传入 storePath 或 routing 信息
  // 如果有活跃 session 且不是 "default"，拼接到 key 中
  const canonicalMainKey = normalizeMainKey(mainKey);
  const canonical = buildAgentMainSessionKey({ agentId, mainKey: canonicalMainKey });

  if (activeSessionName && activeSessionName !== "default") {
    return `${canonical}:${activeSessionName}`;
  }
  return canonical;
}
```

**注意**：`resolveSessionKey` 当前是纯函数，不读文件。为了不破坏签名，改为在 `initSessionState()` 中处理路由逻辑——先调用 `resolveActiveSessionKey()` 获取活跃 session key，然后直接设置到 ctx.SessionKey 上。

### 修改：`src/auto-reply/reply/session.ts`

在 `initSessionState()` 开头，DM 场景下：
1. 加载 routing 元数据
2. 获取活跃 session 名
3. 将活跃 session 的完整 key 设置到 `sessionCtxForState.SessionKey`
4. 后续流程自然使用正确的 session key

### Thinking Agent 衔接

Thinking Agent 通过 intent 触发 Chat Agent 时，消息也会经过 `initSessionState()`。由于我们在 `initSessionState()` 中统一处理路由，Thinking Agent 的消息会自动路由到当前活跃 session。

**验证路径**：
1. Thinking Agent 写入 intent
2. Chat Agent 被触发（通过 cron 或 webhook）
3. `initSessionState()` 查询 routing → 获取活跃 session key
4. 消息加入活跃 session 的 transcript

### 端到端测试场景

1. 用户在 TG 发消息 → 路由到活跃 session
2. `/new coding` → 创建 coding session，后续消息路由到 coding
3. `/switch default` → 切回 default，后续消息路由到 default
4. Thinking Agent 触发主动聊天 → 加入当前活跃 session

## 验收标准

- [ ] DM 消息正确路由到活跃 session
- [ ] 切换 session 后，新消息进入新 session
- [ ] 切换 session 后，旧 session 的历史不丢失
- [ ] Thinking Agent 主动聊天进入当前活跃 session
- [ ] Group 消息不受影响（仍然按 group ID 隔离）
- [ ] 现有 `/reset` 命令仍然正常工作（重置当前活跃 session）

## 测试要求

- [ ] 集成测试：消息路由到正确的 session
- [ ] 集成测试：session 切换后消息路由变化
- [ ] 集成测试：Thinking Agent 触发的消息路由
- [ ] 回归测试：group 消息路由不受影响

---
completed_by: w-7d3e
completed_at: 2026-02-09T13:00:00Z
commit: be29f17bf
files_changed:
  - openclaw/src/auto-reply/reply/session.ts
  - openclaw/src/auto-reply/reply/session-routing.test.ts
test_result: "86 passed, 0 failed"
---
