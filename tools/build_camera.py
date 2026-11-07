"""Let the fight camera pull back when the fighters separate.

Every stage shipped with

    zoomout = 1
    zoomin = 1

which is the camera's zoom switched off: 1 is "always show the screen at 1:1",
so the view could pan along the level but never widen. Two players walking apart
therefore ran out of screen at 960px from the centre and stopped, instead of the
camera pulling back the way MUGEN and Ikemen stages normally do.

zoomout is the smallest zoom the view may pull back to, so a smaller number is a
wider view:

    zoomout = 0.75   shows 2560x1440 of the stage instead of 1920x1080

0.75 is what the engine's own stages use, and it is the safest value for this
art: the painted backdrops run out to x=+-4096, but only 1080px tall, so pulling
back much further starts to show unpainted floor below the set. zoomin is left at
1 so the default framing does not change.

The stage generators write the same pair, so a rebuilt stage keeps the camera.

Run:  python3 tools/build_camera.py
"""

from __future__ import annotations

import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ZOOMOUT = "0.75"
ZOOMIN = "1"

# every stage the game can load: the shipped ones and the HD set
PATTERNS = ("stages/*.def", "data/**/stages/*.def", "data/stages/*.def")


def stage_files():
    seen, out = set(), []
    for pattern in PATTERNS:
        for path in sorted(glob.glob(os.path.join(ROOT, pattern), recursive=True)):
            real = os.path.realpath(path)
            if real in seen or not os.path.isfile(path):
                continue
            seen.add(real)
            out.append(path)
    return out


def camera_bounds(text):
    """Start and end of the [Camera] section, or None."""
    start = re.search(r"(?im)^\[Camera\]\s*$", text)
    if not start:
        return None
    nxt = re.compile(r"(?m)^\[", re.I).search(text, start.end())
    return start.start(), (nxt.start() if nxt else len(text))


def set_key(body, key, value):
    pattern = re.compile(r"(?im)^([ \t]*" + re.escape(key) + r"[ \t]*=[ \t]*)([^;\r\n]*)(.*)$")
    line = "%s = %s" % (key, value)
    if pattern.search(body):
        return pattern.sub(lambda m: line + m.group(3), body, count=1), False
    return body.rstrip("\r\n") + "\n" + line + "\n", True


def patch(path):
    with open(path, encoding="utf-8", errors="surrogateescape", newline="") as f:
        text = f.read()
    bounds = camera_bounds(text)
    if bounds is None:
        return None
    start, end = bounds
    head, body, tail = text[:start], text[start:end], text[end:]
    added = []
    for key, value in (("zoomout", ZOOMOUT), ("zoomin", ZOOMIN)):
        body, new = set_key(body, key, value)
        if new:
            added.append(key)
    new_text = head + body + tail
    if new_text != text:
        with open(path + ".tmp", "w", encoding="utf-8",
                  errors="surrogateescape", newline="") as f:
            f.write(new_text)
        os.replace(path + ".tmp", path)
    return added


def main():
    patched, skipped = [], []
    for path in stage_files():
        added = patch(path)
        name = os.path.relpath(path, ROOT)
        if added is None:
            skipped.append(name)
        else:
            patched.append((name, added))
    for name, added in patched:
        print("  %-40s zoomout %s%s" % (name, ZOOMOUT,
                                        " (+%s)" % ", ".join(added) if added else ""))
    if skipped:
        print("  no [Camera] section: %s" % ", ".join(skipped))
    print("camera: %d stage(s) zoom out to %s, %d skipped"
          % (len(patched), ZOOMOUT, len(skipped)))
    return 0 if patched else 1


if __name__ == "__main__":
    raise SystemExit(main())
