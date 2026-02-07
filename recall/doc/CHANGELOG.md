# Recall 版本历史

## v0.6.3 (2026-02-01)

### 修复
- **对话中调用工具会卡住** - 工具调用后正确继续 LLM 循环
  - 问题：对话中调用工具会卡住，前端显示永久的"回复中..."状态
  - 原因：`_process_response()` 执行工具后没有继续调用 LLM
  - 修复：参考 `llm.py` 实现完整的工具调用循环
  - 将 assistant 消息（包含 tool_calls）和 tool 结果添加到对话历史
  - 循环调用 LLM 直到没有工具调用或达到最大迭代次数（3次）

### 变更
- `curious_ai.py`
  - 重构 `_handle_user_message()` 方法，添加工具调用循环
  - 重构 `_explore()` 方法，添加工具调用循环
  - 删除不再需要的 `_process_response()` 方法

### 新增
- `tests/unit/test_curious_ai.py` - CuriousAI 单元测试（8 个测试用例）
  - 纯文本回复测试
  - 单次/多次工具调用循环测试
  - 最大迭代次数限制测试
  - send_message 工具测试
  - 对话历史更新测试
  - 探索模式工具循环测试

---

## v0.6.2 (2026-01-31)

### 重构
- **配置系统重构** - 从 Python 文件存储改为数据库存储，支持热更新
  - 新增 `settings` 表存储配置
  - 配置修改后立即生效，无需重启应用
  - 主应用和 Web 服务共享同一数据库，配置同步

### 新增
- `db.py` - 新增配置存储函数
  - `get_setting(key, default)` - 获取单个配置
  - `set_setting(key, value)` - 设置单个配置
  - `get_all_settings()` - 获取所有配置
  - `set_all_settings(settings)` - 批量设置配置

- `config.py` - 重构为配置模块
  - `DEFAULT_SETTINGS` - 默认配置字典
  - `config.get(key)` - 从数据库读取配置（支持热更新）
  - `config.set(key, value)` - 写入配置到数据库
  - `config.init_defaults()` - 初始化默认配置

### 变更
- `web/app.py` - 配置 API 改为读写数据库
- `app.py` - 截图循环使用 `config.get()` 读取配置，支持热更新
- `curious_ai.py` - AI 循环使用 `config.get()` 读取配置，支持热更新

---

## v0.6.1 (2026-01-31)

### 修复
- **聊天界面用户消息不显示** - 发送消息后立即显示
  - 问题：用户发送消息后，消息不会立即显示，需要等待轮询才能看到
  - 修复：采用乐观更新策略，发送时立即显示用户消息
  - 发送失败时自动移除临时消息并显示错误提示
  - 改进轮询去重逻辑，同时检查 ID 和内容，避免消息重复

### 变更
- `web/frontend/src/views/ChatView.vue`
  - `handleSend()` 函数添加乐观更新逻辑
  - `pollMessages()` 函数改进去重逻辑（ID + 内容双重检查）

---

## v0.6.0 (2026-01-31)

### 新增
- **拟人 AI 聊天** - CuriousAI 后台独立线程运行
  - 主动探索用户数据，发现有趣的事情会主动提问
  - 双向消息：用户和 AI 都可以主动发送消息
  - `send_message` 工具：AI 通过工具调用发送消息给用户
  - 情景设定：好奇的 AI，只能通过截图和对话探索世界
  - 提问前先检索记忆库，避免重复提问

- **对话持久化** - 消息存入数据库
  - 切换标签页后回来能继续之前的对话
  - 新增 `ai_messages` 表存储对话历史

- **AI 日志页面** - 显示 AI 后台活动
  - 新增侧边栏 "AI 日志" 导航
  - 显示探索、工具调用、错误等活动
  - 新增 `ai_logs` 表存储日志

- **AI 设置** - 可配置的探索参数
  - `AI_EXPLORE_INTERVAL` - 探索间隔（默认 5 分钟）
  - `AI_MIN_QUESTION_INTERVAL` - 最小提问间隔（默认 10 分钟）
  - `AI_ENABLED` - 是否启用主动探索

