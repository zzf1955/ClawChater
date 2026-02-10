---
id: "010"
title: "修复 recall 前端白屏问题"
priority: high
depends_on: []
module: recall
branch: main
estimated_scope: small
---

## 背景

recall 启动后访问 http://127.0.0.1:5000 白屏/404。经测试，Flask 路由本身正常（test_client 测试 GET / 返回 200，静态资源也能正确加载），问题可能出在 recall 整体启动流程中 Flask 线程未正常启动。

## 技术方案

### 1. 排查 Flask 线程启动问题

检查 `app.py` 中 `_start_web_server()` 方法：
- 添加 try/except 包裹 Flask 启动，捕获并记录异常
- 确保 `db.init_db()` 在 Flask 线程启动前已完成
- 检查 `web/app.py` 导入 `config` 和 `db` 时是否有副作用导致失败

### 2. 改进 Flask 启动可靠性

修改 `recall/app.py:_start_web_server()`：
```python
def _start_web_server(self):
    try:
        from web.app import app
        import logging as flask_logging
        flask_logging.getLogger('werkzeug').setLevel(flask_logging.ERROR)
        app.run(host='127.0.0.1', port=WEB_PORT, debug=False, use_reloader=False)
    except Exception as e:
        log.error(f"Web 服务器启动失败: {e}", exc_info=True)
```

### 3. 验证前端构建产物

- 确认 `web/static/dist/index.html` 存在且内容正确
- 确认 `web/static/dist/assets/` 下的 JS/CSS 文件存在
- 如果需要，重新构建前端

### 4. 实际启动测试

- 运行 `conda run -n recall python main.py` 启动 recall
- 浏览器访问 http://127.0.0.1:5000 验证页面加载
- 检查 `logs/recall.log` 中是否有错误信息

## 验收标准

- [x] recall 启动后 http://127.0.0.1:5000 能正常显示 Vue 前端
- [x] Flask 启动失败时有明确的错误日志
- [x] 前端页面能正常加载截图列表和配置页面

## 测试要求

- [x] 手动启动 recall 并访问前端页面
- [x] 检查 recall.log 无异常错误

---
completed_by: w-7e3b
completed_at: 2026-02-08T12:00:00+08:00
commit: 1066a6c
files_changed:
  - recall/app.py
  - recall/tests/integration/test_web_api.py
test_result: "17 passed, 0 failed"
---
