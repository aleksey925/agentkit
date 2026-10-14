---
name: proj-mem
description: Write, refactor, or extend the **project-root** `CLAUDE.md` (the one at the repository root). NOT for `~/.claude/CLAUDE.md` (user-global), `.claude.local.md` (personal override), or nested package-level `CLAUDE.md` files — different scope and style.
---

# Project CLAUDE.md Writer

Writes or refactors a project's `CLAUDE.md` so that a fresh Claude session can pick up the project's positioning, design contracts, and build commands without reading any code.

The skill is opinionated on *structure* and *tone*. Content comes from the user (for things only they know) and from the repo itself (for things the code already proves).

## Scope: project-root CLAUDE.md only

This skill targets exactly one file: `./CLAUDE.md` at the **repository root** — the file checked into git and shared with the team.

It does **not** apply to:

| File | Purpose | Why this skill is wrong for it |
|---|---|---|
| `~/.claude/CLAUDE.md` | User-wide preferences across all projects (code style, testing conventions, git workflow, etc.) | Different content rules — code-style guidance, language-specific defaults, and tooling preferences belong here. The three-section template doesn't fit. |
| `./.claude.local.md` | Personal overrides for this project, gitignored | Personal scratch — no enforced structure expected. |
| `./packages/*/CLAUDE.md`, nested `CLAUDE.md` | Module- or feature-level context inside a monorepo | Scoped to a sub-area, often heavily implementation-flavored. The portable, code-free style of this skill doesn't fit. |

If the user is clearly asking about one of those, stop and say so — don't silently rewrite the wrong file.

## Output structure

Always exactly three top-level sections, in this order:

1. `## What this is`
2. `## Design decisions`
3. `## Project commands`

Nothing else at the top level. No "Code style", "Testing guidelines", "Git workflow", "Contribution rules", "Architecture overview", "Folder layout". Those either belong in the user's global `~/.claude/CLAUDE.md` (cross-project preferences) or in the codebase itself (architecture is readable from the code).

If the user dictates a rule that belongs in one of those buckets, save the rule for them but flag it: *"this looks like a global preference — you may want it in `~/.claude/CLAUDE.md`, not the project file, otherwise it'll only apply here."*

## Line length

Hard-wrap every line in `CLAUDE.md` at **79 characters**. This applies to
prose, list items, and table-free content alike. Wrap long sentences across
multiple lines rather than letting a paragraph run as one long line.

Exception: never break inside a fenced code block, a Markdown table row, or a
single unbreakable token (a long URL or backticked path). Those stay on one
line even if they exceed 79.

When refactoring or augmenting an existing file, re-wrap any lines you touch
to satisfy this limit.

## Workflow

The skill operates in one of three modes. Decide which one applies before doing anything else.

| Mode | Trigger | Action |
|---|---|---|
| **A. Create** | `./CLAUDE.md` does not exist | Build the file from scratch (interview + derive). |
| **B. Refactor** | File exists; user asks to "rewrite", "restructure", "clean up", "fix the structure of" | Restructure under the template, preserving meaning. |
| **C. Augment from session** | File exists; user asks to "add", "update", "save this to", "record", "fold in", "записать", "обновить" — referring to something discussed in the current conversation | Read the existing file + extract relevant decisions from the live conversation; merge. |

If it's ambiguous, ask once: *"do you want me to restructure the existing file, or fold in what we just discussed?"*

### Mode A — Create

1. List the repo root. Inspect obvious tooling files: `Makefile`, `Taskfile.yml`, `justfile`, `package.json` scripts, `pyproject.toml`, `go.mod`, `Cargo.toml`, lockfiles.
2. **Derive without asking**:
   - *Project commands* from the build tool's targets/scripts. If none exists, fall back to language-idiomatic commands (`go test ./...`, `pytest`, `pnpm test`, ...).
   - *Tech-stack hint for the intro* from manifests/imports — one short cue ("terminal client", "REST API", "CLI tool"), not the whole stack.
3. **Interview in one batched message** (not one question at a time):
   1. *"In one or two sentences: what does this project do, and for whom?"*
   2. *"What design rules does this project enforce that aren't obvious from reading the code? Things like 'X always goes through Y', 'never do Z because of W'. Bullet points are fine — I'll structure them."*
   3. *Project commands sanity* — only if you couldn't derive obvious targets.
   If the user says "nothing comes to mind" for design decisions, leave a placeholder (`<!-- TODO: add design decisions as they emerge -->`) instead of fabricating.
4. Write the file using the templates below. Show the result and ask whether any section needs tweaking.

### Mode B — Refactor

1. Read the existing `CLAUDE.md`.
2. **Preserve the user's meaning, restructure the form**: lift concepts buried under implementation chatter, drop file paths and function names, regroup rules under shared parents where they share a motivation, enforce the standard / why / deviation shape.
3. Run the same repo inspection as Mode A to refresh *Project commands* — old commands often go stale.
4. If the file contains content that doesn't fit any of the three sections (code style, testing rules, contribution guidelines), surface them to the user: *"these look like global preferences — want me to drop them here, or move to `~/.claude/CLAUDE.md`?"* Don't silently delete.
5. Show a diff (or the new file) and confirm before overwriting.

### Mode C — Augment from session

This is the common case where a design decision was discussed in chat and the user wants it captured without re-explaining.

