"""Give every fighter a VS portrait entrance animation.

[VS Screen] p1.anim names an action in the *character's* own AIR, so a portrait
can only move if the character has something to play. build_portraits.py bakes
each fighter's portrait as sprite 9000,1 with a 0,0 axis, which means an ordinary
AIR action playing that sprite lands exactly where the still picture did: frame
offsets are in character units and scale by the same motif/character localcoord
factor as the portrait (1.5 x 1920/960 = 3x for this roster's 960x720 characters),
so -340 starts the fighter 1020px to the left, outside its window, and the ramp
below walks it in over 43 frames - about 0.7s, long enough to survive the screen's
20-frame fade-in and still be seen.

One action for both sides: p2.facing = -1 mirrors it, so a build that negates
frame offsets walks P2 in from the right as well.

Re-running refreshes the block, so a tuning change reaches every character; an
AIR without 9000,1 art (the intro/ending files) is left alone.

Run:  python3 tools/add_vs_portrait_anim.py
"""

from __future__ import annotations

import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sff

ACTION = 9000
FRAMES = ((-340, 7), (-250, 7), (-175, 7), (-115, 6),
          (-70, 6), (-35, 5), (-12, 5), (0, -1))
MARK = "[Begin Action %d]" % ACTION


def body() -> str:
    lines = [MARK, ";VS portrait entrance - see tools/add_vs_portrait_anim.py"]
    lines += ["9000,1, %d,0, %d" % (x, ticks) for x, ticks in FRAMES]
    return "\n".join(lines) + "\n"


def has_portrait(sff_path: str) -> bool:
    try:
        _raw, sprites, _pals = sff.read_sff(sff_path)
    except Exception:
        return False
    return any(s.get("group") == 9000 and s.get("number") == 1 for s in sprites)


def main() -> None:
    added = refreshed = noart = 0
    for air in sorted(glob.glob("chars/*/*.air")):
        stem = os.path.splitext(air)[0]
        if not has_portrait(stem + ".sff"):
            noart += 1
            continue
        text = open(air, encoding="utf-8", errors="replace").read()
        if MARK in text:
            i = text.index(MARK)
            j = text.find("\n[Begin Action", i)
            new = text[:i] + body() + ("" if j < 0 else text[j:])
            if new != text:
                refreshed += 1
        else:
            if not text.endswith("\n"):
                text += "\n"
            new = text + "\n" + body()
            added += 1
        if new != text:
            with open(air, "w", encoding="utf-8", newline="\n") as f:
                f.write(new)
    print("VS portrait action %d: %d added, %d refreshed, %d without 9000,1 art"
          % (ACTION, added, refreshed, noart))


if __name__ == "__main__":
    main()
