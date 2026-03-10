# architecture (未实现)

- 当前项目正在重构，recall_old 目录是旧项目，现在要全面进行迁移。其中新的架构在 architect 中，这个文档并不是当前架构。

## 文件结构

/Users/zzf/share/ClawChater/recall/
  app.py                        # FastAPI入口，挂载路由，启停Engine
  config.py                     # 静态配置 + 路径工具函数
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
    monitor/
      __init__.py
      resource_monitor.py       # GPU/CPU监控
      screen_monitor.py         # 屏幕变化检测
      time_monitor              # 定期抛出事件
    core/
      __init__.py
      event_bus.py              # 事件总线
      events.py                 # 所有事件类型（很小，一个文件够）
      engine.py                 # 编排器：持有EventBus，组装所有服务
  
  frontend/                     # React+Vite+Tailwind
  data/
    recall.db
    screenshots/
  tests/

## 核心数据流

### HTTP 请求链路

- 请求从 app.py 进入，由 api/routes.py 分发。
- 路由函数直接调用 db/screenshot.py、db/summary.py、db/setting.py 中的 CRUD 函数完成数据读写，返回 JSON。
- 不经过 engine，不经过 services。

### 后台常驻链路

- app.py 启动时创建 services/core/engine.py 中的 Engine 实例。
- Engine 在构造阶段做三件事：

  - 创建 EventBus
  - 实例化所有 monitor 和 worker
  - 把自己的处理方法注册到 EventBus 上
- 随后 Engine.start() 以 asyncio task 形式启动三个 monitor 的循环。

### 三个 monitor

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
    - 调用系统 API 截屏
    - 按 data/screenshots/YYYY-MM-DD/HH/{id}.jpg 路径写入文件系统
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

### 事件类型汇总

- services/core/events.py 中定义三种事件：screen_change、force_capture、resource_available。
- 所有事件只携带最少信息（时间戳即可），业务数据不通过事件传递，而是通过数据库流转。
- 这是整个系统解耦的关键：
  - monitor 不知道 capture 的存在
  - capture 不知道 ocr_worker 的存在
  - 它们之间唯一的共享状态是 SQLite 中 screenshots 表的 ocr_status 字段

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
  - 返回更新后的完整配置。
