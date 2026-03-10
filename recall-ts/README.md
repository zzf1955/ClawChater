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
npm run test   # 运行 api 单元测试（含建库/配置分层）
npm run lint   # 类型检查
```

## SQLite 数据模型（api）

后端启动时会自动执行 SQLite 初始化和迁移（`schema_migrations`），默认数据库路径来自 `api/config.json` 的 `DB_PATH`。

### `screenshots`

- `id`：自增主键
- `file_path`：截图文件路径（唯一）
- `timestamp`：截图时间（ISO 字符串）
- `phash`：图片哈希（可空）
- `ocr_text`：OCR 文本（可空）
- `ocr_status`：OCR 状态（`pending | done | error`）
- `window_title`：窗口标题（可空）
- `process_name`：进程名（可空）
- `created_at`：记录创建时间

### `summaries`

- `id`：自增主键
- `start_time`：摘要起始时间
- `end_time`：摘要结束时间
- `summary`：摘要正文
- `activity_type`：活动类型（可空）
- `created_at`：记录创建时间

### `settings`

- `key`：配置项键（主键）
- `value`：JSON 序列化后的配置值
- `updated_at`：最后更新时间

## 配置优先级

配置读取顺序如下（后者覆盖前者）：

1. 内置默认值（`api/src/config/default-settings.ts`）
2. 静态配置文件（`api/config.json`）
3. SQLite `settings` 表中的动态配置

运行时通过 `ConfigService` 读写配置，写入会持久化到 `settings` 并触发变更监听回调（用于后续热更新广播接入）。

## 目录约定

- `api/config.json`：静态配置（随版本管理）
- `api/data/recall.db`：SQLite 数据库（运行时生成）
- `api/screenshots/`：截图文件目录（运行时生成，供后续采集模块使用）
