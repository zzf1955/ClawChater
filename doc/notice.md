# Notice

- 当前项目正在重构，recall_old 目录是旧项目，现在要全面进行迁移。其中新的架构在 architect 中，还未实现。
- 运行 FastAPI `TestClient` 相关测试时需安装 `httpx`，已在 `recall/requirements.txt` 补充该依赖。
- 调试屏幕检测/截图/OCR 触发链路时，可查看 `recall/data/logs/recall.log`；日志级别可通过 `RECALL_LOG_LEVEL` 覆盖，默认 `DEBUG`。
