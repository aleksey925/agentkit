---
name: readme-style
description: >-
  How the user wants a project README written. Use whenever you write,
  rewrite, review or extend a README.md or another page for the people
  who install, run or configure a project: install steps, settings,
  feature notes.
---

# README style

A README is read by someone who wants to install, run or configure the
project. Every paragraph answers their question: "is this about me, and
what do I do?" It is not the place to explain how the code is built.

## Describe a setting: case, effect, reason

Write each description in this order:

1. **The case.** When does the reader need it? "If the app runs behind a
   reverse proxy, set:". A reader whose case it is not skips the rest.
2. **The technical effect.** What the setting does, in mechanical terms:
   which header it reads, which flag it sets, which file it writes. Many
   readers understand the mechanism faster than an explanation.
3. **The reason.** What goes wrong without it, in one or two sentences.
   Be concrete: real numbers, the symptom the reader would see.

Do not mix the three. A paragraph that starts with a reason, puts the
setting in the middle and the condition at the end makes the reader
put it together.

Each part is needed:

- an effect without the case leaves "do I need this?";
- a reason without the effect leaves "and so what?" - "the browser then
  sends the cookie only over HTTPS" does not say what the setting does;
- a case and an effect without the reason leave "why bother?".

Bad - reason, action and condition mixed, and no effect:

```
Behind a proxy that handles HTTPS, set `TRUSTED_PROXY=true` and
`AUTH_SECURE=always`. The proxy must replace the `X-Forwarded-For` header
the client sent. Otherwise a client can fake its address and get around
the limit on sign-in attempts.
```

Good:

```
If the app runs behind a reverse proxy (nginx, Caddy or any other), set:

- `TRUSTED_PROXY=true` - the app then takes the user's address from the
  `X-Forwarded-For` header and the scheme from `X-Forwarded-Proto`,
  instead of from the connection. Without it, every request comes from
  the proxy's address, and the limit on wrong passwords counts all users
  together: 10 wrong passwords from anyone lock everyone out for 15
  minutes. The proxy must set `X-Forwarded-For` itself, otherwise anyone
  can write a new address there for each try and guess passwords
  without a limit.
- `AUTH_SECURE=always` - if the proxy serves HTTPS. The app then always
  sets the `Secure` flag on the sign-in cookie, and a browser will never
  send a cookie with this flag over plain http. This matters if the proxy
  still answers on plain http.
```

### In a settings table

A table cell is short, but it still says what the setting does and what
every value means. "`Secure` flag of the session cookie; `always` behind
an HTTPS proxy" leaves `auto` and `never` unexplained. Better:

```
`Secure` flag of the sign-in cookie: `auto` sets it when the request
came over HTTPS, `always` always, `never` never
```

For `WATCH`, which says how the app finds files changed outside it,
"set to `poll` when the notes are on a network share" gives the case but
not the effect. Say what `auto` and `poll` do, then when to pick `poll`
and why.

## Each fact has one home

Put a fact next to the thing it explains, and say it once. A reader
looks for it there, and two copies drift apart.

- An install section holds the ways to install and run, and nothing
  else. What a setting means goes beside that setting.
- A note on a value goes under its table: how to hash a password
  belongs beside `AUTH_USERS`, the list of users who can sign in, not in
  the install steps.
- A note on a requirement goes beside what it requires: "the folder has
  to be writable for uid 1001" belongs beside the folder setting.
- Before adding a paragraph, check that a later section does not say
  it already. A term explained in the install section and again at the
  start of the configuration section is one fact in two places.

## Leave out the design rationale

Why the code is built this way belongs in the project's `CLAUDE.md` or
design docs, not in the README. Keep a "why" only when it changes what
the reader does.

Signs of rationale: "rather than", "is written down rather than
derived", "for the same reason", "deliberately does not", "would
otherwise", a reason about a future change or about another part of
the code.

Bad:

```
The app serves one folder of notes. `SPACE_NAME` names it, and it is
required. It is the one segment every URL of that folder is served
under - `/s/notes/doc/python/redis.md` - so it is written down rather
than derived: a name taken from the directory would turn one `mv` into
a site-wide URL change.
```

Good:

```
The app serves one folder of notes. `SPACE_NAME` is its name, and it is
required. The name is part of every URL of the folder:
`/s/notes/doc/python/redis.md`.
```

The same goes for the inner workings that do not change what the reader
does: "the check is a trial merge and not a commit count" becomes "it
compares content, not commits".

## Check every fact against the code

Before writing or rewriting a fact - a default, a limit, a command, a
flag name, a path, a default state of a checkbox - find it in the code.

- A rewrite can make a true sentence false. "A credential is named,
  never written down inline" was about the config file; shortened to
  "the token is never written into the settings" it became false,
  because one environment variable holds the token directly.
- An old README goes stale. An example still used `--gen-hash` after
  the command became `hash`.
- Replace vague words with the value you found: "the editable size cap"
  becomes "up to 2MB", "a run of failures" becomes "10 wrong passwords".
- When the text gives a number, count: "the messages tell four things
  apart" stood over a list of six.
- Run an example through the program before you publish it: load a
  sample config with the project's own parser, run a sample command.
  A key the parser refuses is a broken example. When something cannot
  be run here, say which part was not checked.

## A lead-in covers the whole block

A sentence before a command or an example describes all of it or none
of it. "Outside docker, give it the path to your notes folder:" above a
command with three flags explains one flag and reads as odd. Better:
"Run it with the same settings as the docker example, given as flags:".

A block with no lead-in at all can read as part of the step before it:
a `serve` command right after `go install` looks like a build step.

## A configuration example is a real setup

An example file (`docker-compose.yml`, a sample config) shows one
setup that several people would really run, advanced if that is what
real use looks like. It is not the settings reference again.

- No commented-out options. A reader cannot tell which of them their
  case needs, and the reference already lists them all.
- Every value in it is one the setup uses. An option at its default
  value stays out.
- Comments say only what the file cannot: which files to create next
  to it and how, a trap such as `$` in a compose file.
- Keep credentials the way the docs recommend, in files rather than
  inline, so a copied example is a safe one.

## Wording

- No jargon. Replace it with what it means:
  - "the ticker" -> "the background fetch"
  - "folds it in" -> "commits it too"
  - "a large corpus" -> "many notes"
  - "headless deployment" -> "a server used only by scripts"
  - "what a request writes" -> "notes saved through the app"
- No informal abbreviations like "smth".
- "such as" already means the list is not complete; do not add "or
  something else".
- In a list of settings: `` `NAME=value` - text ``. A hyphen after the
  backticked value, not a period.
