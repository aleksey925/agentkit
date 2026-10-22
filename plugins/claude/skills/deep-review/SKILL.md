---
name: deep-review
description: "Heavy multi-agent code review with a self-fixing loop. Use when the user says 'deep review', 'deep', or wants an exhaustive review of changes by parallel specialist agents plus codex, fixing confirmed issues until clean."
argument-hint: "[staged|unstaged|uncommitted|branch|auto] [base] [plan-file] [no-codex] [context...]"
allowed-tools: Read, Glob, Grep, Bash, Agent
---

# deep-review

Exhaustive code review of the current changes. Several specialist reviewers run
in parallel, an external codex pass adds an independent view, and a fixer
subagent verifies and fixes confirmed issues. The cycle repeats until a
critical re-check comes back clean. The fixer does NOT commit - all fixes are
left in the working tree for the user to review and commit.

## Arguments

`$ARGUMENTS` may contain, in any order:

- a **diff mode** (default `auto`):
  - `staged` - only `git add`-ed changes (`git diff --cached`)
  - `unstaged` - only not-yet-added changes (`git diff`)
  - `uncommitted` - everything not committed = staged + unstaged (`git diff HEAD`)
  - `branch` - the whole branch's work vs base, including uncommitted
  - `auto` - staged if any, else unstaged, else branch
- a **base** branch (only meaningful with `branch` mode; defaults to the
  detected default branch)
- a **plan file** path (optional `.md` file describing the intent of the
  changes)
- the keyword **`no-codex`** to skip the external codex phase for this run
- any remaining **free-form text** is taken as review context (what the change
  is about / what to focus on) - no key needed; see Step 1

When no plan file is passed explicitly, the skill looks in the plans dir
(default `docs/plans`, overridable via `DEEP_REVIEW_PLANS_DIR`) and its
`complete/` subdir, where finished plans are archived, and uses a discovered
plan only when one clearly belongs to the changes under review - never just
because it is the only file there (it may be left over from another branch).
Otherwise it runs without a plan, which is normal. When in doubt about the
mode, use `auto`.

The codex phase can also be turned off persistently via the
`CODEX_ENABLED` environment variable (set it to `0`/`false`/`off`/`no`).
Otherwise it runs whenever the `codex` binary is installed.

## File resolution

All bundled files live in the skill folder `$HOME/.claude/skills/deep-review`.
Resolve `$HOME` to its absolute path and substitute it into every subagent
prompt before spawning.

- playbook: `$HOME/.claude/skills/deep-review/references/review.md`
- agents: `$HOME/.claude/skills/deep-review/references/agents/*.txt`
- prompts: `$HOME/.claude/skills/deep-review/references/prompts/*.md`
- scripts: `$HOME/.claude/skills/deep-review/scripts/*.sh`

## Process

### Step 1. Resolve the plan and review context

Parse `$ARGUMENTS` into `mode`, `base`, `plan-file`, and the `no-codex`
keyword (any may be absent). These are a small fixed vocabulary: the diff
modes (`staged`/`unstaged`/`uncommitted`/`branch`/`auto`), a base branch name,
a path to an existing `.md` plan, and `no-codex`. Treat ANY remaining
unrecognized text as free-form review context (`CONTEXT_ARG`) - there is no
`context=` key, the user just types what they were doing. A bare mode keyword
counts as a mode only as a standalone leading token; once prose begins, the
rest is context. Treat a token as the plan only if that `.md` file exists on
disk - otherwise it is context too.

If a plan file was passed explicitly, use it. Otherwise scan the plans dir:

```bash
bash $HOME/.claude/skills/deep-review/scripts/list-plans.sh
```

Decide by relevance to the current changes, never by how many files are listed.
Adopt a candidate only when it clearly belongs to these changes - the working
session did work toward it, or its content matches the diff. In every other
case - no candidates, no clear link, or several plausible ones - run without a
plan. Do NOT auto-adopt a plan just because it is the only file in the dir,
and do NOT ask the user to pick one.

Carry the chosen `plan-file` (possibly empty) into the steps below.

### Step 2. Resolve the diff

Resolve the diff command:

```bash
bash $HOME/.claude/skills/deep-review/scripts/resolve-diff.sh <mode> <base>
```

