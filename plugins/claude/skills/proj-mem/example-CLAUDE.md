## What this is

kafka-tui is a terminal client for Apache Kafka in the spirit of k9s. It lets
developers browse topics, produce messages, and inspect consumer groups
without leaving the shell.

## Design decisions

### Reference UX: k9s

The app's UX is largely modeled on k9s - navigation flow, modal browsing, and
shortcut conventions. Where a k9s shortcut maps cleanly to a Kafka concept, we
reuse it; where there is no direct analogue, we follow the same shape
(single-letter actions in browse contexts, capitals for mutating variants,
`ctrl+` only when a modifier is genuinely needed) rather than invent a new
style.

### Single source of behavior

When a behavior must be uniform across the app (edit semantics, paste
sanitization, global key handling, etc.), it lives in one shared place that
all consumers route through. New screens and inputs reuse that
implementation rather than re-deriving it.

Why: the contracts described below hold by default, not by discipline. If
every screen had to re-implement edit or paste handling, the contract would
drift the moment somebody forgot a detail. Implementation form is not
prescribed (shared module, common base, component wrapper - whatever fits);
the rule is that there is exactly one implementation and everything goes
through it.

### Reserved global shortcuts

*Applies the single-source rule above: one dispatcher owns these keys; no
screen rebinds them locally.*

A fixed set of keys is owned by the host dispatcher and not rebindable by
screens: `ctrl+c` (quit), `:` (command bar), `/` (filter prompt), `?`
(help), `ctrl+r` (refresh-interval picker).

Deviation: when the active screen has an overlay (e.g. a modal form), a
global is skipped if its action does not apply in that context. The key
falls through to the overlay instead of firing a no-op global - that's how
the picker's own `esc` closes it without the dispatcher trying to remount
one on top.

### Compound shortcuts via popup menus

Where a screen-level action has 2-5 close variants (e.g. copy: record /
key / value / headers; or seek: latest / earliest / from offset / …), we
don't burn a separate key per variant or hide them behind a chord prefix.
The entry key opens a popup menu listing every variant, each with a
digit shortcut (1-N).

Why: the popup is **discoverable** - new users navigate with arrows +
Enter and see every variant labeled - and **fast** - experienced users
get chord-level speed because the digit confirms in a single keypress
(`c` then `2` to copy the key). One key learnt at the screen level, not
N keys scattered across actions.

How to apply: when an action splits into a small fixed set of variants
and a clean one-letter mapping per variant isn't obvious (or clashes
with existing keys like j/k/h navigation), route through the shared
menu component from the screen's entry shortcut. While the popup is
open it owns the input stream - the screen's own bindings are suspended
until the menu confirms or cancels.

## Project commands

- `make build` - build the binary into `dist/`
- `make lint` - run formatters and linters
- `make test` - run the test suite
- `make race` - run tests with the race detector
- `make deps` - refresh `go.mod` and the vendored deps
