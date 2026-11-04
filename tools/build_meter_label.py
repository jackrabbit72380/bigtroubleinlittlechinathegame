"""Replace the MAXIMUM! lettering baked into the full-power meter sprite.

The small power meter under the health bar is a 202x18 sprite with the word
MAXIMUM! painted into its orange fill. AUDACITY belongs in exactly that spot, so
this rubs the old lettering out (the bar is a vertical gradient, so a clean
column of it rebuilds the covered strip) and paints AUDACITY in the same place
and style.

Run:  python3 tools/build_meter_label.py
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import sff  # noqa: E402

FIGHT_SFF = os.path.join(ROOT, "data", "fight.sff")
FONT = os.path.join(ROOT, "data", "ikemen1", "fonts", "Display.ttf")

KEY = (44, 0)              # frontMax: the bar shown at full power
WORD = "AUDACITY"
CORE = (146, 24, 8, 255)   # letter body, the dark red the old word used
EDGE = (255, 138, 74, 255)  # hot rim around each letter
CLEAN_X = 26               # column of untouched bar used as the fill colour


def _bbox(img):
    """Find the dark-red lettering inside the orange bar."""
    px = img.load()
    xs, ys = [], []
    for y in range(img.height):
        for x in range(24, img.width - 8):
            r, g, b, a = px[x, y]
            if a > 128 and r < 205 and g < 90 and b < 90:
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return (max(0, min(xs) - 4), max(0, min(ys) - 2),
            min(img.width, max(xs) + 5), min(img.height, max(ys) + 3))


def repaint(img):
    img = img.convert("RGBA").copy()
    box = _bbox(img)
    if box is None:
        raise SystemExit("no MAXIMUM! lettering found in sprite 44,0")
    px = img.load()
    d = ImageDraw.Draw(img)
    for y in range(box[1], box[3]):
        d.line([(box[0], y), (box[2] - 1, y)], fill=px[CLEAN_X, y])

    font = None
    for path in (FONT, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            font = ImageFont.truetype(path, 14)
            break
        except OSError:
            continue
    if font is None:
        raise SystemExit("no TrueType face available to letter the meter")

    cx = (box[0] + box[2]) / 2.0
    cy = (box[1] + box[3]) / 2.0
    d.text((cx, cy), WORD, font=font, anchor="mm", fill=CORE,
           stroke_width=1, stroke_fill=EDGE)
    return img


def main():
    raw, sprites, pals = sff.read_sff(FIGHT_SFF)
    out, done = [], False
    for sp in sprites:
        if (sp["group"], sp["number"]) == KEY:
            img = repaint(sff.decode_sprite(raw, sp, pals, sp["pal"]))
            out.append({"group": KEY[0], "number": KEY[1], "image": img,
                        "axis": sp["axis"]})
            done = True
        else:
            out.append({"group": sp["group"], "number": sp["number"],
                        "raw": sp["raw"], "format": sp["format"],
                        "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                        "axis": sp["axis"], "pal": sp["pal"],
                        "link": sp["link"]})
    if not done:
        raise SystemExit("sprite 44,0 is missing from data/fight.sff")
    blob = sff.write_sff(out, [p["rgba"] for p in pals])
    open(FIGHT_SFF + ".tmp", "wb").write(blob)
    os.replace(FIGHT_SFF + ".tmp", FIGHT_SFF)
    print("sprite 44,0: MAXIMUM! replaced with AUDACITY")


if __name__ == "__main__":
    main()
