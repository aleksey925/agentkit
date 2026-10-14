---
name: mkskill
description: "Helps create or edit existing skills interactively"
allowed-tools: Read, Glob, Grep, Bash, Write, Edit, AskUserQuestion
---

## Workflow

1. **Discovery**: list existing skills from `~/.claude/skills/` (personal)
   and `.claude/skills/` (project, if present).
2. **Clarify intent**: determine whether the user wants to create a new skill
   or edit an existing one. Skip the question when the conversation already
   makes it clear.
3. **For editing**: read the current `SKILL.md` and show its content before
   proposing changes.
4. **Location (new only)**: ask where it lives - `~/.claude/skills/`
   (personal, all projects) or `.claude/skills/` (project, shareable via
   git).
5. **Discussion**: understand what the skill does, its constraints, when it
   should trigger, and whether it needs arguments (`$ARGUMENTS`, `$1`,
   `$2`).
6. **Preview**: before writing, show the full `SKILL.md` (new) or a clear
   before/after (edit).
7. **Confirm**: wait for explicit approval before writing any file.
8. **Apply**: create `<name>/SKILL.md` (making the directory) and confirm.

## Skill file structure

A skill is a directory `<name>/` holding `SKILL.md`, plus optional support
files (`references/`, `scripts/`, examples) the body points to.

```markdown
---
name: <name>
description: "<what it does AND when to use it>"
argument-hint: "[hint]" # optional
allowed-tools: Read, Bash # optional
---

Skill body. Use $ARGUMENTS for user input, or $1, $2 for positional args.
```
