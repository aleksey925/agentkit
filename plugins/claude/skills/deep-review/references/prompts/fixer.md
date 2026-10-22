# Fixer prompt

Use this for the fixer agent after collecting review findings (substitute
`PLAN_CONTEXT`, `PROGRESS_FILE_PATH`, `FINDINGS_LIST`, and the resolved
absolute `$HOME`):

```
Code review found the following issues. Verify and fix them.

PLAN_CONTEXT
Progress file: PROGRESS_FILE_PATH (read it for context on what previous
iterations found and fixed)

FINDINGS:
FINDINGS_LIST

STEP 1 - VERIFY:
For each finding, read the actual code at the specified file:line. Check 20-30
lines of context. Classify as:
- CONFIRMED: real issue, fix it
- FALSE POSITIVE: doesn't exist or already mitigated, discard

STEP 2 - FIX:
- Fix all confirmed issues (including adding missing tests if flagged)

STEP 3 - VALIDATE (MANDATORY - code MUST compile and tests MUST pass):
- Build, test, and run the project's validation commands. If a plan was
  supplied and lists validation commands, use those. Otherwise infer them from
  the project (Makefile targets, package scripts, the test runner used by the
  existing tests). If you genuinely cannot determine how to build or test,
  state that explicitly in your report instead of claiming success.
- If anything fails: fix it and re-run everything.
- NEVER leave the tree in a broken state.

STEP 4 - DO NOT COMMIT:
Leave all fixes in the working tree, unstaged. The user reviews and commits
manually. Do NOT run git add, git commit, git stash, or any command that
moves changes out of the working tree.

STEP 5 - LOG PROGRESS:
Log details: echo "- confirmed: <list>
- false positives: <list>
- fixes: <what changed>
- validation: <what passed or could not be run>" | bash $HOME/.claude/skills/deep-review/scripts/append-progress.sh PROGRESS_FILE_PATH
IMPORTANT: Use ONLY the append-progress.sh script. Do NOT use cat >>, echo >>,
or heredocs directly.

STEP 6 - REPORT (MANDATORY - this is your return value to the parent):
Your final response MUST include a structured summary starting with "FIXES:"
on its own line, followed by one line per fix:
FIXES:
- fixed: <file>:<line> - <what was fixed>
- fixed: <file>:<line> - <what was fixed>
- false positive: <description> - <why discarded>

This report is shown to the user. Be specific about what changed.
```

`PLAN_CONTEXT` is built in SKILL.md Step 4: "Plan file: <path> (read it to find
validation commands and intent)", or the provided/inferred review context when
there is no plan, or an empty string when neither applies.
