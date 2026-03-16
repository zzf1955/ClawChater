# Recall

## 目录

- `app.py`: FastAPI 入口，挂载路由与引擎生命周期
- `config.py`: 基础配置和路径工具
- `db/`: SQLite schema 与数据访问函数
- `api/`: HTTP 路由与请求模型
- `services/`: 事件与后台服务骨架
- `frontend/`: React + Vite + Tailwind 前端工程
- `data/`: 数据目录（运行时自动创建）

## 后端本地启动

```bash
# 在项目根目录执行
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows (Git Bash)
# source .venv/Scripts/activate
pip install -r recall/requirements.txt
uvicorn recall.app:app --reload
```

## 前端本地启动

```bash
cd recall/frontend
npm install
npm run dev
```

## 一体化启动（FastAPI 托管前端）

```bash
conda activate recall
cd recall/frontend
npm install
npm run build

# 回到项目根目录
cd ../..
uvicorn recall.app:app --host 127.0.0.1 --port 8000
```

- 浏览器访问：`http://127.0.0.1:8000/screenshots`
- API 仍通过同一服务访问：`http://127.0.0.1:8000/api/config`
- SPA fallback 已启用：直接访问 `/screenshots`、`/config`、`/summaries` 不会 404

### 前端 API 地址策略

- 生产/一体化模式默认同源访问：前端请求 `/api/**`，无需额外配置。
- 如需指向其他后端地址，可在前端构建前设置 `VITE_API_BASE_URL`，例如：

```bash
cd recall/frontend
VITE_API_BASE_URL=http://127.0.0.1:9000 npm run build
```

## 最小自检

```bash
# 在项目根目录执行
pytest recall/tests/test_config.py
python -m compileall recall
cd recall/frontend && npm run build
```

## 回归测试基线

```bash
# 在项目根目录执行
./scripts/run_regression.sh
```

- 后端集成链路：`pytest recall/tests/test_regression_pipeline.py recall/tests/test_api.py`
- 前端 smoke：`cd recall/frontend && npm run test:unit && npm run test:e2e`
- 详细说明：`doc/testing-baseline.md`
