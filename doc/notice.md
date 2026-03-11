# Notice

- 当前项目正在重构，recall_old 目录是旧项目，现在要全面进行迁移。其中新的架构在 architect 中，还未实现。
- 运行 FastAPI `TestClient` 相关测试时需安装 `httpx`，已在 `recall/requirements.txt` 补充该依赖。
- 直接执行 `scripts/migrate_recall_old_db.py` 时，需确保仓库根目录在 `PYTHONPATH`。脚本内已增加基于 `__file__` 的路径注入，避免 `ModuleNotFoundError: recall`。
