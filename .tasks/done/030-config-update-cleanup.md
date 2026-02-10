---
id: "030"
title: "配置更新 + 废弃旧任务清理"
priority: medium
depends_on: ["027"]
module: openclaw
branch: main
estimated_scope: small
---

## 背景

新架构需要更新 OpenClaw 配置和清理旧的 backlog 任务。

## 技术方案

### 配置更新：`~/.openclaw/openclaw.json`

1. **Cron job 配置**：Thinking Agent 的 cron job 改为 persistent session
```json5
{
  "sessionTarget": "persistent"  // 原来是 "isolated"
}
```

2. **A2A 通信启用**：
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

3. **Thinking Agent 工具权限**：确保包含 `sessions_send`
```json5
{
  agents: {
    entries: {
      thinking: {
        tools: ["web_fetch", "read", "write", "cron", "bash", "sessions_send"]
      }
    }
  }
}
```

### 废弃旧任务

将以下 backlog 任务移到 done（标记为 superseded）：
- `024-multi-session-data-model.md` → 被 027-030 替代
- `025-session-commands.md` → 被 027-030 替代
- `026-session-routing-integration.md` → 被 027-030 替代

### 清理文件

- 删除 `~/.openclaw/workspace/intents.json`（如果存在）

## 验收标准

- [ ] openclaw.json 配置正确更新
- [ ] Thinking Agent 有 sessions_send 工具权限
- [ ] A2A 通信配置正确
- [ ] 旧任务 024-026 标记为 superseded
- [ ] intents.json 已删除

## 测试要求

- [ ] Gateway 启动正常（`pnpm start gateway`）
- [ ] `node openclaw.mjs gateway health` 返回正常
- [ ] Thinking Agent 的 cron job 正确加载 persistent 配置

---
completed_by: w-7d3e
completed_at: 2026-02-09T12:00:00Z
commit: (config-only, no git commit — runtime config files in ~/.openclaw/)
files_changed:
  - ~/.openclaw/openclaw.json (added sessions_send tool, agentToAgent config)
  - ~/.openclaw/cron/jobs.json (sessionTarget: persistent)
  - ~/.openclaw/workspace/intents.json (deleted)
  - .tasks/done/024-multi-session-data-model.md (already in done)
  - .tasks/done/025-session-commands.md (already in done)
  - .tasks/done/026-session-routing-integration.md (already in done)
test_result: "config validation passed, JSON valid"
---
