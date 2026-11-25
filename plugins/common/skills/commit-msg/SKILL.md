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

**Before calling something new**, check whether it already exists on
master. If it does, describe what changed in it, not `add ...`.

## Requirements

1. Identify the HIGH-LEVEL GOAL of the changes, not implementation details
2. Write the ENTIRE commit message in lowercase (title and body) - the only
   exceptions are tokens that are case-sensitive by nature, such as code
   identifiers, file paths, env vars
3. Drop articles (a, an, the), headline style: `fix login timeout`, not
   `fix the login timeout`. Keep one only where the text gets unclear
   without it
4. Write the commit message following this format:

**Title:**

- Use imperative mood (add, fix, update, refactor, remove, etc.)
- Describe the PURPOSE/GOAL, not implementation mechanics
- Do NOT include implementation details (e.g., "add custom context" is a detail, "improve type safety" is a goal)
- For a branch with many changes, find the theme they share (a redesign, a
  migration, a new feature) and name it the way a user would. Do not put one
  of several equal features in the title
- If one change is the main goal of the work and the others follow from it
  or adjust it, the title names that goal, and the rest go to bullets. Do not
  put the goal and a secondary change together in one title
- A broad theme is fine when the changes are many and different, but it must
  be true for all of them. Do not name a side effect as the theme when it was
  not the goal (`unify options` when the goal was a new feature)
- Keep it at most 72 characters

**Body (bullet points):**

- Add bullet points ONLY if there are additional changes besides the main feature
- Use HIGH-LEVEL descriptions that group related changes by purpose:
  - All dependency/version updates → `update deps`
  - All changes for type safety → `fix mypy issues` or `improve type annotations`
  - All linter config changes → `update linter config`
- Maximum 2-4 bullet points (group aggressively!)
- Group in one bullet only changes with one purpose; never list unrelated
  changes in one bullet with commas - if they do not fit in 4 bullets, drop
  the minor ones
- Keep each bullet short, one idea, at most 72 characters
- Focus on WHY, not WHAT (e.g., "fix all mypy issues" instead of "add type annotations to 5 functions")
- Write the result, not the method: `optimize release binary size`, not
  `embed assets gzip-compressed and ship fonts as woff2 only`
- Each bullet must be clear on its own: name the part of the product it
  touches (static site, editor, API), do not rely on the bullets around it
- Do not use words from the code or the project docs that a user never sees
- Start a new feature with `add`: `add note export to pdf`, not
  `export note to pdf`, which reads like a one-time action

**Example format:**
refactor bot and improve type safety

- fix all mypy issues
- update deps

**Example for a branch with many features:**
redesign app and improve its user experience

- make static site look and work like main app
- open notes on static site without page reload
- add note export to markdown, html or pdf
- optimize release binary size

**For simple changes without additional modifications:**
fix authentication timeout issue

**BAD example (too detailed, focuses on mechanics):**
refactor bot to use custom context and improve type safety

- switch pre-commit hooks to use local ruff installation
- add CallbackQueryContext helper for cleaner callback handling
- enable PLC0415 linter rule
- update pre-commit-hooks to v6.0.0
- update mypy to 1.19.0

**Before output**, check the message against the rules: all lowercase, no
articles, title and each bullet at most 72 characters, no unrelated changes
in one bullet.

After analyzing the changes, output ONLY the commit message text, without any explanations or commentary.
