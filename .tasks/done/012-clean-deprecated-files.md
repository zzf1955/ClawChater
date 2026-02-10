---
id: "012"
title: "清理废弃脚本和旧版前端文件"
priority: medium
depends_on: []
module: recall
branch: main
estimated_scope: small
---

## 背景

之前清理 AI/LLM 代码时（任务 001-007），部分废弃文件和引用未被清理干净。同时 Vue 前端上线后，旧版静态前端文件仍然存在。

## 技术方案

### 1. 删除旧版前端文件

- `recall/web/static/app.js` — 旧版 JS，已被 Vue 前端替代
- `recall/web/static/style.css` — 旧版 CSS，已被 Vue 前端替代
- `recall/web/templates/index.html` — 旧版 Jinja2 模板，已被 Vue SPA 替代
- 删除 `recall/web/templates/` 目录（如果为空）

### 2. 清理脚本中的 AI 引用

**`scripts/test_config.py`**：
- 删除 `AI_EXPLORE_INTERVAL`、`AI_ENABLED` 等 AI 配置引用
- 更新硬编码路径 `D:/BaiduSyncdisk/Desktop/recall` → 使用相对路径

**`scripts/test_api_config.py`**：
- 删除 `AI_EXPLORE_INTERVAL`、`AI_MIN_QUESTION_INTERVAL`、`AI_ENABLED` 引用

### 3. 修复硬编码路径

**`scripts/create_icon.py`**：
- 修复 `D:/BaiduSyncdisk/Desktop/recall/assets/icon.ico` → 使用 `Path(__file__).parent.parent`

**`scripts/test_config.py`**：
- 修复 `sys.path.insert(0, 'D:/BaiduSyncdisk/Desktop/recall')` → 使用相对路径

## 验收标准

- [x] 旧版前端文件已删除（app.js, style.css, templates/index.html）
- [x] 脚本中无 AI 配置引用
- [x] 脚本中无硬编码的旧路径
- [x] 现有测试全部通过

## 测试要求

- [x] 运行 `pytest tests/ -v` 确保测试通过
- [x] 前端仍能正常构建和访问

---
completed_by: w-7e3b
completed_at: 2026-02-08T12:20:00+08:00
commit: f2ee9cf
files_changed:
  - recall/web/static/app.js (deleted)
  - recall/web/static/style.css (deleted)
  - recall/web/templates/index.html (deleted)
  - recall/scripts/test_config.py
  - recall/scripts/test_api_config.py
  - recall/scripts/create_icon.py
test_result: "17 passed, 0 failed"
---
