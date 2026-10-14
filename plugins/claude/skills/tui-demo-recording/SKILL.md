---
name: tui-demo-recording
description: >-
  Record an automated demo GIF or asciinema cast of a terminal UI (TUI) or CLI
  app for a README, headless with no human at the keyboard (VHS-driven). Use
  whenever the user wants to record a demo, make a demo gif, create a
  screencast, or show a terminal app in action for the README - for kafka-tui
  or any other TUI/CLI app.
---

# Recording a TUI/CLI demo for a README

Produce a polished, looping demo GIF of a terminal app, driven entirely by a
script (no human pressing keys), inside a headless container, and embed it in
the README. The hard part is not the recording, it is the dozen small traps
that each silently waste a render. This skill front-loads them.

## Why VHS, not raw asciinema

asciinema records a *live* interactive session - someone has to actually press
keys. You (Claude) are non-interactive and cannot sit in a full-screen TUI
pressing `j`/`k`/`enter`. [VHS](https://github.com/charmbracelet/vhs) (from
Charm, who also make Bubble Tea) scripts the whole session as a `.tape` file
(`Type`, `Sleep`, `Down`, `Enter`...), drives it headlessly, and outputs
GIF / MP4 / WebM **and** an asciinema `.cast`. So the artifact you author - the
tape - is exactly the kind of thing you can write and iterate on. Use VHS even
if the user says "asciinema"; VHS can emit a `.cast` too.

GIF is the safe README format: GitHub renders `![demo](img/demo.gif)`
everywhere. `<video>`/mp4 from a repo path does not render reliably on GitHub.

## The workflow

1. Install the VHS toolchain (`scripts/install-vhs-toolchain.sh`).
2. Make the app reachable + seed realistic data so every screen looks full.
3. Read the app's **real** keybindings from its code (never guess).
4. Smoke-test VHS, then write the `.tape` and verify each screen with
   `Screenshot` (you cannot watch the live session - screenshots are your eyes).
5. Render, dodging the 0-byte GIF memory ceiling.
6. Polish for the README and embed it.
7. Clean up and tell the user what was left behind.

Treat steps 4-5 as a loop: build the tape incrementally, screenshot every
transition, read the PNGs, fix, repeat. A render is cheap; a wrong assumption
about a keybinding or cursor position is what wastes time.

## Step 1 - Install the toolchain

Run `scripts/install-vhs-toolchain.sh` (needs `sudo` + network + Go). It
installs `vhs`, `ttyd`, `ffmpeg`, `chromium`, monospace+emoji fonts, and writes
the chromium no-sandbox fix (Step 2). Gotchas it already handles, so you know
why:

- **`ttyd` is not in Debian apt.** VHS needs it. The script pulls the static
  binary from `tsl0922/ttyd` GitHub releases (`ttyd.aarch64` / `ttyd.x86_64`)
  into `~/.local/bin`.
- **`vhs` lands in `$(go env GOBIN)`** when GOBIN is set (mise sets it to the
  toolchain bin dir), *not* `GOPATH/bin`. Resolve the real path before calling
  it; `go install` reports success either way.
- After install, put `~/.local/bin` and the Go bin dir on PATH for the session.

## Step 2 - The headless chromium sandbox fix (the #1 silent failure)

VHS renders frames with a headless Chromium (via go-rod). In a container Chromium
cannot create its sandbox namespace and dies with
`Failed to move to new namespace ... Operation not permitted` -> `recording
failed`, no GIF. Fix: pass `--no-sandbox`.

The trap: Debian's `/usr/bin/chromium` is a wrapper **script** that sets
`CHROMIUM_FLAGS=""` near the top, so exporting `CHROMIUM_FLAGS` in the
environment is wiped. But the script *sources* `/etc/chromium.d/*`, so drop the
flags there (the install script does this):

```sh
echo 'export CHROMIUM_FLAGS="$CHROMIUM_FLAGS --no-sandbox --disable-dev-shm-usage --disable-gpu --disable-software-rasterizer"' | sudo tee /etc/chromium.d/00-vhs
```

Validate the whole pipeline with a trivial tape before touching the real app:

```
Output "/tmp/smoke.gif"
Set Shell "bash"
Type "echo hello from vhs"
Enter
Sleep 800ms
```

If `/tmp/smoke.gif` is a non-zero file, rendering works.

## Step 3 - Isolate config and reach the backing service

