# agentkit

Skills for Claude Code and Codex: code review, commit messages, READMEs,
transcripts and frames from a video, and more.

Skills are split into two plugins: `core` works in Claude Code and Codex,
`cc-only` only in Claude Code. Each skill is a folder in
`plugins/<plugin>/skills/`, with a `SKILL.md` that says what it does.

## Installation

### From the marketplace

The marketplace is this GitHub repository: the agent clones it and installs the
plugins it lists.

Claude Code:

```sh
claude plugin marketplace add https://github.com/aleksey925/agentkit.git
claude plugin install core@agentkit
claude plugin install cc-only@agentkit
```

Codex:

```sh
codex plugin marketplace add https://github.com/aleksey925/agentkit.git
codex plugin add core@agentkit
```

### From a local copy

The script links each skill into `~/.claude/skills` and `~/.agents/skills`, so
a change in the repo shows up in the agent at once:

```sh
git clone https://github.com/aleksey925/agentkit.git
cd agentkit
python3 scripts/install-skills.py
```

- `--dry-run` - print what would change, change nothing.
- `--agent claude` or `--agent codex` - install for one agent only.
- `--copy` - copy the skills instead of linking them.
- `--uninstall` - remove what the script installed.

The script never replaces a skill folder you changed by hand: it skips it and
lists it at the end.
