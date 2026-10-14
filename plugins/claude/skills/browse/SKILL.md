---
name: browse
description: Access websites with the guarantee of accurate, up-to-date data
---

Alternative way to reach websites when the default `WebFetch` / `WebSearch`
don't work (site blocks them, returns incomplete content, etc.).

Use the **`browse.sh`** runner shipped next to this file - a thin wrapper
around **agent-browser** (a native CLI that drives Chrome for agents) with the
container and stealth settings baked in. Call it by its absolute path
(`<this skill's dir>/browse.sh`); it forwards every argument to agent-browser,
so `browse.sh open`, `browse.sh snapshot`, `browse.sh click @e2` behave exactly
like the underlying commands but always launch masked.

## Setup

One time per container - installs Node, a browser, and agent-browser
(arch-aware: Chrome for Testing on x86, system chromium on ARM):

```bash
browse.sh setup
```

## Usage

A background daemon starts on the first command and persists, so calls chain
and keep the session warm:

```bash
browse.sh open example.com
browse.sh snapshot              # accessibility tree; elements get refs like @e2
browse.sh click @e2
browse.sh fill @e3 "hello"
browse.sh screenshot out.png
browse.sh close
```

- prefer `snapshot` over screenshots - it's text, token-cheap, and yields
  deterministic `@eN` refs to act on (`click @e2`, `fill @e3 "..."`).
- add `--json` for machine-readable output (`snapshot --json`).
- SPAs render async: `wait <ms | selector | condition>` after `open`.
- read data without a screenshot: `get text|html|value|attr|title|url @e2`.
- run parallel pages with isolated state: `--session <name>`.

Command groups:

- nav: `open`, `close`, `back`, `forward`, `reload`, `tab`
- interact: `click`, `fill`, `type`, `press`, `hover`, `check`/`uncheck`,
  `select`
- read: `snapshot`, `screenshot`, `get`, `is`
- advanced: `eval <js>`, `wait`, `find`, `batch`

Full reference: `browse.sh skills get core --full`.

## Stealth

The runner injects [stealth.js](stealth.js) and a Windows User-Agent on launch,
hiding the headless bot signals most sites check (`navigator.webdriver`,
platform, WebGL renderer). It is always on - nothing to configure.

This clears what most sites check. It can't reach a few deep signals (Service
Worker UA, Linux fonts, worker WebGL), so CreepJS-grade fingerprinters can
still flag the browser - nothing in this skill closes that gap.

## Limitations

- If a command hangs, the daemon is wedged - `browse.sh close --all`, then
  retry.

## Fallback (just in case)

A Playwright MCP variant is kept as a backstop, in case agent-browser itself
breaks or a site blocks it in a way the runner can't work around. Same
stealth.js, different engine (Playwright instead of agent-browser's CDP) - so
it's worth a try when the main path fails, but not as a routine alternative:
[playwright-mcp/playwright-mcp.md](playwright-mcp/playwright-mcp.md).