Store the printed command as `DIFF_COMMAND` and use it unchanged for the whole
run (it diffs against the working tree, so it picks up the fixer's changes on
re-review). Run `DIFF_COMMAND` once now. If it prints nothing, there is nothing
to review - tell the user and stop.

### Step 3. Resolve the progress file path

```bash
PROGRESS_FILE_PATH=$(bash $HOME/.claude/skills/deep-review/scripts/progress-path.sh <plan-file>)
```

(omit `<plan-file>` when no plan was given). With a plan the file sits next to
the plan itself (`<plan-dir>/<plan-name>.progress.md`), so an archived plan in
`complete/` keeps its sidecar alongside it; without one it is
`<plans-dir>/review-<runid>.progress.md`, unique per run so concurrent
plan-less reviews never share a file. Review artifacts live next to their plan,
or in the plans dir when there is none. Resolve this ONCE now and reuse the
same path for the whole run; the file itself is created in Step 4.5, after the
context is built.

The progress file is the shared memory between iterations: every fixer pass
appends what it confirmed, fixed, and dismissed, and every later reviewer
reads it.

### Step 4. Build PLAN_CONTEXT

Assemble `PLAN_CONTEXT` ONCE for the whole run from up to three sources, in
this order of weight. Ground it in the diff: describe only what explains THESE
changes, and drop session details unrelated to the diff.

- **plan file** (authoritative): include "The plan file at <path> describes the
  goal and requirements - use it to understand what the code is supposed to
  do."
- **provided context** (`CONTEXT_ARG` from Step 1, the user's own words): the
  strongest free-text signal. Include as "Review focus (provided by user):
  <text>". On conflict with the session, the provided text wins.
- **session synthesis** (inferred): if the current working session did work
  that explains the diff, summarize the intent in 1-3 sentences and include it
  as "Inferred intent (from the working session, may be incomplete): <text>".
  Mark it inferred so reviewers treat it as a hint, not a spec - they must not
  flag the code for deviating from a guessed goal.

If none of the three apply, `PLAN_CONTEXT` = "" (empty string) - a pure diff
review. This one string is substituted into every reviewer and the codex
prompt, so the same context reaches internal agents and the external reviewer
alike.

Also derive `CONTEXT_HEADER` for the progress file: the SAME provided and
inferred intent text that went into `PLAN_CONTEXT` (without the plan pointer),
joined onto a single line. When a session synthesis was used, its inferred
intent MUST be part of `CONTEXT_HEADER` too - the progress file is the only
durable record of it, so dropping it loses the synthesis entirely. The config
block's `context:` line names the sources; `CONTEXT_HEADER` carries their actual
text. Empty only when nothing but a plan, or nothing at all, was given.

For the fixer, `PLAN_CONTEXT` is "Plan file: <path> (read it to find validation
commands and intent)", or the provided/inferred context text when there is no
plan, or "" when absent.

### Step 4.5. Create the progress file and print the run configuration

Create the progress file now that the context is known:

```bash
bash $HOME/.claude/skills/deep-review/scripts/init-progress.sh "$PROGRESS_FILE_PATH" "<plan-file>" "<CONTEXT_HEADER>"
```

`plan-file` and `CONTEXT_HEADER` are positional - when either is absent pass an
empty string `""` (do NOT drop the argument, or the next one shifts into its
place). An empty plan is recorded as `(none)`; an empty context omits the
`Context:` line. This records the plan path or the synthesized context in the
header so codex and later phases can read it.

Then print a single standardized configuration block and proceed without
asking for confirmation:

```
deep review - run configuration
mode:     <mode> (<auto-selected | as given>)
diff:     <DIFF_COMMAND>
plan:     <plan path | none>
context:  <one of the states below>
progress: <PROGRESS_FILE_PATH>
codex:    <enabled | disabled>
```

`codex` is `disabled` if the user passed `no-codex` or `codex-enabled.sh`
prints `no`, otherwise `enabled` (running that script here is fine - Phase C
checks it again). Add a `base:` line only in `branch` mode. The `context:`
line states exactly one source state:

- `plan <path>` (append `+ provided ("<short>")` if context was also supplied)
- `provided ("<short>") + session synthesis`
- `session synthesis (inferred, no input provided)`
- `none - pure diff review`

### Step 5. Review loop

