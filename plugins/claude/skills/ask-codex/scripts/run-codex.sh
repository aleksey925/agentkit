#!/bin/bash
# run a codex consultation and return output
# usage: run-codex.sh "<prompt>"
# outputs codex response to stdout

set -e

prompt="$1"
if [ -z "$prompt" ]; then
    echo "error: usage: run-codex.sh '<prompt>'" >&2
    exit 1
fi

# clean skip instead of a 127 "command not found" if codex is absent
if ! command -v codex >/dev/null 2>&1; then
    echo "codex not installed - skipping consultation" >&2
    exit 0
fi

# codex's sandbox uses bubblewrap, which needs unprivileged user namespaces.
# in an externally-sandboxed env (e.g. a container that blocks userns) bwrap
# can't start, so any --sandbox mode other than danger-full-access fails. probe
# the actual capability rather than guessing from /.dockerenv - the kernel
# sysctls can claim userns is allowed while seccomp still blocks it.
if [ -n "${CODEX_SANDBOX:-}" ]; then
    sandbox_args=("--sandbox" "$CODEX_SANDBOX")
elif command -v unshare >/dev/null 2>&1 && ! unshare -Ur true 2>/dev/null; then
    sandbox_args=("--dangerously-bypass-approvals-and-sandbox")
else
    sandbox_args=("--sandbox" "read-only")
fi

args=("exec" "${sandbox_args[@]}")

# -c overrides switch provider routing in a way some corporate codex
# proxies / wrappers reject (e.g. "Error: Model provider 'responses' not
# found"). Set CODEX_NO_OVERRIDES=1 to skip the overrides and fall through
# to the proxy's defaults. Only the literal value `1` activates suppression.
if [ "${CODEX_NO_OVERRIDES:-}" != 1 ]; then
    args+=(
        "-c" "model=${CODEX_MODEL:-gpt-5.6-sol}"
        "-c" "model_reasoning_effort=${CODEX_EFFORT:-high}"
        "-c" "stream_idle_timeout_ms=3600000"
        "-c" "project_doc=$HOME/.claude/CLAUDE.md"
        "-c" "project_doc=./CLAUDE.md"
    )
fi

# stdin redirected from /dev/null: codex exec reads stdin to append a
# <stdin> block even when a prompt arg is given, so an inherited open pipe
# (e.g. background launch) would block read_to_end forever. /dev/null gives
# immediate EOF; empty stdin is ignored when a prompt arg is present.
codex "${args[@]}" "$prompt" < /dev/null
