"""Give the in-fight captions the same cream-gold as the rest of the game.

fight.def carries its own text specs, and most of them are the stock three
fields (font, bank, align), which the engine draws in its default white. The
menus and the VS screen set a cream-gold on every caption, so ROUND 1, FIGHT,
the HITS! combo text and the fighters' names read as a different game.

Ikemen accepts the colour as three extra fields - this file already does that
for the combo counters, e.g. ``p1.counter.font = 4,0,0, 230,255,242`` - so each
spec with exactly three fields gains the same gold the motif's captions use.

Only three-field specs are touched: anything that already carries a colour was
chosen on purpose (the per-side counter tints) and a second run is a no-op.

Run:  python3 tools/build_fight_text.py
"""

from __future__ import annotations

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGHT_DEF = os.path.join(ROOT, "data", "fight.def")

# The colour every caption in the motif already uses (system.def's title.font,
# stage.font and the fighter names on the select screen).
GOLD = "255, 228, 140"

# <key>.font = <index>, <bank>, <align>   with nothing else on the line
THREE = re.compile(r"^(\s*[A-Za-z0-9_.]+\.font\s*=\s*)(\d+\s*,\s*-?\d+\s*,\s*-?\d+)(\s*)$")


def build():
    if not os.path.isfile(FIGHT_DEF):
        raise SystemExit("data/fight.def is missing")

    with open(FIGHT_DEF, encoding="utf-8", errors="replace", newline="") as f:
        text = f.read()

    out, changed = [], 0
    for line in text.splitlines(True):
        body = line.rstrip("\r\n")
        ending = line[len(body):]
        match = THREE.match(body)
        if match:
            out.append("%s%s, %s%s" % (match.group(1), match.group(2), GOLD, ending))
            changed += 1
        else:
            out.append(line)

    if changed:
        with open(FIGHT_DEF + ".tmp", "w", encoding="utf-8", newline="") as f:
            f.write("".join(out))
        os.replace(FIGHT_DEF + ".tmp", FIGHT_DEF)

    # Read back: one captioned spec has to carry the colour now.
    with open(FIGHT_DEF, encoding="utf-8", errors="replace") as f:
        check = f.read()
    if "round.default.font" in check:
        line = next(l for l in check.splitlines() if l.strip().startswith("round.default.font"))
        if "," not in line.split("=", 1)[1] or len(line.split("=", 1)[1].split(",")) < 6:
            raise SystemExit("round.default.font did not pick up the colour: %r" % line)
    print("fight text: %d caption(s) given the gold, %d already coloured"
          % (changed, sum(1 for l in text.splitlines() if ".font" in l and "=" in l)
             - changed))


if __name__ == "__main__":
    build()
