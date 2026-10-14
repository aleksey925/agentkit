---
name: fix-review
description: "Verify code-review findings and fix the confirmed ones"
argument-hint: "[extra context]"
allowed-tools: Read, Glob, Grep, Bash, Edit, Write, AskUserQuestion
---

Act on the findings from the code review earlier in this conversation,
plus any extra context in `$ARGUMENTS`.

For each finding: re-check the code to confirm the problem is real. Fix the
confirmed ones; discard false positives with a one-line reason. If you can't
tell, ask instead of guessing.

After fixing, `git add` the changed files and run linters and tests.

When done, report grouped by outcome:

- **Fixed** — `path/to/file:line` + one line on what changed.
- **False positive** — `path/to/file:line` + why it was discarded.
- **Needs input** — `path/to/file:line` + the question blocking the fix.

#$ARGUMENTS
