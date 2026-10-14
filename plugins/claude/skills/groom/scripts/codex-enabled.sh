#!/bin/bash
# decide whether the codex cross-review should run
# prints "yes" or "no" to stdout (always exits 0 so the caller can branch
# on the value, not on an exit code)
#
# the cross-review is skipped when:
#   - CODEX_ENABLED is set to a falsey value (0/false/off/no), OR
#   - the `codex` binary is not installed

case "${CODEX_ENABLED:-1}" in
0 | false | off | no | FALSE | OFF | NO)
    echo "no"
    exit 0
    ;;
esac

if command -v codex >/dev/null 2>&1; then
    echo "yes"
else
    echo "no"
fi