**Isolate the app's config under a throwaway `HOME`** so you neither read nor
clobber the user's real setup, and the picker/screens show only your demo data:

```
export HOME=/tmp/demo-home   # put the app's config under here
```

Beware **project-layer config**: many tools also load `<repo>/.kafka-tui/`,
`.myapp/`, etc. by walking up from the *current directory* (like `.git`). Run
the app from a **neutral cwd** (e.g. `cd /tmp/demo-home`) so the repo's own
config does not merge in and surprise you with extra entries.

**Reaching a backing service on the Docker host** (DB, broker, API): on Docker
Desktop `host.docker.internal` resolves to the host, so `host.docker.internal:PORT`
usually just works. The classic trap is a service that **advertises
`localhost`** (Kafka `advertised.listeners`, some DBs): the bootstrap connects,
but follow-up traffic is told to dial `localhost`, which is the *container's*
localhost -> fails. Workaround that needs no host change: run a tiny in-container
forwarder so the advertised `localhost:PORT` relays to the host:

```bash
node scripts/tcp-forward.mjs 9092 host.docker.internal 9092 &
```

Then point the app at `localhost:PORT`. Prove the full path (not just the
bootstrap) before recording - e.g. do a real produce+consume / read+write, not
only a metadata/ping call.

## Step 4 - Seed realistic data

Empty screens make a bad demo. Before recording, create entities with varied,
realistic names and fill them so lists, detail views, and aggregates look
populated (e.g. several topics with different partition counts, JSON messages
with headers, consumer groups with *different* lag values including one caught
up). Use the app's own client library to seed - see the app reference for a
ready-made seeder.

## Step 5 - Read the app's real keybindings

Do **not** guess keys. Grep the app's source (key dispatcher, per-screen
keymaps, help screen) for the exact tokens (`enter`, `/`, `:`, `c`, `s`, `ctrl+r`,
digits...) and the navigation graph (how you enter/leave each screen). A tape
written against guessed keys silently lands on the wrong screen. The app
reference captures this map for known apps; for a new app, spend a few minutes
mapping it first (an Explore subagent is good for this).

## Step 6 - Write the .tape (syntax traps)

VHS tape gotchas that each cost a render:

- **Quote string/path args**: `Output "/tmp/demo.gif"`, `Set Shell "bash"`.
  Unquoted paths with `/` fail to parse.
- **`Home` / `End` keys do not exist** in VHS. To jump to the top of a list use
  `Up 20` (clamps at the first row); for bottom, `Down 20`.
- **Counts work**: `Down 3`, `Up 10`.
- **Hide setup**: wrap the `export HOME` / `cd` / `clear` in `Hide ... Show` so
  they do not appear in the GIF.
- **`Screenshot "/tmp/x.png"`** captures the current frame to a PNG. This is how
  you verify (Step 7). Sprinkle them at every screen transition.
- Knobs: `Set FontSize`, `Set Width`, `Set Height`, `Set Padding`,
  `Set TypingSpeed 55ms`, `Set Framerate 20`.
- Launch the app by **absolute path** (`/abs/app-demo ...`); the tape's shell
  starts in an arbitrary cwd.
- **Build in the container and copy the binary somewhere the host can't
  overwrite.** When the repo is a shared mount from a macOS/Windows host, a
  host-side rebuild silently replaces `dist/<app>` with a non-Linux binary
  mid-session and the next launch dies with `cannot execute binary file: Exec
  format error`. Build, then `cp dist/app /tmp/app-demo` and point the tape at
  `/tmp/app-demo`.

Structure the tape as: hidden setup -> launch -> one screen per "scene" with a
short `Sleep` so the viewer can read it -> a clean ending (Step 10).

## Step 7 - The Screenshot-verify loop (your eyes)

You cannot watch the live session, so **screenshot every transition and read the
PNGs**. Fast signal without even opening the image: a screenshot that is the
**shell prompt** (the app exited or never launched) is tiny (~10 KB); a real
full screen is 60-500 KB. Use `ls -la` sizes to triage, then `Read` the
suspicious ones. A frame that shows only your typed launch command and no UI
means you shot it before the app finished starting and connecting - give the
first screen a >=3s lead before the first screenshot.

Verify: each screen rendered, the **cursor landed on the row you intended**
(off-by-one after a filter/clear is common - reset with `Up 20` then `Down N`),
colors/truecolor look right, and value views actually switched (two screenshots
with *identical byte size* mean the keypress did nothing).

Check the **last frame** so the loop is clean (Step 10):

