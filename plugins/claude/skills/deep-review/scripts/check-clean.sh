#!/bin/bash
# list uncommitted changes (staged, unstaged, untracked) - the review covers
# only committed branch work, so these would be left out of it
# usage: check-clean.sh
# prints one `git status --porcelain` line per path and exits 1 when anything
# is found; review progress files (*.progress.md) are skipped

set -e

# --untracked-files=all lists untracked files one by one: without it a plans dir
# holding only progress files shows up as one `?? docs/plans/` line and is not skipped
dirty=$(git status --porcelain --untracked-files=all | grep -v '\.progress\.md"\?$' || true)

if [ -n "$dirty" ]; then
    echo "$dirty"
    exit 1
fi
