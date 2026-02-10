---
id: "027"
title: "Thinking Agent 持久 Session 支持"
priority: high
depends_on: []
module: openclaw
branch: main
estimated_scope: medium
---

## 背景

当前 Thinking Agent 每次 Cron 触发都创建新的 isolated session（`resolveCronSession()` 每次生成新 UUID）。这导致 Thinking Agent 没有连续性，每次都是全新上下文。需要改为持久 session，复用同一个 sessionId，依赖已有的 auto-compaction 机制处理 token 溢出。

## 技术方案

### 修改：`src/cron/isolated-agent/session.ts`

`resolveCronSession()` 当前逻辑：
```typescript
const sessionId = crypto.randomUUID(); // 每次新建
```

改为：
```typescript
const entry = store[params.sessionKey];
// 如果 store 中已有该 key 的 entry 且有 sessionId，复用它
const sessionId = (params.persistent && entry?.sessionId)
  ? entry.sessionId
  : crypto.randomUUID();
const isNewSession = sessionId !== entry?.sessionId;
```

新增 `persistent` 参数，由调用方传入。

### 修改：`src/cron/isolated-agent/run.ts`

`runCronIsolatedAgentTurn()` 中：
- 从 cron job 配置读取 `sessionTarget`（`"isolated"` | `"persistent"`）
- 传递 `persistent` 参数给 `resolveCronSession()`
- persistent 模式下，`runSessionKey` 不再追加 `:run:${runSessionId}`，直接使用 `agentSessionKey`

### 配置：`~/.openclaw/cron/jobs.json`

Thinking Agent 的 cron job 改为：
```json
{
  "sessionTarget": "persistent",
  ...
}
```

### 验证 auto-compaction

persistent session 会随时间增长。确认 `runEmbeddedPiAgent()` 中的 auto-compaction 机制（context overflow → `compactEmbeddedPiSessionDirect()`）在 cron 模式下正常工作。

## 验收标准

- [ ] Thinking Agent 的 cron 任务复用同一个 sessionId
- [ ] session transcript 文件持续追加，不会每次新建
- [ ] context overflow 时 auto-compaction 正常触发
- [ ] `sessionTarget: "isolated"` 的其他 cron job 行为不变
- [ ] persistent session 的 session store entry 正确更新（tokens、model 等）

## 测试要求

- [ ] 单元测试：`resolveCronSession()` persistent 模式复用 sessionId
- [ ] 单元测试：`resolveCronSession()` isolated 模式仍生成新 UUID
- [ ] 单元测试：persistent 模式下首次运行（无 entry）生成新 UUID

---
completed_by: w-7d3e
completed_at: 2026-02-09T13:30:00Z
commit: d935a6f84
files_changed:
  - openclaw/src/cron/isolated-agent/session.ts
  - openclaw/src/cron/isolated-agent/session.test.ts
  - openclaw/src/cron/isolated-agent/run.ts
  - openclaw/src/cron/types.ts
test_result: "27 passed, 0 failed"
---
