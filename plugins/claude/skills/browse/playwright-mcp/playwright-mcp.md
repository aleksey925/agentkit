# Playwright MCP fallback

Backstop for the `browse` skill, for when the main path (agent-browser via
`browse.sh`) breaks or a site blocks it in a way the runner can't work around.
Same [stealth.js](../stealth.js), different engine - Playwright instead of
agent-browser's CDP. Use it only when the main path fails.

Like `browse.sh`, the [playwright-mcp.sh](playwright-mcp.sh) wrapper bakes in
the headless flags, Windows UA, and the absolute `stealth.js` path, so there is
nothing to hand-edit. Call it by its absolute path.

## Which mode

Pick by how many steps you need on the page, and decide BEFORE you start:

- **A single action**, or a chain you can honestly express in one
  `mcp-call.sh` invocation -> one-shot (below). Just do it, no need to ask.
- **Several actions on one page** (navigate -> inspect -> click ->
  screenshot), or an ongoing session -> this is the MCP-mode case (the
  browser stays alive between calls, so state and `eN` refs persist). But
  MCP mode needs an edit to `.mcp.json` plus a Claude Code restart, so do
  NOT pick for the user: **STOP and ask with `AskUserQuestion`**. Never
  silently grind through one-shot for a multi-step task.

When you ask, frame the real trade-off so the choice is informed:

- **MCP mode** - one-time `.mcp.json` edit + restart now; afterwards the
  browser lives between calls and refs/state persist, so multi-step flows
  are comfortable.
- **One-shot** - no config edit, no restart; but everything must go in one
  invocation, refs/state do not survive between calls, and every retry
  starts a fresh browser from scratch. Workable, but clumsy and brittle for
  multi-step flows.

## Setup

One time per container - install Chrome for Testing and its system deps (needs
`sudo`):

```bash
playwright-mcp.sh setup
```

It installs through the MCP's own installer on purpose: @playwright/mcp pins a
specific Chrome-for-Testing build, and a separately-installed chromium is a
different version the server rejects.

## MCP mode

Use this for several actions on one page - the browser stays alive between
calls, so state and refs persist.

Point `.mcp.json` at the wrapper - that is the whole config, since the script
supplies every flag and the stealth path:

```json
{
  "mcpServers": {
    "playwright": {
      "type": "stdio",
      "command": "<ABSOLUTE_PATH_TO_SKILL>/playwright-mcp/playwright-mcp.sh"
    }
  }
}
```

Restart Claude Code after adding it. Tools (from `tools/list`):

- nav: `browser_navigate`, `browser_navigate_back`, `browser_tabs`
- interact: `browser_click`, `browser_type`, `browser_fill_form`,
  `browser_press_key`, `browser_hover`, `browser_select_option`,
  `browser_drag`, `browser_file_upload`, `browser_drop`,
  `browser_handle_dialog`
- read: `browser_snapshot` (prefer over screenshots),
  `browser_take_screenshot`, `browser_console_messages`,
  `browser_network_requests`
- advanced: `browser_evaluate`, `browser_run_code_unsafe`, `browser_wait_for`
  (SPAs need it after navigate), `browser_resize`, `browser_close`

The browser is installed from the shell (`setup`); there is no install tool.

## Without registering: `mcp-call.sh`

For a single action, or a chain you can run in one invocation, without
touching `.mcp.json`. [mcp-call.sh](mcp-call.sh) (a thin node driver,
[mcp-call.js](mcp-call.js)) starts the server, does the JSON-RPC handshake,
sends each command, and waits for the matching `id` - no `sleep` races. Each
arg (or `--file` line) is one command, in either form:

**Every invocation is a fresh server and a fresh browser** - state and `eN`
refs do NOT survive between invocations. So put the whole flow (navigate,
dismiss, click, screenshot) in ONE invocation, and prefer targeting that
needs no prior snapshot:

- `browser_click` (and `browser_hover`) take a **CSS selector** in `target`,
  not only an `eN` ref - so you can act without a snapshot at all.
- no stable selector (cookie banners and the like)? click by text with
  `browser_evaluate`.
