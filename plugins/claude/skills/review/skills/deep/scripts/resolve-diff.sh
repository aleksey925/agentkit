#!/bin/bash
# resolve a review diff mode into a concrete git diff command
# usage: resolve-diff.sh <mode> [base]
#   modes: staged | unstaged | uncommitted | branch | auto
#   base:  branch to compare against (branch/auto modes); defaults to the
#          repository's detected default branch
# prints the git diff command to stdout; a short note about the chosen mode
# goes to stderr so stdout stays a clean, runnable command

set -e

mode="${1:-auto}"
base="$2"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

resolve_base() {
    if [ -n "$base" ]; then
        echo "$base"
    else
        bash "$SCRIPT_DIR/detect-branch.sh"
    fi
}

if [ "$mode" = "auto" ]; then
    if ! git diff --cached --quiet 2>/dev/null; then
        mode="staged"
    elif ! git diff --quiet 2>/dev/null; then
        mode="unstaged"
    else
        mode="branch"
    fi
    echo "auto-selected mode: $mode" >&2
fi

case "$mode" in
staged)      echo "git diff --cached" ;;
unstaged)    echo "git diff" ;;
uncommitted) echo "git diff HEAD" ;;
branch)
    # diff from the merge-base to the WORKING TREE (not ...HEAD): the fixer
    # leaves fixes uncommitted, so a commits-only range would hide them on
    # re-review. a concrete merge-base sha keeps the command stable across
    # iterations.
    b=$(resolve_base)
    mb=$(git merge-base "$b" HEAD 2>/dev/null || echo "$b")
    echo "git diff $mb"
    ;;
*)
    echo "error: unknown mode '$mode' (use staged|unstaged|uncommitted|branch|auto)" >&2
    exit 1
    ;;
esac
