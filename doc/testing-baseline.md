# 测试基线（task008）

## 目标链路

覆盖最小回归主流程：触发 -> 截图 -> OCR -> API 查询。

## 本地最小环境

1. Python 3.11+
2. Node.js 20+
3. 在仓库根目录执行：
   - `python -m pip install -r recall/requirements.txt`
   - `cd recall/frontend && npm install`
   - `cd recall/frontend && npx playwright install chromium`

## 一键回归

在仓库根目录执行：

```bash
./scripts/run_regression.sh
```

该命令按顺序运行：

1. 后端集成回归：
   - `recall/tests/test_regression_pipeline.py`
   - `recall/tests/test_api.py`
2. 前端单测 smoke：`npm run test:unit`
3. 前端 E2E smoke：`npm run test:e2e`

## CI 入口

已提供 GitHub Actions 流水线：

- 文件：`.github/workflows/regression.yml`
- 触发：`pull_request` 与 `main` 分支 push
- 执行内容：安装依赖 + Playwright 浏览器 + `./scripts/run_regression.sh`
