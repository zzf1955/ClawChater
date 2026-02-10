---
id: "011"
title: "清理 config.py 配置不一致"
priority: high
depends_on: []
module: recall
branch: main
estimated_scope: small
---

## 背景

`config.py` 中存在两套配置值：`DEFAULT_SETTINGS` 字典和模块级变量。两者的值不一致，例如：
- `FORCE_CAPTURE_INTERVAL`: DEFAULT_SETTINGS=300, 模块级=1111
- `MIN_CAPTURE_INTERVAL`: DEFAULT_SETTINGS=10, 模块级=5
- `JPEG_QUALITY`: DEFAULT_SETTINGS=85, 模块级=100

新代码使用 `config.get()` 读取数据库/默认值，旧代码可能使用 `config.JPEG_QUALITY` 等模块级变量。这导致行为不一致。

## 技术方案

### 1. 检查模块级变量的使用情况

搜索所有 `config.FORCE_CAPTURE_INTERVAL`、`config.MIN_CAPTURE_INTERVAL`、`config.JPEG_QUALITY` 等模块级变量的引用。

### 2. 统一配置读取方式

- 将所有模块级变量的引用改为 `config.get('KEY')`
- 删除 `config.py` 第 73-85 行的模块级变量（除 `SCREENSHOT_DIR`）
- `SCREENSHOT_DIR` 保留，因为它是路径常量，不需要热更新

### 3. 需要检查的文件

- `recall/ocr_worker.py` — 可能使用 `config.GPU_USAGE_THRESHOLD`、`config.OCR_BATCH_SIZE`
- `recall/web/app.py` — 使用 `config.SCREENSHOT_DIR`
- `recall/core/capture.py` — 已使用 `config.get()` ✅
- `recall/utils/` 下的文件

## 验收标准

- [x] `config.py` 中模块级变量只保留 `SCREENSHOT_DIR`
- [x] 所有代码统一使用 `config.get('KEY')` 读取配置
- [x] 现有测试全部通过

## 测试要求

- [x] 运行 `pytest tests/ -v` 确保所有测试通过
- [x] 检查 `config.get()` 能正确返回默认值和数据库值

---
completed_by: w-7e3b
completed_at: 2026-02-08T12:10:00+08:00
commit: 8d0bfcd
files_changed:
  - recall/config.py
  - recall/ocr_worker.py
test_result: "17 passed, 0 failed"
---
