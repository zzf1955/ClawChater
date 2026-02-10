---
id: "002"
title: "清理 db.py — 删除 AI 消息/对话/日志相关表和方法"
priority: high
depends_on: ["001"]
module: recall
branch: main
estimated_scope: medium
---

## 背景

db.py 中包含大量 AI 聊天相关的数据库表和方法，需要全部清理。

## 技术方案

修改 `recall/db.py`：

### 删除数据库表（init_db 中）
- `conversations` 表
- `ai_messages` 表
- `ai_logs` 表
- 相关索引

### 删除方法（Database 类）
- `_migrate_ai_messages_table()`
- `_migrate_messages()`
- `add_ai_message()`
- `get_ai_messages_since()`
- `get_recent_ai_messages()`
- `get_messages_by_conversation()`
- `update_message()`
- `clear_ai_messages()`
- `create_conversation()`
- `get_conversation()`
- `get_all_conversations()`
- `get_active_conversation()`
- `set_active_conversation()`
- `update_conversation()`
- `delete_conversation()`
- `add_ai_log()`
- `get_recent_ai_logs()`

### 删除向后兼容层函数
- 所有对应的模块级兼容函数（add_ai_message, get_ai_messages_since 等）

## 验收标准

- [x] Database 类只保留截图、分组、配置相关方法
- [x] init_db() 只创建 screenshots、groups、settings 表
- [x] 向后兼容层只保留截图和配置相关函数
- [x] 无语法错误

## 测试要求

- [x] `pytest tests/unit/test_db.py -v` 通过
- [x] 如果 test_db.py 中有 AI 相关测试，一并删除

---
completed_by: w-7e3b
completed_at: 2026-02-08T12:10:00+08:00
commit: 64dacc8
files_changed:
  - recall/db.py
  - recall/tests/unit/test_db.py
test_result: "8 passed, 0 failed"
---