Read `references/review.md` and follow it as the fanout playbook. It is a
playbook for THIS orchestrator session - the parallel Agent calls must be
emitted from here, never delegated to a subagent (subagents cannot spawn
agents). Substitute `DIFF_COMMAND`, `PROGRESS_FILE_PATH`, and `PLAN_CONTEXT`
into every assembled prompt.

Run the phases in this order:

**Phase A - comprehensive** (`REVIEW_PHASE = comprehensive`): emit the 5 agents
together, collect the strict report. If it has any findings, spawn the fixer
(see Step 6) with that report. One pass.

**Phase B - smells** (`REVIEW_PHASE = smells`): run the single smells agent,
collect the report. If it has findings, spawn the fixer. One pass.

**Phase C - codex** (external): first decide whether to run it. Skip the whole
phase if the user passed `no-codex`, otherwise run:

```bash
bash $HOME/.claude/skills/deep-review/scripts/codex-enabled.sh
```

If it prints `no` (disabled via `CODEX_ENABLED`, or `codex` not installed),
skip the phase. If it prints `yes`, loop up to **5** iterations:

1. Read `references/prompts/codex-review.md` and substitute placeholders. Write
   the result with the Write tool to
   `/tmp/deep-review-<name>.codex-prompt.txt`, where `<name>` is the progress
   file name without `.progress.md` (overwrite it each iteration). Do NOT
   paste the prompt into the command or write it with `echo` or an unquoted
   heredoc: it contains backticks, and the shell would run them as commands,
   so codex would get the prompt without its output format rule.
2. Run
   `bash $HOME/.claude/skills/deep-review/scripts/run-codex.sh "$(cat <prompt-file>)"`
   with `run_in_background: true`. Wait for the notification - do NOT poll or
   sleep.
3. Check the result. The tool result merges stdout and stderr, so judge the
   combined text. It is a codex failure, not a clean review, when the exit
   code is non-zero, the output is empty, or the output has neither
   `NO ISSUES FOUND` nor any `CRITICAL`/`MAJOR`/`MINOR` tag. On failure report
   `Codex review: failed - <exit code or reason>, <first output line>` and go
   to Phase D.
4. Scan the output for `CRITICAL` or `MAJOR` (case-insensitive, whole word).
   Findings win over the marker: if codex printed `NO ISSUES FOUND` but also a
   CRITICAL or MAJOR finding, treat it as findings. The phase is clean only
   when the marker is present and no CRITICAL or MAJOR was found - go to
   Phase D.
5. Otherwise spawn the fixer with the full codex output. If there was no
   CRITICAL or MAJOR (minor findings only), stop the loop after the fixer;
   otherwise go back to item 1.

**Phase D - critical re-check** (`REVIEW_PHASE = critical`): emit the 2 agents
together. If the report is `Critical re-check: clean ...`, the review is DONE.
Otherwise spawn the fixer and repeat Phase D, up to **3** iterations.

If a phase loop hits its iteration cap with findings still open, stop and
report the remaining findings to the user honestly rather than looping forever.

### Step 6. Spawn the fixer

After any phase that returned findings, read `references/prompts/fixer.md`,
substitute `PLAN_CONTEXT`, `PROGRESS_FILE_PATH`, `FINDINGS_LIST` (the strict
report from the phase), and the resolved `$HOME`. Spawn ONE
`general-purpose` subagent with that prompt and `mode: "bypassPermissions"`
(the fixer edits files and runs build/test commands - bypass keeps the loop
autonomous). The fixer verifies each finding, fixes confirmed ones, validates,
logs to the progress file, and leaves everything uncommitted. Read its
`FIXES:` report.

Only ONE fixer runs at a time - never in parallel with reviewers (they would
race on the working tree).

### Step 7. Final summary

When the loop finishes, give the user a short summary:

- which phases ran and how many fixer passes happened,
- total confirmed fixes vs false positives (from the fixer reports),
- any findings left open if a cap was hit, and a codex failure if there was
  one,
- a section **"Decisions made by the fixer"**: collect the entries with
  `grep -E '^(\[[^]]*\] )?\[(decision|deviation)\]' "$PROGRESS_FILE_PATH"` and
  list one bullet per entry with its reason. If there are none, say so. The
  pattern anchors at the line start, so markers quoted inside findings are
  skipped,
- a reminder that fixes are uncommitted in the working tree, plus the path to
  the progress file.
