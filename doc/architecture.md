# architecture

- 当前项目正在重构，`recall_old` 是历史实现，`recall/` 是当前主线实现。
- `recall_old/` 当前策略：归档保留（只读，不再新增功能）。

## 文件结构

recall/
  app.py                        # FastAPI入口，挂载路由，启停Engine
  config.py                     # 静态路径常量 + AppSettings（环境变量驱动）+ ensure_data_dirs()
  db/                           # 数据层
    __init__.py
    database.py                 # 连接管理、建表
    schema.sql                  # DDL
    screenshot.py               # screenshots CRUD
    summary.py                  # summaries CRUD
    setting.py                  # settings(动态配置) CRUD
  
  api/                          # HTTP接口层
    __init__.py
    routes.py                   # REST路由
    schemas.py                  # Pydantic模型
  
  services/                     # 业务服务（被Engine编排）
    __init__.py
    capture.py                  # 截屏
    ocr_worker.py               # OCR批处理
    ocr_engine.py               # OCR引擎工厂（RapidOCR / tesseract fallback）
    incoming_watcher.py         # 监控 incoming 目录，导入远程截图
    monitor/
      __init__.py
      resource_monitor.py       # GPU/CPU监控
      screen_monitor.py         # 屏幕变化检测
      time_monitor.py           # 定期抛出事件
      utils.py                  # 公共工具（读取动态配置、参数校验）
    core/
      __init__.py
      event_bus.py              # 事件总线
      events.py                 # 所有事件类型（很小，一个文件够）
      engine.py                 # 编排器：持有EventBus，组装所有服务

  utils/
    time_parse.py               # ISO8601 时间字符串解析（支持 Z 后缀）

  slave.py                      # 远程截图客户端（Slave 模式）
  frontend/                     # React+Vite+Tailwind
  data/
    recall.db
    screenshots/
    logs/                       # 运行日志（recall.log）
  tests/

## 核心数据流

### HTTP 请求链路

- 请求从 app.py 进入，由 api/routes.py 分发。
- 路由函数直接调用 db/screenshot.py、db/summary.py、db/setting.py 中的 CRUD 函数完成数据读写，返回 JSON。
- 不经过 engine，不经过 services。
- 例外：POST /api/config 在写库后向 EventBus 发出 config_updated 事件，Engine 收到后重新从数据库读取配置并推给各 monitor（实现热更新）。

### 后台常驻链路

- app.py 启动时创建 services/core/engine.py 中的 Engine 实例。
- Engine 在构造阶段做三件事：

  - 创建 EventBus
  - 实例化所有 monitor 和 worker
  - 把自己的处理方法注册到 EventBus 上
- 随后 Engine.start() 以 asyncio task 形式启动所有 monitor 的循环（三个常驻 monitor；若设置了 RECALL_INCOMING_DIR 则额外启动 IncomingWatcher）。

### 三个常驻 monitor

- 各自独立运行，只做一件事：检测条件，向 EventBus 抛事件。

- services/monitor/screen_monitor.py

  - 定期截取屏幕缩略图，与上一帧做 phash 比对。
  - 差异超过阈值时，向 EventBus 发出 screen_change 事件。
  - 它不截图、不存盘，只负责判定"屏幕变了"。

- services/monitor/time_monitor.py

  - 维护一个计时器，距离上次截图超过强制间隔（比如 30 秒）时，向 EventBus 发出 force_capture 事件。
  - 纯时间驱动，不关心屏幕是否变化。

- services/monitor/resource_monitor.py

  - 定期采样 GPU/CPU 使用率。
  - 当负载低于阈值时，向 EventBus 发出 resource_available 事件。
  - 只报告资源状态，不关心有没有待处理任务。

### Engine 接收事件，调度两个 worker

- 收到 screen_change 或 force_capture 时：
  - Engine 调用 services/capture.py 执行一次完整截图。
  - capture 做三件事：
    - 调用系统 API 截屏（macOS 用 screencapture，Windows 用 PIL.ImageGrab）
    - 按 data/screenshots/YYYY-MM-DD/HH/{timestamp}.jpg 路径写入文件系统
    - 调用 db/screenshot.py 插入一条元数据记录，ocr_status 设为 pending
  - 完成后 Engine 重置 time_monitor 的计时器，避免刚截完图又被强制触发。

