#!/usr/bin/env bash
# Run the real Ikemen GO engine against this repo, on a Linux box with no root,
# no GPU and no display.
#
# The game itself does not ship an engine: docs/INSTALL.md tells you to drop a
# build beside it. That makes "does the Developer Keys screen actually open?"
# impossible to answer on a headless machine unless you build the whole stack, so
# this script does exactly that, without root:
#
#   * resolves the X/GL library closure through apt --print-uris (no install),
#     downloads those .deb files and unpacks them into a private sysroot
#   * runs Xvfb on a virtual display, software-rendered by Mesa llvmpipe
#   * downloads the official Ikemen GO Linux release and points it at this repo's
#     data/, chars/, stages/, font/, sound/ and external/ by symlink
#   * drives the game with xdotool and writes PNG captures of the screen
#
# Xvfb shells out to a hard-coded /usr/bin/xkbcomp, which we cannot create
# without root, so the virtual display is started inside `unshare -r -m` with an
# overlay mount on /usr/bin. That needs unprivileged user namespaces; the script
# says so plainly if the kernel refuses.
#
# Usage:
#   bash tools/engine_linux.sh --script tools/engine_drive/keys.txt --out artifacts/engine
#
# The drive script is one command per line:
#   wait 18          pause for N seconds
#   key Return       send a key (xdotool syntax, e.g. Return, Down, Escape, ctrl+F1)
#   shot name        capture the screen to <out>/name.png
#   log              print the engine's log so far
#
# Everything lands in ${IKEMEN_STACK:-/tmp/ikemen-stack}, which is disposable: the
# stack is rebuilt from the network on a fresh machine.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STACK="${IKEMEN_STACK:-/tmp/ikemen-stack}"
SYSROOT="$STACK/sysroot"
ENGINE="$STACK/engine"
# The nightly, not a tagged release: docs/INSTALL.md and the release workflow both
# pull releases/download/nightly, and the bundled screenpack targets it. A tagged
# build starts the attract-mode demo and dies with "Invalid data: inrunstate".
ENGINE_TAG="${IKEMEN_ENGINE:-nightly}"
ENGINE_ARCHIVE="${IKEMEN_ARCHIVE:-Ikemen_GO-dev-linux.zip}"
ENGINE_URL="https://github.com/ikemen-engine/Ikemen-GO/releases/download/${ENGINE_TAG}/${ENGINE_ARCHIVE}"
OUT="$ROOT/artifacts/engine"
SCRIPT=""
DISPLAY_NUM="${IKEMEN_DISPLAY:-:99}"

# Packages the engine and the virtual display need. The engine links GTK for its
# file dialogs, ALSA/Pulse for sound and Wayland/EGL for display fallbacks, so
# even an X11 run needs all of them present.
PACKAGES=(
  xvfb x11-xkb-utils xkb-data x11-apps xdotool libxdo3
  libgl1 libglx-mesa0 libgl1-mesa-dri
  libgtk-3-0t64 libasound2t64 libpulse0 libxss1
  libwayland-egl1 libwayland-client0 libwayland-cursor0 libdecor-0-0
)

say() { printf '%s\n' "$*"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --script) SCRIPT="$2"; shift 2 ;;
    --out)    OUT="$2"; shift 2 ;;
    --reset)  rm -rf "$STACK"; shift ;;
    -h|--help) sed -n '2,40p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) say "unknown argument: $1"; exit 2 ;;
  esac
done

mkdir -p "$OUT"
# absolute, because the session script changes directory into the engine
OUT="$(cd "$OUT" && pwd)"