```bash
ffmpeg -y -sseof -0.4 -i /tmp/demo.gif -frames:v 1 /tmp/last.png   # then Read it
```

## Step 8 - Render and dodge the 0-byte GIF

The nastiest trap: a long tape (~50s) at high resolution (e.g. 1360x800) makes
ffmpeg's GIF palette pass exceed memory and write a **0-byte file - while VHS
prints "Creating ... GIF" and exits 0**. Always verify the output is non-zero
and valid:

```bash
ls -la /tmp/demo.gif
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,nb_read_frames -count_frames -of default=noprint_wrappers=1 /tmp/demo.gif
```

If it is 0 bytes: lower the resolution and/or framerate. **1100x540 at
`Set Framerate 20` reliably renders a ~35-40s demo at ~1.5 MB.** This also
keeps the GIF small enough for a README. (Single-session tapes encode fine;
multi-session tapes that relaunch the app mid-tape with `Hide`/clear/`Show` can
also corrupt the encode - prefer one continuous session.)

## Step 9 - Headless idle quit and unstable screens

In a headless container some apps self-quit after a few seconds of *idle* - e.g.
a config file-watcher (fsnotify) fails on the mounted FS and arms a delayed
`tea.Quit`. Symptom: a screenshot drops to the shell a few seconds after the app
last received input (later frames become tiny shell prompts), even though the
app is rock-solid on a real host.

The key realization: it is triggered by **inactivity, not by a specific
screen**. A tape that keeps sending a key every couple of seconds keeps the app
alive for the whole run - the full ~35s interactive demo records fine - while an
idle `Sleep 8s` probe catches the quit. (It is easy to misread this as "the
picker / startup screen is broken" because a passive screen you just look at is
where the idle quit bites first.) So:

- **Keep the tape busy.** Avoid idle gaps longer than ~3s; the steady stream of
  navigation keystrokes a good demo already has is enough. Don't park on a screen
  with a long `Sleep` and expect it to survive.
- **Don't trust a timed idle screenshot as a stability verdict.** The idle
  tolerance varies by build (seen from ~5s to 11s). Verify by rendering the
  actual interactive tape, not by sleeping on one screen.
- **Genuinely passive screens** (a picker/splash you only look at) may quit
  before you can park on them. Capture those as a **static PNG** taken in the
  first couple of seconds and add it to the README beside the GIF; note it
  records fine on the user's real machine (a container artifact, not an app bug).

## Step 10 - Polish for the README

- **Cut dead vertical space**: TUIs fill the terminal height, so sparse screens
  (a few rows) leave a big empty band. Lower `Set Height` until the tallest
  screen you show (often the help overlay or a full list) just fits. ~540 px at
  FontSize 12 is a good starting point.
- **Pick the width/font from the busiest hint bar.** The header hints clip when
  the menu pane runs out of columns, so the screen with the most (or longest)
  hints is the constraint - check that one, not an average screen. If it clips,
  shrink the font first (more columns at the same width) before widening the
  frame (widening grows frame area -> Step 8 risk). Some apps truncate long hints
  with "..." gracefully - decide whether that reads fine or is worth a few more
  columns. (FontSize 12 / Width 1100 is a reasonable start, not a guarantee.)
- **End on a content screen, not the shell.** Finish the tape with a `Sleep` on
  a nice screen and *no* final quit, so VHS stops there and the loop rejoins the
  start cleanly. A trailing `Ctrl+C` leaves a shell-prompt flash in the loop.
- **Embed** near the top, right under the one-line description:
  `![app demo](img/demo.gif)`. Keep the GIF under a couple MB.

## Step 11 - Clean up and report

Tell the user explicitly what you left behind, since most of it touches their
state or machine:
- **Seed data** written to their service (topics/tables/rows) - offer to remove it.
- **Background processes** you started (the forwarder) - still running.
- **Ephemeral container changes** (installed `vhs`/`ttyd`/`ffmpeg`/`chromium`,
  `/etc/chromium.d/00-vhs`, the throwaway `HOME`) - gone on container rebuild.
- Where the `.tape` lives so they can re-render with one `vhs demo.tape`.

## App-specific notes

`references/` holds per-app worked examples (exact launch command, keybinding
map, seeder, stable-path notes, a ready `.tape`). **kafka-tui** is the fully
worked example - read `references/kafka-tui.md` when the target is kafka-tui.
For a new app, write a short new reference as you go so the next run is easy.
