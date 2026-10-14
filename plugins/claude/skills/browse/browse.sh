#!/usr/bin/env bash
# entry point for the browse skill: agent-browser with container + stealth
# defaults baked in. use it exactly like agent-browser.
#   browse.sh setup            one-time: install node, chromium, agent-browser
#   browse.sh <cmd> [args...]  any agent-browser command (open, snapshot, ...)
set +e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# run agent-browser, falling back to mise when the shim is not on PATH
ab() {
  if command -v agent-browser >/dev/null 2>&1; then
    agent-browser "$@"
  else
    mise exec node@lts -- agent-browser "$@"
  fi
}

if [ "$1" = "setup" ]; then
  mise use -g node@lts
  command -v agent-browser >/dev/null 2>&1 || npm install -g agent-browser
  if [ "$(uname -m)" = "x86_64" ]; then
    ab install --with-deps
  else
    # no Chrome-for-Testing ARM64 build; a fresh container has an empty apt
    # index, so refresh it before installing chromium
    sudo apt-get update
    sudo apt-get install -y chromium
  fi
  exit $?
fi

# the daemon reads these once, at start; the wrapper sets them on every call so
# the first invocation always launches masked
export AGENT_BROWSER_ARGS="--no-sandbox,--disable-blink-features=AutomationControlled"
export AGENT_BROWSER_INIT_SCRIPTS="$SKILL_DIR/stealth.js"
export AGENT_BROWSER_USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

# chromium path is needed only on ARM (x86 downloads Chrome for Testing)
if [ "$(uname -m)" != "x86_64" ] && [ -z "$AGENT_BROWSER_EXECUTABLE_PATH" ] \
   && [ -x /usr/bin/chromium ]; then
  export AGENT_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium
fi

ab "$@"
