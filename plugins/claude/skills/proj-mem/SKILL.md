---
name: proj-mem
description:
  Write, refactor, or extend the **project-root** `CLAUDE.md` (the one at the
  repository root), and the project docs it indexes (`docs/design`, `docs/adr`,
  `docs/quirks.md`, ...). Also use it to split a `CLAUDE.md` that grew too long
  into those docs. NOT for `~/.claude/CLAUDE.md` (user-global),
  `.claude.local.md` (personal override), or nested package-level `CLAUDE.md`
  files - different scope and style.
---

# Project CLAUDE.md Writer

Writes or refactors a project's `CLAUDE.md` and the docs it points to.

`CLAUDE.md` is loaded into every session, so every line costs context in every
task, and in a long file each rule is easier to miss. It holds only what a task
in any part of the project needs: what the project is, where things are, the
rules that hold everywhere, an index of the docs, and the commands. Everything
else - how a part works, the reasons behind the rules, decisions, facts about
outside systems - lives in `docs/`.

Content comes from the user (for things only they know) and from the repo
itself (for things the code already proves).

## Scope: project-root CLAUDE.md only

This skill targets exactly one file: `./CLAUDE.md` at the **repository root** -
the file checked into git and shared with the team - and the `docs/` it
indexes.

It does **not** apply to:

| File                                         | Purpose                                                                                         | Why this skill is wrong for it                                                                              |
| -------------------------------------------- | ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `~/.claude/CLAUDE.md`                        | User-wide preferences across all projects (code style, testing conventions, git workflow, etc.) | Holds what applies to every project of the user. The section template of this skill doesn't fit.            |
| `./.claude.local.md`                         | Personal overrides for this project, gitignored                                                 | Personal scratch - no enforced structure expected.                                                          |
| `./packages/*/CLAUDE.md`, nested `CLAUDE.md` | Module- or feature-level context inside a monorepo                                              | Scoped to a sub-area. Its knowledge belongs in the doc of that part, which this skill writes under `docs/`. |

If the user is clearly asking about one of those, stop and say so - don't
silently rewrite the wrong file.

## Output structure

In this order:

1. `# <project name>` and a short paragraph: what the project is
2. `## Related projects` - only when a task here may need another project
3. `## Layout`
4. `## Rules`
5. `## Docs` - once the project has `docs/`
6. `## Commands`

Nothing else at the top level. No "Code style", "Testing guidelines", "Git
workflow", "Architecture overview". A preference that holds in every project of
the user belongs in `~/.claude/CLAUDE.md`; how a part works belongs in its doc.
A convention of this project only - the language version, the style it follows,
how it treats comments - is a rule in `## Rules`.

If the user dictates a rule that looks the same for all their projects, save it
for them but flag it: _"this looks like a global preference - you may want it
in `~/.claude/CLAUDE.md`, not the project file, otherwise it'll only apply
here."_

## Line length

Hard-wrap every line in `CLAUDE.md` and the docs at **79 characters**: run
`prettier --write --prose-wrap always --print-width 79` on each file you
change. Prettier leaves code blocks, table rows and long URLs as they are.

## Workflow

The skill operates in one of four modes. Decide which one applies before doing
anything else.

| Mode                        | Trigger                                                                                                                                                               | Action                                                                                 |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| **A. Create**               | `./CLAUDE.md` does not exist                                                                                                                                          | Build the file from scratch (interview + derive).                                      |
| **B. Refactor**             | File exists; user asks to "rewrite", "restructure", "clean up", "fix the structure of"                                                                                | Restructure under the template, preserving meaning.                                    |
| **C. Augment from session** | File exists; user asks to "add", "update", "save this to", "record", "fold in", "записать", "обновить" - referring to something discussed in the current conversation | Read the existing file + extract relevant decisions from the live conversation; merge. |
| **D. Split into docs**      | File exists and holds rules of one part, reasons or long explanations; or the user asks to move knowledge out of it ("too big", "ADR", "docs")                        | Follow "Moving knowledge out of CLAUDE.md" below.                                      |

If it's ambiguous, ask once: _"do you want me to restructure the existing file,
or fold in what we just discussed?"_

### Mode A - Create

1. List the repo root. Inspect obvious tooling files: `Makefile`,
   `Taskfile.yml`, `justfile`, `package.json` scripts, `pyproject.toml`,
   `go.mod`, `Cargo.toml`, lockfiles.
2. **Derive without asking**:
   - _Commands_ from the build tool's targets/scripts. If none exists, fall
     back to language-idiomatic commands (`go test ./...`, `pytest`,
     `pnpm test`, ...).
   - _Layout_ from the folders of the repo.
   - _A tech-stack hint for the intro_ from manifests/imports - one short cue
     ("terminal client", "REST API", "CLI tool"), not the whole stack.
