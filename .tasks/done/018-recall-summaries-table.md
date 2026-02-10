---
id: "018"
title: "Recall DB 新增 summaries 表 + 摘要 API"
priority: high
depends_on: []
module: recall
branch: main
estimated_scope: small
---

## 背景

三层记忆架构的 Layer 1 需要在 Recall 数据库中存储 OCR 定时摘要。Thinking Agent 每 30 分钟生成活动摘要，通过 HTTP API 写回 Recall DB，后续分析时也通过 API 读取历史摘要。

## 技术方案

### 1. 新增 summaries 表

在 `recall/db.py` 的 `init_db()` 中添加：

```sql
CREATE TABLE IF NOT EXISTS summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    summary TEXT NOT NULL,
    activity_type TEXT,  -- work/entertainment/social/learning/other
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_summaries_time ON summaries(start_time, end_time);
```

### 2. DB 操作函数

在 `recall/db.py` 中添加：
- `insert_summary(start_time, end_time, summary, activity_type) -> int`
- `get_summaries(hours=24) -> list[dict]`
- `get_latest_summary() -> dict | None`（用于判断是否需要生成新摘要）

### 3. API 端点

在 `recall/web/app.py` 中添加：

- `POST /api/summaries` — 写入摘要
  - Body: `{ "start_time": "ISO8601", "end_time": "ISO8601", "summary": "...", "activity_type": "..." }`
  - 返回: `{ "id": 1 }`

- `GET /api/summaries?hours=24` — 查询最近 N 小时的摘要
  - 返回: `[{ "id": 1, "start_time": "...", "end_time": "...", "summary": "...", "activity_type": "..." }]`

## 验收标准

- [ ] summaries 表在 DB 初始化时自动创建（IF NOT EXISTS，不影响已有数据）
- [ ] POST /api/summaries 能正确写入并返回 id
- [ ] GET /api/summaries?hours=N 能按时间范围查询
- [ ] 空数据时返回空数组，不报错

## 测试要求

- [ ] 单元测试：insert_summary + get_summaries CRUD
- [ ] 单元测试：get_latest_summary 边界条件
- [ ] API 测试：POST 和 GET 端点正常/异常情况

---
completed_by: w-1cfc
completed_at: 2026-02-08T00:00:00+08:00
commit: 20ba038
files_changed:
  - recall/db.py
  - recall/web/app.py
  - recall/tests/unit/test_db.py
  - recall/tests/integration/test_web_api.py
test_result: "30 passed, 0 failed"
---
