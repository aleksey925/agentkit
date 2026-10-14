#!/usr/bin/env bash
# entrypoint for mcp-call.js: ensure a working node (via mise) is on PATH, then
# drive the playwright MCP server. forwards all args to mcp-call.js.
set -uo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# the mise shim resolves `node` even when no version is active, so probe by
# actually running it; only then fall back to activating/installing via mise.
if ! node -e '' >/dev/null 2>&1; then
  if command -v mise >/dev/null 2>&1; then
    eval "$(mise env -s bash 2>/dev/null)" || true
    node -e '' >/dev/null 2>&1 || mise use -g node@24 >/dev/null 2>&1 || true
    eval "$(mise env -s bash 2>/dev/null)" || true
  fi
fi

if ! node -e '' >/dev/null 2>&1; then
  echo "mcp-call: no working node found (tried mise). install node, then retry." >&2
  exit 127
fi

exec node "$DIR/mcp-call.js" "$@"
