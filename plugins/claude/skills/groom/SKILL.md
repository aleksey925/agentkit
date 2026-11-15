---
name: groom
description: "Groom a raw task into a clean design-doc plan: a subagent explores the project and drafts a solution, cross-reviewed by codex. Refine it interactively via your file annotations, or let agents groom autonomously to convergence."
argument-hint: "[auto] [ask] [no-codex] [preset=default|hard] [model=<slug>] [effort=low|medium|high|xhigh|max|ultra] <task | plan.md>"
allowed-tools: Read, Glob, Grep, Bash, Agent
---

# groom

Turn a raw idea into a clean, detailed design doc (a plan) before any code
is written. A subagent explores the project and drafts a solution; a critic
(codex, or an internal agent when codex is absent) cross-reviews it. The
result is a plan ready for implementation.

Two modes:

- **interactive** (default) - one pass per invocation; you refine the doc
  by editing the file and leaving markers, then re-run.
- **auto** (`auto` flag) - the orchestrator drives an autonomous
  critic/refiner loop to convergence, with no annotation between rounds.
  Add `ask` to answer a round of clarifying questions up front, then let it
  run on its own.

You are ONLY the orchestrator. You never write the design yourself and
never change code. Subagents explore and write the design doc; the critic
reviews it; you coordinate, run the critic, manage the file, and talk to the
user. groom designs only - it does NOT implement and does NOT commit.

## File resolution

`SKILL_DIR` is the absolute path of the folder that contains this SKILL.md.

## Modes and arguments

Parse `$ARGUMENTS`. These bare words anywhere in the args are flags - pull
them out first, then read what remains:

- `auto` - run the autonomous convergence loop (Auto run) instead of the
  interactive single pass.
- `ask` - only meaningful with `auto`: run the clarification gate before the
  loop. Ignored without `auto`.
- `no-codex` - skip the codex cross-review this round (the critic falls back
  to the internal agent in auto mode).
- `preset=<name>`, `model=<slug>`, `effort=<level>` - codex model choice,
  passed to `run-codex.sh` as `--preset`, `--model`, `--effort` on every
  codex run.

What remains after removing the flags:

- a path to an existing `.md` file -> CONTINUE mode: refine that design doc.
- other free text -> FIRST RUN: that text is the task.
- empty -> FIRST RUN: the task is what was just discussed in this
  conversation (synthesize it).

Codex runs by default on every round, including the first, whenever the
`codex` binary is installed. `no-codex` turns it off for this round; the
`CODEX_ENABLED` environment variable turns it off persistently (set it to
`0`/`false`/`off`/`no`). Whether codex runs is decided by
`SKILL_DIR/scripts/codex-enabled.sh`.

## Annotation markers (how you disagree)

The design doc is the single source of truth. You edit it in your own
editor and leave markers, each on its own line:

- `?? <question>` - a question. The refiner answers it (reported back in
  chat) and changes the design only if the answer requires it.
- `!! <objection or directive>` - revise the design to address it.
- `== ` or `LOCKED` at the start of a section - decided. Not changed, not
  reopened (by the refiner or by codex).
- plain prose you changed (no marker) - authoritative. Kept as is, never
  reverted.

The refiner removes every `??`/`!!` marker after handling it.

## Output

A design doc at `docs/plans/<date>-<topic>.md`. Compute the path with
`date +%Y%m%d` and a short hyphenated slug from the task. Create
`docs/plans/` if missing.

## Process

Pick the flow by mode: without `auto`, run the interactive First / Continue
run below. With `auto`, run the Auto run instead. The Codex round and the
subagent prompts are shared by both.

### First run (interactive)

1. Resolve the task and the `no-codex` flag. Compute the plan file path.
2. Spawn ONE explorer subagent (Agent, `subagent_type: "general-purpose"`)
   with the Explorer prompt, `<TASK>` and `<PLAN_FILE>` substituted. It
   studies the project and writes the first design doc. Wait for it.
3. If the Codex round is enabled, run it (see Codex round), then spawn a
   refiner to fold the critique in. If codex is disabled, the explorer's
   draft is the result - do NOT spawn a refiner (there is no critique and no
   markers yet on a first run).
