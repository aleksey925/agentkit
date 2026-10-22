#!/bin/bash
# stage the given files and commit only them
# usage: stage-and-commit.sh <message> <file1> [file2 ...]

set -e

if [ $# -lt 2 ]; then
    echo "error: usage: stage-and-commit.sh <message> <file1> [file2 ...]" >&2
    exit 1
fi

msg="$1"
shift

# an empty path must be rejected here: as a git pathspec it matches everything under
# the current directory, so it would silently commit the whole tree instead of failing
for arg in "$@"; do
    if [ -z "$arg" ]; then
        echo "error: empty file argument" >&2
        exit 1
    fi
done

# :(literal) so a name holding '*', '?' or '[...]' matches itself, not other files
listed=()
for path in "$@"; do
    listed+=(":(literal)$path")
done

git add -- "${listed[@]}"
git commit -m "$msg" -- "${listed[@]}"

# a path-scoped commit runs hooks against a temporary index, so anything a
# pre-commit hook staged never reaches the real index. reset every path the
# commit recorded, or an unlisted one would sit there as a staged deletion.
# :(top) because diff-tree prints root-relative paths and a pathspec resolves
# from the current dir
committed=()
while IFS= read -r -d '' path; do
    committed+=(":(top,literal)$path")
done < <(git diff-tree --no-commit-id --name-only -r --root -z HEAD)
if [ ${#committed[@]} -gt 0 ]; then
    git reset -q -- "${committed[@]}"
fi
