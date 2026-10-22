# Codex review prompt

This is the prompt sent to codex. Substitute `SCOPE` and `CONTEXT` before
passing. How to run codex and how to read its output is defined in SKILL.md
Step 3.

## Prompt

This is a read-only review: do NOT modify any files, and do NOT run any write
or git-mutating commands - only read and report findings.

Review code changes. SCOPE Read source files for context. CONTEXT Check for:
bugs, security issues, race conditions, error handling, code quality.

Tag each finding with severity:

- CRITICAL: bugs causing crashes, data loss, security holes, service outage
- IMPORTANT: logic errors, missed edge cases, wrong data passed to APIs,
  architectural concerns
- MINOR: naming, style, documentation drift, nits

Format each finding on its own line as: `SEVERITY: file:line - description`.

If nothing found: NO ISSUES FOUND.
