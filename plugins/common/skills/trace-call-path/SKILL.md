---
name: trace-call-path
description: >-
  Use whenever the user asks where an error or a code path actually
  happens, or who owns it: "is this our bug or someone else's", "is
  this an external service's fault", "where does this break", "that's
  fine on our side, right?", "where does this handle get called from",
  "what calls what here". Applies at any scale - a single function, one
  backend, or a chain across several services. Traces the real call
  path through the code with file:line references instead of trusting
  the error text or the user's framing, and reports it as a call-chain
  diagram.
---

# Trace an error or call path

An error message (an HTTP error body, a stack trace, a log line) tells
you where something was *caught* or *observed*, not where it was
*caused*. Don't answer "is this our bug" or "where does this happen"
from the wording or from memory - treat it as a hypothesis to verify by
reading the actual code. Agreeing with a leading question ("so this
means X, right?") before checking is the main failure mode this skill
exists to prevent.

This applies at any scale:

- **inside one function/module** - which line/branch actually produces
  the value or raises the error.
- **frontend <-> backend** - which frontend call hits which backend
  route, and where that route's handler lives.
- **across several services** - a request crossing process/network
  boundaries, proxies, or auth layers.

Pick the right scale: don't launch subagents to trace a single-file
bug, and don't try to trace a multi-service chain by reading one file.

## Why this matters

A real example: a JWT parsing error appeared on a test stand during
template creation. The surface reading was "a remote service failed,
so we're fine." Tracing the actual code chain showed the "remote"
service was another deployment of the *same* team's own backend, and
the JWT was supposed to be attached by an internal egress proxy, not a
third party. Only the full trace revealed where the failure really
was - the quick answer would have been wrong. A different hostname,
process, or file is not proof of a different owner or cause.

## How to trace it

Walk the path hop by hop, using the real code (file paths, line
numbers, route/function definitions), not assumptions. Always cite
locations as a repo-relative path with the line number attached by a
colon (`src/foo/bar.py:120`, not just `bar.py` or "in the handler") -
that is the format editors and terminals recognize and turn into a
clickable jump, so the user can go straight there instead of searching.

1. **Entry point** - where the user/caller actually triggers this: a
   frontend action, an API call, a scheduled job. Find the exact
   `path:line`.
2. **Each handoff** - for a frontend call, the exact HTTP route
   (method + path) and the handler function's `path:line` that serves
   it. For a function call inside a backend, the exact function/method
   that gets called next, with its own `path:line`. Follow it however
   many hops it takes.
3. **Outbound calls** (when the path leaves the service) - the exact
   downstream call (class/method), the exact path it hits on the
   downstream host, and any special headers it sets (proxy/egress
   headers, auth client name headers) or deliberately does not set.
4. **Credential attachment** (for cross-service auth errors) - figure
   out who actually attaches the auth token: application code building
   a service-to-service token (verify it's wired into the live code
   path/middleware, not a dead/unused class that merely exists in the
   repo), a forwarded end-user token, or an infra-level proxy that
   injects it outside the app's own code.
5. **Ownership** (when more than one service/repo is involved) - check
   whether a downstream host is a genuine external/third-party system,
   or another deployment/module of the same team's own system. Check
   the project's CLAUDE.local.md sibling projects list and any local
   docs before calling something "external" - a different hostname is
   not proof of a different owner.

For a multi-hop or cross-service trace, independent hops are usually
independent research - delegate them to parallel subagents (Explore /
general-purpose, or forks) instead of tracing serially in the main
thread. For a single-file or single-function trace, just read the code
directly - no subagents needed.

## Reporting the result

Present the path as a short diagram, one hop per line, each hop
carrying its repo-relative `path:line` or `METHOD /path`, so the user
can jump straight to it (plain filenames or "in the handler" are not
enough - they don't resolve to a location in an editor):

```
[Frontend] src/components/TemplateForm.tsx:42
  -> [backend handler] POST /templates
     -> sfmc_notifications/template_manager/handler.py:974
  -> [outbound call] POST {tm_host}/api/v1/externals/pa/templates
     -> sfmc_notifications/repositories/notifications.py:161
  -> [component that broke] X  <- egress proxy (infra, not in repo)
  -> [downstream] template-manager
```

For a single-service or single-function trace, the same idea in
miniature - just the function/line chain, no need to force the
frontend/backend/downstream shape if it doesn't apply.

Follow the diagram with a short plain-language summary (a few
sentences, simple words, no filler) naming the exact `path:line` or
component responsible.

Only state a verdict like "this is not our bug" or "we're fine" after
the trace actually supports it. If the failure is inside the team's own
infrastructure or codebase (their own proxy, their own other
module/deployment, a different function in the same file), say that
plainly instead of calling it "someone else's problem" just because it
is a separate hop, file, or network boundary.
