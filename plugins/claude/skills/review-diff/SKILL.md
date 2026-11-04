---
name: review-diff
description: "Code review of changes that only reports findings and never fixes them. Parallel specialist agents (bugs, tests, style, docs) review uncommitted changes, a branch, files or commits; codex adds a second view when asked. Any reviewer can be turned off."
argument-hint: "[codex] [preset=default|hard] [model=<slug>] [effort=low|medium|high|xhigh|max|ultra] [no-bugs] [no-tests] [no-style] [no-docs] [plan.md] [scope or context...]"
allowed-tools: Read, Glob, Grep, Bash, Agent, Write
---

# review-diff

Review the changes and report findings. You MUST NOT write or change any code
during this task - this skill only reports. Fixing is a separate step
(`fix-review`).

Up to four specialist reviewers run in parallel, each with its own checklist.
Codex runs next to them only when asked. Then you verify every finding against
the code and report the real ones.

## Arguments

`$ARGUMENTS` may contain, in any order:

- `codex` - also run an external codex review
- `preset=<name>`, `model=<slug>`, `effort=<level>` - codex model choice,
  passed to `run-codex.sh` as `--preset`, `--model`, `--effort`. They do not
  turn codex on by themselves. Presets: `default` (newest `sol` model, effort
  `medium`) and `hard` (newest `astra` model, effort `xhigh`). Without
  `preset=`, the preset comes from the `CODEX_PRESET` environment variable,
  then `default`
- `no-bugs`, `no-tests`, `no-style`, `no-docs` - turn off that reviewer
- a path to an existing `.md` plan file that describes the intent of the
  changes
- any other text: what to review (files, commits, a branch, a PR number)
  and/or what the change is about. Decide which by its meaning.

If all four reviewers are turned off and `codex` is not given, tell the user
there is nothing to run and stop.

## File resolution

`SKILL_DIR` is the absolute path of the folder that contains this SKILL.md.

- reviewers: `SKILL_DIR/references/agents/<name>.txt`, where `<name>` is
  `bugs`, `tests`, `style` or `docs`
- codex prompt: `SKILL_DIR/references/codex-review.md`
- codex runner: `SKILL_DIR/scripts/run-codex.sh`

## Step 1. Determine what to review

1. **If `$ARGUMENTS` names a scope** - review what the user specified (e.g.,
   specific files, commits, a branch, or a PR number).
2. **Otherwise**, run `git status` and `git branch --show-current`:
   1. **If there are uncommitted changes** (staged or unstaged tracked files) -
      review those changes: `git diff` and `git diff --cached`.
   2. **If there are NO uncommitted changes AND the current branch is NOT
      `main` or `master`** - review all changes on the current branch relative
      to the main branch: `git diff <main-branch>...HEAD` and
      `git log <main-branch>..HEAD`.
   3. **If there are NO uncommitted changes AND the current branch IS `main`
      or `master`** - ask the user what they want to review.

Write the result as `SCOPE`: one or two sentences that tell a reviewer how to
see the changes, e.g. "Run `git diff` and `git diff --cached` to see the
changes under review." Run those commands once yourself. If they show nothing,
tell the user there is nothing to review and stop.

## Step 2. Build the context

Assemble `CONTEXT` from up to three sources. Describe only what explains THESE
changes.

- **plan file**: "The plan file at <path> describes the goal and
  requirements. Use it to understand what the code is supposed to do."
- **text from the user** (the non-scope part of `$ARGUMENTS`): "Review focus
  (provided by user): <text>". On conflict with the session, this wins.
- **session synthesis**: if the current session did work that explains the
  changes, summarize the intent in 1-3 sentences as "Inferred intent (from the
  working session, may be incomplete): <text>". Reviewers treat it as a hint,
  not a spec.

If none apply, `CONTEXT` is an empty string.

## Step 3. Run the reviewers

**If you do not have the Agent tool** (for example, you run inside a
subagent), do the review yourself in one pass: read the file of every enabled
reviewer and use it as your checklist, follow the rules of the shared preamble
below, and go to Step 4. Codex still runs if asked.

**Otherwise**, for every enabled reviewer read its file and prepend the shared
preamble (substitute `SCOPE` and `CONTEXT`). Then in ONE response emit one
Agent tool call per enabled reviewer (`subagent_type: "general-purpose"`),
plus the codex call if `codex` was given. All calls in one response run in
parallel; calls in separate responses run one after another. Do NOT embed the
diff in the prompts - each reviewer runs the commands itself.

Shared preamble:

```
You are a READ-ONLY reviewer. Do NOT edit files, and do NOT run git stash,
git checkout, git reset, or any other command that changes the working tree
or the index. Other reviewers run in parallel.

SCOPE Read the actual source files for full context - do not review from the
diff alone.

CONTEXT

Be pragmatic: catch real problems, not issues invented to look thorough. For
each finding, describe a concrete scenario in which it causes a problem; if
you cannot, drop it. An empty result is a valid outcome.

Tag every finding with severity:
- CRITICAL - bugs, data loss, security vulnerabilities, service outage
- IMPORTANT - logic errors, missed edge cases, wrong data passed to APIs,
  architectural concerns
- MINOR - naming, style, comments, documentation drift, nits

Put each finding on its own line as `SEVERITY: file:line - description`,
followed by a line `Scenario: <the concrete situation>`. If you find nothing,
reply exactly NO ISSUES FOUND.
```

**Codex** (only when `codex` was given):

1. Read `SKILL_DIR/references/codex-review.md`, substitute `SCOPE` and
   `CONTEXT`, and write the prompt with the Write tool to
   `/tmp/review-diff-<timestamp>.codex-prompt.txt`. Do NOT paste the prompt
   into the command or write it with `echo` or an unquoted heredoc: it
   contains backticks, and the shell would run them as commands.
2. Run this with `run_in_background: true`, in the same response as the
   reviewer agents:

   ```bash
   bash "SKILL_DIR/scripts/run-codex.sh" \
     [--preset <name>] [--model <slug>] [--effort <level>] "$(cat <prompt-file>)"
   ```

   When the agents return, wait for the codex notification - do NOT poll or
   sleep.

3. The result merges stdout and stderr. Treat it as a codex failure when the
   exit code is non-zero, the output is empty, or it has neither
   `NO ISSUES FOUND` nor any `CRITICAL`/`IMPORTANT`/`MINOR` tag. On failure,
   note the reason for the report and continue without codex. The
   `warning: ...` and `codex: model ..., effort ...` lines come from the
   script, not from codex, so do not take them as the reason.

## Step 4. Verify the findings

Collect findings from all reviewers and codex. Merge duplicates (same
file:line and same problem). For each finding, read the code at file:line with
enough context and check that it is real. Drop false positives - things that
seemed wrong but are correct on a closer look. Fix the severity if a reviewer
got it wrong. Be skeptical: a short report of real problems is better than a
long one with noise.

## Step 5. Report

For each finding, start the first line with the file path and line number in
the standard linter format, then severity, a short problem summary, and the
sources in brackets. Put the scenario on the next line:

```
path/to/file.py:42: CRITICAL - short problem summary [bugs+codex]
Scenario: concrete situation where this causes a failure.
```

Group findings by severity: CRITICAL first, then IMPORTANT, then MINOR. If no
issues are found, say so explicitly. Do not say what was done correctly.

After the findings, add one line: which reviewers ran, codex status (off, ran,
or failed with the reason), and how many findings were dropped as false
positives.

#$ARGUMENTS
