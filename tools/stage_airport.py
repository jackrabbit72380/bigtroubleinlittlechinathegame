"""Airport Terminal: a departures hall with the fight in the middle of it.

What has to read on screen:

  * a full-height curtain wall of glazing across the back, with structural piers
    between the bays and a transom line above head height
  * the apron behind it: parked airliners nose-in at their gates with wing, fin,
    engines and cabin windows, jet bridges, service trucks and a control tower
  * a coffered ceiling with recessed light strips and hanging gate signs
  * polished terrazzo, cut into tiles that foreshorten towards the camera
  * rows of airport waiting chairs in bays, so there is seating everywhere the
    camera can pan
  * a security checkpoint: walk-through detector, X-ray machine with its belt
    and grey trays, and stanchions with retractable belts
  * a baggage carousel with a loop of belt and cases riding it

Geometry is the shared HD model: 4000x1080 canvas, floor at zoffset 900,
localcoord 1920x1080, camera travel +/-1788. Nothing painted here blocks the
fighters' feet.

Run:  python3 tools/stage_airport.py      (part of tools/build_all.py)
"""

from __future__ import annotations

import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art
import stages_hd as hd

W, H = hd.W, hd.H
CX, FLOOR_Y, px = hd.CX, hd.FLOOR_Y, hd.px

CEIL_Y = px(36)                  # underside of the ceiling
GLASS_TOP = px(30)               # head of the glazing
GLASS_BOT = px(196)              # window sill
HORIZON = px(118)                # apron meets sky