- snapshot+ref is the last resort here: a ref is only valid inside the
  snapshot that produced it, so you must navigate and snapshot in the SAME
  invocation to even read it.

```bash
MC="$HOME/.claude/skills/browse/playwright-mcp/mcp-call.sh"

# tool + JSON args, or tool alone, or a full JSON-RPC object (passthrough)
"$MC" 'browser_navigate {"url":"https://opera.com"}' 'browser_snapshot' --full
"$MC" '{"method":"tools/list","params":{}}'          # inspect a tool's schema
echo 'browser_snapshot' | "$MC" --json               # pipe + raw output
```

A full flow in one invocation - open a page, dismiss the cookie banner by
text, scroll to load lazy images, then full-page screenshot:

```bash
"$MC" \
  'browser_navigate {"url":"https://www.opera.com"}' \
  'browser_evaluate {"function":"() => { const b=[...document.querySelectorAll(\"button\")].find(x=>/accept all/i.test(x.textContent)); b?.click(); return !!b; }"}' \
  'browser_wait_for {"time":2}' \
  'browser_take_screenshot {"filename":"opera-full.png","fullPage":true}'
```

Output per call is `→ [id] tool` then `OK`/`ERROR` and the text content.
Flags: `--full` (don't truncate - needed to read a full snapshot and find
`@eN` refs), `--json` (raw responses), `--debug` (server stderr), `--file P`
(commands from a file; handy for long chains). For a single action pass one
command; for several, chain them in one invocation as above, not across
calls.

## Tool arguments & gotchas

- **`target`, not `ref`.** `browser_click`, `browser_hover`,
  `browser_take_screenshot` (element shots), etc. take `element` (a
  human-readable description) plus **`target`** (the `eN` ref from a snapshot,
  or a CSS selector). Passing `ref` fails with
  `Invalid input: expected string ... at target`. The snapshot prints refs as
  `[ref=eN]`, which is the value you put in `target`.
- **Screenshot paths are sandboxed.** `filename` must be relative; files land
  in the project dir or `.playwright-mcp`. An absolute path like
  `/tmp/x.png` is rejected (`File access denied: outside allowed roots`).
- **`fullPage` + lazy images.** A full-page shot of a page with lazy-loaded
  images shows blank boxes where they never scrolled into view. Scroll first
  (`browser_evaluate '() => window.scrollTo(0, document.body.scrollHeight)'`,
  wait, then screenshot) if you need them rendered.
- **node comes from mise.** Bare `node` may be a mise shim with no active
  version; `mcp-call.sh` activates it for you, so use the wrapper rather than
  calling `node` directly.

## Bare-bones fifo (last resort)

If node is unavailable, drive the server directly. Fragile - fixed `sleep`s,
no response matching - so prefer `mcp-call.sh`:

```bash
mkfifo /tmp/mcp_pipe 2>/dev/null || true
"$HOME/.claude/skills/browse/playwright-mcp/playwright-mcp.sh" < /tmp/mcp_pipe &
MCP_PID=$!
exec 3>/tmp/mcp_pipe

echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe","version":"1.0"}}}' >&3
sleep 2
echo '{"jsonrpc":"2.0","method":"notifications/initialized"}' >&3
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"browser_navigate","arguments":{"url":"TARGET_URL"}}}' >&3
sleep 5
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"browser_snapshot","arguments":{}}}' >&3
sleep 3

exec 3>&-
kill $MCP_PID 2>/dev/null
rm /tmp/mcp_pipe
```

## Stealth & limits

The wrapper always injects `stealth.js`: hides `navigator.webdriver`, sets
platform and UA to Windows, adds `window.chrome`, plugins, WebGL renderer, and
Client Hints (verified - a masked page reports `platform: Win32`, the Windows
UA, `window.chrome` present, plugins populated). It can't reach Service Worker
UA, Linux fonts, or worker WebGL, so CreepJS-grade fingerprinters still flag
it.

Redirect check: a headless browser with no ad blocker can hit a JS full-page
redirect (e.g. to a big retailer). Confirm with `curl -sI -L <url>` (a real
redirect shows 301/302) or `WebFetch`; if both return the original site, the
browser redirect is fake.
