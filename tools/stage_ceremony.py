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

W, H = hd.W, hd.H
CX, FLOOR_Y, px = hd.CX, hd.FLOOR_Y, hd.px
BAY = throne.BAY

STATUE_W = px(132)                    # arms flare past the torso, as in the still
STATUE_H = px(104)                    # 468
STATUE_TOP = px(16)                   # 72: whole crown stays in frame
HALO_R = px(44)

PLINTH_TOP = STATUE_TOP + px(96)      # 504: under the crossed legs
PLINTH_HALF = px(72)                 # a broad drum, as wide as the whole figure
STEPS = [(px(84), px(19)), (px(104), px(22)), (px(124), px(22)), (px(144), px(18))]

JADE = (108, 138, 116)
JADE_LIT = (176, 204, 172)
JADE_DK = (44, 58, 50)
GOLD = (206, 168, 86)
GOLD_DK = (110, 80, 36)
NEON = (64, 246, 160)

LIGHTS = []


def _segment(d, a, b, w0, w1, fill=JADE, lit=JADE_LIT, edge=JADE_DK):
    """One tapered limb: thick at the shoulder, narrow at the wrist."""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    ln = max(1e-6, math.hypot(dx, dy))
    nx, ny = -dy / ln, dx / ln
    d.polygon([(ax + nx * w0, ay + ny * w0), (bx + nx * w1, by + ny * w1),
               (bx - nx * w1, by - ny * w1), (ax - nx * w0, ay - ny * w0)], fill)
    # a lit stripe just inside the upper contour: reads as a rounded arm
    if lit:
        d.polygon([(ax + nx * w0, ay + ny * w0), (bx + nx * w1, by + ny * w1),
                   (bx + nx * (w1 - px(1.8)), by + ny * (w1 - px(1.8))),
                   (ax + nx * (w0 - px(1.8)), ay + ny * (w0 - px(1.8)))], lit)
    # and a dark line along the lower contour so the arm separates from the torso
    if edge:
        d.polygon([(ax - nx * w0, ay - ny * w0), (bx - nx * w1, by - ny * w1),
                   (bx - nx * (w1 - px(1.0)), by - ny * (w1 - px(1.0))),
                   (ax - nx * (w0 - px(1.0)), ay - ny * (w0 - px(1.0)))], edge)


def _joint(d, cx, cy, r, fill=JADE, edge=None):
    """Deltoid or elbow: a round cap so the limb has a body, not a stick end.

    Filled without a contour by default: the segments either side already carry
    their own edges, and circling every joint turned the arm into a row of beads.
    """
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)
    if edge:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=edge,
                  width=max(1, px(1.0)))


def _hand(d, cx, cy, r, fist=True):
    """A hand: fist with knuckles and a thumb, or a palm turned up offering."""
    d.ellipse([cx - r, cy - r * 0.95, cx + r, cy + r * 0.95], fill=JADE)
    d.ellipse([cx - r, cy - r * 0.95, cx + r, cy + r * 0.95], outline=JADE_DK,
              width=max(1, px(1.0)))
    if fist:
        for k in (-0.55, -0.18, 0.18, 0.55):        # knuckle bumps
            kx = cx + k * r * 1.25
            d.arc([kx - r * 0.34, cy - r * 1.16, kx + r * 0.34, cy - r * 0.30],
                  190, 350, fill=JADE_LIT, width=max(1, px(1.1)))
        d.arc([cx - r * 1.02, cy - r * 1.02, cx + r * 1.02, cy + r * 0.55],
              200, 340, fill=JADE_LIT, width=max(1, px(1.2)))
        d.line([(cx - r * 0.55, cy + r * 0.55), (cx + r * 0.60, cy + r * 0.35)],
               fill=JADE_DK, width=max(1, px(1.0)))       # finger seam
    else:
        d.arc([cx - r * 0.9, cy - r * 0.9, cx + r * 0.9, cy + r * 0.7],
              200, 340, fill=JADE_LIT, width=max(1, px(1.2)))
        for k in (-0.45, -0.05, 0.35, 0.72):            # fingers curled up
            d.line([(cx + k * r * 0.85, cy - r * 0.55),
                    (cx + k * r * 1.05, cy + r * 0.55)],
                   fill=JADE_DK, width=max(1, px(0.9)))
        d.line([(cx - r * 0.80, cy + r * 0.10), (cx - r * 1.15, cy + r * 0.55)],
               fill=JADE_DK, width=max(1, px(1.2)))       # thumb
    # wrist bangle, gold, sitting where the arm meets the hand
    d.rectangle([cx - r * 0.80, cy + r * 0.80, cx + r * 0.80,
                 cy + r * 0.80 + px(2.4)], fill=GOLD)
    d.line([(cx - r * 0.80, cy + r * 0.80), (cx + r * 0.80, cy + r * 0.80)],
           fill=GOLD_DK, width=max(1, px(0.8)))


