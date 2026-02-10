---
id: "017"
title: "Screen Agent 两步编排 + 端到端集成测试"
priority: high
depends_on: ["015", "016"]
module: screen-agent
branch: feature/dual-session-chat
estimated_scope: medium
---

## 背景

Screen Agent 需要编排两步 hook 调用：
1. 发 OCR 到 Thinking Session → 等待分析完成 → intents.json 被更新
2. 触发 Chat Session → Chat Agent 读意图 → 主动和用户聊天

同时需要端到端验证整个流程。

## 技术方案

### 1. 两步编排逻辑

文件：`screen-agent/openclaw_client.py`

```python
def run_heartbeat(self, ocr_summary: str) -> bool:
    """完整的 heartbeat 流程"""
    # Step 1: Thinking
    result = self.send_to_thinking_session(ocr_summary)
    if not result.get("ok"):
        logger.warning(f"Thinking session failed: {result}")
        return False

    # Step 2: 触发 Chat（给 Chat Session 发一条触发消息）
    trigger_result = self.trigger_chat_session()
    return trigger_result.get("ok", False)

def trigger_chat_session(self) -> dict:
    """触发 Chat Agent 检查意图并主动聊天"""
    payload = {
        "message": "有新的屏幕观察，请查看 intents.json 中的待处理意图。",
        "name": "Screen Agent",
        "channel": "telegram",
        "to": "8168126294",
        "deliver": True,
        "wakeMode": "now",
        "sessionKey": "hook:screen-agent-chat",
    }
    resp = self.client.post(
        f"{self.base_url}/hooks/agent",
        headers={"Authorization": f"Bearer {self.token}"},
        json=payload,
    )
    return resp.json()
```

### 2. 等待 Thinking 完成

hooks 是异步的（立即返回 runId）。两种策略：
- **简单方案**：Step 1 后等待固定时间（如 30 秒）再触发 Step 2
- **轮询方案**：检查 intents.json 的修改时间判断是否完成

先用简单方案，后续优化。

### 3. 修改 main.py 主循环

将当前的 `send_message()` 替换为 `run_heartbeat()`。

### 4. 端到端测试流程

1. 启动 Recall（提供 OCR 数据）
2. 启动 OpenClaw（Gateway + Telegram Bot）
3. 运行 Screen Agent 一次 heartbeat
4. 验证：intents.json 被更新 → Telegram 收到消息
5. 在 Telegram 回复 → 验证 facts.json 被更新

## 验收标准

- [ ] Screen Agent 两步编排逻辑实现
- [ ] Thinking → Chat 的时序控制正确
- [ ] 错误处理：Thinking 失败时不触发 Chat
- [ ] 端到端流程跑通：OCR → 意图 → Telegram 消息 → 用户回复 → 事实记录
- [ ] DRY_RUN 模式仍然可用

## 测试要求

- [ ] 单元测试：两步编排的成功/失败路径
- [ ] 集成测试：手动运行一次完整 heartbeat 流程
- [ ] 验证 Telegram 收到自然的对话消息（非机械转发）
- [ ] 验证 facts.json 在用户回复后被更新

---
completed_by: w-7e3b
completed_at: 2026-02-08T16:45:00+08:00
commit: 0445b06
files_changed:
  - screen-agent/openclaw_client.py
  - screen-agent/main.py
  - screen-agent/test_thinking_session.py
test_result: "11 passed, 0 failed (单元测试); 集成测试需完整环境"
notes: |
  - run_heartbeat(): Thinking → 等待30s → Chat 触发
  - Thinking 失败时不触发 Chat（已测试验证）
  - DRY_RUN 模式跳过等待、打印 payload（已测试验证）
  - 端到端集成测试需要 Recall + OpenClaw + Telegram 同时运行
---
