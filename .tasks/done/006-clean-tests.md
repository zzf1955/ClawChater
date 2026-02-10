---
id: "006"
title: "清理 conftest.py 和剩余测试中的 AI 引用"
priority: medium
depends_on: ["002", "003", "004"]
module: recall
branch: main
estimated_scope: small
---

## 背景

tests/conftest.py 中可能包含 Mock LLM、AI 相关 fixtures，需要清理。同时检查其他测试文件是否有 AI 相关引用。

## 技术方案

### 修改 `recall/tests/conftest.py`
- 删除 Mock LLM 相关 fixtures
- 删除 memory 相关 fixtures
- 删除 message_queue 相关 fixtures
- 保留数据库、截图相关 fixtures

### 检查并修改
- `recall/tests/unit/test_db.py` — 删除 AI 消息/对话相关测试用例
- `recall/tests/integration/test_web_api.py` — 删除 AI 相关 API 测试

## 验收标准

- [x] conftest.py 无 AI/LLM/memory 相关 fixtures
- [x] 所有测试文件无 AI 相关引用
- [x] `pytest tests/ -v` 全部通过

## 测试要求

- [x] `pytest tests/ -v` 全部通过

---
completed_by: w-7e3b
completed_at: 2026-02-08T12:20:00+08:00
commit: bfe17a2
files_changed:
  - recall/tests/conftest.py
  - recall/tests/integration/test_web_api.py
test_result: "15 passed, 0 failed"
---
