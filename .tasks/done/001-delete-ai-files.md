---
id: "001"
title: "删除 AI/LLM 相关文件和目录"
priority: high
depends_on: []
module: recall
branch: main
estimated_scope: small
---

## 背景

精简 recall 模块，去掉所有 AI 聊天/记忆功能，使其成为纯截图工具 + 数据库。第一步是删除不再需要的文件。

## 技术方案

删除以下文件和目录：

### 目录
- `recall/memory/` — 整个记忆系统（text_memory, vector_memory, summarizer, extractor）

### Python 文件（仅 .pyc 存在的）
- `recall/__pycache__/llm.cpython-311.pyc`
- `recall/__pycache__/curious_ai.cpython-311.pyc`
- `recall/__pycache__/message_queue.cpython-311.pyc`

### 测试文件
- `recall/tests/unit/test_curious_ai.py`
- `recall/tests/unit/test_message_queue.py`
- `recall/tests/unit/test_text_memory.py`

### 脚本文件
- `recall/scripts/test_llm.py`
- `recall/scripts/test_tools.py`

### 前端文件
- `recall/web/frontend/src/views/ChatView.vue`
- `recall/web/frontend/src/views/AILogView.vue`
- `recall/web/frontend/src/components/MarkdownRenderer.vue`

## 验收标准

- [x] 上述所有文件和目录已删除
- [x] 没有误删截图相关文件
- [x] git status 确认删除正确

## 测试要求

- [x] 删除后无需运行测试（后续任务会修改引用并测试）

---
completed_by: w-7e3b
completed_at: 2026-02-08T12:00:00+08:00
commit: 0bbd665
files_changed:
  - recall/memory/__init__.py
  - recall/memory/extractor.py
  - recall/memory/summarizer.py
  - recall/memory/text_memory.py
  - recall/memory/vector_memory.py
  - recall/scripts/test_llm.py
  - recall/scripts/test_tools.py
  - recall/tests/unit/test_curious_ai.py
  - recall/tests/unit/test_message_queue.py
  - recall/tests/unit/test_text_memory.py
  - recall/web/frontend/src/components/MarkdownRenderer.vue
  - recall/web/frontend/src/views/AILogView.vue
  - recall/web/frontend/src/views/ChatView.vue
test_result: "N/A - 删除任务无需测试"
---