- 收到 resource_available 时：

  - Engine 调用 services/ocr_worker.py 尝试执行一轮 OCR。
  - ocr_worker 的逻辑：

    - 调用 db/screenshot.py 查询所有 ocr_status=pending 的记录，拿到 id 列表。
    - 如果 id 数量达到 batch_size，取前 batch_size 个组成一批。
    - 如果数量不足 batch_size 但大于零，说明没有更多待处理图片会进来，也把这些全部组成一批。
    - 如果数量为零，直接返回，本轮不执行。
    - 根据 id 从 db/screenshot.py 拿到 file_path，读取图片文件，调用 OCR 引擎批量推理。
    - 逐条调用 db/screenshot.py 更新对应记录的 ocr_text 和 ocr_status，成功设为 done，失败设为 error。
    - OCR 引擎由 services/ocr_engine.py 的 create_ocr_engine() 工厂函数创建：优先使用 RapidOCR（onnxruntime，自动检测 CUDA），不可用时 fallback 到 tesseract 命令行。

- 收到 config_updated 时：
  - Engine 调用各 monitor 的 reload_config() 方法，从数据库重新读取 SCREEN_CHECK_INTERVAL、CHANGE_THRESHOLD、FORCE_INTERVAL 等动态配置，立即生效，无需重启。

### 事件类型汇总

- services/core/events.py 中定义四种事件：screen_change、force_capture、resource_available、config_updated。
- 所有事件只携带最少信息（时间戳 + 可选 payload），业务数据不通过事件传递，而是通过数据库流转。
- 这是整个系统解耦的关键：
  - monitor 不知道 capture 的存在
  - capture 不知道 ocr_worker 的存在
  - 它们之间唯一的共享状态是 SQLite 中 screenshots 表的 ocr_status 字段

## 多端截图（Slave / Host 模式）

支持多台机器协作截图：Slave 机器只截图，通过 syncthing 同步到 Host，Host 端自动导入并 OCR。

### 架构

```
Slave 机器                          Host 机器
┌──────────────┐                   ┌──────────────────────────┐
│ recall.slave │                   │ Engine                   │
│  截图 + phash │──syncthing──────▶│  IncomingWatcher         │
│  写入 sync_dir│  (自动同步)       │   轮询 incoming_dir      │
└──────────────┘                   │   导入 DB + 移动文件      │
                                   │  OCR Worker              │
                                   │   处理 pending 截图       │
                                   └──────────────────────────┘
```

### Slave 端使用

Slave 是一个轻量独立脚本，不需要数据库和 OCR 环境，只需要截图能力。

```bash
# 基本用法
python -m recall.slave --sync-dir /path/to/syncthing/recall-incoming

# 完整参数
python -m recall.slave \
    --sync-dir /path/to/syncthing/recall-incoming \
    --device-id my-laptop \
    --interval 5 \
    --no-change-only   # 禁用 phash 变化检测，每次都截图
```

也可用环境变量配置：

| 环境变量 | 说明 | 默认值 |
|---------|------|-------|
| `RECALL_SYNC_DIR` | syncthing 同步目录（必填） | — |
| `RECALL_DEVICE_ID` | 设备标识 | 主机名 |
| `RECALL_CAPTURE_INTERVAL` | 截图间隔（秒） | 5 |

每次截图产出两个文件：
- `{device_id}_{timestamp}.jpg` — 截图
- `{device_id}_{timestamp}.json` — 元数据（device_id, captured_at, platform, phash）

JSON sidecar 在 JPG 之后写入，IncomingWatcher 以 JSON 存在作为"就绪"信号。

### Host 端配置

Host 端只需设置环境变量指向 syncthing 同步到本机的目录：

```bash
export RECALL_INCOMING_DIR=/path/to/syncthing/recall-incoming
```

Engine 启动时如果检测到 `RECALL_INCOMING_DIR`，会自动启动 IncomingWatcher：
- 每 3 秒轮询 incoming 目录
- 发现 `.jpg` + `.json` 配对文件后，插入 DB（`ocr_status=pending`），移动到标准 `data/screenshots/YYYY-MM-DD/HH/` 目录
- 已有 OCR 流程自动处理导入的截图

### Host 端全部环境变量

| 环境变量 | 说明 | 默认值 |
|---------|------|-------|
| `RECALL_HOST` | 监听地址 | `127.0.0.1` |
| `RECALL_PORT` | 监听端口 | `8000` |
| `RECALL_RELOAD` | 热重载（开发用） | `0` |
| `RECALL_INCOMING_DIR` | Slave 同步目录，设置后自动启用 IncomingWatcher | — |
| `RECALL_FRONTEND_DIST` | 前端静态文件目录 | `recall/frontend/dist` |
| `RECALL_SERVE_FRONTEND` | 是否挂载前端静态文件 | `1` |
| `RECALL_LOG_FILE` | 日志文件路径 | `data/logs/recall.log` |
| `RECALL_LOG_LEVEL` | 日志级别 | `DEBUG` |

