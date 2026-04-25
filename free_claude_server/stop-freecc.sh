#!/usr/bin/env bash
# Stop Free Claude Code proxy using PID file.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="/tmp/free-claude-code.pid"
PORT="${FREECC_PORT:-8082}"

if [[ ! -f "$PID_FILE" ]]; then
    echo "No PID file found: $PID_FILE"
    echo "Server may already be stopped."
    exit 0
fi

PID="$(cat "$PID_FILE" 2>/dev/null || true)"
if [[ -z "$PID" ]]; then
    echo "PID file is empty. Removing stale file."
    rm -f "$PID_FILE"
    exit 0
fi

if ! kill -0 "$PID" >/dev/null 2>&1; then
    echo "Process $PID is not running. Removing stale PID file."
    rm -f "$PID_FILE"
    exit 0
fi

# Soft stop first
kill "$PID" >/dev/null 2>&1 || true

for _ in {1..30}; do
    if ! kill -0 "$PID" >/dev/null 2>&1; then
        break
    fi
    sleep 0.2
done

# Force stop if still alive
if kill -0 "$PID" >/dev/null 2>&1; then
    echo "Process $PID did not stop gracefully. Sending SIGKILL..."
    kill -9 "$PID" >/dev/null 2>&1 || true
    sleep 0.2
fi

if kill -0 "$PID" >/dev/null 2>&1; then
    echo "Failed to stop process $PID"
    exit 1
fi

rm -f "$PID_FILE"
echo "Free Claude Code proxy stopped (pid=$PID, port=$PORT)."
