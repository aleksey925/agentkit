#!/bin/bash
# run codex non-interactively and print its output
#
# the preset (default: $CODEX_PRESET, then "default") picks a model family and
# a reasoning effort; --model and --effort override the preset values.

set -e
# without pipefail a failed `codex debug models` that still printed a catalog
# would count as a successful lookup
set -o pipefail

usage="usage: run-codex.sh [--preset NAME] [--model SLUG] [--effort LEVEL] '<prompt>'"
fallback_effort=medium
preset="${CODEX_PRESET:-default}"
model=""
effort=""

require_value() {
    if [ $# -lt 2 ]; then
        echo "error: $1 needs a value" >&2
        exit 1
    fi
}

# one line per model: "<slug> <visibility> <priority> <levels>", where levels
# is ",low,medium," or "-" when the catalog does not list them
catalog_filter='.models[] | "\(.slug // error("model without slug")) \(.visibility // "-") \(.priority // 999999 | floor) \(if has("supported_reasoning_levels") then "," + (.supported_reasoning_levels | map(.effort) | join(",")) + "," else "-" end)"'

# succeeds when dotted version $1 is newer than $2 (an empty $2 is the oldest)
version_newer() {
    local newer older i a b
    IFS=. read -r -a newer <<<"$1"
    IFS=. read -r -a older <<<"$2"
    i=0
    while [ "$i" -lt "${#newer[@]}" ] || [ "$i" -lt "${#older[@]}" ]; do
        a="${newer[i]:-}"
        b="${older[i]:-}"
        if [ -z "$a" ]; then
            return 1
        fi
        if [ -z "$b" ] || [ $((10#$a)) -gt $((10#$b)) ]; then
            return 0
        fi
        if [ $((10#$a)) -lt $((10#$b)) ]; then
            return 1
        fi
        i=$((i + 1))
    done
    return 1
}

# fills the empty model and effort from $catalog; fails when no model is listed
pick_from_catalog() {
    local slug visibility priority levels version
    local best="" best_version="" top="" top_priority=""
    local version_re='^[0-9]+(\.[0-9]+)*$'
    if [ -z "$model" ]; then
        while read -r slug visibility priority levels; do
            if [ "$visibility" != list ]; then
                continue
            fi
            if [ -z "$top" ] || [ "$priority" -lt "$top_priority" ]; then
                top="$slug"
                top_priority="$priority"
            fi
            version="${slug#gpt-}"
            version="${version%-"$family"}"
            if [ "gpt-$version-$family" = "$slug" ] && [[ $version =~ $version_re ]] &&
                version_newer "$version" "$best_version"; then
                best="$slug"
                best_version="$version"
            fi
        done <<<"$catalog"
        if [ -z "$top" ]; then
            return 1
        fi
        model="${best:-$top}"
    fi
    if [ -z "$effort" ]; then
        effort="$preset_effort"
        while read -r slug visibility priority levels; do
            if [ "$slug" = "$model" ]; then
                case "$levels" in
                - | *",$preset_effort,"*) ;;
                *",$fallback_effort,"*) effort="$fallback_effort" ;;
                *) effort="" ;;
                esac
                break
            fi
        done <<<"$catalog"
    fi
}

while [ $# -gt 0 ]; do
    case "$1" in
    --preset)
        require_value "$@"
        preset="$2"
        shift 2
        ;;
    --model)
        require_value "$@"
        model="$2"
        shift 2
        ;;
    --effort)
        require_value "$@"
        effort="$2"
        shift 2
        ;;
    --*)
        echo "error: unknown option $1" >&2
        exit 1
        ;;
    *) break ;;
    esac
done

if [ $# -ne 1 ] || [ -z "$1" ]; then
    echo "error: $usage" >&2
    exit 1
fi
prompt="$1"

case "$preset" in
default)
    family=sol
    preset_effort=medium
    ;;
hard)
    family=astra
    preset_effort=xhigh
    ;;
*)
    echo "error: unknown codex preset '$preset' (known: default, hard)" >&2
    exit 1
    ;;
esac

# clean skip instead of a 127 "command not found" if codex is absent
if ! command -v codex >/dev/null 2>&1; then
    echo "codex not installed - skipping" >&2
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
if [ "${CODEX_NO_OVERRIDES:-}" = 1 ]; then
    ignored=""
    if [ -n "$model" ]; then
        ignored="--model"
    fi
    if [ -n "$effort" ]; then
        ignored="${ignored:+$ignored and }--effort"
    fi
    if [ -n "$ignored" ]; then
        echo "warning: CODEX_NO_OVERRIDES=1 - ignoring $ignored" >&2
    fi
else
    if [ -z "$model" ] || [ -z "$effort" ]; then
        lookup_error=""
        if ! command -v jq >/dev/null 2>&1; then
            lookup_error="jq not found"
        elif ! catalog="$(codex debug models </dev/null 2>/dev/null | jq -r "$catalog_filter" 2>/dev/null)" ||
            ! pick_from_catalog; then
            lookup_error="codex model lookup failed"
        fi
        if [ -n "$lookup_error" ]; then
            echo "warning: $lookup_error - skipping the codex model catalog" >&2
            effort="${effort:-$preset_effort}"
        fi
    fi
    echo "codex: model ${model:-<codex default>}, effort ${effort:-<codex default>}" >&2

    if [ -n "$model" ]; then
        args+=("-c" "model=$model")
    fi
    if [ -n "$effort" ]; then
        args+=("-c" "model_reasoning_effort=$effort")
    fi
    args+=(
        "-c" "stream_idle_timeout_ms=3600000"
        "-c" "project_doc=$HOME/.claude/CLAUDE.md"
        "-c" "project_doc=./CLAUDE.md"
    )
fi

# stdin redirected from /dev/null: codex exec reads stdin to append a
# <stdin> block even when a prompt arg is given, so an inherited open pipe
# (e.g. background launch) would block read_to_end forever. /dev/null gives
# immediate EOF; empty stdin is ignored when a prompt arg is present.
# exec so a kill on the background task reaches codex, not this wrapper shell.
exec codex "${args[@]}" "$prompt" </dev/null
