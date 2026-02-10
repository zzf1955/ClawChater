---
id: "003"
title: "清理 config.py — 删除 LLM 和 CuriousAI 配置"
priority: high
depends_on: ["001"]
module: recall
branch: main
estimated_scope: small
---

## 背景

config.py 包含 LLM API Key、Base URL、Model 以及 CuriousAI 相关配置，需要全部删除。

## 技术方案

修改 `recall/config.py`：

### 删除 DEFAULT_SETTINGS 中的项
- `AI_EXPLORE_INTERVAL`
- `AI_MIN_QUESTION_INTERVAL`
- `AI_ENABLED`

### 删除模块级常量
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL`
- `AI_EXPLORE_INTERVAL`（兼容变量）
- `AI_MIN_QUESTION_INTERVAL`（兼容变量）
- `AI_ENABLED`（兼容变量）

## 验收标准

- [x] config.py 只包含截图、OCR、数据聚合相关配置
- [x] 无 LLM/AI 相关配置残留
- [x] 无语法错误

## 测试要求

- [x] Python 可正常 import config 无报错

---
completed_by: w-d4a1
completed_at: 2026-02-08T00:00:00+08:00
commit: ea1eeb5
files_changed:
  - recall/config.py
test_result: "import config OK, 0 failed"
---
