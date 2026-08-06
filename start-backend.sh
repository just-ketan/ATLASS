#!/usr/bin/env bash
# ATLASS backend launcher — matches the Vercel frontend (VITE_API_BASE_URL → port 8000).
#
# Usage:
#   ./start-backend.sh              # Platform API (frontend) on :8000
#   ./start-backend.sh --with-v2    # Platform :8000 + v2 cognition API :8001
#   ./start-backend.sh --v2-only    # v2 only on :8001
#
# Environment:
#   ATLASS_HOST       default 0.0.0.0
#   ATLASS_PORT       default 8000  (set VITE_API_BASE_URL to http://localhost:8000 locally)
#   ATLASS_V2_PORT    default 8001
#   ATLASS_RELOAD     default 1 (uvicorn --reload)
#   ATLASS_DATA_DIR   default <repo>/data

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

RUN_V1=1
RUN_V2=0

for arg in "$@"; do
  case "$arg" in
    --with-v2) RUN_V2=1 ;;
    --v2-only) RUN_V1=0; RUN_V2=1 ;;
    -h|--help)
      sed -n '2,14p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      exit 1
      ;;
  esac
done

if [[ -f "$ROOT/backend/.venv/bin/python" ]]; then
  PYTHON="$ROOT/backend/.venv/bin/python"
elif [[ -f "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  echo "No virtualenv found. Create one and install deps:" >&2
  echo "  python3 -m venv backend/.venv && backend/.venv/bin/pip install -r backend/requirements.txt" >&2
  exit 1
fi

export PYTHONPATH="${ROOT}/backend:${ROOT}"
export ATLASS_DATA_DIR="${ATLASS_DATA_DIR:-$ROOT/data}"

HOST="${ATLASS_HOST:-0.0.0.0}"
PORT="${ATLASS_PORT:-8000}"
V2_PORT="${ATLASS_V2_PORT:-8001}"
RELOAD="${ATLASS_RELOAD:-1}"

mkdir -p "$ATLASS_DATA_DIR" "$ROOT/data/uploads" "$ROOT/data/v2"

UVICORN_ARGS=()
if [[ "$RELOAD" == "1" ]]; then
  UVICORN_ARGS+=(--reload)
fi

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}ATLASS backend${NC}"
echo "  Python:    $PYTHON"
echo "  Data dir:  $ATLASS_DATA_DIR"
echo "  Frontend:  set VITE_API_BASE_URL=http://localhost:${PORT} (local)"
echo "  Vercel:    set VITE_API_BASE_URL=https://<your-backend-host>"

cleanup() {
  [[ -n "${V2_PID:-}" ]] && kill "$V2_PID" 2>/dev/null || true
  [[ -n "${V1_PID:-}" ]] && kill "$V1_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

if [[ "$RUN_V2" == "1" ]]; then
  echo -e "${GREEN}Starting ATLASS v2 API on http://${HOST}:${V2_PORT}${NC}"
  "$PYTHON" -m uvicorn atlasse_v2.api.app:app \
    --host "$HOST" --port "$V2_PORT" "${UVICORN_ARGS[@]}" &
  V2_PID=$!
  sleep 1
fi

if [[ "$RUN_V1" == "1" ]]; then
  echo -e "${GREEN}Starting ATLASS Platform API on http://${HOST}:${PORT}${NC}"
  echo "  Health: http://localhost:${PORT}/health"
  if [[ "$RUN_V2" == "1" ]]; then
    "$PYTHON" -m uvicorn atlasse.platform.api:app \
      --host "$HOST" --port "$PORT" "${UVICORN_ARGS[@]}" &
    V1_PID=$!
    wait "$V1_PID" "$V2_PID"
  else
    exec "$PYTHON" -m uvicorn atlasse.platform.api:app \
      --host "$HOST" --port "$PORT" "${UVICORN_ARGS[@]}"
  fi
else
  wait "$V2_PID"
fi