1. Read the existing `CLAUDE.md`.
2. **Scan the current conversation** for content worth saving. Filter aggressively — only keep things that:
   - Are *durable* design rules (not one-off tactical decisions or debugging steps).
   - Concern *contracts*, *conventions*, *naming*, *invariants*, *forbidden patterns*, *deviations from a standard* — i.e. things that fit the design-decisions section.
   - OR concern *commands the user runs* that are missing from the file.

   Skip: code that was written, bugs that were fixed, ephemeral context (PR numbers, ticket IDs), implementation details, things already obvious from reading the code.

3. For each candidate, decide whether it's:
   - **An addition** — new concept, doesn't exist in the file → draft a new design subsection.
   - **An update** — replaces or amends an existing rule → propose an in-place edit.
   - **A new command** → add to *Project commands*.

4. Present the candidates to the user **before writing**, in a numbered list with the proposed CLAUDE.md text inline. Example:
   > Found 2 things worth saving from this session:
   > 1. *(addition)* New subsection under Design decisions: **Reference UX: k9s** — "The app's UX is largely modeled on k9s..."
   > 2. *(update)* Existing "Handing the terminal off" rule changed: editor handoff is now `e`, not `ctrl+o`. Proposed edit shown below.
   >
   > Apply all? Skip any?

5. After the user approves, apply the changes. Re-render the file in full only if structure changed; otherwise edit in place.

When in doubt about whether a session item belongs in CLAUDE.md, prefer to ask the user rather than smuggle it in — and prefer to ask up front in the "found N candidates" message rather than after writing.

## Section templates

### What this is

Two to four sentences. What the project does, for whom, and *just enough* technical positioning that a reader knows what kind of thing they're looking at.

```
## What this is

<Project name> — <one-sentence positioning, including the "what kind of thing it is": CLI, web app, library, service, ...>. <Optional: a sentence on the primary user/use-case>. <Optional: one sentence on a defining stylistic or design lineage>.
```

**Good:**
> kafka-tui is a terminal client for Apache Kafka in the spirit of k9s. It lets developers browse topics, produce messages, and inspect consumer groups without leaving the shell.

**Bad (too detailed — this is README material):**
> kafka-tui is a TUI application written in Go using the bubbletea framework. It connects to Kafka clusters via the franz-go client library and provides screens for topic listing, message browsing with seek capabilities, consumer group offset reset, and message production with history persistence.

### Design decisions

Compact, portable concepts. One subsection per concept. The whole section is the heart of the document — it's the part Claude can't infer from the code.

Each subsection follows the **standard / why / deviations** shape:

```
### <Concept name>

<Standard: 1-3 sentences stating the rule.>

Why: <1-3 sentences explaining the motivation — what would go wrong without this rule, or what past incident drove it>.

Deviation: <optional, only if there's a concrete carve-out>.
```

**Style rules — these are load-bearing:**

- **Concepts, not implementations.** Refer to *roles* ("text inputs", "background workers", "modal forms", "the request pipeline"), never file paths, function names, or types. The concept must survive a future refactor that renames everything.
- **Why, not how.** Explain what would break without the rule, or what the user once burned themselves on. Skip mechanics.
- **Portable.** A rule worth stating should be readable as-is by someone who has never opened the codebase. Anything that requires "see X for context" doesn't belong here.
- **No code blocks.** Code is in the codebase. CLAUDE.md describes the contract.
- **Group related rules under a parent rule when they share a motivation.** E.g. several specific rules might all be instances of "single source of behavior for X" — write the parent once, reference it in the children.

**Good:**
> ### Reserved global shortcuts
>
> A fixed set of keys is owned by the host dispatcher and not rebindable by screens: `ctrl+c`, `:`, `/`, `?`, `ctrl+r`.
>
> Why: these keys must work the same on every screen. Without one dispatcher, screens drift apart and the user learns screen-specific behavior — which defeats the point of "global" keys.
>
> Deviation: when an overlay (e.g. a modal form) is active, a global is skipped if its action does not apply in that context — the key falls through to the overlay instead of firing a no-op global.

**Bad (file paths, mechanics, no "why"):**
> ### Global shortcuts
>
> The `key_dispatch.go:handleGlobal()` function processes `ctrl+c`, `/`, `?`, `ctrl+r` before passing the event to the active screen via `Screen.Update()`. See `routing.go` for the full chain.

### Project commands

A flat list. One command per line, then `-`, then a single short clause of intent.

```
## Project commands

- `make build` - build the binary into `./dist/`
- `make lint` - run formatters and linters; auto-fixes what it can
- `make test` - run the test suite
- `make race` - run tests with the race detector
- `make deps` - refresh vendored deps from the manifest
```

**Style:**

- Backtick the command. Use `-` (hyphen) as separator. No trailing period needed.
- Order roughly: build → lint → test → run → deps → other.
- One verb per line. If a command does several things, describe the *outcome*, not the steps.
- If there's no Makefile / package script, list the raw commands (`go test ./...`, `uv sync`, `pnpm test`, `cargo build --release`).

## Reference

A complete, real-world example following this style lives alongside this skill at `example-CLAUDE.md`. When in doubt about tone, structure, or how compact a design subsection should feel, read that file. It is the canonical reference — match its register.
