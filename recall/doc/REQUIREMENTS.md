# 需求单

用户在此记录需求，Claude 读取并执行。

---

## 待开发

### 移动端

- 安卓端与pc端在同一wifi下传输图片，安卓端单向传输到pc端，然后删除

### PC端

- 新的ai聊天模块的测试模块
- 细化prompt，workflow，对话agent的运作方式

---

## 开发中

<!-- Claude 细化后的需求会移到这里 -->

---

## 已完成

<!-- 完成的需求移到这里 -->

1. **拟人 AI 聊天 + 对话持久化 + 设置持久化** (v0.6.0)
   - CuriousAI 后台独立线程运行，主动探索用户数据
   - 双向消息：用户和 AI 都可以主动发送消息
   - send_message 工具：AI 通过工具调用发送消息
   - 对话持久化：消息存入数据库，切换标签页后可继续
   - AI 日志页面：显示 AI 后台活动（探索、工具调用等）
   - 设置持久化：AI 探索间隔、提问间隔、开关可配置
   - 情景设定：好奇的 AI，只能通过截图和对话探索世界

2. **Android 截图浏览功能** (v0.5.9)
   - 截图列表界面（2列网格，按时间倒序）
   - 大图预览（手势缩放、左右滑动切换）
   - 主界面"浏览截图"入口按钮

2. **记忆、RAG、聊天功能细化** (v0.5.7)
   - 统一工具测试脚本 `scripts/test_tools.py`
   - 时间处理统一为北京时间
   - LLM 配置集中到 `config.py`
   - 模型更新为 `claude-haiku-4-5-20251001`

2. **对话窗口 Markdown 渲染** (v0.5.6)
   - AI 助手回复支持 Markdown 格式渲染
   - 代码块语法高亮（Python、JavaScript、JSON、SQL、Bash 等）
   - 支持列表、粗体、斜体、引用块、表格
   - 使用 DOMPurify 防止 XSS 攻击

2. **LLM 工具调用修复** (v0.5.4)
   - 修复 Function Calling 不工作的问题
   - 将工具定义从 OpenAI 格式改为 Anthropic 原生格式
   - 现在 LLM 可以正确调用 search_memory、search_screenshots、get_activity 工具

2. **LLM 聊天界面** (v0.5.2)
   - 为 LLM 功能添加 Web 图形界面
   - 后端：`/api/chat` 和 `/api/chat/clear` API
   - 前端：ChatView.vue 聊天组件
   - 侧边栏新增"AI 助手"导航

2. **LLM 测试接口** (v0.5.3)
   - 命令行交互式测试脚本 `scripts/test_llm.py`
   - 独立LLM实例，不影响正常聊天
   - 显示详细调试信息（tool calls、迭代次数）
   - 支持命令：/clear、/history、/system、/quit

