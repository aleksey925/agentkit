# Codex review prompt

This is the prompt sent to codex. Substitute `DIFF_COMMAND`, `PLAN_CONTEXT`,
and `PROGRESS_FILE_PATH` before passing.

Run: `bash ${CLAUDE_PLUGIN_ROOT}/skills/deep/scripts/run-codex.sh "<prompt>"`
with `run_in_background: true`. You will be notified when done - do NOT poll
or sleep.

`DIFF_COMMAND` is the command resolved by `resolve-diff.sh` for this run.

If `codex` is not installed, skip this phase.

## Prompt

This is a read-only review: do NOT modify any files, and do NOT run any write
or git-mutating commands - only read and report findings.

Review code changes. Run DIFF_COMMAND to see changes. Read source files for
context. PLAN_CONTEXT Read the progress file at PROGRESS_FILE_PATH for context
on previous review iterations and fixes - re-evaluate all findings
independently, previous fixes may be incomplete or wrong. Check for: bugs,
security issues, race conditions, error handling, code quality.

Tag each finding with severity:
- CRITICAL: bugs causing crashes, data loss, security holes, race conditions
- MAJOR: real correctness issues - incorrect behavior, missing error handling,
  broken contracts
- MINOR: style, documentation drift, doc/code inconsistencies, nits, optional
  improvements

Format each finding on its own line as: `SEVERITY: file:line - description`.

If nothing found: NO ISSUES FOUND.
