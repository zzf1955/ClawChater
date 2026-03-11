# Recall 迁移收口方案（task009）

更新时间：2026-03-11

## 1. 旧新模块映射

| recall_old | recall（新架构） | 状态 | 说明 |
|---|---|---|---|
| `main.py` + `app.py` | `recall/app.py` | 已替代 | 统一 FastAPI 入口与生命周期管理 |
| `web/app.py` (Flask API) | `recall/api/routes.py` | 已替代 | 新版 API 由 FastAPI 路由提供 |
| `db.py`（单文件 CRUD） | `recall/db/database.py` + `recall/db/screenshot.py` + `recall/db/summary.py` + `recall/db/setting.py` | 已替代 | 数据层按领域拆分 |
| `ocr_worker.py` | `recall/services/ocr_worker.py` | 已替代 | OCR 处理逻辑迁入 services |
| `core/capture.py` | `recall/services/capture.py` | 已替代 | 截图能力迁入 services |
| `core/container.py` + `core/interfaces.py` | `recall/services/core/engine.py` + `event_bus.py` + `events.py` | 架构升级 | 从 DI 容器转为事件编排 |
| `utils/gpu.py` | `recall/services/monitor/resource_monitor.py` | 已替代 | 资源检测通过 monitor 事件化 |
| `web/frontend` (Vue) | `recall/frontend` (React + Vite) | 已替代 | 前端技术栈升级 |
| `tests/unit` + `tests/integration` | `recall/tests` | 已替代 | 回归测试入口统一 |
| `groups` 表与 `group_id` 字段 | 无直接替代 | 下线 | 新架构不再维护分组聚合表 |

## 2. 数据与配置迁移策略

### 2.1 数据字段映射

| 旧字段 | 新字段 | 规则 |
|---|---|---|
| `screenshots.path` | `screenshots.file_path` | 优先转换为 `screenshots/...` 相对路径 |
| `screenshots.timestamp` | `screenshots.captured_at` | 原值透传（ISO8601） |
| `screenshots.ocr_status` | `screenshots.ocr_status` | 非 `pending/done/error` 统一降级为 `error` |
| `settings.value`（JSON 字符串） | `settings.value`（纯字符串） | 反序列化后再标准化为字符串 |
| `summaries.*` | `summaries.*` | 主键与字段透传 |

### 2.2 迁移脚本

新增脚本：`scripts/migrate_recall_old_db.py`

能力：
- 支持 `--dry-run`（默认建议先 dry-run）
- 自动初始化新 schema
- 输出一致性报告（数量、状态分布、时间跨度、样本字段）
- 支持 `--report` 产出 JSON 报告

示例：

```bash
cd /Users/zzf/share/ClawChater
python scripts/migrate_recall_old_db.py \
  --old-db /path/to/recall_old/data/recall.db \
  --new-db /path/to/recall/data/recall.db \
  --report /tmp/migration_report.json
```

dry-run 示例：

```bash
cd /Users/zzf/share/ClawChater
python scripts/migrate_recall_old_db.py \
  --old-db /path/to/recall_old/data/recall.db \
  --dry-run \
  --report /tmp/migration_dry_run_report.json
```

## 3. Dry-run 与一致性校验记录

执行时间：2026-03-11（Asia/Shanghai）

执行命令：

```bash
python scripts/migrate_recall_old_db.py \
  --old-db tmp/old_sample.db \
  --dry-run \
  --report tmp/migration_dry_run_report.json \
  --sample-size 3
```

结果摘要：
- `screenshots` 数量：旧 3 / 新 3
- `summaries` 数量：旧 2 / 新 2
- `settings` 数量：旧 3 / 新 3
- 状态分布：旧 `{done:1,pending:1,weird_status:1}` → 新 `{done:1,pending:1,error:1}`
- 时间跨度一致性：通过（`2026-03-10T10:00:00Z` 到 `2026-03-10T10:02:00Z`）
- 报告文件：`tmp/migration_dry_run_report.json`

## 4. 切换与回滚清单

### 4.1 冻结点

- 冻结点 F1：停止 `recall_old` 写入（停止截图与 OCR 后台任务）
- 冻结点 F2：备份旧库与截图目录（`recall_old/data/`）
- 冻结点 F3：执行迁移并通过抽样校验后，才切流到新服务

### 4.2 切换步骤（演练/生产一致）

1. 停止旧服务，确认无新增截图写入。
2. 备份 `recall_old/data/recall.db` 与 `recall_old/data/screenshots/`。
3. 在新架构环境初始化并执行迁移脚本。
4. 用 `tmp/migration_dry_run_report.json` 同维度校验线上迁移报告（数量、状态、时间跨度、样本字段）。
5. 启动新服务 `uvicorn recall.app:app`，执行 API 健康检查与前端 smoke。
6. 观察 1 个采集周期（至少含一次截图+一次 OCR），确认新数据持续入库。

### 4.3 回滚步骤

1. 立即停止新服务写入。
2. 恢复备份的 `recall_old/data/`。
3. 启动 `recall_old` 服务，执行最小健康检查（截图、OCR、查询）。
4. 记录回滚原因并修复后重新演练。

### 4.4 责任人

- 执行负责人：Recall 维护者（`zzf621`）
- 验收负责人：项目 Owner（负责确认功能连续性与数据一致性）

## 5. 旧目录后续策略

- `recall_old/` 进入“归档保留”状态：默认只读，不再新增功能。
- 保留周期建议：至少 2 个发布周期（用于紧急回滚）。
- 达成以下条件后可下线：
  - 新架构连续稳定运行
  - 迁移报告归档齐全
  - 无未关闭回滚风险项
