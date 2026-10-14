---
name: flow
description: "Orchestrate a dev workflow: implement a task in a subagent, then loop code-review + fix until clean. Or run just the review-fix loop on current changes."
argument-hint: "[review | plan.md | task] [max_review=N]"
allowed-tools: Read, Glob, Bash, Agent, AskUserQuestion
---

# flow

Orchestrate a development workflow as an ordered list of stages.

You are ONLY the orchestrator. You never read source code, never edit or
fix code, never run the review yourself. Every bit of real work happens
inside a spawned subagent. You only: spawn one agent at a time, read its
short structured result, and decide what to do next.

## Modes and arguments

Resolve the mode from `$ARGUMENTS`:

1. Starts with `review` → template `review` (review loop only, no task).
2. A path to an existing `.md` file → template `implement+review`, the
   task is that plan file. Remember this path as `<PLAN_FILE>` - the
   archive step at the end uses it.
3. Any other free text → template `implement+review`, the text is the
   task description.
4. Empty → template `implement+review`, the task is what was just
   discussed in this conversation (you synthesize it, see Stage: task).

Optional flag anywhere in the args: `max_review=N` caps how many rounds
that still find issues are allowed before giving up (default 3). Clean
confirmation rounds do not count against it.

## Templates

- `implement+review` (default): stages `[task, review-loop]`
- `review`: stages `[review-loop]`

## Stage: task

Goal: get the task implemented in the working tree by a fresh subagent.

1. Build a clear, self-contained task description (`<TASK>`):
   - plan file → read it and use its contents,
   - conversation → write the discussed task as a short, standalone
     brief (the subagent has a fresh context and knows nothing about our
     chat).
2. Echo the resolved task to the user in one short block before spawning,
   so a misunderstanding is caught early.
3. Spawn exactly ONE subagent (Agent tool, `subagent_type:
   "general-purpose"`) with the Implementer prompt below, `<TASK>`
   substituted. Wait for it to return.
4. Read its report only. If it reports it could not finish, tell the user
   what blocked it and stop. Do NOT investigate or fix it yourself.

Never parallelize this stage. One implementer, then move on.

## Stage: review-loop

Track two counters: `clean_streak` (consecutive CLEAN rounds, start 0) and
`fix_rounds` (rounds that found issues, start 0). The loop stops only after
TWO clean rounds in a row - the second is an extra confirmation pass to
finally catch anything left.

Repeat:

1. Spawn ONE review subagent (Agent tool, `subagent_type:
   "general-purpose"`) with the Reviewer prompt below.
2. Read only its returned verdict (the last line). Do NOT read the code.
   - `VERDICT: DIRTY (<n> issues)` → set `clean_streak` to 0, add 1 to
     `fix_rounds`, report the round's found/fixed list to the user (one
     line each). If `fix_rounds` has reached `max_review`, stop and report
     "max review rounds (<N>) reached, still has issues - stopping".
     Otherwise loop again with a fresh subagent.
   - `VERDICT: CLEAN` → add 1 to `clean_streak`.
     - `clean_streak` == 1 → report "review clean - running one more
       confirmation pass" and loop again with a fresh subagent.
     - `clean_streak` == 2 → report "review clean, confirmed by a second
       pass" and stop. The workflow is done.

`max_review` caps only the rounds that still find issues (`fix_rounds`).
Clean confirmation rounds are always allowed and are never blocked by the
cap, so the extra confirmation pass always runs.

Each round is a fresh subagent: the first CLEAN verifies the previous
round's fixes, the second CLEAN is the final catch-all pass.

## After the workflow

- Archive the finished plan when the task came from a `<PLAN_FILE>` (mode 2
  - not `review` mode and not a free-text or conversation task). Reaching
  this section means the implementation finished: a blocked task stage stops
  the workflow earlier, so it never gets here. Archive regardless of the
  review outcome - even if the review loop found issues, stopped at the
  `max_review` cap, or never ran. Move the plan and its `.progress.md`
  sidecar (if one exists) into a `complete/` folder next to the plan:

  ```bash
  plan="<PLAN_FILE>"
  dest="$(dirname "$plan")/complete"
  mkdir -p "$dest"
  git mv "$plan" "$dest"/ 2>/dev/null || mv "$plan" "$dest"/
  progress="${plan%.md}.progress.md"
  [ -f "$progress" ] && { git mv "$progress" "$dest"/ 2>/dev/null || mv "$progress" "$dest"/; }
  ```

  For the standard `docs/plans/<name>.md` layout this lands the plan in
  `docs/plans/complete/`. `git mv` keeps the move staged when the plans dir
  is tracked; the `mv` fallback handles the common case where `docs/` is
  git-ignored.
- Report a short summary: task done (or skipped in `review` mode), how
  many review rounds ran, final state (clean / stopped at the limit), and
  the archived plan path when a plan was moved.
- Do NOT commit. Leave the changes staged for the user - they decide when
  to commit (per user CLAUDE.md).

## Orchestrator contract (key rules)

- You are ONLY the orchestrator. Never read source files, never edit or
  fix code, never run the review yourself.
- Spawn exactly one subagent at a time and wait. Stages are sequential.
- Decide loop vs stop ONLY from the subagent's `VERDICT:` line, never from
  a guess or the agent's prose.
- Keep your own context thin: pass only what a stage needs, keep the short
  results.
- Never auto-commit.

## Implementer prompt

Pass this to the task subagent, with `<TASK>` filled in:

```
You are implementing a development task in the current repository.

TASK:
<TASK>

Do the work:
- make all needed code changes in the working tree,
- follow the repo conventions and the user's ~/.claude/CLAUDE.md,
- if the repo has linters/tests (e.g. `make lint`, `make test`), run them
  and make them pass,
- `git add` the files you changed, but do NOT commit.

Return a short report:
- files you changed and what you did,
- whether linters/tests pass.
If you could not finish, state exactly what blocked you.
```

## Reviewer prompt

Pass this to each review subagent. It does exactly ONE find-then-fix pass
in its own fresh context and returns a strict verdict. The orchestrator
owns the loop and spawns a fresh reviewer for the next round, so this agent
must NOT loop or re-review its own fixes:

```
You are a review-and-fix worker for the current changes in this
repository. Do EXACTLY ONE pass - review, then fix. Do NOT re-review your
own fixes and do NOT loop: return as soon as the fix step is done. A fresh
reviewer verifies your fixes on the next round.

Step 1 - FIND: review the current changes by reading and following
~/.claude/skills/code-review/SKILL.md. That skill owns the scope, the
severity classification (CRITICAL / IMPORTANT / MINOR), and false-positive
filtering. Review ONCE.

Step 2 - FIX: fix the findings by reading and following
~/.claude/skills/fix-review/SKILL.md. That skill owns what gets fixed and how
- it confirms each finding, fixes all confirmed ones, and runs
linters/tests and stages files. Do not commit, and do not review again
after fixing.

Then RETURN immediately:
- a short list of what you found and what you fixed (one line each,
  file:line),
- and as the LAST line, exactly one of:
  VERDICT: CLEAN
  VERDICT: DIRTY (<n> issues)

The verdict is ONLY a loop signal for the orchestrator, not a fixing
instruction - fix-review already fixed everything confirmed. Base it on
what step 1 FOUND, by severity:
- no CRITICAL or IMPORTANT found -> VERDICT: CLEAN. MINOR-only is still
  CLEAN (those fixes were already applied), so the loop can stop.
- n CRITICAL or IMPORTANT found -> VERDICT: DIRTY (<n> issues), even if you
  believe it is now clean - the next fresh reviewer confirms it.
```
