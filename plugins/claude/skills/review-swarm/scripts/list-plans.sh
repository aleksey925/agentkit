#!/bin/bash
# list candidate plan files, one path per line: active plans in the plans dir
# plus archived ones in its complete/ subdir (where a finished plan is moved).
# the plans dir defaults to docs/plans and is overridable via
# REVIEW_SWARM_PLANS_DIR. excludes *.progress.md files. prints nothing when no
# plans exist.

set -e

plans_dir="${REVIEW_SWARM_PLANS_DIR:-docs/plans}"

for dir in "$plans_dir" "$plans_dir/complete"; do
    [ -d "$dir" ] || continue
    for f in "$dir"/*.md; do
        [ -e "$f" ] || continue
        case "$f" in
        *.progress.md) continue ;;
        esac
        echo "$f"
    done
done
