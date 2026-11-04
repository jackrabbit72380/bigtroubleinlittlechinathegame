"""Repaint the two top power meters as gold dragons.

Ikemen draws the power bar at the top of the screen from data/fight.sff: the
trough (40,0), a frame (41,0), the filled front (43,0) and a frontMax sprite
(44,0) that only appears at full power. The stock art for that last one is a
white "MAXIMUM!" banner, and the rest is flat grey metal.

This paints them as the gold dragon from the film's iconography instead: the
trough is a dark bronze channel with a scaled floor, the frame is a gold rail
with a dragon's head coiling over the right end, the fill is a gold scaled body
that runs from deep bronze at the tail to bright gold at the jaw, and the full
bar carries the word AUDACITY in cap gold on a dark plate.

Everything is drawn at the sprite's own size and axis. The bar grows right to
left (its axis is the right edge, and range.x runs to -206), so the head sits at
the right and the tail at the left.

Run:  python3 tools/build_powerbar.py
"""

from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art
import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGHT_SFF = os.path.join(ROOT, "data", "fight.sff")

# The stock sizes and axes, read off the shipped file. Keeping them means no
# coordinate in data/fight.def has to move.
TROUGH = (40, 0, 206, 18, (206, 0))
FRAME = (41, 0, 210, 22, (210, 0))
FRONT = (43, 0, 202, 14, (202, 0))
FRONT_MAX = (44, 0, 202, 18, (202, 2))

# Gold ramp: deep bronze in shadow, honey in the body, near-white on the lit
# edge. The concept art's dragon is this range and almost nothing else.
DEEP = (58, 34, 10)
BRONZE = (128, 78, 22)
GOLD = (198, 148, 46)
GOLD_LO = (232, 188, 78)
GOLD_HI = (252, 232, 158)
INK = (16, 9, 4)


