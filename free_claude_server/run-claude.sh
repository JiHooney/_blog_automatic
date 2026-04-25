#!/usr/bin/env bash
# Run Free Claude Code proxy in background and prepare env vars.
# Usage:
#   source ./run-claude.sh   # recommended (exports env vars to current shell)
#   ./run-claude.sh          # starts server only; prints export command

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"
PORT="${FREECC_PORT:-8082}"
BASE_URL="http://localhost:${PORT}"
LOG_FILE="/tmp/free-claude-code.log"
PID_FILE="/tmp/free-claude-code.pid"

read_env_value() {
    local key="$1"
    [[ -f "$ENV_FILE" ]] || return 0

    local raw
    raw="$(grep -E "^[[:space:]]*${key}[[:space:]]*=" "$ENV_FILE" | tail -n 1 || true)"
    raw="${raw#*=}"
    raw="${raw%%#*}"
    raw="$(echo "$raw" | xargs || true)"
    raw="${raw%\"}"
    raw="${raw#\"}"
    raw="${raw%\'}"
    raw="${raw#\'}"
    echo "$raw"
}

if command -v uv >/dev/null 2>&1; then
    UV_CMD=(uv)
elif python -m uv --version >/dev/null 2>&1; then
    UV_CMD=(python -m uv)
else
    echo "uv command not found. Trying to install uv via pip..." >&2
    if python -m pip install --user uv >/dev/null 2>&1 && python -m uv --version >/dev/null 2>&1; then
        UV_CMD=(python -m uv)
    else
        echo "Error: uv is required. Install it first (python -m pip install --user uv)." >&2
        exit 1
    fi
fi

AUTH_TOKEN="${ANTHROPIC_AUTH_TOKEN:-$(read_env_value ANTHROPIC_AUTH_TOKEN)}"
if [[ -z "$AUTH_TOKEN" ]]; then
    AUTH_TOKEN="freecc"
fi

is_server_ready() {
    if command -v curl >/dev/null 2>&1; then
        if [[ -n "$AUTH_TOKEN" ]]; then
            curl -fsS -H "ANTHROPIC_AUTH_TOKEN: ${AUTH_TOKEN}" "${BASE_URL}/v1/models" >/dev/null 2>&1
        else
            curl -fsS "${BASE_URL}/v1/models" >/dev/null 2>&1
        fi
    else
        return 1
    fi
}

cd "$SCRIPT_DIR"

# Reuse existing server if healthy
if is_server_ready; then
    echo "Proxy already running: ${BASE_URL}"
else
    # Clean stale pid file
    if [[ -f "$PID_FILE" ]]; then
        old_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
        if [[ -n "$old_pid" ]] && ! kill -0 "$old_pid" >/dev/null 2>&1; then
            rm -f "$PID_FILE"
        fi
    fi

    if [[ -f "$PID_FILE" ]]; then
        existing_pid="$(cat "$PID_FILE")"
        if kill -0 "$existing_pid" >/dev/null 2>&1; then
            echo "Proxy process already running (pid=${existing_pid}): ${BASE_URL}"
        fi
    else
        nohup "${UV_CMD[@]}" run uvicorn server:app --host 0.0.0.0 --port "$PORT" >>"$LOG_FILE" 2>&1 < /dev/null &
        SERVER_PID=$!
        disown "$SERVER_PID" 2>/dev/null || true
        echo "$SERVER_PID" >"$PID_FILE"

        for _ in {1..50}; do
            if is_server_ready; then
                break
            fi
            sleep 0.2
        done

        if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
            echo "Error: proxy server failed to start. See $LOG_FILE" >&2
            rm -f "$PID_FILE"
            exit 1
        fi

        echo "Proxy started in background: ${BASE_URL} (pid=${SERVER_PID})"
    fi
fi

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
    # Sourced: persist env vars in current shell
    export ANTHROPIC_BASE_URL="$BASE_URL"
    export ANTHROPIC_AUTH_TOKEN="$AUTH_TOKEN"
    echo "Environment exported in current shell."
    echo "  ANTHROPIC_BASE_URL=${ANTHROPIC_BASE_URL}"
    echo "  ANTHROPIC_AUTH_TOKEN=${ANTHROPIC_AUTH_TOKEN}"
    echo "Now run: claude"
else
    # Executed: cannot modify parent shell env
    echo "Server is ready, but this script was executed (not sourced)."
    echo "Run this to set env in your current shell:"
    echo "  export ANTHROPIC_BASE_URL=\"${BASE_URL}\""
    echo "  export ANTHROPIC_AUTH_TOKEN=\"${AUTH_TOKEN}\""
    echo "Then run: claude"
fi
