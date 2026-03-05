# AGENTS.md

## Cursor Cloud specific instructions

### Architecture overview

ClawChater is a three-module system. See `CLAUDE.md` and `README.md` for full details.

| Module | Language | Port | Key commands |
|--------|----------|------|-------------|
| recall | Python (≥3.11) | 5000 | `python3 web/app.py` (Flask API), `pytest tests/ -v` |
| screen-agent | Python (≥3.11) | — | `DRY_RUN=true python3 main.py` |
| openclaw | TypeScript (Node ≥22.12) | 18789 | `pnpm check`, `pnpm test`, `pnpm dev gateway` |

### Linux caveats (Cloud VM)

- **recall `main.py` cannot run on Linux** — it imports `pywin32`, `pystray`, `PySide6` which are Windows-only. Use `python3 web/app.py` directly to start the Flask API on port 5000.
- The Windows-only packages (`pywin32`, `pystray`, `PySide6`, `pywebview`) are **not installed** in the Cloud VM. Only Linux-compatible dependencies from `recall/requirements.txt` are installed (numpy, Pillow, imagehash, psutil, flask, httpx, chromadb, etc.).
- OCR (onnxruntime-gpu, rapidocr) is not available in the Cloud VM (no CUDA GPU). The API works fine without it.

### Running services

- **Recall Flask API**: `cd recall && python3 web/app.py` — starts on `127.0.0.1:5000`
- **Screen Agent**: `cd screen-agent && DRY_RUN=true python3 main.py` — polls Recall API every 5min, defaults to DRY_RUN (prints instead of sending to OpenClaw)
- **OpenClaw Gateway**: `cd openclaw && OPENCLAW_SKIP_CHANNELS=1 OPENCLAW_GATEWAY_TOKEN=dev-test-token pnpm dev gateway --allow-unconfigured` — starts on port 18789. First run builds UI assets automatically.

### Testing

- **recall**: `cd recall && python3 -m pytest tests/ -v` — some tests may error on `ModuleNotFoundError` for `curious_ai` and `message_queue` (pre-existing code gaps, not env issues). Core tests (test_db, test_capture, test_text_memory) pass.
- **screen-agent**: No automated tests; verify by running briefly with `DRY_RUN=true ANALYSIS_INTERVAL=3 timeout 10 python3 main.py`.
- **openclaw**: `cd openclaw && pnpm test` runs unit/extensions/gateway suites in parallel. Individual suites: `npx vitest run --config vitest.unit.config.ts`. Lint: `pnpm check` (runs tsgo + oxlint + oxfmt).

### OpenClaw submodule

OpenClaw is a git submodule. Run `git submodule update --init` if the `openclaw/` directory is empty. See `openclaw/AGENTS.md` for OpenClaw-specific contribution guidelines.

### Recall Vue frontend

The frontend at `recall/web/frontend/` uses npm (no lockfile). Pre-built output is served from `recall/web/static/dist/`. To rebuild: `cd recall/web/frontend && npm install && npm run build`.
