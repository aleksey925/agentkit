#!/usr/bin/env bash
# Install the VHS toolchain for headless TUI demo recording.
# Reusable across apps. Target: Debian/Ubuntu container, arm64 or amd64.
# Requires: passwordless sudo, network, Go (for `vhs`).
set -euo pipefail

ARCH="$(dpkg --print-architecture)" # arm64 | amd64
case "$ARCH" in
  arm64) TTYD_ASSET="ttyd.aarch64" ;;
  amd64) TTYD_ASSET="ttyd.x86_64" ;;
  *) echo "unsupported arch: $ARCH" >&2; exit 1 ;;
esac

echo ">> apt: ffmpeg, chromium, fonts"
sudo apt-get update -y
# package name is `chromium` on Debian, `chromium-browser` on some Ubuntu
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  ffmpeg chromium fonts-jetbrains-mono fonts-noto-color-emoji fonts-dejavu-core \
  || sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
       ffmpeg chromium-browser fonts-jetbrains-mono fonts-noto-color-emoji fonts-dejavu-core

echo ">> ttyd (static binary - not packaged in Debian apt)"
mkdir -p "$HOME/.local/bin"
curl -fsSL -o "$HOME/.local/bin/ttyd" \
  "https://github.com/tsl0922/ttyd/releases/latest/download/${TTYD_ASSET}"
chmod +x "$HOME/.local/bin/ttyd"

echo ">> vhs (go install; lands in \$(go env GOBIN) when set, else GOPATH/bin)"
go install github.com/charmbracelet/vhs@latest

echo ">> chromium no-sandbox fix for headless container"
# Headless Chromium cannot create a sandbox namespace in a container and dies
# with "Failed to move to new namespace ... Operation not permitted".
# Debian's /usr/bin/chromium wrapper resets CHROMIUM_FLAGS="" (so exporting the
# env var is wiped) but sources /etc/chromium.d/* - so set the flags there.
if [ -d /etc/chromium.d ] || sudo mkdir -p /etc/chromium.d; then
  echo 'export CHROMIUM_FLAGS="$CHROMIUM_FLAGS --no-sandbox --disable-dev-shm-usage --disable-gpu --disable-software-rasterizer"' \
    | sudo tee /etc/chromium.d/00-vhs >/dev/null
fi

echo ">> versions"
GO_BIN="$(go env GOBIN)"; GO_BIN="${GO_BIN:-$(go env GOPATH)/bin}"
export PATH="$HOME/.local/bin:$GO_BIN:$PATH"
vhs --version
ttyd --version
ffmpeg -version | head -1
(chromium --version 2>/dev/null || chromium-browser --version 2>/dev/null) | head -1
echo ">> done. Add to PATH for the session:"
echo "   export PATH=\"\$HOME/.local/bin:$GO_BIN:\$PATH\""