def statue_layer():
    """The six-armed figure plus its halo, and the neon rim of the body."""
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd_ = ImageDraw.Draw(halo)
    hy = STATUE_TOP + px(50)
    hd_.ellipse([CX - HALO_R, hy - HALO_R, CX + HALO_R, hy + HALO_R],
                fill=(30, 39, 35))
    hd_.ellipse([CX - HALO_R, hy - HALO_R, CX + HALO_R, hy + HALO_R],
                outline=(70, 90, 76), width=max(2, px(2.0)))
    for k in range(24):
        a = k * (math.tau / 24)
        x0 = CX + math.cos(a) * (HALO_R - px(11))
        y0 = hy + math.sin(a) * (HALO_R - px(11))
        x1 = CX + math.cos(a) * (HALO_R - px(2))
        y1 = hy + math.sin(a) * (HALO_R - px(2))
        hd_.line([(x0, y0), (x1, y1)], fill=(104, 128, 108),
                 width=max(1, px(1.3)))

    body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)

    head_cy = STATUE_TOP + px(33)
    head_r = px(15)
    leg_cy = STATUE_TOP + px(84)
    shoulder_y = STATUE_TOP + px(51)
    hip_y = STATUE_TOP + px(72)

    # crossed legs, a low wide mass with the knees breaking the silhouette
    d.ellipse([CX - px(46), leg_cy - px(13), CX + px(46), leg_cy + px(14)],
              fill=JADE_DK)
    d.arc([CX - px(46), leg_cy - px(13), CX + px(46), leg_cy + px(14)],
          196, 344, fill=JADE_LIT, width=max(1, px(1.6)))
    for k in (-0.66, -0.33, 0.33, 0.66):
        d.line([(CX + k * px(34), leg_cy + px(2)), (CX + k * px(24), leg_cy + px(10))],
               fill=(58, 74, 64), width=max(1, px(1.3)))
    # crossed ankles in the middle
    d.ellipse([CX - px(10), leg_cy + px(2), CX + px(10), leg_cy + px(10)],
              fill=JADE)

    # The still's body is massively heavier than the head: wide traps sloping
    # into a small head, a thick chest, and a big smooth belly over the lap.
    d.polygon([(CX - px(33), shoulder_y), (CX + px(33), shoulder_y),
               (CX + px(28), hip_y), (CX - px(28), hip_y)], JADE)
    d.polygon([(CX - px(33), shoulder_y), (CX - px(16), shoulder_y),
               (CX - px(18), hip_y), (CX - px(28), hip_y)], JADE_LIT)
    for sx in (-1, 1):                                        # trapezius
        d.polygon([(CX + sx * px(31), shoulder_y - px(2)),
                   (CX + sx * px(9), head_cy + px(11)),
                   (CX + sx * px(13), shoulder_y + px(7)),
                   (CX + sx * px(31), shoulder_y + px(7))], JADE)
    d.ellipse([CX - px(27), hip_y - px(20), CX + px(27), hip_y + px(7)],
              fill=JADE, outline=(84, 108, 92), width=max(1, px(1.0)))
    d.arc([CX - px(24), hip_y - px(18), CX + px(24), hip_y + px(2)], 200, 340,
          fill=JADE_LIT, width=max(1, px(1.4)))               # belly highlight
    for sx in (-1, 1):                                        # pecs
        xa, xb = sorted((CX + sx * px(1), CX + sx * px(21)))
        d.ellipse([xa, shoulder_y + px(2), xb, shoulder_y + px(19)],
                  outline=(84, 108, 92), width=max(1, px(1.0)))
    # sash and belt
    d.line([(CX - px(24), hip_y - px(2)), (CX + px(24), hip_y - px(2))],
           fill=GOLD, width=max(2, px(3.0)))
    # necklace
    d.arc([CX - px(14), shoulder_y - px(2), CX + px(14), shoulder_y + px(16)],
          15, 165, fill=GOLD, width=max(1, px(2.0)))

    # Six arms, in the three tiers of the film statue: fists raised level with
    # the head, fists out at the chest, fists resting on the knees. Each is a
    # deltoid, a tapered upper arm, an elbow, a tapered forearm and a hand, so
    # the silhouette is a body rather than sticks off the shoulders.
    for sx in (-1, 1):
        tiers = [
            # (shoulder, elbow, hand, fist?) - in the still the arms are nearly
            # as heavy as the torso: elbows thrown wide, thick upper arms with a
            # bicep swell, forearms coming back in, and big fists.
            ((px(29), shoulder_y + px(1)), (px(49), shoulder_y - px(3)),
             (px(50), shoulder_y - px(16)), True),
            ((px(29), shoulder_y + px(3)), (px(57), shoulder_y + px(9)),
             (px(47), shoulder_y + px(21)), True),
            ((px(27), shoulder_y + px(6)), (px(45), shoulder_y + px(22)),
             (px(38), shoulder_y + px(32)), False),
        ]
        for (sx0, sy0), (ex, ey), (hx, hy), fist in tiers:
            sh = (CX + sx * sx0, sy0)
            el = (CX + sx * ex, ey)
            wr = (CX + sx * hx, hy)
            _segment(d, sh, el, px(11.5), px(8.4))
            _segment(d, el, wr, px(8.0), px(5.8))
            # bicep, swelling just inside the upper arm's own contour
            _joint(d, (sh[0] + el[0]) / 2, (sh[1] + el[1]) / 2, px(10.4))
            _joint(d, *sh, px(12.2), edge=JADE_DK)  # deltoid, outlined: it is a
            _joint(d, *el, px(8.2))                 # shoulder; elbow is soft
            _hand(d, wr[0], wr[1], px(9.0), fist)

    # head
    d.ellipse([CX - head_r, head_cy - head_r, CX + head_r, head_cy + head_r],
              fill=JADE)
    d.ellipse([CX - head_r, head_cy - head_r, CX + head_r, head_cy + head_r],
              outline=JADE_LIT, width=max(1, px(1.3)))
    for sx in (-1, 1):
        # long ears of a bodhisattva, the guardian's not the Buddha's
        d.rectangle([CX + sx * head_r - px(2.4), head_cy - px(6),
                     CX + sx * head_r + px(2.4), head_cy + px(9)], fill=JADE_DK)

    # The face is a demon's, as on the statue in the film: heavy brows over open
    # eyes lit from within, and a snarling jaw whose fangs come up off the lower
    # lip. The eye light is drawn on its own layer (see ``glow``) so the stage
    # lighting cannot dim it.
    eye_y = head_cy - px(2)
    for sx in (-1, 1):
        ex = CX + sx * px(6.5)
        d.polygon([(ex - sx * px(6.5), eye_y - px(7.5)),
                   (ex + sx * px(6.0), eye_y - px(5.0)),
                   (ex + sx * px(5.0), eye_y - px(2.2)),
                   (ex - sx * px(6.5), eye_y - px(2.6))], fill=JADE_DK)
        d.line([(ex - sx * px(6.5), eye_y - px(2.6)),
                (ex + sx * px(5.2), eye_y - px(2.2))], fill=JADE_LIT,
               width=max(1, px(0.9)))
        # A deep socket with a small ember in it, not a big orange disc: the
        # still keeps the light tight and the shadow around it huge.
        d.ellipse([ex - px(4.6), eye_y - px(2.6), ex + px(4.6), eye_y + px(3.0)],
                  fill=(16, 10, 10), outline=JADE_DK, width=max(1, px(0.9)))
        d.ellipse([ex - px(1.7), eye_y + px(0.2), ex + px(1.7), eye_y + px(2.3)],
                  fill=(214, 58, 30))
        d.ellipse([ex - px(1.0), eye_y + px(0.7), ex + px(1.0), eye_y + px(2.0)],
                  fill=(250, 122, 52))
        d.ellipse([ex - px(0.42), eye_y + px(1.1), ex + px(0.42), eye_y + px(1.7)],
                  fill=(255, 238, 196))

    # nose: a broad wedge between the eyes and the jaw
    d.polygon([(CX - px(2.6), head_cy - px(1.0)), (CX + px(2.6), head_cy - px(1.0)),
               (CX + px(3.4), head_cy + px(3.6)), (CX - px(3.4), head_cy + px(3.6))],
              fill=(92, 118, 100))
    d.line([(CX - px(3.4), head_cy + px(3.6)), (CX + px(3.4), head_cy + px(3.6))],
           fill=JADE_DK, width=max(1, px(0.9)))

    # jaw: the mouth opening, teeth along the top of it, fangs off the bottom
    mouth_y = head_cy + px(7.6)
    d.polygon([(CX - px(10.5), mouth_y - px(3.4)),
               (CX - px(6.0), mouth_y - px(0.6)),
               (CX, mouth_y + px(1.2)),
               (CX + px(6.0), mouth_y - px(0.6)),
               (CX + px(10.5), mouth_y - px(3.4)),
               (CX + px(7.4), mouth_y + px(0.4)),
               (CX - px(7.4), mouth_y + px(0.4))], fill=(20, 14, 14))
    d.line([(CX - px(10.5), mouth_y - px(3.4)), (CX - px(6.0), mouth_y - px(0.6)),
            (CX, mouth_y + px(1.2)), (CX + px(6.0), mouth_y - px(0.6)),
            (CX + px(10.5), mouth_y - px(3.4))], fill=(120, 146, 124),
           width=max(1, px(1.0)))                        # upper lip
    for k in (-0.62, -0.36, -0.12, 0.12, 0.36, 0.62):    # small upper teeth
        tx = CX + k * px(9.0)
        d.polygon([(tx - px(0.85), mouth_y - px(2.2)), (tx + px(0.85), mouth_y - px(2.2)),
                   (tx, mouth_y - px(0.2))], fill=(226, 222, 200))
    for k, size in ((-0.50, 1.0), (-0.17, 0.62), (0.17, 0.62), (0.50, 1.0)):
        tx = CX + k * px(13.0)                            # fangs, pointing up
        w, h = px(1.5) * size, px(4.4) * size
        d.polygon([(tx - w, mouth_y + px(3.0)), (tx + w, mouth_y + px(3.0)),
                   (tx, mouth_y + px(3.0) - h)], fill=(240, 236, 214))
        d.line([(tx, mouth_y + px(3.0) - h), (tx + w, mouth_y + px(3.0))],
               fill=(146, 140, 118), width=max(1, px(0.7)))
    d.line([(CX - px(7.4), mouth_y + px(3.2)), (CX, mouth_y + px(3.9)),
            (CX + px(7.4), mouth_y + px(3.2))], fill=JADE_DK,
           width=max(1, px(1.1)))                          # lower lip
    # crown: band plus five points, with a jade cabochon
    d.rectangle([CX - head_r, head_cy - px(17), CX + head_r, head_cy - px(11)],
                fill=GOLD)
    for k in (-0.74, -0.37, 0.0, 0.37, 0.74):
        tip = head_cy - px(24) if k == 0 else head_cy - px(21)
        d.polygon([(CX + k * px(13) - px(2.6), head_cy - px(16)),
                   (CX + k * px(13), tip),
                   (CX + k * px(13) + px(2.6), head_cy - px(16))], fill=GOLD)
    d.ellipse([CX - px(3), head_cy - px(16), CX + px(3), head_cy - px(10)],
              fill=(58, 150, 116))

    rim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    solid = body.split()[3].point(lambda v: 255 if v > 60 else 0)
    glow = solid.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(px(0.7)))
    rim.paste(Image.new("RGBA", (W, H), NEON + (255,)), (0, 0),
              ImageChops.subtract(glow, solid))

    # Eye light, on its own layer: concentric falloff so it blooms over the face
    # and the wall behind it whatever the stage lighting is doing.
    eyes = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ed = ImageDraw.Draw(eyes)
    for sx in (-1, 1):
        ex = CX + sx * px(6.5)
        ey = head_cy - px(1.6)
        for step, (rad, alpha) in enumerate(((px(3.4), 26), (px(2.3), 50),
                                             (px(1.5), 88), (px(0.95), 132))):
            ed.ellipse([ex - rad, ey - rad * 0.86, ex + rad, ey + rad * 0.86],
                       fill=(255, 74, 32, alpha))
    eyes = eyes.filter(ImageFilter.GaussianBlur(px(0.7)))

    layer = Image.alpha_composite(halo, body)
    return layer, rim, eyes


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
    statue, rim, eyes = statue_layer()
    base = Image.alpha_composite(base, statue)
    # The mezzanine strip is drawn before the figure but screened in at the end,
    # so without this it would glow straight across the stone. Punching the
    # statue's silhouette out of the neon layer puts the lines behind it: they
    # meet at the centre and vanish under the body and halo, as they would in
    # the room.
    neon.putalpha(ImageChops.subtract(
        neon.split()[3],
        statue.split()[3].point(lambda v: 255 if v > 40 else 0)))

    for sx in (-1, 1):
        base = throne.guardian(base, CX + sx * px(150), FLOOR_Y, px(28))
    d = ImageDraw.Draw(base)
    for sx in (-1, 1):
        throne.brazier(d, CX + sx * px(112), FLOOR_Y, px(24))
        LIGHTS.append((CX + sx * px(112), FLOOR_Y - px(14), px(46),
                       (255, 168, 88), 130))
    LIGHTS.append((CX, PLINTH_TOP + px(10), px(112), (40, 200, 126), 96))
    LIGHTS.append((CX, STATUE_TOP + px(33), px(76), (52, 200, 132), 70))
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
