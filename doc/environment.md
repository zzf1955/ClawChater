# 开发环境

## Python

- 使用 Conda 环境：`recall`
- 激活命令：`conda activate recall`
- 依赖安装：`python -m pip install -r recall/requirements.txt`

## Node.js / 前端

- 在 `recall/frontend` 目录执行前端命令
- 安装依赖：`npm install`
- 首次运行 E2E 前安装浏览器：`npx playwright install chromium`
- 开发启动：`npm run dev`
- 构建校验：`npm run build`
- 单元测试：`npm run test:unit`
- E2E 测试：`npm run test:e2e`

## 快速自检

- 后端测试：`python -m pytest recall/tests/test_config.py`
- Python 语法检查：`python -m compileall recall`
- 前端回归：`cd recall/frontend && npm run test:unit && npm run test:e2e && npm run build`
