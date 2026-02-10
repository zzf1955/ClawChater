---
id: "025"
title: "Session 管理命令拦截 + TG 响应"
priority: high
depends_on: ["024"]
module: openclaw
branch: main
estimated_scope: medium
---

## 背景

用户需要在 Telegram 中通过斜杠命令管理 session：`/new`、`/switch`、`/list`、`/rename`、`/delete`、`/current`。这些命令应该被拦截，直接返回结果，不经过 LLM。

## 技术方案

### 命令定义

| 命令 | 功能 | 响应 |
|------|------|------|
| `/new [name]` | 创建新 session 并切换 | "✅ 已创建并切换到 session: {name}" |
| `/switch <name>` | 切换到已有 session | "✅ 已切换到 session: {name}" |
| `/list` | 列出所有 session | 表格：名称、创建时间、是否活跃 |
| `/rename <new>` | 重命名当前 session | "✅ 已重命名: {old} → {new}" |
| `/delete <name>` | 删除指定 session | "✅ 已删除 session: {name}" |
| `/current` | 显示当前 session | "当前 session: {name} (创建于 ...)" |

### 修改：`src/auto-reply/reply/session.ts`

在 `initSessionState()` 的 reset trigger 检测之前，新增 session 管理命令检测：

```typescript
// 检测 session 管理命令
const sessionCmd = parseSessionCommand(triggerBodyNormalized);
if (sessionCmd) {
  // 执行命令，返回特殊标记
  const result = await executeSessionCommand(sessionCmd, storePath, agentId);
  // 设置 bodyStripped 为空，标记为管理命令
  // ...
}
```

### 修改：`src/auto-reply/reply/get-reply.ts`

在 agent runner 之前检查是否是 session 管理命令，如果是，直接构建文本响应 payload 返回，跳过 LLM 调用。

### 新文件：`src/config/sessions/session-commands.ts`

命令解析和执行逻辑：
- `parseSessionCommand(body)` — 解析命令，返回 `{ type, args }` 或 null
- `executeSessionCommand(cmd, storePath, agentId)` — 执行命令，返回响应文本
- `formatSessionList(sessions, active)` — 格式化 `/list` 输出

### 修改现有 `/new` 行为

当前 `/new` 是 reset trigger，会创建新 sessionId 但保持同一个 session key。改为：
- `/new` → 调用 `createNamedSession()`，创建新的命名 session 并切换
- `/new` 不再作为 reset trigger（从 `DEFAULT_RESET_TRIGGERS` 中移除或优先匹配 session 命令）
- `/reset` 保留原有行为（重置当前 session 的历史）

## 验收标准

- [ ] 所有 6 个命令正确解析和执行
- [ ] 命令响应直接返回，不经过 LLM
- [ ] `/new` 创建新命名 session 并切换
- [ ] `/new` 不带名字时自动编号（session-1, session-2...）
- [ ] `/switch` 到不存在的 session 时给出友好错误
- [ ] `/delete` 不能删除当前活跃 session
- [ ] `/list` 输出清晰标记当前活跃 session
- [ ] `/reset` 保留原有行为（重置当前 session 历史）

## 测试要求

- [ ] 单元测试：命令解析（各种格式、大小写、带参数/不带参数）
- [ ] 单元测试：命令执行（正常流程 + 错误情况）
- [ ] 集成测试：命令拦截不触发 LLM

---
completed_by: w-7d3e
completed_at: 2026-02-09T12:30:00Z
commit: 50c8f3ed6
files_changed:
  - openclaw/src/auto-reply/reply/commands-multi-session.ts
  - openclaw/src/auto-reply/reply/commands-multi-session.test.ts
  - openclaw/src/auto-reply/reply/commands-core.ts
  - openclaw/src/auto-reply/reply/commands.test.ts
  - openclaw/src/auto-reply/reply/session.test.ts
  - openclaw/src/config/sessions/types.ts
test_result: "81 passed, 0 failed"
---
