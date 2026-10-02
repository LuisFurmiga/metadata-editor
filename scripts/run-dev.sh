#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
trap 'kill 0' EXIT INT TERM
(cd "$ROOT/backend" && python -m uvicorn app.main:app --reload --port 8000) &
(cd "$ROOT/frontend" && npm run dev) &
wait
