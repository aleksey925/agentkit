#!/bin/bash
# resolve where the review progress file should live
# usage: progress-path.sh [plan-file]
#   with a plan file:    <plan-dir>/<plan-name>.progress.md (next to the plan,
#                        so an archived plan in complete/ keeps its sidecar there)
#   without a plan file: <plans-dir>/review-<runid>.progress.md (unique per run)
# the plans dir defaults to docs/plans, override via DEEP_REVIEW_PLANS_DIR. the
# unique run id keeps concurrent plan-less reviews from sharing one file. prints
# the resolved path to stdout; does not create the file.

set -e

plan="$1"
plans_dir="${DEEP_REVIEW_PLANS_DIR:-docs/plans}"

if [ -n "$plan" ]; then
    dir=$(dirname "$plan")
    base=$(basename "$plan")
    name="${base%.*}"
    echo "$dir/$name.progress.md"
else
    runid="$(date '+%Y%m%d-%H%M%S')-$$"
    echo "$plans_dir/review-$runid.progress.md"
fi
