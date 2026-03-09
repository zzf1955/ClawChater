# recall-ts

TypeScript monorepo scaffold for Recall rewrite.

## 目录结构

- `main/`：主流程编排（预留）
- `trigger/`：触发器模块（预留）
- `capture/`：截图采集模块（预留）
- `resource-monitor/`：资源监控模块（预留）
- `ocr-worker/`：OCR worker 模块（预留）
- `api/`：Fastify 后端服务
- `frontend/`：React + Vite + Tailwind 前端

## 环境要求

- Node.js >= 22
- npm >= 10

## 安装依赖

```bash
cd recall-ts
npm install
```

## 启动

```bash
# 启动后端（默认 127.0.0.1:3000）
npm run dev:api

# 启动前端（默认 127.0.0.1:5173）
npm run dev:frontend
```

前端 `vite` 已配置代理：`/health -> http://127.0.0.1:3000`。

## 脚本

```bash
npm run build  # 构建 api + frontend
npm run test   # 运行 api smoke test
npm run lint   # 类型检查
```
