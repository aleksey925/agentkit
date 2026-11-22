---
name: writing-readmes
description: >-
  Rules for a project README and other pages for the people who install, run or
  configure a project. Use whenever you create, rewrite, extend, fix or review
  a README.md, even for a small change: a new setting, an install step, an
  example command, a note on a feature. Also use it when a code change adds or
  changes something the README describes. For an app (server, CLI, TUI) it also
  sets the order and content of the sections. Not for CLAUDE.md or design docs.
---

# Writing READMEs

A README is read by someone who wants to install, run or configure the project.
Every paragraph answers their question: "is this about me, and what do I do?"
It is not the place to explain how the code is built.

The skill goes from the whole README to single sentences: what to leave out,
how to work, the structure, where each fact lives, how to write each kind of
element, the language, and the checks before you finish.

## What to leave out

### Design rationale

Why the code is built this way belongs in the project's `CLAUDE.md` or design
docs, not in the README. Keep a "why" only when it changes what the reader
does.

Signs of rationale: "rather than", "is written down rather than derived", "for
the same reason", "deliberately does not", "would otherwise", a reason about a
future change or about another part of the code.

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

### Inner workings

Name a mechanism only when the reader does something with it: sets it up, sees
it, checks it, or fixes a problem by it. Leave out the rest.

- Keep: "`TRUSTED_PROXY=true` - scrawl then takes the user's address from the
  `X-Forwarded-For` header". The reader sets up the proxy to send that header.
- Keep: "a fetch is followed by a fast-forward and nothing else: scrawl never
  merges". A reader who knows git sees at once what happens when the remote has
  moved on.
- Leave out: "the check is a trial merge and not a commit count". The reader
  does nothing with it; "it compares content, not commits" is enough.

### Notes on unreleased changes

The README describes the current release. A rename or a removal made on a
branch that is not merged, or between dev builds, gets no note on the old name:
nobody runs that name yet. "Up to v0.6.0-dev16 this setting was `APPS_URL`" was
written about a setting renamed on an unmerged branch. A note on an old name
belongs only to a change that breaks a released version, and it goes in the
release notes, not the README.

### What the reader can guess

Describe only what the reader cannot guess. A Back button that goes back needs
no line.

## How to work

