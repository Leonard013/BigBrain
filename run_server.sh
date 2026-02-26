#!/usr/bin/env bash
# Launches the BigBrain MCP server.
# If 'bigbrain' is on PATH (pip install), use it directly.
# Otherwise, fall back to running the module with python.
if command -v bigbrain &>/dev/null; then
    exec bigbrain "$@"
else
    DIR="$(cd "$(dirname "$0")" && pwd)"
    exec python -m bigbrain.server "$@"
fi
