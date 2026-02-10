---
id: "007"
title: "更新文档 — CLAUDE.md 和 framework.md"
priority: low
depends_on: ["002", "003", "004", "005", "006"]
module: recall
branch: main
estimated_scope: small
---

## 背景

代码精简完成后，需要更新文档以反映新的架构。

## 技术方案

### 修改 `recall/CLAUDE.md`
- 项目结构中删除 llm.py、message_queue.py、curious_ai.py、memory/
- 删除 AI 相关注意事项
- 更新模块描述

### 修改 `recall/doc/framework.md`
- 删除记忆系统、AI 聊天相关架构描述
- 更新数据流图

### 修改根目录 `CLAUDE.md`
- 更新 Recall 模块描述（去掉记忆、AI 聊天相关内容）
- 更新架构图

## 验收标准

- [x] 文档准确反映精简后的架构
- [x] 无 AI/LLM/memory 相关描述残留
- [x] 数据流图只包含截图 → OCR → 存储 → Web 展示

## 测试要求

- [x] 无（文档任务）

---
completed_by: w-7e3b
completed_at: 2026-02-08T12:25:00+08:00
commit: 80c3787
files_changed:
  - recall/CLAUDE.md
  - recall/doc/framework.md
  - CLAUDE.md
test_result: "N/A - 文档任务"
---
