#!/bin/zsh
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

echo "Starting Hermes supervisor on :8090"
python3 hermes_supervisor.py > /tmp/hermes_supervisor.log 2>&1 &
SUP_PID=$!

echo "Starting router on :8080"
python3 router_server.py > /tmp/hermes_router.log 2>&1 &
ROUTER_PID=$!

cleanup() {
  kill "$SUP_PID" "$ROUTER_PID" >/dev/null 2>&1 || true
}

trap cleanup EXIT INT TERM

echo
echo "Router:     http://127.0.0.1:8080"
echo "Supervisor: http://127.0.0.1:8090/health"
echo
echo "Logs:"
echo "  /tmp/hermes_router.log"
echo "  /tmp/hermes_supervisor.log"
echo
echo "Press Ctrl+C to stop."

wait
