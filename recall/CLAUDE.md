# CLAUDE.md

Claude Code 开发指导文件。

## 工作流程 Skills

使用 `/start` 或 `/debug` 命令触发对应的工作流程：

| 命令 | 用途 |
|------|------|
| `/start` | 开始开发第一个待开发需求 |
| `/debug` | 开始修复第一个待修复 bug |

详细流程定义在 `.claude/skills/` 目录下。

## 文档体系

| 文件 | 用途 | 维护者 |
|------|------|--------|
| `CLAUDE.md` | Claude Code 开发指导，定义工作流程和项目规范 | 用户 |
| `doc/REQUIREMENTS.md` | 需求单，记录待开发/开发中/已完成的功能需求 | 用户写需求，Claude 细化并更新状态 |
| `doc/BUGS.md` | Bug 列表，记录待修复/已修复的 bug | 用户报告 bug，Claude 修复并更新状态 |
| `doc/CHANGELOG.md` | 版本更新日志，记录每次功能变更 | Claude 开发完成后更新 |
| `doc/README.md` | 项目概况，面向外部的项目介绍 | 用户 |
| `doc/framework.md` | 架构设计文档，记录模块职责和依赖关系 | Claude 重构后更新 |

## 核心原则

- 先跑起来，再完善
- 最小实现，避免过度设计
- 新模块一定要搭配测试，实现新功能一定要通过测试

## 环境

### PC 端
- Python 3.11，conda 环境：`recall`
- GPU: RTX 4060 (CUDA 12.x)
- 代理：`$env:HTTP_PROXY="http://127.0.0.1:7897"; $env:HTTPS_PROXY="http://127.0.0.1:7897"`

### Android 端
- Android SDK：`C:\Users\ZZF\AppData\Local\Android\Sdk`
- adb：`C:\Users\ZZF\AppData\Local\Android\Sdk\platform-tools\adb.exe`

## 常用命令

**重要**：Claude Code 的 Bash 工具在 Windows 上运行于 Git Bash 环境，不要使用 `powershell -Command` 包装命令。

```bash
# PC 启动
conda run -n recall python main.py

# 前端开发
npm run dev --prefix "D:/BaiduSyncdisk/Desktop/recall/web/frontend"

# 前端构建
npm run build --prefix "D:/BaiduSyncdisk/Desktop/recall/web/frontend"

# Android 编译（需要用 cmd 执行 bat 文件）
cmd //c "cd /d D:\\BaiduSyncdisk\\Desktop\\recall\\android\\RecallMobile && gradlew.bat assembleDebug"

# Android 安装到设备
"C:/Users/ZZF/AppData/Local/Android/Sdk/platform-tools/adb.exe" install -r "D:/BaiduSyncdisk/Desktop/recall/android/RecallMobile/app/build/outputs/apk/debug/app-debug.apk"
```

**注意**：
- 路径使用正斜杠 `/` 或双反斜杠 `\\`
- npm 使用 `--prefix` 参数指定项目目录，避免 cd 切换
- Windows bat 文件需要通过 `cmd //c` 执行

## 项目结构

详细架构设计见 `doc/framework.md`。

```
recall/
├── main.py                    # 应用入口
├── app.py                     # 应用协调者
├── config.py                  # 配置管理
├── db.py                      # 数据库层
├── ocr_worker.py              # OCR 处理
│
├── core/                      # 核心业务层
│   ├── interfaces.py          # 接口定义
│   ├── container.py           # 依赖注入容器
│   └── capture.py             # 截图服务
│
├── ui/                        # UI 层
│   ├── tray.py                # 托盘管理
│   └── window.py              # 窗口管理
│
├── web/                       # Web 层
│   ├── app.py                 # Flask API
│   └── frontend/              # Vue 3 前端
│
├── utils/                     # 工具模块
├── tests/                     # 测试模块
│   ├── conftest.py            # pytest fixtures
│   ├── unit/                  # 单元测试
│   └── integration/           # 集成测试
│
├── scripts/                   # 工具脚本
├── data/                      # 数据目录
├── screenshots/               # 截图存储
├── logs/                      # 日志
├── android/                   # Android 端
└── doc/                       # 文档
```

## 注意事项

### 测试优先
- 开发完功能或 debug 之前，先查找是否有现成的测试模块
- 优先使用已有的测试接口进行测试
- 新功能必须编写对应的单元测试（`tests/unit/`）
- 运行测试：`pytest tests/ -v`

### 开发规范
- 新模块必须支持依赖注入（构造函数接受依赖参数）
- 保留全局实例确保向后兼容
- 修改架构后更新 `doc/framework.md`
- 完成开发后更新 `doc/CHANGELOG.md`

### OCR/GPU
- onnxruntime-gpu 需要 CUDA 12.x + cuDNN 9.x
- 必须在 import onnxruntime 前将 cuDNN 路径加入 PATH
- RapidOCR 参数：`det_use_cuda=True`

### 依赖注入
- 所有核心模块支持构造函数注入，便于测试
- 使用 `core/container.py` 管理服务实例
- 测试时使用 `tests/conftest.py` 中的 fixtures 创建隔离环境
