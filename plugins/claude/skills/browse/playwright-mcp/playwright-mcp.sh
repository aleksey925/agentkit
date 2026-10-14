#!/usr/bin/env bash
# fallback entry point for the browse skill: Playwright MCP with the container
# and stealth defaults baked in. used as the .mcp.json command, or directly:
#   playwright-mcp.sh setup    one-time: install Chrome for Testing + deps
#   playwright-mcp.sh          run the MCP server on stdio (masked)
set +e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STEALTH="$DIR/../stealth.js"  # shared with browse.sh, kept at the skill root

if [ "$1" = "setup" ]; then
  # @playwright/mcp pins its own Chrome-for-Testing build, so install through it
  # (a standalone chromium is a different version the server rejects). a fresh
  # container has an empty apt index, so refresh it before --with-deps.
  sudo apt-get update
  mise exec node@lts -- npx -y @playwright/mcp@latest \
    install-browser chrome-for-testing --with-deps
  exit $?
fi

exec mise exec node@lts -- npx -y @playwright/mcp@latest \
  --headless --browser chromium --no-sandbox \
  --viewport-size 1920x1080 \
  --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36" \
  --init-script "$STEALTH" \
  "$@"
