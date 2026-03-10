# Recall Agent 使用指南

本文档面向 Thinking Agent，说明如何使用 Recall 服务获取屏幕记忆数据。

## 服务概述

Recall 是一个屏幕记忆服务，自动记录用户的屏幕活动：
- **自动截图**：检测屏幕变化并截图
- **OCR 识别**：提取截图中的文字
- **智能总结**：生成活动摘要

**服务地址**：`http://127.0.0.1:5000`

---

## API 接口列表

| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/ocr` | GET | 获取 OCR 文本数据（时间戳、窗口、内容） |
| `/api/summaries/list` | GET | 列出时段内的总结起止时间 |
| `/api/summaries` | GET | 按时间范围获取总结（含内容） |
| `/api/summaries/<id>` | GET | 按 ID 获取单条总结 |
| `/api/screenshots/by-timestamp/<ts>` | GET | 按时间戳获取截图图片 |

---

## 接口详情

### 1. 获取 OCR 文本数据

**用途**：获取指定时间范围内的屏幕 OCR 文本，用于了解用户在做什么。

```
GET /api/ocr?start_time=<ISO8601>&end_time=<ISO8601>&limit=<int>
```

**参数**：
- `start_time`（必填）：起始时间，ISO8601 格式
- `end_time`（必填）：结束时间，ISO8601 格式
- `limit`（可选）：最多返回条数，默认 100

**返回示例**：
```json
{
  "data": [
    {
      "id": 123,
      "timestamp": "2026-02-10T20:00:00",
      "window_title": "recall - Visual Studio Code",
      "process_name": "Code.exe",
      "ocr_text": "完整的OCR文本内容..."
    }
  ],
  "count": 1,
  "server_time": "2026-02-10T20:05:00"
}
```

**使用场景**：
- 了解用户最近在做什么
- 搜索特定关键词相关的屏幕内容
- 分析用户活动模式

---

### 2. 列出总结起止时间

**用途**：快速查看某时段是否存在总结，不返回具体内容（节省带宽）。

```
GET /api/summaries/list?start_time=<ISO8601>&end_time=<ISO8601>
```

**参数**：
- `start_time`（必填）：起始时间
- `end_time`（必填）：结束时间

**返回示例**：
```json
{
  "summaries": [
    {
      "id": 1,
      "start_time": "2026-02-10T19:00:00",
      "end_time": "2026-02-10T20:00:00"
    }
  ],
  "count": 1
}
```

**使用场景**：
- 检查某时段是否已有总结
- 获取总结 ID 列表，再按需获取详细内容

---

### 3. 获取总结内容

**用途**：获取指定时间范围内的总结内容。

#### 方式1：按时间范围查询

```
GET /api/summaries?start_time=<ISO8601>&end_time=<ISO8601>
```

**参数**：
- `start_time`（可选）：起始时间
- `end_time`（可选）：结束时间
- `hours`（可选）：往前查询多少小时，默认 24（与 start_time/end_time 互斥）

**返回示例**：
```json
{
  "summaries": [
    {
      "id": 1,
      "start_time": "2026-02-10T19:00:00",
      "end_time": "2026-02-10T20:00:00",
      "summary": "用户在这段时间内在 VS Code 中开发 recall 功能...",
      "activity_type": "development",
      "created_at": "2026-02-10T20:05:00"
    }
  ],
  "count": 1
}
```

#### 方式2：按 ID 获取单条

```
GET /api/summaries/<id>
```

**返回示例**：
```json
{
  "id": 1,
  "start_time": "2026-02-10T19:00:00",
  "end_time": "2026-02-10T20:00:00",
  "summary": "用户在这段时间内在 VS Code 中开发 recall 功能...",
  "activity_type": "development",
  "created_at": "2026-02-10T20:05:00"
}
```

---

### 4. 按时间戳获取截图

**用途**：获取特定时间点的截图图片，用于查看详细信息。

```
GET /api/screenshots/by-timestamp/<timestamp>?format=<file|base64>
```

**参数**：
- `timestamp`（路径参数）：ISO8601 时间戳或 Unix 时间戳
- `format`（可选）：`file`（默认）返回图片文件，`base64` 返回 JSON

**示例**：
```
GET /api/screenshots/by-timestamp/2026-02-10T20:00:00
GET /api/screenshots/by-timestamp/1739193600
GET /api/screenshots/by-timestamp/2026-02-10T20:00:00?format=base64
```

**返回**：
- `format=file`：直接返回 JPEG 图片
- `format=base64`：
  ```json
  {
    "id": 123,
    "timestamp": "2026-02-10T20:00:00",
    "image_base64": "...",
    "content_type": "image/jpeg"
  }
  ```

**注意**：如果精确时间戳没有匹配的截图，会返回最接近的一张。

---

## 典型工作流程

### 工作流程1：了解用户最近在做什么

```
1. 获取最近1小时的 OCR 数据
   GET /api/ocr?start_time=2026-02-10T19:00:00&end_time=2026-02-10T20:00:00

2. 分析 OCR 文本，识别用户活动

3. 如需查看具体截图，按时间戳获取
   GET /api/screenshots/by-timestamp/2026-02-10T19:30:00
```

### 工作流程2：查看历史总结

```
1. 列出某时段的总结
   GET /api/summaries/list?start_time=2026-02-10T09:00:00&end_time=2026-02-10T18:00:00

2. 根据需要获取具体总结内容
   GET /api/summaries/1
```

### 工作流程3：主动了解用户状态

```
1. 获取最近30分钟的 OCR
   GET /api/ocr?start_time=2026-02-10T19:30:00&end_time=2026-02-10T20:00:00&limit=50

2. 挑选不明确的信息，查看具体截图
   GET /api/screenshots/by-timestamp/2026-02-10T19:45:00

3. 综合分析，形成对用户当前状态的理解
```

---

## 最佳实践

### 1. 时间范围控制
- 一次查询不要超过 2 小时的数据
- 使用 `limit` 参数控制返回数量
- 先用 `/api/summaries/list` 快速检查，再按需获取详情

### 2. 截图获取
- 优先使用 OCR 文本判断是否需要截图
- 使用 `format=base64` 时注意数据量
- 精确时间戳查询更快，模糊匹配会稍慢

### 3. 错误处理
- 404 表示没有找到数据
- 400 表示参数错误
- 服务不可用时优雅降级

---

## 示例代码

### Python 示例

```python
import requests
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:5000"

def get_recent_ocr(hours=1):
    """获取最近 N 小时的 OCR 数据"""
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    response = requests.get(f"{BASE_URL}/api/ocr", params={
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "limit": 100
    })
    return response.json()

def get_screenshot(timestamp):
    """获取指定时间戳的截图"""
    response = requests.get(
        f"{BASE_URL}/api/screenshots/by-timestamp/{timestamp}",
        params={"format": "base64"}
    )
    if response.status_code == 200:
        return response.json()
    return None

def list_summaries(start_time, end_time):
    """列出时段内的总结"""
    response = requests.get(f"{BASE_URL}/api/summaries/list", params={
        "start_time": start_time,
        "end_time": end_time
    })
    return response.json()
```

---

## 常见问题

**Q: OCR 数据为空怎么办？**
A: 可能是 OCR 还在处理中，或者该时段没有截图。检查 `/api/status` 确认服务状态。

**Q: 截图时间戳不精确？**
A: 系统会返回最接近的截图。如果需要精确匹配，先查询 OCR 数据获取精确时间戳。

**Q: 如何判断用户是否在忙？**
A: 查看最近的 OCR 数据量和窗口标题变化频率。高频变化通常表示用户在活跃工作。
