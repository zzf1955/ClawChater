---
id: "024"
title: "多 Session 数据模型 + 路由元数据"
priority: high
depends_on: []
module: openclaw
branch: main
estimated_scope: medium
---

## 背景

当前所有 Telegram DM 消息都路由到 `agent:chat:main` 一个 session。需要支持多个命名 session，用户可以在 TG 单聊窗口中切换。

## 技术方案

### 新文件：`src/config/sessions/multi-session.ts`

实现 session 路由元数据的 CRUD：

```typescript
interface SessionRouting {
  activeSession: string;  // 当前活跃 session 名称，如 "default"
  sessions: Record<string, {
    createdAt: number;
    label?: string;       // 用户可读的显示名
  }>;
  nextAutoId: number;     // 自动编号计数器
}
```

**路由元数据存储**：在 `sessions.json` 中使用特殊 key `agent:{agentId}:_routing` 存储。

**核心函数**：
- `loadSessionRouting(storePath, agentId)` — 加载路由元数据，不存在则返回默认值（activeSession="default"）
- `saveSessionRouting(storePath, agentId, routing)` — 保存路由元数据
- `resolveActiveSessionKey(storePath, agentId)` — 返回当前活跃 session 的完整 key
- `createNamedSession(storePath, agentId, name?)` — 创建新 session，无名则自动编号
- `switchSession(storePath, agentId, name)` — 切换活跃 session
- `listSessions(storePath, agentId)` — 列出所有 session 及状态
- `deleteNamedSession(storePath, agentId, name)` — 删除 session（不能删活跃的）
- `renameSession(storePath, agentId, oldName, newName)` — 重命名

**向后兼容**：
- 如果 `_routing` 不存在，自动创建，将现有 `agent:chat:main` 映射为 `default` session
- `default` session 的 store key 保持 `agent:chat:main`（不变）
- 其他 session 的 store key 为 `agent:chat:main:{name}`

### 修改：`src/config/sessions/session-key.ts`

`resolveSessionKey()` 在返回 DM session key 时，查询路由元数据获取活跃 session 名，拼接到 key 中。

## 验收标准

- [ ] `multi-session.ts` 实现所有 CRUD 函数
- [ ] 路由元数据正确持久化到 sessions.json
- [ ] 向后兼容：无 `_routing` 时自动初始化，现有 session 不受影响
- [ ] `default` session 的 key 保持 `agent:chat:main`
- [ ] 其他 session 的 key 格式为 `agent:chat:main:{name}`

## 测试要求

- [ ] 单元测试：CRUD 操作（创建、切换、列表、删除、重命名）
- [ ] 单元测试：向后兼容（无 routing 时的初始化）
- [ ] 单元测试：自动编号逻辑
- [ ] 单元测试：边界情况（删除活跃 session、重命名为已存在名称）

---
completed_by: w-7d3e
completed_at: 2026-02-09T12:00:00Z
commit: afe2eda35
files_changed:
  - openclaw/src/config/sessions/multi-session.ts
  - openclaw/src/config/sessions/multi-session.test.ts
test_result: "24 passed, 0 failed"
---
