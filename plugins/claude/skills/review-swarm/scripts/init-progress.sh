#!/bin/bash
# initialize (overwrite) the progress file with a header
# usage: init-progress.sh <progress-file> [plan-path] [context]
# the plan path is optional; reviews often run with no plan at all
# the context is optional free text (provided and/or session-inferred intent)
# recorded in the header so external reviewers and later phases can read it

set -e

file="$1"
plan="${2:-(none)}"
context="$3"

if [ -z "$file" ]; then
    echo "error: usage: init-progress.sh <progress-file> [plan-path] [context]" >&2
    exit 1
fi

mkdir -p "$(dirname "$file")"

{
    echo "# review progress"
    echo "Plan: $plan"
    [ -n "$context" ] && echo "Context: $context"
    echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "---"
} > "$file"

echo "$file"