4. Tell the user: the chosen approach (subagent's short summary), the file
   path, and how to iterate (edit the file, add `??`/`!!`/`==` markers,
   re-run `/groom <file>`, add `no-codex` to skip the codex pass).

### Continue run (interactive)

1. Read the plan file; check it has `??`/`!!` markers or visible edits.
2. Run the Codex round first (unless it is disabled) and keep its critique
   for the refiner.
3. Spawn ONE refiner subagent with the Refiner prompt (`<PLAN_FILE>`,
   and `<CODEX_BLOCK>` filled with the critique or left empty). It folds in
   your edits, resolves markers, optionally applies codex points, and
   rewrites the file. Wait for it.
4. Relay to the user: a short summary of changes, the answers to each `??`
   question, and the file path. Remind them: when the doc has no markers
   left and they are happy, the plan is ready to implement.

### Auto run (when `auto` is set)

The orchestrator drives the whole loop; the user does not annotate the file
between rounds (the only human step is the optional clarification gate).

1. Resolve the task or plan file, the `ask` flag, and codex enablement.
   Compute or resolve the plan file path.
2. Get the first draft:
   - task (first run) -> spawn the explorer subagent, wait for it. With `ask`
     set, include `<ASK_BLOCK>` so it returns blocking questions alongside the
     draft.
   - existing `.md` (continue) -> use that file as the draft, no explorer.
     With `ask` set, spawn the explorer with `<ASK_BLOCK>` on the existing
     file to collect blocking questions without redrafting.
3. If `ask` is set, run the Clarification gate now, before the loop.
4. Convergence loop, up to **4** rounds:
   1. Pick the critic: if the Codex round is enabled, codex is the critic;
      otherwise spawn the internal critic subagent (Internal critic prompt).
   2. The critic reviews `<PLAN_FILE>` against the real code and returns a
      concise critique ending in a verdict line. If the verdict is
      `DESIGN READY` (no significant problems left), stop the loop.
   3. Spawn the refiner with the critique in `<CODEX_BLOCK>`, fold it in, and
      rewrite the file. Without `ask`, also append to the refiner prompt:
      record each unknown you resolve yourself as an `Assumption:` line under
      `## Risks / open questions`, so the decisions taken stay visible. Wait
      for it, then start the next round.
5. Report to the user: the final approach, how many rounds ran and why it
   stopped (converged or hit the cap), the plan path, and any assumptions
   made.

### Clarification gate (when `ask` is set)

Runs after the first draft, before the convergence loop:

1. Take the BLOCKING questions the explorer returned in step 2 - genuine
   unknowns it could not resolve from the code that would materially change
   the design.
2. If the list is empty (`BLOCKING QUESTIONS: none`), skip the gate.
3. Otherwise present the questions to the user and wait for answers. Spawn the
   refiner to fold the answers into the plan as `== `/LOCKED decisions
   (authoritative, never reopened later).
4. To check whether the answers opened new blocking questions, re-spawn the
   explorer with `<ASK_BLOCK>` on the updated file and repeat from step 2.
   Stop when none remain or the user says to proceed, then run the
   convergence loop.

### Codex round (default; skipped when disabled)

1. Decide whether to run it. Skip the whole round if the user passed
   `no-codex`, otherwise:

   ```bash
   bash "SKILL_DIR/scripts/codex-enabled.sh"
   ```

   If it prints `no` (disabled via `CODEX_ENABLED`, or `codex` not installed),
   skip the round and run the refiner without a codex block. If it prints
   `yes`, run codex.
2. Run codex through the bundled script, in the background (do NOT poll; you
   are notified when it finishes). Substitute `PLAN_FILE` into the Codex
   prompt first:

   ```bash
   bash "SKILL_DIR/scripts/run-codex.sh" \
     [--preset <name>] [--model <slug>] [--effort <level>] \
     "<Codex prompt with PLAN_FILE substituted>"
   ```

   Launch it with `run_in_background: true`. The script handles every codex
   nuance: it skips cleanly if `codex` is not installed, probes whether the
   bubblewrap sandbox can start and falls back to a bypass when userns is
   blocked (e.g. inside a container), and redirects stdin from `/dev/null` so
   a background launch never hangs on `codex exec` reading stdin. The preset
   (from `--preset`, then `CODEX_PRESET`, then `default`) picks the model:
   `default` is the newest `sol` model with effort `medium`, `hard` is the
   newest `astra` model with effort `xhigh`. `--model` and `--effort` override
   it. Overrides: `CODEX_SANDBOX` forces a sandbox mode, `CODEX_NO_OVERRIDES=1`
   drops the `-c` flags for proxies that reject them, and with them the
   preset, `--model` and `--effort`.

3. Keep codex's output as the critique passed to the refiner.

## Orchestrator contract

- You are ONLY the orchestrator. Never write the design doc yourself, never
  edit code. Explorer and refiner subagents do that.
- Spawn one subagent at a time and wait. Stages are sequential.
- The critic is read-only - codex or the internal critic reviews the design,
  it never edits. In auto mode exactly one critic runs per round: codex when
  enabled, the internal critic otherwise.
- The auto loop is bounded - stop at `DESIGN READY` or after 4 rounds, then
  report honestly rather than looping forever.
- Keep your context thin: the critic reads the file itself (you pass the path,
  not the design text); subagents return short summaries.
- groom never implements and never commits. The plan file is the handoff.

## Explorer prompt

```
You are grooming a development task into a clean design - NOT implementing
it. Do not change any code.

TASK:
<TASK>

Steps:
1. Study the parts of this repository relevant to the task (code, tests,
   configs). Understand how things are done here and the real constraints.
2. Design a clean solution. Consider edge cases, failure modes, and simpler
   alternatives - prefer the cleanest approach that fits the existing code.
3. Write a detailed design doc to <PLAN_FILE> with this structure:
   - # <title>
   - ## Problem - what we solve and why
   - ## Context - relevant files and constraints, with file:line refs
   - ## Approach - the proposed solution, step by step
   - ## Key decisions - important choices and the alternatives you
     rejected, with reasons
   - ## Risks / open questions - what could go wrong or is unresolved
   - ## Implementation outline - concrete tasks, in order, ready for an
     implementer
   Follow the repo conventions and the user's ~/.claude/CLAUDE.md.

Return a short summary: the chosen approach in 3-5 lines, plus the file
path. Do not change code.
<ASK_BLOCK>
```

`<ASK_BLOCK>`, inserted only for the clarification gate in `auto ask` mode:

```
Also return, under a separate "BLOCKING QUESTIONS" heading, the genuine
unknowns you could NOT resolve from the code and that would materially change
the design. List only real blockers - not things you can reasonably decide
yourself. If there are none, write "BLOCKING QUESTIONS: none".
```

## Refiner prompt

```
You are refining a design doc at <PLAN_FILE>. This doc IS the source of
truth. Do NOT change any code - only the design doc.

Rules:
1. Plain prose the user changed is AUTHORITATIVE - keep it, build around
   it, never revert it.
2. Sections marked `== ` or `LOCKED` are decided - do not change them and
   do not reopen those decisions.
3. For every `!! ...` marker (objection / directive): revise the design to
   address it. Remove the marker.
4. For every `?? ...` marker (question): answer it. If the answer changes
   the design, update the doc; otherwise leave the design as is. Remove the
   marker and keep the answer to report back.
<CODEX_BLOCK>
Then rewrite <PLAN_FILE> with all `??`/`!!` markers removed and the design
updated. Keep the same section structure.

Return:
- a short summary of what changed,
- the answer to each `??` question (so the orchestrator can relay them).
Do not change code.
```

`<CODEX_BLOCK>`, inserted only when a critique was produced this turn (codex,
or the internal critic in auto mode):

```
5. Also fold in this design review (from codex or the internal critic). Apply
   the valid points; for any point you reject, note why in one line. Respect
   `==` / LOCKED sections even if the review argues against them.

DESIGN REVIEW:
<CODEX_CRITIQUE>
```

## Codex prompt

```
You are a critical co-designer reviewing a proposed software design. You
have read-only access to this project - read the real code to ground your
review.

Read the proposed design at <PLAN_FILE>, then read the source files it
references and check the design against what the code actually does.

Make the design cleaner and catch problems before implementation:
- find design flaws, fragile or wrong decisions, missed cases, hidden
  complexity,
- propose simpler / cleaner alternatives where they exist,
- flag anything in the approach that fights the existing codebase.

Be a critic AND a co-author: not just "this is wrong", but "here is a
cleaner way". Ground every point in real code (file:line). Skip style
nitpicks.

Output a concise list. For each point: the concern, why it matters, and a
concrete suggestion. End with a verdict line on its own: `DESIGN READY` if no
significant problems remain, otherwise `NEEDS WORK`.
```

## Internal critic prompt

Used as the critic in auto mode when codex is disabled or not installed. Same
job as codex, run as a `general-purpose` subagent.

```
You are a critical co-designer reviewing a proposed software design - NOT
implementing it. Do not change any code or the design doc.

Read the proposed design at <PLAN_FILE>, then read the source files it
references and check the design against what the code actually does.

Catch problems before implementation and make the design cleaner:
- find design flaws, fragile or wrong decisions, missed cases, hidden
  complexity,
- propose simpler / cleaner alternatives where they exist,
- flag anything in the approach that fights the existing codebase.

Respect `== ` / LOCKED sections - do not reopen those decisions. Ground every
point in real code (file:line). Skip style nitpicks.

Output a concise list. For each point: the concern, why it matters, and a
concrete suggestion. End with a verdict line on its own: `DESIGN READY` if no
significant problems remain, otherwise `NEEDS WORK`.
```
