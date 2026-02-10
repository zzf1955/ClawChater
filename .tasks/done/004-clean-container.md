---
id: "004"
title: "清理 container.py — 删除 AI 相关服务注册"
priority: high
depends_on: ["001"]
module: recall
branch: main
estimated_scope: small
---

## 背景

core/container.py 的依赖注入容器中注册了 text_memory、vector_memory、summarizer、extractor、message_queue、llm_service 等 AI 相关服务，需要全部删除。

## 技术方案

修改 `recall/core/container.py`：

### 删除 TYPE_CHECKING 导入
- `from message_queue import MessageQueue`
- `from llm import LLMService`
- `from memory.text_memory import TextMemory`
- `from memory.vector_memory import VectorMemory`
- `from memory.summarizer import ActivitySummarizer`
- `from memory.extractor import MemoryExtractor`

### 删除 Container 类的属性
- `text_memory`
- `vector_memory`
- `summarizer`
- `extractor`
- `message_queue`
- `llm_service`

Container 只保留 `database` 属性和 `AppConfig`。

## 验收标准

- [x] Container 类只包含 config、database、reset
- [x] 无 AI/memory 相关导入
- [x] 无语法错误

## 测试要求

- [x] Python 可正常 `from core.container import Container` 无报错

---
completed_by: w-7e3b
completed_at: 2026-02-08T12:15:00+08:00
commit: 9602620
files_changed:
  - recall/core/container.py
test_result: "import 验证通过"
---
