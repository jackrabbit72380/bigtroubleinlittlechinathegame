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


# The wins counter goes on the fighter's own character box. [Face] frames a
# portrait at each top corner of the HUD, and the counter used to float at the
# top centre, over the banner art, where it read as part of the middle of the
# screen instead of as part of that fighter's box. It is centred on each box's
# bottom edge and drawn on layerno 2, so the frame art can never cover it.
WINS_FACE = (
    ("p1.pos", "70, 112"),
    ("p2.pos", "1210, 112"),
    ("p1.text.font", "8, 0, 0, 255, 228, 140"),
    ("p2.text.font", "8, 0, 0, 255, 228, 140"),
    ("p1.layerno", "2"),
    ("p2.layerno", "2"),
)


def place_wins(text):
    """Set the [WinCount] keys, inside that section only."""
    start = text.find("[WinCount]")
    if start < 0:
        return text, []
    nxt = re.compile(r"^\[", re.M).search(text, start + len("[WinCount]"))
    end = nxt.start() if nxt else len(text)
    head, body, tail = text[:start], text[start:end], text[end:]
    changed = []
    for key, value in WINS_FACE:
        pattern = re.compile(r"^;?[ \t]*" + re.escape(key) + r"[ \t]*=[^\r\n]*$", re.M)
        line = "%s = %s" % (key, value)
        if pattern.search(body):
            new = pattern.sub(line, body)
        else:
            new = body.rstrip("\r\n") + "\n" + line + "\n"
        if new != body:
            changed.append(key)
        body = new
    return head + body + tail, changed


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

    # The wins counter moves onto the character boxes, every build: fight.def
    # is reset from the engine copy, so a hand edit there would be lost.
    with open(FIGHT_DEF, encoding="utf-8", errors="replace", newline="") as f:
        text = f.read()
    text, moved = place_wins(text)
    if moved:
        with open(FIGHT_DEF + ".tmp", "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.replace(FIGHT_DEF + ".tmp", FIGHT_DEF)

    # Read back: one captioned spec has to carry the colour now.
    with open(FIGHT_DEF, encoding="utf-8", errors="replace") as f:
        check = f.read()
    wins = check.split("[WinCount]", 1)[-1].split("\n[", 1)[0]
    if "p1.pos = 70, 112" not in wins or "p1.layerno = 2" not in wins:
        raise SystemExit("[WinCount] did not take the character-box layout")
    if "round.default.font" in check:
        line = next(l for l in check.splitlines() if l.strip().startswith("round.default.font"))
        if "," not in line.split("=", 1)[1] or len(line.split("=", 1)[1].split(",")) < 6:
            raise SystemExit("round.default.font did not pick up the colour: %r" % line)
    print("fight text: %d caption(s) given the gold, %d already coloured, "
          "%d win-counter key(s) moved onto the character boxes"
          % (changed, sum(1 for l in text.splitlines() if ".font" in l and "=" in l)
             - changed, len(moved)))


if __name__ == "__main__":
    build()