def _scales(draw, box, rows, colour_lo, colour_hi, alpha=210):
    """Row of overlapping semicircular scales, the way the dragon's hide reads."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    if w <= 2 or h <= 2:
        return
    step = max(4.0, w / 26.0)
    row_h = h / float(rows)
    for r in range(rows):
        cy = y0 + row_h * (r + 0.5)
        k = (r + 0.5) / rows
        fill = tuple(int(round(colour_lo[i] + (colour_hi[i] - colour_lo[i]) * k))
                     for i in range(3)) + (alpha,)
        offset = step * 0.5 if r % 2 else 0.0
        x = x0 + offset - step
        while x < x1 + step:
            rr = step * 0.62
            draw.arc([x - rr, cy - rr * 0.9, x + rr, cy + rr * 0.9],
                     200, 340, fill=fill, width=max(1, int(row_h * 0.38)))
            x += step


def _rim(img, colour, width=1):
    """Put a hard outline under a sprite so it reads on any background."""
    alpha = img.split()[3]
    grown = alpha.filter(ImageFilter.MaxFilter(width * 2 + 1))
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste(Image.new("RGBA", img.size, colour + (255,)), (0, 0), grown)
    out.alpha_composite(img)
    return out


def _head(draw, x, cy, size, facing=1):
    """A dragon's skull in profile: snout, brow, horn, jaw and a lit eye.

    Small as it is at this size, the silhouette is what carries: a wedge that
    opens to the right with a horn sweeping back over the brow.
    """
    s = size / 22.0
    f = facing

    def p(pts):
        return [(x + f * px * s, cy + py * s) for px, py in pts]

    # upper skull and snout
    draw.polygon(p([(-11, -3), (-4, -9), (5, -8), (13, -5), (16, -2),
                    (10, 0), (2, 1), (-6, 2), (-11, 2)]), fill=GOLD, outline=INK)
    # lower jaw, slightly open
    draw.polygon(p([(-8, 2), (2, 3), (13, 1), (9, 5), (0, 6), (-8, 5)]),
                 fill=BRONZE, outline=INK)
    # teeth
    for tx in (-2, 3, 8):
        draw.polygon(p([(tx, 1), (tx + 2, 1), (tx + 1, 4)]), fill=GOLD_HI)
    # horn sweeping back over the brow
    draw.polygon(p([(-6, -8), (-14, -13), (-9, -6)]), fill=GOLD_LO, outline=INK)
    # brow ridge and eye
    draw.polygon(p([(-3, -8), (4, -7), (3, -4), (-4, -5)]), fill=GOLD_HI)
    draw.ellipse(p([(1, -6), (4, -4)])[0] + p([(1, -6), (4, -4)])[1],
                 fill=(228, 60, 32), outline=INK)


def _trough():
    _g, _n, w, h, axis = TROUGH
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=6, fill=DEEP + (255,),
                        outline=INK + (255,), width=1)
    d.rounded_rectangle([2, 2, w - 3, h - 3], radius=5, fill=(30, 18, 8, 255))
    _scales(d, (3, 3, w - 3, h - 3), rows=3, colour_lo=(40, 26, 12),
            colour_hi=(86, 54, 18), alpha=150)
    # the channel darkens towards the tail so the fill reads against it
    for x in range(w):
        k = x / float(w - 1)
        if k < 0.35:
            d.line([(x, 1), (x, h - 2)], fill=(0, 0, 0, int(70 * (1 - k / 0.35))))
    return _rim(img, INK), axis


def _frame():
    _g, _n, w, h, axis = FRAME
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # gold rail: an outer bronze band with a lit top edge
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=8, fill=BRONZE + (255,),
                        outline=INK + (255,), width=1)
    d.rounded_rectangle([1, 1, w - 2, h - 2], radius=7, outline=GOLD + (255,),
                        width=1)
    d.line([(6, 2), (w - 8, 2)], fill=GOLD_HI + (170,), width=1)
    d.line([(6, h - 3), (w - 8, h - 3)], fill=INK + (190,), width=1)
    # the head coils over the right end, where the bar is anchored
    _head(d, w - 13, h // 2, 22.0)
    # a tail curl at the far left, so the bar is a body and not a rail
    tcx, tcy = 9, h // 2
    d.arc([tcx - 7, tcy - 7, tcx + 7, tcy + 7], 80, 330, fill=GOLD + (255,),
          width=3)
    d.arc([tcx - 3, tcy - 3, tcx + 3, tcy + 3], 90, 300, fill=GOLD_HI + (220,),
          width=1)
    return _rim(img, INK), axis


def _front():
    _g, _n, w, h, axis = FRONT
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=5, fill=BRONZE + (255,))
    # body of the dragon: bronze at the tail (left) through to bright gold at
    # the head end (right), because the bar is anchored at its right edge
    for x in range(w):
        k = x / float(w - 1)
        col = tuple(int(round(GOLD_LO[i] + (GOLD_HI[i] - GOLD_LO[i]) * k ** 0.7))
                    for i in range(3))
        d.line([(x, 1), (x, h - 2)], fill=col + (255,))
    _scales(d, (1, 1, w - 1, h - 1), rows=2, colour_lo=GOLD, colour_hi=GOLD_HI,
            alpha=190)
    d.line([(1, 1), (w - 2, 1)], fill=(255, 246, 208, 220), width=1)
    d.line([(1, h - 2), (w - 2, h - 2)], fill=INK + (150,), width=1)
    # spines along the top edge, like the ridge in the concept art
    for x in range(4, w - 2, 11):
        d.polygon([(x, 1), (x + 4, -2), (x + 7, 1)], fill=GOLD + (255,))
    return _rim(img, INK), axis


def _front_max():
    _g, _n, w, h, axis = FRONT_MAX
    body, _ax = _front()
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    img.alpha_composite(body, (0, 0))

    # a lit jaw at the head end and a glow along the whole body
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle([0, 0, w - 1, h - 1], radius=6, fill=GOLD_HI + (120,))
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(3)))

    d = ImageDraw.Draw(img)
    _head(d, w - 12, h // 2, 20.0)

    # The full bar is the only place the word appears; the stock sprite said
    # MAXIMUM here. Dark plate, cap gold letters, so it stays legible over the
    # scales.
    text = "AUDACITY"
    font = art.font(12)
    tracking = 2
    widths = [d.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    tx = max(6, (w * 0.34) - total / 2)
    ty = (h - 12) / 2 - 1
    plate = [tx - 5, 1, min(w - 5, tx + total + 5), h - 2]
    d.rounded_rectangle(plate, radius=3, fill=(14, 8, 3, 205))
    for ch, cw in zip(text, widths):
        d.text((tx, ty), ch, font=font, fill=GOLD_HI + (255,),
               stroke_width=1, stroke_fill=INK + (255,))
        tx += cw + tracking
    return _rim(img, INK), axis


def main():
    if not os.path.isfile(FIGHT_SFF):
        raise SystemExit("data/fight.sff is missing - fetch the engine data first")

    painted = {}
    for (group, number, _w, _h, _axis), maker in (
            (TROUGH, _trough), (FRAME, _frame), (FRONT, _front),
            (FRONT_MAX, _front_max)):
        image, axis = maker()
        painted[(group, number)] = (image, axis)

    raw, sprites, palettes = sff.read_sff(FIGHT_SFF)
    out, done = [], set()
    for sp in sprites:
        key = (sp["group"], sp["number"])
        if key in painted:
            image, axis = painted[key]
            out.append({"group": key[0], "number": key[1], "image": image,
                        "axis": axis})
            done.add(key)
        else:
            out.append({"group": sp["group"], "number": sp["number"],
                        "raw": sp["raw"], "format": sp["format"],
                        "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                        "axis": sp["axis"], "pal": sp["pal"], "link": sp["link"]})
    for key, (image, axis) in painted.items():
        if key not in done:
            out.append({"group": key[0], "number": key[1], "image": image,
                        "axis": axis})

    blob = sff.write_sff(out, [p["rgba"] for p in palettes])
    if blob[:12] != sff.SIG:
        raise SystemExit("refusing to write: built fight.sff has no signature")
    with open(FIGHT_SFF + ".tmp", "wb") as f:
        f.write(blob)
    os.replace(FIGHT_SFF + ".tmp", FIGHT_SFF)

    # Read back and check the sizes the def relies on.
    _d, check, _p = sff.read_sff(FIGHT_SFF)
    have = {(s["group"], s["number"]): s for s in check}
    for (group, number, w, h, axis), _m in ((TROUGH, _trough), (FRAME, _frame),
                                            (FRONT, _front),
                                            (FRONT_MAX, _front_max)):
        s = have.get((group, number))
        if s is None:
            raise SystemExit(f"power bar sprite {group},{number} went missing")
        if (s["w"], s["h"]) != (w, h):
            raise SystemExit(f"power bar sprite {group},{number} is "
                             f"{s['w']}x{s['h']}, expected {w}x{h}")

    sheet = Image.new("RGBA", (240, 120), (18, 20, 26, 255))
    y = 8
    for key in ((40, 0), (41, 0), (43, 0), (44, 0)):
        image, _axis = painted[key]
        sheet.alpha_composite(image, (12, y))
        y += image.height + 8
    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    sheet.convert("RGB").save(os.path.join(ROOT, "artifacts", "powerbar.png"))
    w, h, _a = FRONT_MAX[2], FRONT_MAX[3], FRONT_MAX[4]
    print(f"power bar repainted: trough, frame, front and the {w}x{h} full-bar "
          f"art now reads AUDACITY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