### syncthing 配置要点

1. Slave 机器和 Host 机器都安装 syncthing
2. 在两端共享同一个目录（Slave 写入，Host 读取）
3. Host 端的共享目录路径设为 `RECALL_INCOMING_DIR`
4. 建议 syncthing 设置为"仅发送"（Slave）和"仅接收"（Host）

## 数据库设计

### screenshots 表

- id: INTEGER PRIMARY KEY AUTOINCREMENT
- captured_at: TEXT NOT NULL — ISO8601 格式，截图时刻，是业务时间
- file_path: TEXT NOT NULL — 相对于 data/ 的路径，如 screenshots/2025-01-15/14/123.jpg
- ocr_text: TEXT — OCR 识别结果，pending 状态时为 NULL
- ocr_status: TEXT NOT NULL DEFAULT 'pending' — 取值 pending / done / error
- window_title: TEXT — 截图时的前台窗口标题
- process_name: TEXT — 截图时的前台进程名
- phash: TEXT — 感知哈希，用于屏幕变化比对和去重

说明：

- file_path 存相对路径而非绝对路径，迁移目录时不用刷数据。
- phash 存 TEXT 而非 INTEGER，因为感知哈希通常是 64 位十六进制字符串，TEXT 更通用。

索引：

- captured_at 上建索引，时间范围查询是最高频操作。
- ocr_status 上建索引，ocr_worker 每轮都要查 pending 记录。

### summaries 表

- id: INTEGER PRIMARY KEY AUTOINCREMENT
- start_time: TEXT NOT NULL — 该摘要覆盖的起始时间，ISO8601
- end_time: TEXT NOT NULL — 该摘要覆盖的结束时间，ISO8601
- summary: TEXT NOT NULL — 摘要正文
- activity_type: TEXT — 活动分类，由外部 agent 填写，可为 NULL
- created_at: TEXT NOT NULL DEFAULT (datetime('now'))

索引：

- start_time、end_time 上建联合索引，按时间段查询用。

### settings 表

- key: TEXT PRIMARY KEY — 配置项名称
- value: TEXT NOT NULL — 配置值，统一存字符串，读取时按类型解析
- updated_at: TEXT NOT NULL DEFAULT (datetime('now')) — 最后修改时间

初始数据：

- SCREEN_CHECK_INTERVAL: 屏幕检测间隔秒数，默认 "3"
- CHANGE_THRESHOLD: 屏幕变化阈值，默认 "5"
- OCR_BATCH_SIZE: OCR 每批处理数量，默认 "10"
- GPU_USAGE_THRESHOLD: GPU 繁忙阈值百分比，默认 "70"
- CPU_USAGE_THRESHOLD: CPU 繁忙阈值百分比，默认 "80"
- FORCE_INTERVAL: 强制截图间隔秒数，默认 "30"

说明：

- key-value 结构而非一行多列，加新配置项不用改表结构。
- value 统一为 TEXT，在 db/setting.py 的读取函数中做类型转换（int/float），避免 SQLite 类型混乱。

## API 接口

### 截图相关

- GET /api/screenshots?start_time=&end_time=&limit=
  - 按时间范围查询截图的 ocr 数据列表。
  - start_time、end_time 为 ISO8601 字符串。
  - 返回 JSON 数组，每项包含 id、captured_at、file_path、ocr_text、ocr_status、window_title、process_name。

- GET /api/screenshots/{id}
  - 查询单条截图的完整元数据。
  - 返回 JSON 对象。

- GET /api/screenshots/{id}/image
  - 返回截图原始图片文件。
  - Content-Type 为 image/jpeg，直接用 FileResponse。

### 摘要相关

- GET /api/summaries?start_time=&end_time=
  - 按时间范围查询摘要列表。
  - 返回 JSON 数组。

- POST /api/summaries
  - 写入一条新摘要。
  - 请求体：start_time、end_time、summary、activity_type（可选）。
  - 返回创建的记录。

### 配置相关

- GET /api/config

  - 读取所有动态配置。
  - 返回 JSON 对象，key 为配置名，value 为当前值。

- POST /api/config
  - 批量更新动态配置。
  - 请求体为 JSON 对象，如 {"CHANGE_THRESHOLD": "8", "OCR_BATCH_SIZE": "20"}。
  - 只更新传入的 key，未传入的保持不变。
  - 写库后向 Engine 发出 config_updated 事件，monitor 配置立即热更新生效。
  - 返回更新后的完整配置。
