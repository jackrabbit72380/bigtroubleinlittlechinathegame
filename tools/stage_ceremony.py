"""Lo Pan's Ceremony: the throne hall seen from the statue's side.

The throne room's back wall is a skull gate; the ceremony side of the same
building is the platform the six-armed bodhisattva stands on. This painter keeps
the hall from tools/stage_throne.py - the niche rhythm, the neon balcony strip,
the arcade corridors, torches, guardians and the tiled plaza - and replaces the
skull gate and its narrow staircase with a seated six-armed statue, a lotus
plinth and three broad steps. The steps are the point of the stage: 1316 canvas
px across at the foot, against the throne's 608.

Geometry is in canvas pixels on the shared 8192x1080 canvas. CX is the centre
and FLOOR_Y the plaza line, both owned by tools/stages_hd.py.

Run:  python3 tools/stage_ceremony.py       (part of tools/build_all.py)
"""

from __future__ import annotations

import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art
import stages_hd as hd
import stage_throne as throne
import statue as statue_art

W, H = hd.W, hd.H
CX, FLOOR_Y, px = hd.CX, hd.FLOOR_Y, hd.px
BAY = throne.BAY

STATUE_TOP = px(16)                   # 72: whole crown stays in frame

PLINTH_TOP = STATUE_TOP + px(96)      # 504: under the crossed legs
PLINTH_HALF = px(72)                 # a broad drum, as wide as the whole figure
STEPS = [(px(84), px(19)), (px(104), px(22)), (px(124), px(22)), (px(144), px(18))]

NEON = (64, 246, 160)

LIGHTS = []


def statue_layer():
    """The six-armed guardian, painted as one figure by tools/statue.py."""
    return statue_art.build(hd.SCALE, CX, STATUE_TOP, W, H)