### 新增文件
- `curious_ai.py` - CuriousAI 核心类
- `message_queue.py` - 消息队列管理
- `web/frontend/src/views/AILogView.vue` - AI 日志页面

### 变更
- `config.py` - 新增 AI 配置项
- `db.py` - 新增 `ai_messages` 和 `ai_logs` 表
- `web/app.py` - 新增 `/api/ai/messages`、`/api/ai/history`、`/api/ai/logs` 接口
- `app.py` - 启动时启动 CuriousAI，退出时停止
- `web/frontend/src/views/ChatView.vue` - 改为轮询获取消息
- `web/frontend/src/views/ConfigView.vue` - 新增 AI 设置区块

---

## v0.5.9 (2026-01-31)

### 新增
- **Android 截图浏览功能** - 在移动端查看已截取的截图
  - 截图列表界面（2列网格布局，按时间倒序）
  - 大图预览界面（支持手势缩放、左右滑动切换）
  - 主界面新增"浏览截图"入口按钮

### 新增文件
- `GalleryActivity.kt` - 截图列表界面
- `ImageViewerActivity.kt` - 大图预览界面
- `adapter/ScreenshotAdapter.kt` - 列表适配器
- `adapter/ImagePagerAdapter.kt` - 预览页面适配器
- `activity_gallery.xml` - 列表布局
- `activity_image_viewer.xml` - 预览布局
- `item_screenshot.xml` - 列表项布局
- `item_image_viewer.xml` - 预览项布局

### 依赖
- 新增 Glide 4.16.0（图片加载）
- 新增 PhotoView 2.3.0（手势缩放）

---

## v0.5.8 (2026-01-31)

### 修复
- **Android 14 崩溃问题** - 修复选择"整个屏幕"后应用闪退
  - 添加 `MediaProjection.Callback` 回调（Android 14 必需）
  - 在 `ScreenCapture.start()` 中注册回调，`stop()` 中取消注册
  - 添加 try-catch 错误处理
  - 克隆 Intent 数据以避免传递问题

### 变更
- `ScreenCapture.kt` - 新增 `projectionCallback` 和 `mainHandler`
- `CaptureService.kt` - `startCapture()` 添加异常处理

---

## v0.5.7 (2026-01-31)

