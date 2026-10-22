#!/bin/bash
# resolve the committed branch work under review into a git diff command
# usage: resolve-diff.sh [base]
#   base: branch to compare against; defaults to the repository's detected
#         default branch
# prints the git diff command to stdout

set -e

base="$1"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -z "$base" ]; then
    base=$(bash "$SCRIPT_DIR/detect-branch.sh")
fi

mb=$(git merge-base "$base" HEAD)
echo "git diff $mb HEAD"
