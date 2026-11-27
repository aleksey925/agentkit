#!/usr/bin/env bash
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cache=${MEDIA_EXTRACT_CACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/agentkit/media-extract}
venv=$cache/venv
python_version=3.12

export HF_HOME=$cache/models
export UV_PYTHON_INSTALL_DIR=$cache/python

if [ $# -eq 0 ]; then
    echo "usage: media.sh transcribe|contact-sheet|key-frames <args>" >&2
    exit 2
fi

runnable() {
    case $1 in
        uv) uv --version ;;
        *) "$1" -version ;;
    esac >/dev/null 2>&1
}

# a tool installed in mise but not enabled here has a failing shim; rerun under
# `mise exec` with all its tools, since a shim left out fails inside it
if [ -z "${MEDIA_EXTRACT_VIA_MISE:-}" ] && command -v mise >/dev/null; then
    broken=0
    from_mise=()
    for tool in ffmpeg uv; do
        runnable "$tool" || broken=1
        if mise where "$tool" >/dev/null 2>&1; then
            from_mise+=("$tool")
        fi
    done
    if [ $broken -eq 1 ] && [ ${#from_mise[@]} -gt 0 ]; then
        MEDIA_EXTRACT_VIA_MISE=1 exec mise exec "${from_mise[@]}" -- bash "${BASH_SOURCE[0]}" "$@"
    fi
fi

missing() {
    echo "$1 - see \"Setup and the cache\" in the media-extract SKILL.md" >&2
    exit 1
}

runnable ffprobe || missing "ffprobe is not runnable"
runnable uv || missing "uv is not runnable"
encoders=$(ffmpeg -hide_banner -encoders 2>/dev/null) || missing "ffmpeg is not runnable"
# a minimal ffmpeg build without libwebp fails every frame grab, which the
# frame commands would read as the end of the video
[[ $encoders == *libwebp* ]] || missing "this ffmpeg has no libwebp encoder"

if [ "$1" != transcribe ]; then
    exec uv run --quiet --no-project --python "$python_version" "$here/media.py" "$@"
fi
shift

# a rebuilt machine can keep the venv folder but lose its interpreter, so
# probe the python rather than trusting the directory
if ! "$venv/bin/python" -c "import faster_whisper" 2>/dev/null; then
    echo "setting up $venv" >&2
    rm -rf "$venv"
    uv venv --quiet --python "$python_version" "$venv"
    uv pip install --quiet --python "$venv/bin/python" faster-whisper==1.2.1
fi

exec "$venv/bin/python" "$here/transcribe.py" "$@"