# ---------------------------------------------------------------- dependencies
build_sysroot() {
  say "building a private sysroot in $SYSROOT (no root needed)"
  local aptdir="$STACK/apt"
  mkdir -p "$aptdir/lists/partial" "$aptdir/cache/archives/partial" \
           "$aptdir/etc" "$aptdir/empty" "$STACK/debs" "$SYSROOT"
  printf 'deb http://archive.ubuntu.com/ubuntu noble main universe\ndeb http://archive.ubuntu.com/ubuntu noble-updates main universe\n' \
    > "$aptdir/etc/sources.list"

  local apt=(apt-get
    -o Dir::Etc::sourcelist="$aptdir/etc/sources.list"
    -o Dir::Etc::sourceparts="$aptdir/empty"
    -o Dir::State::Lists="$aptdir/lists"
    -o Dir::Cache="$aptdir/cache"
    -o Dir::State::status=/var/lib/dpkg/status
    -o Acquire::Languages=none)

  "${apt[@]}" update -qq
  # --print-uris resolves the whole dependency closure without installing it.
  "${apt[@]}" --print-uris --yes --no-install-recommends install "${PACKAGES[@]}" \
    | grep -o "http://[^']*\.deb" | sort -u > "$STACK/uris.txt"
  say "  $(wc -l < "$STACK/uris.txt") packages to fetch"
  while read -r uri; do
    curl -sS --output-dir "$STACK/debs" -O "$uri"
  done < "$STACK/uris.txt"
  for deb in "$STACK/debs"/*.deb; do dpkg-deb -x "$deb" "$SYSROOT" 2>/dev/null || true; done
  [ -x "$SYSROOT/usr/bin/Xvfb" ] || { say "Xvfb did not unpack"; exit 1; }
}

build_engine() {
  say "fetching Ikemen GO $ENGINE_TAG"
  mkdir -p "$ENGINE"
  curl -sSL -o "$STACK/engine.zip" "$ENGINE_URL"
  unzip -q -o "$STACK/engine.zip" -d "$ENGINE"
  # -print -quit, not "| head -1": head closes the pipe, find dies on SIGPIPE and
  # pipefail turns that into a silent exit before anything is even printed.
  ENGINE_BIN="$(find "$ENGINE" -maxdepth 1 -type f -name 'Ikemen_GO*' -perm -u+x -print -quit)"
  [ -n "$ENGINE_BIN" ] || { say "engine binary missing from the release"; exit 1; }
}

[ -x "$SYSROOT/usr/bin/Xvfb" ] || build_sysroot
ENGINE_BIN="$(find "$ENGINE" -maxdepth 1 -type f -name 'Ikemen_GO*' -perm -u+x -print -quit 2>/dev/null)"
[ -n "$ENGINE_BIN" ] || build_engine
say "engine: $ENGINE_BIN"

# Point the engine at this repo. Symlinks, so the game runs the working tree and
# nothing is copied: the mod under test is repo/external/mods/devhelp.lua.
for dir in data chars stages font sound external; do
  [ -d "$ROOT/$dir" ] || continue
  rm -rf "${ENGINE:?}/$dir"
  ln -s "$ROOT/$dir" "$ENGINE/$dir"
done

export LD_LIBRARY_PATH="$SYSROOT/usr/lib/x86_64-linux-gnu:$SYSROOT/usr/lib/x86_64-linux-gnu/pulseaudio:$SYSROOT/lib/x86_64-linux-gnu"
export PATH="$SYSROOT/usr/bin:$PATH"
export XDG_RUNTIME_DIR="$STACK/xdg"
mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"

# ------------------------------------------------------------------ the session
write_session() {
  local file="$1"
  cat > "$file" <<SESSION
#!/bin/bash
set -u
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH"
export PATH="$PATH"
export XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR"
mkdir -p "$STACK/ovl/up" "$STACK/ovl/work"
# Xvfb wants /usr/bin/xkbcomp; override /usr/bin inside this namespace only.
mount -t overlay overlay -o lowerdir=/usr/bin,upperdir=$STACK/ovl/up,workdir=$STACK/ovl/work /usr/bin 2>/dev/null \\
  || { echo "cannot overlay /usr/bin - unprivileged user namespaces unavailable"; exit 3; }
cp "$SYSROOT/usr/bin/xkbcomp" /usr/bin/xkbcomp || exit 3

"$SYSROOT/usr/bin/Xvfb" $DISPLAY_NUM -screen 0 1280x720x24 -nolisten tcp -noreset \\
  -xkbdir "$SYSROOT/usr/share/X11/xkb" > "$STACK/xvfb.log" 2>&1 &
XPID=\$!
sleep 5
DISPLAY=$DISPLAY_NUM xdotool getdisplaygeometry >/dev/null 2>&1 \\
  || { echo "virtual display did not come up:"; tail -5 "$STACK/xvfb.log"; kill \$XPID; exit 4; }

cd "$ENGINE"
DISPLAY=$DISPLAY_NUM "$ENGINE_BIN" -log > "$STACK/engine.log" 2>&1 &
EPID=\$!
SESSION

  # each drive command becomes one line of the session script
  if [ -n "$SCRIPT" ]; then
    while read -r verb arg _; do
      [ -n "${verb:-}" ] || continue
      case "$verb" in
        wait) printf 'sleep %s\n' "$arg" >> "$file" ;;
        key)  printf 'DISPLAY=%s xdotool key --clearmodifiers %s\n' "$DISPLAY_NUM" "$arg" >> "$file" ;;
        shot) printf 'DISPLAY=%s xwd -root -silent > %s/%s.xwd 2>/dev/null\n' \
                "$DISPLAY_NUM" "$OUT" "$arg" >> "$file" ;;
        log)  printf 'grep -viE "ALSA|Gdk-WARNING|Failed to assign" %s/engine.log | tail -20\n' "$STACK" >> "$file" ;;
        *)    say "unknown drive verb: $verb";;
      esac
    done < "$SCRIPT"
  else
    printf 'sleep 20\n' >> "$file"
  fi

  cat >> "$file" <<SESSION
kill \$EPID \$XPID 2>/dev/null
wait 2>/dev/null
SESSION
}

SESSION_SH="/tmp/ikemen-session-$$.sh"
write_session "$SESSION_SH"
chmod +x "$SESSION_SH"

say "running the engine on the virtual display (stack: $STACK)"
if command -v unshare >/dev/null && unshare -r true 2>/dev/null; then
  unshare -rm bash "$SESSION_SH" || true
else
  say "unprivileged user namespaces are unavailable here, so /usr/bin/xkbcomp"
  say "cannot be provided and Xvfb will refuse to start. Nothing was run."
  exit 3
fi
rm -f "$SESSION_SH"

# --------------------------------------------------------------- convert frames
for xwd in "$OUT"/*.xwd; do
  [ -e "$xwd" ] || continue
  # Convert, and only drop the raw frame once a PNG exists: a conversion error
  # must leave the capture behind for inspection, not delete the evidence.
  if python3 - "$xwd" <<'PY'
import struct, sys
from PIL import Image
path = sys.argv[1]
raw = open(path, 'rb').read()
if len(raw) < 100:
    print(f'{path}: empty capture'); raise SystemExit(1)
# XWD header: 25 big-endian uint32s, then the window name, then the pixels.
head = struct.unpack('>25I', raw[:100])
hs, depth, w, h = head[0], head[3], head[4], head[5]
bpp, bpl = head[11], head[12]
if bpp not in (24, 32):
    print(f'{path}: unsupported {bpp}-bit pixels'); raise SystemExit(1)
if hs + bpl * h > len(raw):
    print(f'{path}: truncated ({len(raw)} bytes, need {hs + bpl * h})'); raise SystemExit(1)
mode = 'BGRX' if bpp == 32 else 'BGR'
img = Image.frombuffer('RGB', (w, h), raw[hs:hs + bpl * h], 'raw', mode, bpl, 1)
img.save(path[:-4] + '.png')
print(f'  {path[:-4]}.png ({w}x{h})')
PY
  then
    rm -f "$xwd"
  else
    say "  kept $xwd (conversion failed)"
  fi
done

say "engine log: $STACK/engine.log"
say "captures:   $OUT"
