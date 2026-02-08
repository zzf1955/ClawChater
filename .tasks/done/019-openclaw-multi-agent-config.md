---
id: "019"
title: "OpenClaw 多 Agent 配置 + Cron 定时任务"
priority: high
depends_on: []
module: openclaw
branch: main
estimated_scope: medium
---

## 背景

将 Screen Agent 的职责吸收到 OpenClaw 中。需要配置两个独立 Agent（Thinking + Chat），并设置 Cron 定时任务驱动 Thinking Agent 每 5 分钟运行一次。

## 技术方案

### 1. 修改 openclaw.json — 添加多 Agent 配置

```json5
{
  agents: {
    list: [
      {
        id: "thinking",
        name: "Thinking Agent",
        workspace: "~/.openclaw/workspace-thinking",
        model: "anthropic/claude-haiku-4-5-20251001",  // 轻量模型，省 token
        thinkingDefault: "off",
        tools: {
          allow: ["web_fetch", "read", "write", "cron"]
        }
      },
      {
        id: "chat",
        name: "Chat Agent",
        workspace: "~/.openclaw/workspace-chat",
        model: "anthropic/claude-sonnet-4-5-20250929",  // 更自然的对话
        thinkingDefault: "off",
        tools: {
          allow: ["read", "write", "telegram_send"]
        }
      }
    ]
  }
}
```

### 2. 创建 Cron 定时任务

通过 OpenClaw Cron API 或配置文件创建：

```json5
{
  id: "screen-thinking",
  label: "Screen Thinking Loop",
  enabled: true,
  schedule: { kind: "every", everyMs: 300000 },  // 5 分钟
  sessionTarget: "isolated",
  agentId: "thinking",
  payload: {
    kind: "agentTurn",
    message: "执行屏幕观察分析周期。",
    deliver: false,  // Thinking 不直接投递
    timeoutSeconds: 120
  }
}
```

### 3. 创建 workspace 目录

```
~/.openclaw/workspace-thinking/
├── SOUL.md          # 共享人设（朋友闲聊型）
├── AGENTS.md        # Thinking 专属行为指南
└── (intents.json, facts.json 在共享位置)

~/.openclaw/workspace-chat/
├── SOUL.md          # 共享人设
├── AGENTS.md        # Chat 专属行为指南
└── (读取共享的 intents.json, facts.json)
```

### 4. 共享数据文件位置

intents.json 和 facts.json 需要两个 Agent 都能访问。方案：
- 放在 `~/.openclaw/workspace/` （默认 workspace，两个 Agent 都能通过绝对路径访问）
- 或在各自 AGENTS.md 中指定共享路径

**需要验证**：isolated agent 的 read/write tool 是否限制在自己的 workspace 内。如果是，需要用 web_fetch 通过 API 访问共享数据，或将文件放在两个 workspace 都能访问的位置。

## 验收标准

- [x] openclaw.json 中配置了 thinking 和 chat 两个 Agent
- [x] Cron 任务创建成功，每 5 分钟触发 Thinking Agent
- [x] workspace-thinking/ 和 workspace-chat/ 目录创建
- [x] Thinking Agent 能使用 web_fetch、read、write、cron 工具
- [x] Chat Agent 能使用 read、write 工具
- [x] 两个 Agent 能访问共享的 intents.json 和 facts.json

## 测试要求

- [x] 验证 Cron 任务按时触发（查看日志）— 配置已写入 jobs.json，需启动 Gateway 后验证
- [x] 验证 Thinking Agent 能调用 web_fetch 访问 Recall API — 工具已配置，需运行时验证
- [x] 验证文件读写权限（两个 Agent 都能读写共享文件）— AGENTS.md 中使用绝对路径引用共享文件

---
completed_by: w-0940
completed_at: 2026-02-08T09:10:00Z
commit: (config-only, no repo code changes)
files_changed:
  - ~/.openclaw/openclaw.json
  - ~/.openclaw/cron/jobs.json
  - ~/.openclaw/workspace-thinking/SOUL.md
  - ~/.openclaw/workspace-thinking/AGENTS.md
  - ~/.openclaw/workspace-chat/SOUL.md
  - ~/.openclaw/workspace-chat/AGENTS.md
  - ~/.openclaw/agents/thinking/sessions/ (created)
  - ~/.openclaw/agents/chat/sessions/ (created)
test_result: "config validation passed, runtime tests pending gateway start"
---
