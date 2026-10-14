# Review fanout playbook

This file is a playbook for the main orchestrator session - NOT a prompt to
spawn into a subagent. Subagents do not have access to the Agent tool in
current Claude Code, so the parallel fanout below must be initiated from the
main session.

Resolve placeholders (`DIFF_COMMAND`, `PROGRESS_FILE_PATH`, `PLAN_CONTEXT`,
`REVIEW_PHASE`), then follow the instructions below from the main session:
launch the specified parallel Agent calls, collect findings from all returned
agents, and pass them to the fixer subagent. The orchestrator does NOT fix
issues itself - the fixer is a separate subagent that handles fixes.

## How to fan out (READ THIS CAREFULLY)

In your NEXT assistant response, emit N Agent tool_use blocks TOGETHER - all N
must appear in the same response, no text between them, no pausing to read
results. Multiple tool_use blocks in one response run in PARALLEL; tool_use
blocks spread across separate responses run SEQUENTIALLY (Nx runtime). The
agents are fully independent - no shared state, no ordering. Do NOT use
run_in_background. After emitting all N tool calls, stop generating - the
orchestrator response ends there, agents run in parallel, and your next
response begins after all N return.

Each agent prompt MUST include: "CRITICAL: You are a READ-ONLY reviewer. Do
NOT run git stash, git checkout, git reset, or any command that modifies the
working tree. Other agents run in parallel. Only use git diff, git log, git
show, and read files."

Each agent prompt MUST require severity tagging on every finding. Tag
categories:
- CRITICAL: bugs causing crashes, data loss, security holes, race conditions
- MAJOR: real correctness issues - incorrect behavior, missing error handling,
  broken contracts
- MINOR: style, doc drift, doc/code inconsistencies, nits, optional
  improvements

Agents must format each finding on its own line as:
`SEVERITY: file:line - description`. Findings without an explicit severity
prefix are treated as MINOR.

Do NOT embed diffs in agent prompts - tell each agent to run the diff command
itself. Embedding large diffs slows parallel launch and inflates context.

## Shared preamble

For every agent in every phase, read the agent's prompt file, then prepend
this preamble (substitute `DIFF_COMMAND`, `PROGRESS_FILE_PATH`, and
`PLAN_CONTEXT`):

"CRITICAL: You are a READ-ONLY reviewer. Do NOT run git stash, git checkout,
git reset, or any command that modifies the working tree. Other agents run in
parallel. Only use git diff, git log, git show, and read files.

Run `DIFF_COMMAND` to see all changes under review. Read the actual source
files for full context - do not review from the diff alone.

PLAN_CONTEXT

Read the progress file at PROGRESS_FILE_PATH for context on previous review
iterations and fixes. Re-evaluate all findings independently - previous fixes
may be incomplete or wrong, and previously dismissed issues may be real.

Tag every finding with severity (CRITICAL/MAJOR/MINOR) and format each on its
own line as: `SEVERITY: file:line - description`."

`PLAN_CONTEXT` is built once in SKILL.md Step 4 from up to three sources (plan
file, user-provided context, session synthesis), or an empty string when none
apply. Substitute whatever that step produced - do not rebuild it here.

## Comprehensive mode (5 agents)

Used when `REVIEW_PHASE` is `comprehensive`.

Read each agent's prompt file (these are plain reads, not parallel work):

```
${CLAUDE_PLUGIN_ROOT}/skills/deep/references/agents/quality.txt
${CLAUDE_PLUGIN_ROOT}/skills/deep/references/agents/implementation.txt
${CLAUDE_PLUGIN_ROOT}/skills/deep/references/agents/testing.txt
${CLAUDE_PLUGIN_ROOT}/skills/deep/references/agents/simplification.txt
${CLAUDE_PLUGIN_ROOT}/skills/deep/references/agents/documentation.txt
```

For each, prepend the shared preamble above.

In your next assistant response, emit 5 Agent tool_use blocks together. Each
with `subagent_type: "general-purpose"`, `mode: "bypassPermissions"`, and the
assembled prompt for one of the 5 specialists (quality, implementation,
testing, simplification, documentation). The reviewers are read-only;
bypassPermissions keeps the parallel fanout from stalling on per-command
approval prompts.

After ALL 5 agents return, produce a STRICT bullet-list report - no prose
summary, no narrative, no "agents converge on" sentences. Format requirements:

- Group findings by severity in this order: CRITICAL, MAJOR, MINOR. Use a
  heading per severity (`### CRITICAL`, `### MAJOR`, `### MINOR`). Skip a
  severity heading if it has zero findings.
- Under each heading, one bullet per finding using EXACTLY this shape:
  `- <agent-name>: <file:line> - <description>`
- Preserve the original agent attribution (`quality`, `implementation`,
  `testing`, `simplification`, `documentation`). Do NOT rewrite as "agents".
- If two agents reported the same file:line + same issue, merge into one
  bullet and prefix both agent names separated by `+`
  (e.g. `- quality+implementation: main.go:12 - ...`).
- Do NOT verify, fix, or dismiss findings here - the fixer agent does that.
  Just emit the report verbatim from agent outputs.
- Omit agents that found nothing entirely.
- After the bullet list, on its own line, emit one summary line:
  `Total: <N> findings (<C> critical, <M> major, <m> minor)`.

Do NOT add explanatory prose, recommendations, or commentary. The list goes
straight to the fixer.

## Smells mode (1 agent)

Used when `REVIEW_PHASE` is `smells`. Read
`${CLAUDE_PLUGIN_ROOT}/skills/deep/references/agents/smells.txt`, prepend the
shared preamble, and run it as a single `general-purpose` agent with
`mode: "bypassPermissions"`. Produce the same strict bullet-list report (the
only agent name is `smells`).

## Critical-only mode (2 agents)

Used when `REVIEW_PHASE` is `critical`.

Read only `quality.txt` and `implementation.txt`. Prepend the shared preamble,
plus:

"Report ONLY critical and major issues - bugs, security vulnerabilities, data
loss risks, broken functionality, incorrect logic, missing critical error
handling. Ignore style, minor improvements, suggestions. Tag every reported
finding with severity (CRITICAL or MAJOR) and format each on its own line as:
`SEVERITY: file:line - description`."

In your next assistant response, emit 2 Agent tool_use blocks together. Same
`subagent_type` and `mode: "bypassPermissions"` as comprehensive mode.

After BOTH agents return, produce the same STRICT bullet-list report as
comprehensive mode. Additional rules for this mode:

- Drop any MINOR findings if agents returned them anyway. Only CRITICAL and
  MAJOR headings appear here.
- If neither agent reported CRITICAL or MAJOR findings, emit exactly:
  `Critical re-check: clean - no critical/major findings.` and stop.