### 变更
- **LLM 配置集中化** - 将分散的 API 配置统一到 `config.py`
  - 新增 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL` 配置项
  - `llm.py`、`memory/summarizer.py`、`memory/extractor.py` 改为从 config 导入
  - 模型更新为 `claude-haiku-4-5-20251001`

- **时间处理统一** - 修复截图搜索的时间查询问题
  - `llm.py` 的 `search_screenshots()` 改用 Python `datetime.now()` 计算时间范围
  - 原 SQLite `datetime('now')` 使用 UTC 时间，与本地时间不一致

### 新增
- **统一工具测试脚本** - `scripts/test_tools.py`
  - 测试 `search_memory` 工具（向量记忆库）
  - 测试 `search_screenshots` 工具（截图搜索）
  - 测试 `get_activity` 工具（活动总结）
  - 测试 LLM 工具调用集成

### 使用方式
```bash
# 运行工具测试
python scripts/test_tools.py
```

---

## v0.5.6 (2026-01-30)

### 新增
- **对话窗口 Markdown 渲染** - AI 助手回复支持富文本格式
  - 代码块语法高亮（支持 Python、JavaScript、JSON、SQL、Bash 等）
  - 支持列表、粗体、斜体、引用块、表格等 Markdown 格式
  - 链接可点击跳转
  - 用户消息保持纯文本显示

### 前端
- 新增 `MarkdownRenderer.vue` 组件
- 新增依赖：`marked`（Markdown 解析）、`highlight.js`（代码高亮）、`dompurify`（XSS 防护）

### 变更
- `ChatView.vue` - AI 消息使用 MarkdownRenderer 渲染
- `style.css` - 新增 `.markdown-body` 样式类
- `main.js` - 引入 highlight.js 主题

---

## v0.5.5 (2026-01-30)

### 修复
- **BUG-001: 托盘图标常驻** - 关闭前端窗口后程序不再退出
  - 问题：关闭 webview 窗口后整个程序退出
  - 修复：添加窗口关闭事件处理，拦截关闭操作改为隐藏窗口
  - 托盘图标现在常驻，可通过托盘菜单重新打开窗口或退出程序

### 变更
- `app.py` - 新增 `_on_window_closing()` 方法处理窗口关闭事件
- `app.py` - 托盘线程改为非守护线程（`daemon=False`），确保程序不会意外退出
- `app.py` - `_on_open_window()` 新增 `restore()` 调用，确保窗口不是最小化状态

---

## v0.5.4 (2026-01-30)

### 修复
- **LLM 工具调用** - 修复 Function Calling 不工作的问题
  - 原因：API 代理只支持 Anthropic 原生格式，不支持 OpenAI 格式
  - 将 `llm.py` 中的工具定义从 OpenAI 格式改为 Anthropic 原生格式
  - 现在 LLM 可以正确调用 `search_memory`、`search_screenshots`、`get_activity` 工具

### 变更
- `llm.py` - `TOOLS` 定义改用 Anthropic 原生格式（`input_schema` 替代 `parameters`）

---

## v0.5.3 (2026-01-30)

### 新增
- **LLM 测试脚本** - 命令行交互式测试工具
  - `scripts/test_llm.py` - 独立LLM实例，不影响正常聊天
  - 支持命令：`/clear` 清空对话、`/history` 查看历史、`/system` 查看系统提示词、`/quit` 退出
  - 显示详细调试信息：tool calls、迭代次数

### 变更
- `llm.py` - `chat()` 方法新增 `debug` 参数，返回详细调试信息

### 使用方式
```bash
conda run -n recall python scripts/test_llm.py
```

---

## v0.5.2 (2026-01-30)

### 新增
- **AI 助手聊天界面** - 为 LLM 功能添加 Web 图形界面
  - 新增 `ChatView.vue` 聊天视图组件
  - 支持与 Recall 助手实时对话
  - 支持清空对话历史
  - 侧边栏新增"AI 助手"导航入口

### 后端
- `web/app.py` 新增 `/api/chat` 和 `/api/chat/clear` API 端点

### 前端
- `web/frontend/src/views/ChatView.vue` - 聊天界面组件
- `web/frontend/src/api/index.js` - 新增 `sendMessage` 和 `clearChat` API 函数

---

## v0.5.1 (2026-01-30)

### 修复
- **托盘图标** - 使用 `assets/icon.png` 作为托盘图标，不再动态绘制
  - 暂停时在图标右下角显示橙色圆点指示
  - 若图标文件不存在则回退到动态绘制

---

## v0.5.0 (2026-01-30)

### 新增
- **Android 移动端基础框架** - 实现手机端截图功能
  - `android/RecallMobile/` - Android Studio 项目
  - MediaProjection API 实现屏幕截图
  - Foreground Service 后台持续运行
  - 屏幕变化检测（缩略图像素对比）
  - Room 数据库存储截图元数据
  - 可配置截图间隔、变化阈值、强制截图间隔

### 技术栈
- Kotlin + Android SDK 34
- 最低支持 Android 10 (API 29)
- AndroidX + Material Design 3
- Room Database + Coroutines

### 项目结构
```
android/RecallMobile/
├── app/src/main/java/com/recall/mobile/
│   ├── MainActivity.kt        # 主界面+权限请求
│   ├── SettingsActivity.kt    # 设置界面
│   ├── service/CaptureService.kt  # 前台服务
│   ├── capture/
│   │   ├── ScreenCapture.kt   # 截图逻辑
│   │   └── ChangeDetector.kt  # 变化检测
│   └── data/
│       ├── AppDatabase.kt     # Room数据库
│       ├── Screenshot.kt      # 数据实体
│       └── AppPreferences.kt  # 配置存储
```

### 存储格式
- 与PC端一致：`Pictures/Recall/YYYY-MM-DD/HH/HHMMSS.jpg`

### 待开发
- WiFi 同步到 PC 端
- PC 端上传接口

---

## v0.4.0 (2026-01-30)

### 重大变更
- **GUI框架重构** - 从 PySide6 迁移到 PyWebView + Vue 3
  - 使用 PyWebView 替代 PySide6 窗口
  - 使用 pystray 替代 QSystemTrayIcon 托盘图标
  - 前端使用 Vue 3 + Vite + Tailwind CSS

### 新增
- `web/frontend/` - Vue 3 前端项目
  - 截图浏览页面（网格展示、搜索、分页、大图预览）
  - 配置管理页面
  - 响应式布局
  - 现代化 UI 设计

### 变更
- `app.py` - 重写托盘和窗口逻辑
- `web/app.py` - 支持 Vue 构建产物的静态文件服务
- `requirements.txt` - 移除 PySide6，添加 pywebview 和 pystray

### 删除
- `gui/` 目录下的 PySide6 代码（不再需要）

### 构建前端
```bash
cd web/frontend
npm install
npm run build
```

---

## v0.3.2 (2026-01-30)

### 变更
- 日志改为追加模式（`mode='a'`），不再每次启动覆盖历史日志
- 移除控制台日志输出（StreamHandler），只写文件

### 新增
- `run.pyw` - 无窗口启动入口（待解决 .pyw 文件关联问题）

### 待解决
- `.pyw` 文件在 conda 环境下无法直接双击运行，需要后续用 VBS 脚本或 PyInstaller 打包解决

---

## v0.3.1 (2026-01-25)

### 修复
- **OCR GPU加速修复** - OCR从CPU模式切换到GPU模式
  - 问题1：缺少cuDNN 9.x依赖，导致CUDAExecutionProvider加载失败
  - 问题2：RapidOCR参数格式错误，应使用`det_use_cuda=True`而非`Det={"use_cuda": True}`
  - 修复后OCR速度从4-6秒降至1-1.5秒（GPU正常速度）

### 变更
- 启动时自动将pip安装的cuDNN路径加入PATH
- 每次启动清空日志文件

### 新增依赖
- `nvidia-cudnn-cu12` - cuDNN 9.x for CUDA 12

---

## v0.3.0 (2026-01-25)

### 变更
- 项目结构重组
  - 工具脚本移至 `scripts/` 目录
  - 日志文件移至 `logs/` 目录
- 添加日志功能（同时输出到文件和控制台）
- 启动时记录CUDA/GPU状态

### 项目结构
```
recall/
├── main.py, config.py   # 核心文件
├── scripts/             # 工具脚本
├── logs/                # 日志、PID、待处理列表
├── screenshots/         # 截图存储
└── doc/                 # 文档
```

### 文件说明
- `logs/recall.pid` - 进程ID文件，用于防止重复启动和停止服务
- `logs/pending_ocr.txt` - 无GPU时记录待处理图片路径
- `logs/recall.log` - 运行日志

---

## v0.2.1 (2026-01-25)

### 变更
- 图片格式从PNG改为JPEG（节省存储空间）
- OCR支持GPU加速（自动检测CUDA）
- 无GPU时标记图片待处理，不阻塞截图

### 新增
- `process_ocr.py` - 批量处理待OCR图片的脚本
- `pending_ocr.txt` - 待处理图片列表
- `JPEG_QUALITY` 配置项

### 工作流程
- 有GPU：截图时实时OCR
- 无GPU：截图保存到pending列表，之后用process_ocr.py批量处理

---

## v0.2.0 (2026-01-25)

### 新增
- OCR文字识别功能（使用RapidOCR）
- 截图保存时自动进行OCR，结果保存到同名txt文件

### 依赖
- 新增 rapidocr-onnxruntime

---

## v0.1.0 (初始版本)

### 功能
- 屏幕截图自动记录
- 基于像素变化检测触发截图
- 定时强制截图（默认5分钟）
- 后台服务管理（restart.py / restart.bat）
- PID文件管理

### 配置项
- `CHANGE_THRESHOLD` - 像素变化阈值 (1%)
- `FORCE_CAPTURE_INTERVAL` - 强制截图间隔 (300秒)
- `MIN_CAPTURE_INTERVAL` - 最小截图间隔 (1秒)
- `SCREENSHOT_DIR` - 截图存储目录

### 存储结构
- 按日期和小时分目录：`screenshots/YYYY-MM-DD/HH/HHMMSS.jpg`

### 依赖
- pillow
- numpy
