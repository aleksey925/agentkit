---
name: commit-msg
description: "Generate a commit message for current changes (uncommitted or branch)"
---

# commit-msg

## Your task

Generate a concise Git commit message in English for current changes.

## Detection strategy

1. First, check for uncommitted changes: `git status --porcelain`
2. If there are uncommitted changes → analyze them with `git diff` and `git diff --cached`
3. If no uncommitted changes → check if current branch differs from master/main using `git diff master...HEAD`
4. If neither → report "no changes to commit"

**Important:** When analyzing a branch with multiple commits, generate a SINGLE unified commit message that summarizes ALL changes (squash commit style). Do not list individual commits.

## Requirements

1. Identify the HIGH-LEVEL GOAL of the changes, not implementation details
2. Write the ENTIRE commit message in lowercase (title and body) - the only
   exceptions are tokens that are case-sensitive by nature, such as code
   identifiers, file paths, env vars
3. Write the commit message following this format:

**Title:**
- Use imperative mood (add, fix, update, refactor, remove, etc.)
- Write entirely in lowercase
- Describe the PURPOSE/GOAL, not implementation mechanics
- Do NOT include implementation details (e.g., "add custom context" is a detail, "improve type safety" is a goal)
- Keep it at most 72 characters

**Body (bullet points):**
- Add bullet points ONLY if there are additional changes besides the main feature
- Use HIGH-LEVEL descriptions that group related changes by purpose:
  - All dependency/version updates → `update deps`
  - All changes for type safety → `fix mypy issues` or `improve type annotations`
  - All linter config changes → `update linter config`
- Maximum 2-4 bullet points (group aggressively!)
- Write each bullet point entirely in lowercase
- Focus on WHY, not WHAT (e.g., "fix all mypy issues" instead of "add type annotations to 5 functions")

**Example format:**
refactor bot and improve type safety

- fix all mypy issues
- update deps

**For simple changes without additional modifications:**
fix authentication timeout issue

**BAD example (too detailed, focuses on mechanics):**
refactor bot to use custom context and improve type safety

- switch pre-commit hooks to use local ruff installation
- add CallbackQueryContext helper for cleaner callback handling
- enable PLC0415 linter rule
- update pre-commit-hooks to v6.0.0
- update mypy to 1.19.0

After analyzing the changes, output ONLY the commit message text, without any explanations or commentary.
