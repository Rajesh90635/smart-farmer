#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../ai"
source .venv/bin/activate 2>/dev/null || true
pytest tests/ -v
