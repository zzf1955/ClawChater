#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_ROOT"
python -m pytest recall/tests/test_regression_pipeline.py recall/tests/test_api.py

cd "$REPO_ROOT/recall/frontend"
npm run test:unit
npm run test:e2e