STEEL = (158, 168, 178)
STEEL_DARK = (92, 100, 108)
TERRAZZO = (172, 168, 162)
SKY_HIGH = (78, 126, 176)
SKY_LOW = (212, 226, 234)
APRON = (122, 124, 126)
SEAT = (34, 40, 50)
SEAT_LIT = (62, 72, 86)
SIGN = (18, 46, 74)


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# --------------------------------------------------------------- outside world
def airliner(d, cx, ground, length, livery=(236, 238, 240), tail=(188, 48, 52)):
    """A parked airliner in profile, seen through the glazing."""
    body_h = max(8, int(length * 0.17))
    mid = ground - body_h * 1.05
    x0, x1 = cx - length // 2, cx + length // 2
    nose = int(length * 0.16)

    d.rounded_rectangle([x0 + nose, mid - body_h // 2, x1, mid + body_h // 2],
                        radius=body_h // 2, fill=livery)
    d.ellipse([x0, mid - body_h // 2, x0 + nose * 2, mid + body_h // 2], fill=livery)
    d.polygon([(x1 - body_h, mid - body_h // 2),
               (x1 + int(length * 0.10), mid - int(body_h * 0.18)),
               (x1 + int(length * 0.10), mid + int(body_h * 0.12)),
               (x1 - body_h, mid + body_h // 2)], fill=livery)

    fin_h = int(body_h * 2.1)
    fx = x1 - int(length * 0.05)
    d.polygon([(fx - int(length * 0.10), mid - body_h // 2),
               (fx, mid - body_h // 2 - fin_h),
               (fx + int(length * 0.03), mid - body_h // 2 - fin_h),
               (fx + int(length * 0.04), mid - body_h // 2)], fill=tail)
    d.polygon([(fx - int(length * 0.12), mid),
               (fx + int(length * 0.02), mid - body_h // 3),
               (fx + int(length * 0.02), mid - body_h // 3 + int(body_h * 0.28)),
               (fx - int(length * 0.12), mid + int(body_h * 0.14))], fill=livery)

    d.line([(x0 + nose, mid + body_h // 8), (x1 - body_h, mid + body_h // 8)],
           fill=mix(livery, tail, 0.75), width=max(2, body_h // 9))
    win_y = mid - body_h // 6
    step = max(3, int(body_h * 0.55))
    wx = x0 + nose * 2
    while wx < x1 - body_h * 1.6:
        d.rectangle([wx, win_y, wx + max(2, body_h // 7), win_y + max(2, body_h // 5)],
                    fill=(46, 58, 70))
        wx += step
    d.polygon([(x0 + nose // 2, mid - body_h // 2),
               (x0 + nose * 2, mid - body_h // 2),
               (x0 + nose * 2, mid - body_h // 6),
               (x0 + nose // 2, mid - body_h // 8)], fill=(38, 52, 64))

    wy = mid + body_h // 2 - int(body_h * 0.08)
    wing_c = mix(livery, (104, 112, 120), 0.34)
    root_f, root_b = cx + int(length * 0.04), cx - int(length * 0.15)
    tip_f, tip_b = cx - int(length * 0.22), cx - int(length * 0.29)
    drop = int(body_h * 0.80)
    d.polygon([(root_f, wy), (tip_f, wy + drop),
               (tip_b, wy + drop + int(body_h * 0.12)), (root_b, wy + int(body_h * 0.22))],
              fill=wing_c)
    d.line([(root_f, wy), (tip_f, wy + drop)],
           fill=mix(wing_c, (255, 255, 255), 0.40), width=max(2, body_h // 12))
    for ex in (cx - int(length * 0.02), cx + int(length * 0.14)):
        nw, nh = max(6, int(length * 0.085)), max(4, int(body_h * 0.55))
        ey = wy + int(body_h * 0.26)
        d.rounded_rectangle([ex, ey, ex + nw, ey + nh], radius=nh // 2,
                            fill=(186, 190, 196))
        d.ellipse([ex + nw // 6, ey + nh // 4,
                   ex + nw - nw // 6, ey + nh - nh // 4],
                  fill=(38, 42, 46))

    for gx in (x0 + nose * 2, x1 - body_h * 2):
        d.line([(gx, mid + body_h // 2), (gx, ground - int(body_h * 0.2))],
               fill=STEEL_DARK, width=max(2, body_h // 10))
        d.ellipse([gx - body_h // 3, ground - int(body_h * 0.2), gx + body_h // 3, ground],
                  fill=(32, 34, 38))
    return x0, x0 + nose * 2, mid - body_h // 6


def apron(base):
    """Sky, concrete apron, runway furniture, tower and the parked aircraft."""
    d = ImageDraw.Draw(base)
    for y in range(0, HORIZON):
        d.line([(0, y), (W, y)], fill=mix(SKY_HIGH, SKY_LOW, (y / max(1, HORIZON)) ** 0.75))

    rnd = random.Random(8)
    cloud = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cloud)
    for _ in range(26):
        cx = rnd.randint(-px(60), W)
        cy = rnd.randint(px(4), int(HORIZON * 0.7))
        rw, rh = rnd.randint(px(30), px(110)), rnd.randint(px(8), px(22))
        cd.ellipse([cx - rw, cy - rh, cx + rw, cy + rh],
                   fill=(255, 255, 255, rnd.randint(26, 62)))
    base.alpha_composite(cloud.filter(ImageFilter.GaussianBlur(px(5))))

    d = ImageDraw.Draw(base)
    d.rectangle([0, HORIZON, W, GLASS_BOT + px(24)], fill=APRON)
    for x in range(-px(40), W + px(40), px(30)):
        d.line([(x, HORIZON), (x - px(10), GLASS_BOT + px(20))], fill=(112, 114, 116), width=1)
    for i in range(7):
        y = HORIZON + int((GLASS_BOT + px(20) - HORIZON) * (i / 7) ** 1.5)
        d.line([(0, y), (W, y)], fill=(114, 116, 118), width=1)
    d.line([(0, HORIZON + px(6)), (W, HORIZON + px(7))], fill=(230, 230, 224), width=px(1.4))
    for x in range(0, W, px(70)):
        d.line([(x, HORIZON + px(16)), (x + px(30), HORIZON + px(17))],
               fill=(228, 228, 222), width=px(1))

    tx = CX + px(240)
    d.rectangle([tx - px(14), HORIZON - px(56), tx + px(14), HORIZON], fill=(150, 158, 168))
    d.polygon([(tx - px(26), HORIZON - px(56)), (tx + px(26), HORIZON - px(56)),
               (tx + px(20), HORIZON - px(74)), (tx - px(20), HORIZON - px(74))],
              fill=(126, 138, 150))
    d.rectangle([tx - px(20), HORIZON - px(70), tx + px(20), HORIZON - px(58)],
                fill=(206, 226, 236))

    for cx, ln, tail in ((CX - px(210), px(150), (186, 42, 48)),
                         (CX + px(40), px(132), (30, 82, 146)),
                         (CX + px(250), px(112), (204, 142, 38))):
        ground = HORIZON + px(rnd.randint(26, 40))
        airliner(d, cx, ground, ln, tail=tail)

    for vx, vc in ((CX - px(60), (232, 196, 64)), (CX + px(150), (216, 220, 226))):
        vy = GLASS_BOT - px(20)
        d.rounded_rectangle([vx, vy - px(12), vx + px(38), vy], radius=px(3), fill=vc)
        d.rectangle([vx + px(6), vy - px(20), vx + px(26), vy - px(12)],
                    fill=mix(vc, (40, 44, 48), 0.45))
        for wx in (vx + px(8), vx + px(30)):
            d.ellipse([wx - px(4), vy - px(4), wx + px(4), vy + px(4)], fill=(34, 36, 40))


# ------------------------------------------------------------------- structure
def ceiling(base):
    d = ImageDraw.Draw(base)
    d.rectangle([0, 0, W, CEIL_Y], fill=(194, 196, 198))
    for x in range(-px(20), W, px(96)):
        d.rectangle([x + px(6), px(6), x + px(88), CEIL_Y - px(5)], fill=(206, 208, 210))
        d.line([(x + px(6), px(6)), (x + px(6), CEIL_Y - px(5))],
               fill=(206, 210, 214), width=px(1))
        d.rectangle([x + px(16), px(13), x + px(78), px(21)], fill=(255, 250, 232))
    d.rectangle([0, CEIL_Y - px(6), W, CEIL_Y], fill=(172, 176, 180))
    d.line([(0, CEIL_Y), (W, CEIL_Y)], fill=(168, 172, 178), width=px(1.4))

    for x, text in ((CX - px(120), "GATE 14"), (CX + px(30), "DEPARTURES"),
                    (CX + px(190), "GATE 15")):
        y0, y1 = CEIL_Y + px(4), CEIL_Y + px(16)
        for rx in (x - px(26), x + px(26)):
            d.line([(rx, CEIL_Y), (rx, y0)], fill=STEEL_DARK, width=px(1))
        d.rectangle([x - px(34), y0, x + px(34), y1], fill=SIGN)
        d.rectangle([x - px(34), y0, x + px(34), y1], outline=(120, 168, 200), width=px(1))
        f = art.font(int(px(6.6)))
        w = f.getlength(text)
        d.text((x - w / 2, y0 + px(3)), text, font=f, fill=(224, 244, 255))


def glazing(base):
    """Glass tint, reflections, mullions, transom, sill and the structural piers."""
    glass = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glass)
    gd.rectangle([0, GLASS_TOP, W, GLASS_BOT], fill=(126, 178, 208, 20))
    rnd = random.Random(21)
    for _ in range(90):
        x = rnd.randint(-px(40), W)
        w = rnd.randint(px(6), px(26))
        gd.polygon([(x, GLASS_TOP), (x + w, GLASS_TOP),
                    (x + w + px(26), GLASS_BOT), (x + px(26), GLASS_BOT)],
                   fill=(255, 255, 255, rnd.randint(4, 12)))
    base.alpha_composite(glass)

    d = ImageDraw.Draw(base)
    for x in range(-px(20), W + px(40), px(52)):
        d.rectangle([x, GLASS_TOP, x + px(4), GLASS_BOT], fill=(96, 104, 112))
        d.line([(x, GLASS_TOP), (x, GLASS_BOT)], fill=(168, 176, 184), width=px(1))
    ty = GLASS_TOP + px(58)
    d.rectangle([0, ty, W, ty + px(4)], fill=(100, 108, 116))
    d.line([(0, ty), (W, ty)], fill=(190, 198, 206), width=px(1))
    d.rectangle([0, GLASS_BOT, W, GLASS_BOT + px(7)], fill=(210, 204, 196))
    d.line([(0, GLASS_BOT), (W, GLASS_BOT)], fill=(236, 232, 224), width=px(1))
    d.rectangle([0, GLASS_BOT + px(7), W, GLASS_BOT + px(10)], fill=(176, 172, 166))

    for x in range(-px(30), W + px(60), px(168)):
        d.rectangle([x, CEIL_Y, x + px(20), GLASS_BOT + px(10)], fill=(186, 190, 194))
        d.rectangle([x, CEIL_Y, x + px(3), GLASS_BOT + px(10)], fill=(214, 218, 222))
        d.rectangle([x + px(17), CEIL_Y, x + px(20), GLASS_BOT + px(10)], fill=(176, 180, 184))
        d.rectangle([x - px(2), GLASS_BOT - px(3), x + px(22), GLASS_BOT + px(10)],
                    fill=(198, 200, 202))


def departure_board(base, x, y):
    """Split-flap departures board on a pier."""
    d = ImageDraw.Draw(base)
    w, hgt = px(62), px(40)
    d.rectangle([x - w, y, x + w, y + hgt], fill=(16, 18, 20))
    d.rectangle([x - w, y, x + w, y + hgt], outline=(96, 100, 106), width=px(1))
    f = art.font(int(px(4.4)))
    fsmall = art.font(int(px(3.6)))
    d.text((x - w + px(3), y + px(2)), "DEPARTURES", font=fsmall, fill=(230, 190, 90))
    rows = (("UA 214  DENVER", "ON TIME"), ("CA 88  BEIJING", "BOARDING"),
            ("AA 7  CHICAGO", "GATE 14"), ("PA 2  HONG KONG", "DELAYED"))
    for i, (left, right) in enumerate(rows):
        ry = y + px(9) + i * px(7)
        d.text((x - w + px(3), ry), left, font=f, fill=(120, 226, 150))
        tw = f.getlength(right)
        d.text((x + w - px(3) - tw, ry), right, font=f, fill=(120, 226, 150))


# ---------------------------------------------------------------------- floor
def floor(base):
    d = ImageDraw.Draw(base)
    d.rectangle([0, FLOOR_Y, W, H], fill=TERRAZZO)
    for x in range(-px(20), W + px(40), px(26)):
        d.line([(x, FLOOR_Y), (x - px(9), H)], fill=(176, 172, 166), width=1)
    for i in range(1, 7):
        y = FLOOR_Y + int((H - FLOOR_Y) * (i / 7) ** 1.6)
        d.line([(0, y), (W, y)], fill=(178, 174, 168), width=1)

    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    for x in range(-px(20), W + px(40), px(52)):
        rd.rectangle([x, FLOOR_Y, x + px(6), FLOOR_Y + px(34)],
                     fill=(255, 255, 255, 26))
    base.alpha_composite(refl.filter(ImageFilter.GaussianBlur(px(6))))
    d = ImageDraw.Draw(base)
    d.line([(0, FLOOR_Y), (W, FLOOR_Y)], fill=(120, 116, 112), width=px(1.4))


def seat_row(base, cx, y, s=1.0, seats=4):
    """A bench of airport chairs: backs, seat pans, armrests, legs."""
    d = ImageDraw.Draw(base)

    def u(v):
        return int(round(v * s))

    w = u(px(15))
    gap = max(1, u(px(2.4)))
    total = seats * w + (seats - 1) * gap
    x = cx - total / 2
    back_h = u(px(24))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([x - u(px(4)), y + u(px(2)), x + total + u(px(4)), y + u(px(9))],
               fill=(18, 20, 24, 96))
    base.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(u(px(1.6)))))
    for i in range(seats):
        sx = x + i * (w + gap)
        d.rounded_rectangle([sx, y - back_h, sx + w, y - u(px(2))],
                            radius=u(px(2)), fill=SEAT)
        d.rounded_rectangle([sx + u(px(1)), y - back_h + u(px(1)),
                             sx + w - u(px(1)), y - u(px(4))],
                            radius=u(px(2)), fill=SEAT_LIT)
        d.rounded_rectangle([sx, y - u(px(3)), sx + w, y + u(px(3))],
                            radius=u(px(2)), fill=mix(SEAT, (20, 24, 30), 0.3))
        d.line([(sx + u(px(3)), y + u(px(3))), (sx + u(px(3)), y + u(px(6)))],
               fill=STEEL_DARK, width=max(1, u(px(0.9))))
        d.line([(sx + w - u(px(3)), y + u(px(3))), (sx + w - u(px(3)), y + u(px(6)))],
               fill=STEEL_DARK, width=max(1, u(px(0.9))))
    for i in range(seats + 1):
        ax = x + i * (w + gap) - gap / 2
        d.line([(ax, y - back_h + u(px(2))), (ax, y + u(px(2)))],
               fill=STEEL, width=max(1, u(px(1.4))))
    d.line([(x, y + u(px(5))), (x + total, y + u(px(5)))],
           fill=STEEL_DARK, width=max(1, u(px(1))))
    d.line([(x, y + u(px(5))), (x + total, y + u(px(5)))],
           fill=STEEL, width=max(1, u(px(0.7))))


def seats(base):
    """Rows of chairs in bays along the hall, backs to the glazing."""
    for cx in range(-px(60), W + px(120), px(300)):
        seat_row(base, cx, FLOOR_Y - px(6), s=1.55, seats=4)
        seat_row(base, cx + px(110), FLOOR_Y + px(4), s=1.3, seats=3)


# ------------------------------------------------------------------ checkpoint
def stanchion(base, x, y, h=px(26)):
    d = ImageDraw.Draw(base)
    d.ellipse([x - px(3), y - px(2), x + px(3), y + px(4)], fill=(70, 74, 80))
    d.line([(x, y - px(2)), (x, y - h)], fill=STEEL, width=max(2, px(1.6)))
    d.ellipse([x - px(2.4), y - h - px(2.4), x + px(2.4), y - h + px(2.4)],
              fill=(186, 192, 198))


def belt_between(base, x0, x1, y):
    """Retractable belt: sags a little between two posts."""
    d = ImageDraw.Draw(base)
    mid = (x0 + x1) / 2
    d.line([(x0, y - px(10)), (mid, y - px(7)), (x1, y - px(10))],
           fill=(38, 40, 46), width=max(2, px(0.9)))
    d.line([(x0, y - px(8)), (mid, y - px(5)), (x1, y - px(8))],
           fill=(120, 40, 44), width=max(1, px(0.5)))


def security(base, cx):
    """Walk-through detector, X-ray machine with belt and trays, belt queue."""
    d = ImageDraw.Draw(base)
    y = FLOOR_Y + px(6)

    ax, aw, ah = cx - px(78), px(34), px(46)
    d.rectangle([ax - px(2), y - ah - px(4), ax + aw + px(2), y - ah], fill=(206, 210, 214))
    for side in (ax, ax + aw):
        d.rectangle([side - px(3), y - ah, side + px(3), y], fill=(196, 200, 204))
        d.line([(side - px(3), y - ah), (side - px(3), y)], fill=(232, 236, 240), width=px(1))
        d.line([(side + px(3), y - ah), (side + px(3), y)], fill=(160, 164, 170), width=px(1))
    d.ellipse([ax + aw / 2 - px(2), y - ah - px(3), ax + aw / 2 + px(2), y - ah + px(1)],
              fill=(120, 226, 140))

    bx0 = cx + px(6)
    bx1 = bx0 + px(66)
    d.rounded_rectangle([bx0, y - px(34), bx1, y], radius=px(2), fill=(176, 182, 190))
    d.rounded_rectangle([bx0 + px(2), y - px(32), bx1 - px(2), y - px(4)],
                        radius=px(2), fill=(150, 158, 168))
    d.rectangle([bx0 + px(8), y - px(26), bx0 + px(24), y - px(6)], fill=(28, 30, 34))
    for i in range(6):
        sy = y - px(26) + i * px(3.4)
        d.line([(bx0 + px(9), sy), (bx0 + px(23), sy)], fill=(58, 62, 70), width=px(1))
    d.rectangle([bx0 - px(10), y - px(11), bx1 + px(10), y - px(4)], fill=(58, 62, 68))
    d.line([(bx0 - px(10), y - px(11)), (bx1 + px(10), y - px(11))],
           fill=(110, 116, 124), width=px(0.8))
    for tx in (bx0 - px(6), bx0 + px(30), bx0 + px(58)):
        d.polygon([(tx, y - px(11)), (tx + px(16), y - px(11)),
                   (tx + px(14), y - px(17)), (tx - px(2), y - px(17))],
                  fill=(206, 208, 212))
    d.rectangle([bx1 - px(16), y - px(46), bx1 - px(4), y - px(36)], fill=(38, 42, 48))
    d.rectangle([bx1 - px(15), y - px(45), bx1 - px(5), y - px(37)], fill=(96, 176, 208))

    for sx in (cx - px(120), cx - px(30), cx + px(70)):
        stanchion(base, sx, y + px(12))
    belt_between(base, cx - px(120), cx - px(30), y + px(12))
    belt_between(base, cx - px(30), cx + px(70), y + px(12))


def carousel(base, cx, cy):
    """Baggage carousel: stainless loop of belt with cases riding it."""
    d = ImageDraw.Draw(base)
    rx, ry = px(96), px(22)
    d.ellipse([cx - rx - px(6), cy - ry - px(10), cx + rx + px(6), cy + ry + px(10)],
              fill=(186, 190, 196))
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(46, 48, 54))
    d.ellipse([cx - rx + px(8), cy - ry + px(4), cx + rx - px(8), cy + ry - px(4)],
              fill=(64, 66, 72))
    for i in range(34):
        a = 2 * math.pi * i / 34
        x = cx + math.cos(a) * (rx - px(12))
        y = cy + math.sin(a) * (ry - px(5))
        d.line([(x, y), (x + px(4), y + px(1))], fill=(122, 126, 132), width=px(1))

    rnd = random.Random(31)
    for i, a in enumerate((0.4, 1.5, 2.6, 3.9, 5.1)):
        x = cx + math.cos(a) * (rx - px(20))
        y = cy + math.sin(a) * (ry - px(8))
        w = px(20) + rnd.randint(0, int(px(6)))
        h = px(12) + rnd.randint(0, int(px(4)))
        col = ((122, 74, 48), (58, 74, 96), (94, 96, 100), (140, 44, 44), (46, 60, 44))[i % 5]
        d.rounded_rectangle([x - w / 2, y - h, x + w / 2, y], radius=px(2), fill=col)
        d.line([(x - w / 2 + px(2), y - h + px(3)), (x + w / 2 - px(2), y - h + px(3))],
               fill=mix(col, (255, 255, 255), 0.25), width=px(1))

    d.rectangle([cx - px(34), cy - px(52), cx + px(34), cy - px(40)], fill=SIGN)
    f = art.font(int(px(4.6)))
    text = "BAGGAGE CLAIM"
    tw = f.getlength(text)
    d.text((cx - tw / 2, cy - px(50)), text, font=f, fill=(226, 244, 255))


# -------------------------------------------------------------------- the arena
def paint():
    base = hd.blank([(0, (150, 176, 196)), (60, (196, 210, 220)),
                     (150, (214, 222, 228)), (240, (206, 206, 204))])
    apron(base)
    glazing(base)
    ceiling(base)
    floor(base)
    departure_board(base, CX - px(150), CEIL_Y + px(26))

    seats(base)
    security(base, CX - px(150))
    carousel(base, CX + px(170), FLOOR_Y + px(22))

    base = art.vignette(base, 0.32)
    base = art.grain(base, 3, seed=13)

    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    for i in range(px(24)):
        a = int(190 * (1 - i / px(24)) ** 1.4)
        fd.line([(0, H - i), (W, H - i)], fill=(8, 10, 12, a))
    fd.line([(0, H - px(6)), (W, H - px(7))], fill=(52, 56, 62, 210), width=px(1.2))
    return [("bg", 0, 0, base, 0),
            ("fg", 3, 0, fg, 1)]


def main():
    hd.STAGES["airport_terminal"] = ("Airport Terminal", paint)
    hd.build("airport_terminal")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