- **New README or a full rewrite.** For an app, read the example in
  [Structure of an app README](#structure-of-an-app-readme) first, then follow
  the order of sections there.
- **Extending or fixing a part.** Change that part only. Keep the structure and
  the names the README already has, unless the user asks to change them. Apply
  the rules below to the text you write, and run
  [Before finishing](#before-finishing) on it.
- **Review.** Check the text against the rules below and the list in
  [Before finishing](#before-finishing).

In every case, find a fact in the code before you write it: a default, a limit,
a command, a flag name, a path, the default state of a checkbox.

- A rewrite can make a true sentence false. "A credential is named, never
  written down inline" was about the config file. Shortened to "the token is
  never written into the settings", it became false: one environment variable
  holds the token directly.
- An old README goes stale: an example still used `--gen-hash` after the
  command became `hash`.
- Replace vague words with the value you found: "the editable size cap" becomes
  "up to 2MB", "a run of failures" becomes "10 wrong passwords".
- Name the exact thing that was checked (`localStorage`), not a wider word
  ("data") that also covers what was not.
- Steps in the UI of another product (a cloud console, a DNS provider) cannot
  be checked in the code, and that UI changes. Do not write them from memory:
  ask the user for the current menu path, or say plainly that the steps were
  not checked.
- A limit of a browser or an OS needs a source: the project's notes of what was
  seen (in scrawl, `docs/quirks.md`) or a run. A line with neither goes, above
  all one that says "likely". "Safari on macOS likely cannot open mini apps"
  had no source, and the user opened one in Safari at once.

## Structure of an app README

This order is for an app: something people install and run, such as a server, a
CLI or a TUI. A library has other needs (how to call it from code, an API
reference), so do not force this order on it.

`SKILL_DIR/references/app-readme.md` is a full README written this way, for
scrawl, a notes web app. Read it before you write or restructure the README of
an app, and match its tone and level of detail.

Sections, in this order. Leave out a section the app has nothing for.

1. **Title, badges and one line** saying what the app gives: "Markdown notes in
   any browser, from a folder or a git repository." See [Badges](#badges).
2. **Intro**: one short paragraph on what the reader can do with it and the
   main idea that sets it apart, then one line on how it ships: "one static
   binary or a Docker image". Right after it, the main picture, see
   [Main picture](#main-picture).
3. **Features**: a list, each item a bold name and what it gives the user, in
   one or two lines. What it gives, not how it is built.
4. **Why <app>**: the problem the app was made for; a fair comparison with the
   best-known tool for the same job, with facts; and "When something else fits
   better", which says plainly what the app does not do. This is about the
   reader's choice of tool, not the design rationale the README leaves out.
5. **Contents**: a table of contents between `<!-- toc -->` and
   `<!-- tocstop -->`. Update it when a heading changes.
6. **Quick start**: a few ready-to-paste runs, from the safest to the full
   setup. The first one changes nothing on the reader's machine (in scrawl:
   read-only, no history, no sign-in, `--rm`). Name each by what the reader
   wants: "Look at your notes", "Use local folder". Under each command, a short
   list explains every setting in it the reader would not guess, so they can
   understand the run without scrolling down.
7. **Installation**: one subsection per way to get it (Docker, a package
   manager, from source), and nothing else: no section on how to run it. Link
   to Quick start and Configuration instead of repeating them.
8. **A section per feature** that needs more than its line in Features: what
   the user sees, its limits, how to turn it off. Name it from the user's side:
   "How your changes are kept", "Offline". See
   [Feature sections](#feature-sections).
9. **Configuration**: first the terms the reader needs (in scrawl, what a space
   is) and the kinds of settings, then tables of
   `variable | required | default | meaning`, grouped by case (server settings,
   one space, several spaces).
10. **A section per advanced setup** that needs more than a few settings (in
    scrawl, a git repository as a space): how it behaves, what to keep safe,
    what to do when it goes wrong.
11. **API**: how to get a token, ready `curl` calls, the rules a client has to
    follow, each error code with what to do about it, and a table for the
    remaining endpoints.
12. **Command line**: one block with every command and a short note on the same
    line.
13. **License**: one link.

The order goes from "what is it, and is it for me?" to "let me try it", then
install, use, configure, and connect from scripts. A reader can stop as soon as
they have what they need.

## Each fact has one home

Put a fact next to the thing it explains, and say it once. A reader looks for
it there, and two copies drift apart.

- An install section holds the ways to install, and nothing else. How to run is
  in Quick start, what a setting means goes beside that setting.
- A note on a value goes under its table: how to hash a password belongs beside
  `AUTH_USERS`, the list of users who can sign in, not in the install steps.
- A note on a requirement goes beside what it requires: "the folder has to be
  writable for uid 1001" belongs beside the folder setting.
- A note under a Quick start command is not a second copy. It says in a line or
  two what the setting does in this run. All its values, its default and when
  to set it stay in Configuration.
- Before adding a paragraph, check that a later section does not say it
  already. A term explained in the install section and again at the start of
  the configuration section is one fact in two places.

## Feature sections

A limit of a feature on one platform is a limit, not part of the main idea: it
goes in the feature's list of limits, not in its intro. Write it as case,
effect and reason, so the reader sees why the app acts differently there and
what they keep: "In Safari, Run opens the app in a new tab. Inside a page of
the app, Safari keeps the app's `localStorage` only in memory, so what it saved
is lost once Safari closes."

### Main condition and limits

The first sentence of a feature says what it gives and the condition the reader
must meet, together. A condition left for the list below gets missed. "A mini
app opens with no network, but only after you have run it once with a network
in that browser" - not "opens with no network" with the first run as the third
item.

- **A limit of one mode lives in that mode's section.** That mini apps are not
  kept offline on your machine is said in "On your machine"; "With no network"
  does not repeat it. A reader of another mode skips it there.
- **No setup in a feature section.** How to set up the server and its settings
  is in the setup sections. "If scrawl runs on a server with `MINI_APPS_URL`
  and Offline access is on" at the start of "With no network" repeats them and
  hides what the feature gives.
- **No excuse for a limit.** "On your machine a mini app is not kept, but there
  you do not need it" reads as an excuse. State the limit, or drop it if the
  mode's section has it.
- **No workaround the README calls unsafe.** Offering `scrawl.localhost` to
  keep mini apps offline, while "On your machine" says not to use it with a
  password, gives the reader two opposite answers.
- **Screen text is for a troubleshooting entry.** In a feature description the
  condition is enough; "Before that, Run with no network shows `...`" added
  nothing once the first sentence named the condition.
- **No reason from inside the code**: "the browser treats the mini app as
  another site and gives scrawl's worker no cookie" goes. The reader does
  nothing with it.

Bad - technical, a mode's limit in the shared section, an unsafe workaround:

```
With Offline access on, a mini app opens with no network once it ran with one,
and keeps the data it saved in the browser.

- The whole folder of the mini app is kept, not files from other sites such as
  a CDN.
- Inside scrawl, it works where scrawl and the mini app are on one site: a
  domain with `MINI_APPS_URL`, or locally `http://scrawl.localhost:7272`, which
  is not safe with a password, see On your machine. At `127.0.0.1` and
  `localhost` the mini app runs inside scrawl but is not kept there, and with
  no network Run shows `This browser does not keep this mini app for offline
  use.`: there the browser treats the mini app as another site and gives
  scrawl's worker no cookie. In a new tab it is kept.
```

Good:

```
If Offline access is on, a mini app opens with no network too, with the data it
saved, but only after you have run it once with a network in that browser.

- Only the files in the mini app's folder are kept. What it loads from the
  internet, such as a library from a CDN, is not, so such a mini app may not
  work with no network.
- A mini app with a service worker of its own decides itself what to keep.
```

### Section about safety

A section such as "How your changes are kept" tells the reader what they can
rely on. Open it with one line that says what is promised: "scrawl makes sure a
change is not lost and does not overwrite another one". Start each item with
what the reader gets, then one plain sentence on when it matters. The way it is
done stays out.

Bad - the mechanism is the point:

```
- **When you save**, the note is written to a temporary file and renamed
  into place, so a crash never leaves half a note behind.
```

Good:

```
- **A save is all or nothing**: if the server stops in the middle, the note
  stays as it was.
```

### Feature with several setups

When a feature works differently by where or how the app runs, give each mode a
heading of its own, named from the reader's side: "On your machine", "On
server", "With no network". Under each: how to start it, what the reader gets,
what does not work and the fix. Do not sort the cases of all modes into shared
lists such as "works", "works with a setting", "does not work": the reader then
has to pick their own case out of every list.

- The intro of the feature says only what holds in every mode, then a short
  list of the modes with a link and a few words each. A default that belongs to
  one mode, such as the local host apps run on, goes in that mode.
- Describe the general requirement first, then a product as one example. "On
  server, apps run behind any proxy with https, such as nginx, Caddy or
  Cloudflare Tunnel", then what any proxy needs, then a link to a subsection
  with the Cloudflare steps. A text that names one product at the start reads
  as if it were the only way.

## How to write each element

### Setting: case, effect, reason

Write each description in this order:

1. **The case.** When does the reader need it? "If the app runs behind a
   reverse proxy, set:". A reader whose case it is not skips the rest.
2. **The technical effect.** What the setting does, in mechanical terms: which
   header it reads, which flag it sets, which file it writes. Many readers
   understand the mechanism faster than an explanation.
3. **The reason.** What goes wrong without it, in one or two sentences. Be
   concrete: real numbers, the symptom the reader would see.

Do not mix the three. A paragraph that starts with a reason, puts the setting
in the middle and the condition at the end makes the reader put it together.

Each part is needed:

- an effect without the case leaves "do I need this?";
- a reason without the effect leaves "and so what?" - "the browser then sends
  the cookie only over HTTPS" does not say what the setting does;
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

### Setting in a table

In a table the order changes: the reader finds a row by the name of the
setting, not by their case. So the cell says first what the setting does and
what every value means, then when to pick a value and why. The cell is short,
but it still covers every value. "`Secure` flag of the session cookie; `always`
behind an HTTPS proxy" leaves `auto` and `never` unexplained. Better:

```
`Secure` flag of the sign-in cookie: `auto` sets it when the request
came over HTTPS, `always` always, `never` never
```

For `WATCH`, which says how the app finds files changed outside it:

```
how changes made outside scrawl are found: `auto` - the system reports
them, plus a rescan every `RESCAN`; `poll` - the rescan only. Use `poll`
for a network share: the system does not report changes made there from
another machine
```

### Error the reader sees

Write it as what they see, why, and what to do:

1. The exact text on the screen, in backticks. Quote it as the program prints
   it, even when the README now calls the thing by another name.
2. The cause in plain words, and when it happens.
3. The action that fixes it.

Bad - the mechanism first, and three ideas in one sentence:

```
Right after Run the frame says `To use this app, sign in to scrawl and open
it from there`: the browser did not keep the app's cookie inside the frame.
"Open in a new tab" works.
```

Good:

```
If you see `To use this app, sign in to scrawl and open it from there` right
after Run, your browser blocks the app inside scrawl. This can happen when scrawl runs on your computer and
the browser has strict privacy settings. Press "Open in a new tab" at the
top: the app opens in a new tab and works there.
```

### Warning about a risk

A warning says what to do, for whom, and what can happen otherwise. Most are
about a rare case, so keep it to a few sentences, but do not cut it so short
that the reader cannot see why.

1. **The action first**: "Open scrawl at `http://127.0.0.1:7272`, not at
   `localhost`".
2. **The default it depends on**, if the text has not said it yet. A warning
   about `localhost` means nothing until the reader knows that mini apps run at
   `app-<id>.localhost` by default.
3. **The case**, named by what the reader set up: "If scrawl has a password".
   "If scrawl asks for a password" read as unclear.
4. **What can happen, and what cannot**, in the reader's words: "could sign you
   out or sign you in as another user. It cannot read your notes". Not the
   code's words ("neighbor names", "cookie tossing").
5. **How rare it is**: if it takes something made to do harm, say so: "a mini
   app written to do harm could ... A usual mini app does nothing like this".

Do not make it sound worse than it is: "unauthorized access" for an app that
can only switch the sign-in scares the reader for nothing. Before calling a
case too rare to mention, check whether the README's own Quick start leads into
it: the scrawl case is the local run with a password, which is the second Quick
start run.

Bad - the reader cannot tell why, nor how serious it is:

```
- With a password, open scrawl only at `127.0.0.1`. At `localhost` or
  `scrawl.localhost` a mini app can sign you out, or into another account.
```

Good:

```
Nothing to set. Open scrawl at the link it prints at start,
`http://127.0.0.1:7272`, not at `localhost`. In this setup the names under
`localhost`, such as `app-<id>.localhost`, belong to mini apps. If scrawl has a
password and is opened at `localhost` too, a mini app written to do harm could
sign you out of scrawl or sign you in as another user. A usual mini app does
nothing like this.
```

### Main picture

One picture right after the intro, not a set of screenshots: one screen of the
app on a desktop and on a phone at once. In scrawl it is one note in a browser
window, with a phone on the right that overlaps the window a little and shows
the same note.

- **The screen**: the main one, with a page that shows several features at
  once. The scrawl note has a task list, a Gantt chart, a diagram and a table.
- **Frames**: draw a frame around each shot so it reads as a real device: a
  window with a title bar and an address, a phone with its status bar. On the
  phone, show the app as it looks installed to the home screen, if it can be
  installed.
- **Content**: everything on the screen looks like real use, the sidebar too.
  The tree shows folders such as `projects`, `databases`, `reference`, not test
  words or folders like `showcase/`. If the project has sample data (in scrawl,
  `examples/data`), make it look real and shoot it. Otherwise make up content
  for the shot and keep it out of the repository unless asked.
- **Both themes**: two files, light and dark. `<picture>` shows the one that
  matches the reader's GitHub theme:

  ```
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/screenshots/hero-dark.webp">
    <img alt="..." src="docs/screenshots/hero-light.webp">
  </picture>
  ```

- **A script makes it**: it starts the app on the sample data, takes the shots
  with a headless browser and puts them into the frames. After a change in the
  UI the picture is made again with one command, both themes alike. In scrawl:
  `make readme-promo`, the script in `scripts/readme-shots/`.
- **Format**: `.webp`. Shoot the desktop at 2x and the phone at 3x. The picture
  is about 2400px wide and about 120KB a file.
- **Alt text** says what the picture shows: "One note with a diagram, a chart,
  a table and a task list, on a laptop and on a phone".
- The pictures get a folder of their own, such as `docs/screenshots/`. If the
  project's `CLAUDE.md` lists its folders, add it there.

### Badges

A few badges in a row under the title, before the one line: the release, the
license, the language, how it ships (Docker), and a platform feature the reader
cares about (PWA). All in one style:

- `style=for-the-badge` and the same dark `labelColor=18191D` on every badge.
- A badge with a value (release, license) gets a color for the value.
- A badge with no value is only a name on the dark color, with the logo in the
  brand's color: `logoColor=00ADD8` for Go.
- A badge links to what it names: the release to the latest release, the
  license to `LICENSE`, Docker to the install section. A badge with nothing to
  open has no link.

```
[![Release](https://img.shields.io/github/v/release/aleksey925/scrawl?style=for-the-badge&labelColor=18191D&color=2f80ed)](https://github.com/aleksey925/scrawl/releases/latest)
[![License](https://img.shields.io/github/license/aleksey925/scrawl?style=for-the-badge&labelColor=18191D&color=464A54)](LICENSE)
![Go](https://img.shields.io/badge/Go-18191D?style=for-the-badge&logo=go&logoColor=00ADD8)
[![Docker](https://img.shields.io/badge/Docker-18191D?style=for-the-badge&logo=docker&logoColor=2496ED)](https://github.com/aleksey925/scrawl/#docker)
![PWA](https://img.shields.io/badge/PWA-18191D?style=for-the-badge&logo=pwa&logoColor=A97BFF)
```

### Lead-in before a block

A sentence before a command or an example describes all of it or none of it.
"Give it the path to your notes folder:" above a command with five settings
explains one of them and reads as odd. Better: "Run this in a folder of
markdown files:", with a list under the command for the settings.

### Configuration example

An example file (`docker-compose.yml`, a sample config) shows one setup that
several people would really run, advanced if that is what real use looks like.
It is not the settings reference again.

- No commented-out options. A reader cannot tell which of them their case
  needs, and the reference already lists them all.
- Every value in it is one the setup uses. An option at its default value stays
  out.
- Comments say only what the file cannot: which files to create next to it and
  how, a trap such as `$` in a compose file.
- Keep credentials the way the docs recommend, in files rather than inline, so
  a copied example is a safe one.

## Language

### One name for one thing

- Call the project by its name, never "the app", above all when the README also
  describes apps or other things a reader could call that: "the same reader as
  scrawl", "scrawl runs as uid 1001".
- Pick one word for each thing and keep it in the whole README: the feature
  ("mini app", not "HTML app", "small app" and "app" by turns), the place it
  shows in ("inside scrawl", not "a frame", "the run screen" and "a page of
  scrawl"). Define a new term in the first sentence of its section: "A mini app
  is a `.html` file of your notes that runs inside scrawl."
- Leave the words of the code out: frame, run screen, ticket, "the cookie
  inside the frame". Say what the reader sees: "inside scrawl", "opens in a new
  tab".
- Write the names of a UI as they appear, in backticks, joined by `->`:
  `Networking` -> `Tunnels`.
- When a new name is needed, offer the user a few options with what speaks for
  and against each. A name that differs from the screen and the settings means
  changing them too, or a README that says one thing and a screen another.

### Wording

- Write for a reader at about B1 English: short sentences, one idea in each,
  common words, "you" for the reader.
- No jargon. Replace it with what it means:
  - "the ticker" -> "the background fetch"
  - "folds it in" -> "commits it too"
  - "a large corpus" -> "many notes"
  - "headless deployment" -> "a server used only by scripts"
  - "what a request writes" -> "notes saved through the app"
- No informal abbreviations like "smth".
- Headings have no articles: "On server", "From source", "Webhook instead of
  polling".
- "such as" already means the list is not complete; do not add "or something
  else".
- In a list of settings: `` `NAME=value` - text ``. A hyphen after the
  backticked value, not a period.
- A list with one item is a sentence.
- To make a paragraph shorter, keep every fact and cut the words around them:
  join sentences that say one thing, drop lead-ins such as "Out of the box, ...
  only through", and let examples after a colon stand for a list of ways. A
  paragraph on Obsidian went from 160 words to 110 with nothing lost.

## Before finishing

Run these checks on the text you wrote or changed, and in a review on the text
you review. Each one is an action, not a box to tick.

- Read the whole section you touched, not only your own lines. Another session
  or a review fixer may have written a line that breaks these rules: a note on
  a dev build came in with "fix code review findings", and a copy of the README
  carried it on.

- Every fact is found in the code: defaults, limits, commands, flags, paths.
- Every number is counted: "the messages tell four things apart" stood over a
  list of six.
- Every `#anchor` link matches a heading, and Contents matches the headings. A
  renamed heading breaks the links to it, and nothing warns about that.
- A term you removed or renamed is gone from the whole README. A sentence
  elsewhere may still lean on it: after "neighbor names" left one section,
  another still said "which with a password is a neighbor name, see ...".
- Every example you can run is run: load a sample config with the project's own
  parser, run a sample command. A key the parser refuses is a broken example.
- Say plainly which parts were not checked: an example that cannot run here,
  steps in the UI of another product.