3. **Interview in one batched message** (not one question at a time):
   1. _"In one or two sentences: what does this project do, and for whom?"_
   2. _"What rules does this project enforce that aren't obvious from reading
      the code? Things like 'X always goes through Y', 'never do Z'. Bullet
      points are fine - I'll structure them."_ Ask for the reason too: it goes
      to the doc of the part.
   3. _Commands sanity_ - only if you couldn't derive obvious targets.
   4. _"Are there projects next to this one that a task here may need to read -
      a library it uses, a service it calls, a tool that builds it?"_ Only if
      the parent folder holds other projects.

   If the user says "nothing comes to mind" for rules, leave a placeholder
   (`<!-- TODO: add rules as they emerge -->`) instead of fabricating.

4. Write the file using the templates below, and a doc under `docs/` for every
   rule of one part. Show the result and ask whether any section needs
   tweaking.

### Mode B - Refactor

1. Read the existing `CLAUDE.md`.
2. **Preserve the user's meaning, restructure the form** under the templates
   below.
3. Run the same repo inspection as Mode A to refresh _Commands_ and _Layout_ -
   they often go stale.
4. If the file holds rules of one part, reasons or long explanations, do Mode D
   as part of the refactor.
5. If the file contains content that holds in every project of the user,
   surface it: _"these look like global preferences - want me to drop them
   here, or move to `~/.claude/CLAUDE.md`?"_ Don't silently delete.
6. Show a diff (or the new file) and confirm before overwriting.

### Mode C - Augment from session

This is the common case where a design decision was discussed in chat and the
user wants it captured without re-explaining.

1. Read the existing `CLAUDE.md` and the `## Docs` index.
2. **Scan the current conversation** for content worth saving. Filter
   aggressively - only keep things that:
   - Are _durable_ rules (not one-off tactical decisions or debugging steps).
   - Concern _contracts_, _conventions_, _invariants_, _forbidden patterns_,
     _deviations from a standard_.
   - OR concern _commands the user runs_ that are missing from the file.

   Skip: code that was written, bugs that were fixed, ephemeral context (PR
   numbers, ticket IDs), things already obvious from reading the code.

3. For each candidate, decide where it lives:
   - A rule that holds everywhere → `## Rules`, in short, with a link.
   - A rule of one part, or the reason of any rule → the doc of that part.
   - A decision with the options turned down → a new ADR.
   - A fact about an outside system → `docs/quirks.md`.
   - A new doc → a new line in the `## Docs` index.
   - A new command → `## Commands`.

   And whether it is an **addition** (a new rule) or an **update** (it replaces
   or amends an existing one, edited in place).

4. Present the candidates to the user **before writing**, in a numbered list
   with the proposed text inline. Example:

   > Found 2 things worth saving from this session:
   >
   > 1. _(addition, `docs/design/remote-sync.md`)_ "A push after a write runs
   >    in the background, about 3 seconds after the last action..."
   > 2. _(update, `## Rules`)_ The rule "A person never waits on git..." now
   >    says that a write with an API token still pushes in its request.
   >
   > Apply all? Skip any?

5. After the user approves, apply the changes.

When in doubt about whether a session item belongs in the project's knowledge,
prefer to ask the user rather than smuggle it in - and prefer to ask up front
in the "found N candidates" message rather than after writing.

## Docs

### Doc types

One kind of knowledge per place:

| Place                     | Holds                                                                                                                                           | How it changes                                                                                          |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `docs/design/<part>.md`   | how one part works and the rules it keeps, with the reasons                                                                                     | kept current: a change in behavior updates its doc in the same change                                   |
| `docs/ui/<screen>.md`     | how a screen looks and behaves, in a project with a UI                                                                                          | kept current the same way                                                                               |
| `docs/adr/NNNN-<slug>.md` | one decision, with the options turned down                                                                                                      | never rewritten: a new decision is a new file, and the old one's status names the file that replaced it |
| `docs/quirks.md`          | facts about outside systems found by hitting them: browsers, libraries, git, the OS                                                             | grows; the fact is written here once, and a rule that depends on it cites it in a few words             |
| `docs/plans/`             | plans of past and current work, and whatever comes with them (progress notes, reviews); their form is up to the tool or person that writes them | describes the code at the time it was written, not the code today                                       |

Create only the types the project has content for. A doc may name files, types
and functions: it is read while working on that part and changes together with
the code. A reason that must survive goes into the doc of its part, not into a
code comment.

