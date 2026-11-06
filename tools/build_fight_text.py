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


# The round banner. The stock motif spells the round "R   %i" in the 180px
# Round face, so round 2 announced itself as "R 2". It is spelled out now, in the
# Display face the VS screen's fighter names use - the same face the menus show -
# at twice the cell so it still reads as an announcement between the rounds.
ROUND_KEYS = (
    ("round.default.text", '"ROUND %i"'),
    ("round.default.font", "10,0,0, 255, 228, 140"),
    ("round.default.scale", "2, 2"),
    ("round.single.text", '"ROUND %i"'),
    ("round.single.font", "10, 0, 0, 255, 228, 140"),
    ("round.single.scale", "2, 2"),
    ("round.final.font", "10,0,0, 255, 228, 140"),
    ("round.final.scale", "2, 2"),
)


def place_round_banner(text):
    """Point [Round] at the Display face, wording the banner out."""
    made = False
    if "fonts/Display.def" not in text:
        fonts = list(re.finditer(r"^font(\d+)\s*=[^\r\n]*$", text, re.M))
        if not fonts:
            return text, False
        last = fonts[-1]
        eol = "\r\n" if text[last.start():last.end()].endswith("\r") else "\n"
        line = "font%d = ikemen1/fonts/Display.def   ;the VS screen's face" % (
            int(last.group(1)) + 1)
        text = text[:last.end()] + eol + line + text[last.end():]
        made = True

    start = text.find("[Round]")
    if start < 0:
        return text, made
    nxt = re.compile(r"^\[", re.M).search(text, start + len("[Round]"))
    end = nxt.start() if nxt else len(text)
    head, body, tail = text[:start], text[start:end], text[end:]
    for key, value in ROUND_KEYS:
        pattern = re.compile(r"^[ \t]*" + re.escape(key) + r"[ \t]*=[^\r\n]*$", re.M)
        line = "%s = %s" % (key, value)
        new = pattern.sub(line, body, count=1) if pattern.search(body) \
            else body.rstrip("\r\n") + "\n" + line + "\n"
        if new != body:
            made = True
        body = new
    return head + body + tail, made


# The demo caption. It is set in the motif's own Body face, the one the menus,
# the select captions and the fighter names use, but at 1.5x that cell: the
# caption sits alone in the top corner of a running fight next to a round banner
# drawn 68px tall, so setting it at the menus' own 20px left it reading as a
# footnote. Body's 20px cell scaled 1.5 lands 30px in the 1280 fight space, 45px
# on a 1920 screen - half the round banner, and still the menus' face.
BODY = "ikemen1/fonts/Body.def"
MODE_SCALE = "1.5, 1.5"       # Body's 20px cell in the 1280 fight space


def font_slot(text, path):
    """Index of the [Files] font already pointing at path, or a new one."""
    for m in re.finditer(r"^font(\d+)\s*=\s*([^\r\n]*)$", text, re.M):
        value = m.group(2).split(";")[0].strip().lower()
        if value == path.lower():
            return text, int(m.group(1))
    fonts = list(re.finditer(r"^font(\d+)\s*=[^\r\n]*$", text, re.M))
    if not fonts:
        return text, None
    last = fonts[-1]
    idx = int(last.group(1)) + 1
    eol = "\r\n" if text[last.start():last.end()].endswith("\r") else "\n"
    line = "font%d = %s   ;the menus' face, for the demo caption" % (idx, path)
    return text[:last.end()] + eol + line + text[last.end():], idx


def place_demo_caption(text):
    """Point the [Mode] caption at the Body face, at the menus' size."""
    text, idx = font_slot(text, BODY)
    if idx is None:
        return text, False
    start = text.find("[Mode]")
    if start < 0:
        return text, False
    nxt = re.compile(r"^\[", re.M).search(text, start + len("[Mode]"))
    end = nxt.start() if nxt else len(text)
    head, body, tail = text[:start], text[start:end], text[end:]
    made = False
    # Both keys are written next to the caption they belong to. The first run of
    # this appended the scale at the end of the section, which is a screenful
    # below in the middle of the fight.def help text: still [Mode], but nobody
    # reading the block would find it. The scale is deleted and re-inserted
    # beside the caption every run, so a stray copy cannot survive.
    font_line = "demo.text.font = %d, 0, -1, 255, 228, 140" % idx
    scale_line = "demo.text.scale = %s" % MODE_SCALE
    lines = [l for l in body.splitlines(True)
             if not re.match(r"^;?[ \t]*demo\.text\.scale[ \t]*=", l)]
    body = "".join(lines)
    font_re = re.compile(r"^;?[ \t]*demo\.text\.font[ \t]*=[^\r\n]*$", re.M)
    if font_re.search(body):
        body = font_re.sub(font_line, body, count=1)
    else:
        body = body.rstrip("\r\n") + "\n" + font_line + "\n"
    lines = body.splitlines(True)
    for anchor in ("demo.text.text", "demo.text.font", "demo.pos"):
        hit = next((i for i, l in enumerate(lines) if l.strip().startswith(anchor)), None)
        if hit is not None:
            eol = "\r\n" if lines[hit].endswith("\r\n") else "\n"
            lines.insert(hit + 1, scale_line + eol)
            break
    else:
        lines.append(scale_line + "\n")
    body = "".join(lines)
    made = True
    return head + body + tail, made


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

    # fight.def is reset from the engine copy on every build, so the round
    # banner is set here rather than left as a hand edit.
    with open(FIGHT_DEF, encoding="utf-8", errors="replace", newline="") as f:
        text = f.read()
    text, banner = place_round_banner(text)
    if banner:
        with open(FIGHT_DEF + ".tmp", "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.replace(FIGHT_DEF + ".tmp", FIGHT_DEF)

    # The demo caption is set at the menus' size, every build, for the same
    # reason: the engine copy resets it to the Pixel face.
    with open(FIGHT_DEF, encoding="utf-8", errors="replace", newline="") as f:
        text = f.read()
    text, caption = place_demo_caption(text)
    if caption:
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
    if 'round.default.text = "ROUND %i"' not in check:
        raise SystemExit("the round banner did not take the wording")
    if "fonts/Display.def" not in check:
        raise SystemExit("the Display face was not registered in fight.def")
    mode = check.split("[Mode]", 1)[-1].split("\n[", 1)[0]
    if "fonts/Body.def" not in check or "demo.text.scale = %s" % MODE_SCALE not in mode:
        raise SystemExit("[Mode] did not take the menus' face and size: %r" % mode)
    print("fight text: %d caption(s) given the gold, %d already coloured, "
          "%d win-counter key(s) moved onto the character boxes"
          % (changed, sum(1 for l in text.splitlines() if ".font" in l and "=" in l)
             - changed, len(moved)))


if __name__ == "__main__":
    build()