def dais():
    """Lotus plinth and four broad steps down to the plaza."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # lotus plinth: a band of petals under the figure
    d.polygon([(CX - PLINTH_HALF, PLINTH_TOP), (CX + PLINTH_HALF, PLINTH_TOP),
               (CX + PLINTH_HALF + px(6), PLINTH_TOP + px(12)),
               (CX - PLINTH_HALF - px(6), PLINTH_TOP + px(12))],
              fill=(96, 84, 68))
    for k in range(-10, 11):
        cx = CX + k * PLINTH_HALF / 10.5
        d.ellipse([cx - px(4.4), PLINTH_TOP + px(1), cx + px(4.4), PLINTH_TOP + px(11)],
                  outline=(140, 122, 96), width=max(1, px(0.9)))
    d.line([(CX - PLINTH_HALF, PLINTH_TOP), (CX + PLINTH_HALF, PLINTH_TOP)],
           fill=(168, 146, 110), width=max(1, px(1.4)))

    # steps: wide terraces, each with a lit top face and a dark riser
    y = PLINTH_TOP + px(12)
    for half, depth in STEPS:
        y2 = min(FLOOR_Y, y + depth)
        d.polygon([(CX - half, y), (CX + half, y),
                   (CX + half + px(10), y2), (CX - half - px(10), y2)],
                  fill=(74, 62, 54))
        d.polygon([(CX - half, y), (CX + half, y),
                   (CX + half, y + px(5)), (CX - half, y + px(5))],
                  fill=(138, 120, 96))
        d.line([(CX - half - px(10), y2), (CX + half + px(10), y2)],
               fill=(26, 20, 18), width=max(1, px(1.4)))
        # jade inlay across the tread, and a low offering bowl either side
        d.rectangle([CX - px(30), y + px(6), CX + px(30), y + px(8.5)],
                    fill=(52, 116, 96))
        LIGHTS.append((CX - half * 0.86, y + px(4), px(26), (255, 168, 88), 90))
        LIGHTS.append((CX + half * 0.86, y + px(4), px(26), (255, 168, 88), 90))
        y = y2
    return img


def paint():
    LIGHTS.clear()
    base = hd.blank([
        (0, (14, 8, 9)), (40, (52, 24, 20)), (86, (62, 30, 23)),
        (130, (44, 24, 20)), (170, (32, 20, 19)), (200, (18, 12, 13)),
        (240, (8, 7, 9)),
    ])
    d = ImageDraw.Draw(base)

    hd.stone(d, 0, 0, W, FLOOR_Y, (54, 39, 35), (29, 21, 20), rows=62, seed=12,
             jitter=0.55)
    for x in range(0, W, px(44)):
        d.rectangle([x + px(3), px(1), x + px(38), px(9)], fill=(21, 13, 13))

    # The mezzanine is the throne hall's own: one niche per bay and the same
    # balustrade, only bay 0 skipped where the figure stands, exactly as the
    # throne skips it for the gate. No bare wall either side of the centre.
    neon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nd = ImageDraw.Draw(neon)

    for i in range(-9, 10):
        if i == 0:
            continue
        x = CX + i * BAY
        if not (-BAY < x < W + BAY):
            continue
        y0 = throne.ring_y(x)
        throne.niche(d, x, y0 - px(3), BAY * 0.60, px(40), face=(94, 78, 63),
                     deep=(9, 7, 9), lights=False)
        hd.glyph(nd, x - BAY * 0.10, y0 - px(31), BAY * 0.20, (255, 54, 38),
                 seed=i + 4, width=px(1.8))
        nd.rectangle([x - BAY * 0.115, y0 - px(36), x + BAY * 0.115, y0 - px(6)],
                     outline=(255, 46, 34), width=max(1, px(0.9)))

    for i in range(-9, 10):
        x = CX + i * BAY
        if not (-BAY < x < W + BAY):
            continue
        y0 = throne.ring_y(x)
        d.rectangle([x - BAY / 2, y0, x + BAY / 2, y0 + px(12)], fill=(46, 34, 30))
        for k in range(-4, 5):
            bxx = x + k * BAY * 0.105
            d.rectangle([bxx - px(1.3), y0 + px(2), bxx + px(1.3), y0 + px(12)],
                        fill=(102, 88, 72))
        d.line([(x - BAY / 2, y0), (x + BAY / 2, y0)], fill=(158, 138, 114),
               width=max(1, px(1.6)))
    # Blue and red run the whole wall and meet on the centre line, passing
    # behind the statue - the strip is composited before the figure, so the
    # stone hides it where it overlaps and it reappears either side.
    throne.ring_line(nd, px(1.5), (58, 214, 240), px(2.2))
    throne.ring_line(nd, px(4.5), (238, 52, 42), px(1.6))

    for i in range(-9, 10):
        x = CX + i * BAY
        if not (-BAY < x < W + BAY) or abs(i) <= 2:
            continue
        y0 = throne.ring_y(x)
        base_y = FLOOR_Y - px(8)
        h = min(px(104), base_y - (y0 + px(24)))
        if h < px(46):
            continue
        throne.niche(d, x, base_y, BAY * 0.80, h, face=(86, 72, 58),
                     deep=(12, 9, 10), lacquer=(74, 42, 28), lights=False)
        throne.corridor(d, x, base_y - h, base_y, BAY * 0.26)
        if i % 2 == 0:
            throne.torch(d, x + BAY * 0.33, base_y - px(52))

    base = Image.alpha_composite(base, dais())
    figure, rim, eyes = statue_layer()
    base = Image.alpha_composite(base, figure)
    # The mezzanine strip is drawn before the figure but screened in at the end,
    # so without this it would glow straight across the stone. Punching the
    # statue's silhouette out of the neon layer puts the lines behind it: they
    # meet at the centre and vanish under the body, as they would in the room.
    neon.putalpha(ImageChops.subtract(
        neon.split()[3],
        figure.split()[3].point(lambda v: 255 if v > 40 else 0)))

    for sx in (-1, 1):
        base = throne.guardian(base, CX + sx * px(150), FLOOR_Y, px(28))
    d = ImageDraw.Draw(base)
    for sx in (-1, 1):
        throne.brazier(d, CX + sx * px(112), FLOOR_Y, px(24))
        LIGHTS.append((CX + sx * px(112), FLOOR_Y - px(14), px(46),
                       (255, 168, 88), 130))
    # warm light on the stone, not green: the green in this room is the tube,
    # and the figure is grey stone with the neon laid over it
    LIGHTS.append((CX, PLINTH_TOP + px(10), px(112), (255, 184, 112), 84))
    LIGHTS.append((CX, STATUE_TOP + px(33), px(76), (255, 212, 158), 52))
    throne.plaza(d, FLOOR_Y)

    base = hd.shade(base, [(hd.light(cx, cy, r, col, peak), px(8), 1.2)
                           for cx, cy, r, col, peak in LIGHTS])
    base = hd.finish(base, 5, 3, 0.32, FLOOR_Y)
    base = art.screen(base, neon, glow_radius=px(3), gain=1.5, passes=2)
    base = art.screen(base, rim, glow_radius=px(1.6), gain=0.5, passes=2)
    base = art.screen(base, eyes, glow_radius=px(2.2), gain=1.35, passes=2)
    base.putalpha(Image.new("L", (W, H), 255))

    ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(ring).arc([CX - px(170), -px(8), CX + px(170), px(190)],
                             196, 344, fill=NEON, width=max(2, px(1.5)))
    base = art.screen(base, ring, glow_radius=px(4), gain=1.3)

    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    for i in range(px(26)):
        a = int(200 * (1 - i / px(26)) ** 1.6)
        fd.line([(0, H - i), (W, H - i)], fill=(6, 5, 8, a))

    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, fg, 1)]


def main():
    hd.STAGES["lopans_ceremony"] = ("Lo Pan's Ceremony", paint)
    hd.build("lopans_ceremony")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