### Design and ui docs

The part's name as the title, one line on what the doc covers, then a section
per topic. Each rule is a bullet: the rule, its exception if there is one, and
its reason, in one paragraph. A reason is never invented: when the source gives
none, the rule stands without one. A rule backed by an ADR or a quirk links to
it.

```
# Storage

How the notes on disk are read, written and watched.

## Writes

- Writes are atomic: temp file in the same directory, then rename. The temp
  file is opened with `O_CREATE|O_EXCL`, because `os.Root` follows no symlink
  when both are set, so a link planted at the temp path cannot redirect the
  write.
- Uploads land in a folder next to the document and named after it
  (`python/notes.md` -> `python/notes/`), which is what the corpus looks like.
```

### Quirks

`docs/quirks.md` opens with a line on what it holds, then a section per outside
system. Each fact is one bullet and ends with a link to the doc that depends on
it or works around it.

```
# Quirks

Facts about the systems scrawl runs on that no spec says and that were found by
hitting them. A rule cites a fact in a few words; the fact itself is written
here.

## iOS and Safari

- A field whose text is under 16px zooms the page when it takes the focus and
  never zooms back. [Touch](ui/touch.md)
- `:active` is drawn only when the document has a `touchstart` listener.
  [Touch](ui/touch.md)
```

### ADR

Write an ADR only for a decision whose source names the options turned down or
the reason against them. Never invent a reason: when the source gives none, the
rule stays in its design doc without an ADR. The design doc keeps the rule and
links to the ADR; the context and the options turned down live only in the ADR.

```
# <N>. <The decision, as a short statement>

Status: accepted. Where it applies: [<part>](../design/<part>.md#<section>).

## Context

<What made a decision necessary. Only facts the source gives.>

## Decision

<What was decided.>

## Options turned down

- <Option>: <why not, in the source's words.>

## Consequences

- <What follows from it that a reader must keep in mind.>
```

`Context` and `Consequences` may be left out when the source has nothing for
them.

### Moving knowledge out of CLAUDE.md

1. Split the file into units (a bullet or a subsection) and give each unit one
   place: `## Rules`, a design doc or a ui doc. Group a doc into sections.
2. Move the text word for word, best with a script, so nothing is retyped. Only
   the reasons that go to an ADR are cut, and the rule links there.
3. Write the ADRs and `docs/quirks.md`, then the short rules and the index of
   `CLAUDE.md`.
4. Check before reporting:
   - every sentence of the old file is found in the new files (a script that
     ignores line breaks); the ones that are not are exactly the reasons moved
     to ADRs;
   - every link and anchor resolves;
   - a fresh reader (a subagent) compares each short rule, each ADR and each
     quirk with its source, looking for lost exceptions, stronger or weaker
     wording, and reasons the source does not give. The text written anew is
     where the meaning drifts; the moved text is not.

## Section templates

### Title and intro

The project name as the title, then two to four sentences: what the project
does, for whom, and _just enough_ technical positioning that a reader knows
what kind of thing they're looking at.

**Good:**

> Single Go binary that serves directories of markdown files as a notes web app
> with in-browser editing. A directory may be a git clone it pushes back to.
> Runs in Docker, no external services, all state on disk.

**Bad (too detailed - this is README material):**

> kafka-tui is a TUI application written in Go using the bubbletea framework.
> It connects to Kafka clusters via the franz-go client library and provides
> screens for topic listing, message browsing with seek capabilities, consumer
> group offset reset, and message production with history persistence.

### Related projects

Projects usually sit side by side in one parent folder, so a related project is
a sibling: `../<name>`. List only the projects a task here may need to read or
change. Each line is the name as a link to its folder, then two sentences: what
it is, and how it is connected to this project - what this one takes from it or
gives it, and when to look there.

```
## Related projects

- [agentkit](../agentkit) - the skills and agent settings shared by all
  projects. A skill used here is changed there, not in its installed copy.
- [k9s](../k9s) - a checkout of k9s, the app whose UX this one follows.
  Read it to see how a k9s screen or shortcut behaves before copying it.
```

**Style:**

- A related project is something to read, not a dependency: code, tests and
  builds never reach into it.
- Copy nothing from it: the path and two sentences. Its details belong in its
  own `CLAUDE.md`.
- Drop a project from the list when the connection ends.

### Layout

A code block: one line per folder or notable file, then what it holds. It tells
a session where to look without listing the tree.

````
## Layout

```
main.go                the serve command: config, wiring, shutdown
store/                 safe filesystem access, tree, CRUD, watcher
server/                HTTP server, handlers, page cache
server/assets/app/     the built frontend, generated by `make ui`
web/                   react and mantine source for all of them
vendor/                dependencies, checked in, `make deps` regenerates
docs/design/           how each part works and the rules it keeps
```
````

