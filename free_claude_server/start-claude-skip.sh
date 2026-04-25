#!/usr/bin/env bash
# Start free-claude-code proxy and launch Claude Code with --dangerously-skip-permissions.
# This script must be sourced OR executed - it always launches claude interactively.
# Usage: bash start-claude-skip.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start proxy (reuse if already running) by sourcing run-claude.sh
source "$SCRIPT_DIR/run-claude.sh"

export ANTHROPIC_BASE_URL="$ANTHROPIC_BASE_URL"
export ANTHROPIC_AUTH_TOKEN="$ANTHROPIC_AUTH_TOKEN"

echo ""
echo "Launching: claude --dangerously-skip-permissions"
echo ""

exec claude --dangerously-skip-permissions
