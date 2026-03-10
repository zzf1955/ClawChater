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
cd /Users/zzf/share/ClawChater
python -m venv .venv
source .venv/bin/activate
pip install -r recall/requirements.txt
uvicorn recall.app:app --reload
```

## 前端本地启动

```bash
cd /Users/zzf/share/ClawChater/recall/frontend
npm install
npm run dev
```

## 最小自检

```bash
cd /Users/zzf/share/ClawChater
pytest recall/tests/test_config.py
python -m compileall recall
cd recall/frontend && npm run build
```