**Style:**

- Top-level folders, and a nested one only when it holds something a task looks
  for (generated output, a second entry point).
- Say what the folder is for, not what files it has. Mark what is generated and
  by which command.

### Rules

The rules that hold everywhere and that a task in any part can break. One line
opens the section, then a flat list:

```
## Rules

These hold everywhere. The rules of each part, and the reasons, are in the doc
the link names.

- Go 1.25, module `github.com/aleksey925/scrawl`.
- The code has no comments, apart from tool directives and the `arrange`,
  `act`, `assert` markers of a test; config files keep theirs. A reason that
  must survive goes into the doc it belongs to.
- Every filesystem operation goes through `store`, which is built on `os.Root`.
  Never join paths against the OS root anywhere else. The command line is the
  one exception: it reads the files the person running it named.
  [storage](docs/design/storage.md#access)
- Write endpoints require auth and CSRF and are refused in read-only mode. A
  `Bearer` API token authenticates instead of the cookie and skips the
  cross-origin check, and a `:ro` token is refused the same writes.
  [server](docs/design/server.md#guards)
```

**What goes here:**

- Conventions of the project: the language version, the style it follows, how
  it treats comments.
- The one place that everything goes through, security boundaries, invariants
  that any task can break.
- Nothing that matters to one part only: that rule lives in the doc of the
  part.

**Style:**

- One to four lines per rule. No subsections, no `Why:` lines, no history of
  the bug that taught it: the reason lives in the doc, and a second copy here
  drifts from it.
- End the rule with a link to the doc section that holds its full form and
  reason. A convention with no doc has no link.
- A short rule keeps every exception and limit of the full one. A summary that
  drops an exception reads as a wider ban or a wider permission than the real
  rule.
- Name the code the rule protects - the package, the env variable, the call -
  when the name is the rule. The mechanics stay in the doc.

**Bad (a reason and a story in `CLAUDE.md`, the exception lost):**

> ### Filesystem access
>
> All file access goes through `store`.
>
> Why: in March a handler joined a user path against `/` and served
> `/etc/passwd`, so we moved every operation onto `os.Root`, which refuses a
> path that escapes the root, even through a symlink.

### Docs

The section says in one line what each place under `docs/` holds and how it
changes, then gives the index: one line per doc, the words a task will use,
then a link. The index lists every doc a task may need, not only the ones in
`docs/`: the README of a part, the guide of a test suite.

```
## Docs

One kind of knowledge per place:

- `docs/design/` - how a part works and the rules it keeps, with the reasons.
  Kept current: a change in behavior updates its doc in the same change.
- `docs/adr/` - one decision per file, with the options turned down. An ADR is
  not rewritten: a new decision is a new file.
- `docs/quirks.md` - facts about browsers, libraries, git and the OS, found by
  hitting them.

Before changing a part, read its doc:

- `store`, `os.Root`, atomic writes, the watcher, uploads, paths, the trash:
  [storage](docs/design/storage.md)
- a clone, `--ff-only`, diverged, reset, credentials, the webhook:
  [remote sync](docs/design/remote-sync.md)
- why something is built the way it is: [`docs/adr/`](docs/adr/)
- a strange browser, library or git behavior:
  [`docs/quirks.md`](docs/quirks.md)
- the dev server, the build output, the theme file format:
  [`web/README.md`](web/README.md)
```

**Style:**

- Lead with the words a task will contain - commands, concepts, screens - not
  only the doc's title: a session opens a doc only when a line matches what it
  is doing.
- Every doc has a line, and each line's words match what the doc holds.
- When a doc is added or a topic moves, the index changes in the same edit.

### Commands

An optional line on how to set up the checkout, then a code block: one command
per line and what it does.

````
## Commands

Toolchain versions come from `mise.toml`: `mise install && make deps`.

```
make build      build the binary into dist/
make test       tests
make race       tests with the race detector
make lint       every pre-commit hook
make run        run ./examples/data with auth disabled
```
````

**Style:**

- Order roughly: build → test → lint → run → other.
- If a command does several things, describe the _outcome_, not the steps. Say
  what must be committed after it, if anything.
- If there's no Makefile / package script, list the raw commands
  (`go test ./...`, `uv sync`, `pnpm test`, `cargo build --release`).

## Reference

A complete example following this style lives alongside this skill at
`example-CLAUDE.md`, a shortened copy of a real project's file. When in doubt
about tone, structure, or how short a rule should be, read that file and match
its register.
