---
id: "015"
title: "实现 Thinking Session — 后台 OCR 分析与意图生成"
priority: high
depends_on: ["014"]
module: screen-agent
branch: feature/dual-session-chat
estimated_scope: medium
---

## 背景

Screen Agent 当前通过 `/hooks/agent` 发送 OCR 数据，使用隔离 session。
需要改为使用持久化的 Thinking Session，让 agent 能积累上下文，
并将分析结果写入 intents.json 而非直接投递到 Telegram。

## 技术方案

### 1. 修改 Screen Agent 的 hook 调用

文件：`screen-agent/openclaw_client.py`

```python
def send_to_thinking_session(self, ocr_summary: str) -> dict:
    """发送 OCR 数据到 Thinking Session"""
    prompt = self._build_thinking_prompt(ocr_summary)
    payload = {
        "message": prompt,
        "name": "Screen Agent",
        "sessionKey": "hook:screen-agent-thinking",  # 持久化 session
        "deliver": False,  # 不投递到 Telegram
        "wakeMode": "now",
    }
    resp = self.client.post(
        f"{self.base_url}/hooks/agent",
        headers={"Authorization": f"Bearer {self.token}"},
        json=payload,
    )
    return resp.json()
```

### 2. Thinking Prompt 模板

在 hook message 中嵌入角色指令（因为 hook session 没有独立 system prompt）：

```
你是一个屏幕活动分析助手。你的任务是分析用户的屏幕活动，生成观察和问题。

## 你的工作流程
1. 用 read 工具读取 facts.json，了解已知事实（避免重复提问）
2. 分析下面的 OCR 数据
3. 如果发现值得聊的内容，用 write 工具更新 intents.json
4. 只添加新意图，保留未处理的旧意图

## 当前 OCR 数据
{ocr_summary}
```

### 3. 修改 Screen Agent 主循环

文件：`screen-agent/main.py`

将当前的 `send_message()` 改为两步：
1. `send_to_thinking_session(ocr_summary)` — 分析
2. `trigger_chat_session()` — 触发 Chat Agent（见任务 017）

## 验收标准

- [ ] Screen Agent 使用持久化 sessionKey 发送 OCR
- [ ] deliver 设为 False（不直接投递）
- [ ] Thinking prompt 模板包含读 facts.json、写 intents.json 的指令
- [ ] Agent 能正确调用 read/write 工具操作 workspace 文件
- [ ] 手动调用 hook 后，intents.json 被正确更新

## 测试要求

- [ ] 手动 POST /hooks/agent 验证 thinking session 工作
- [ ] 验证 intents.json 被正确写入
- [ ] 验证 facts.json 被正确读取（不报错）
- [ ] 验证 session 历史被保留（第二次调用能看到之前的上下文）

---
completed_by: w-7e3b
completed_at: 2026-02-08T16:15:00+08:00
commit: 17c7b29
files_changed:
  - screen-agent/openclaw_client.py
  - screen-agent/main.py
  - screen-agent/test_thinking_session.py
test_result: "6 passed, 0 failed (单元测试); 集成测试需 OpenClaw 运行环境"
---
