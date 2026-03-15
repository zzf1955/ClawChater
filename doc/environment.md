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

## 多端截图（可选）

Slave 端（远程截图机器）：

```bash
# 必须指定同步目录
export RECALL_SYNC_DIR=/path/to/syncthing/recall-incoming
# 可选
export RECALL_DEVICE_ID=my-laptop        # 默认: 主机名
export RECALL_CAPTURE_INTERVAL=5         # 默认: 5 秒

python -m recall.slave
```

Host 端（主服务器）：

```bash
# 指向 syncthing 同步到本机的目录，Engine 启动时自动启用 IncomingWatcher
export RECALL_INCOMING_DIR=/path/to/syncthing/recall-incoming
```

## 快速自检

- 后端测试：`python -m pytest recall/tests/test_config.py`
- Python 语法检查：`python -m compileall recall`
- 前端回归：`cd recall/frontend && npm run test:unit && npm run test:e2e && npm run build`
