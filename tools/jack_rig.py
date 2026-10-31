"""A jointed, true-colour Jack Burton, drawn at 3x the base character's scale.

The roster's fighters are 106px tall inside a 1280x960 stage, which is why they
read as specks next to the HD backdrops. Jack is drawn at 318px here so he fills
a third of the screen like a modern HD fighter; the other fighters follow one at
a time.

Everything is authored in body-space pixels (feet at y=0, up is -y), rendered at
SUPERSAMPLE and reduced, so edges are clean rather than pixel-stepped. The figure
is real anatomy: pelvis, ribcage, shoulder and hip joints, upper/lower segments,
a hand that can grip, and a head with a face.

Angles are degrees. 0 = hanging straight down, positive = swung towards the
enemy (the right of the screen).
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFilter

# --------------------------------------------------------------------- metrics
HIP_Y = -156.0
CHEST_Y = -208.0
NECK_Y = -250.0
HEAD_Y = -286.0

SHOULDER_HALF = 40.0
HIP_HALF = 22.0
UPPER_ARM = 60.0
FORE_ARM = 54.0
THIGH = 74.0
SHIN = 72.0

CANVAS = (300, 420)
AXIS = (150, 366)          # foot contact point inside the canvas
SUPERSAMPLE = 2

# --------------------------------------------------------------------- palette
INK = (26, 18, 14)
SKIN = (232, 184, 150)
SKIN_LIT = (250, 212, 180)
SKIN_SH = (198, 146, 112)
SKIN_DEEP = (158, 108, 80)
TANK = (247, 247, 246)
TANK_LIT = (255, 255, 255)
TANK_SH = (206, 208, 213)
TANK_DEEP = (168, 172, 180)
DENIM = (98, 128, 160)
DENIM_LIT = (138, 168, 198)
DENIM_SH = (68, 92, 118)
DENIM_DEEP = (46, 64, 86)
DENIM_SEAM = (176, 196, 216)
BOOT = (86, 58, 36)
BOOT_LIT = (120, 86, 54)
BOOT_SH = (52, 34, 20)
HAIR = (108, 70, 40)
HAIR_LIT = (146, 100, 58)
HAIR_DARK = (60, 36, 18)
STEEL = (196, 204, 214)
STEEL_LIT = (236, 242, 248)
STEEL_SH = (118, 128, 142)
METAL = (62, 64, 70)
METAL_LIT = (104, 108, 118)


def _d(a):
    """Unit vector for an angle (0 = down, + = toward the enemy)."""
    r = math.radians(a)
    return (math.sin(r), math.cos(r))


def _up(a):
    """Unit vector for a segment pointing up, tilted by `a` degrees."""
    r = math.radians(a)
    return (math.sin(r), -math.cos(r))


def _add(p, v, k=1.0):
    return (p[0] + v[0] * k, p[1] + v[1] * k)


# ------------------------------------------------------------------------ pose
DEFAULT = dict(
    lean=2.0, head=0.0, crouch=0.0, hx=0.0,
    sn=6.0, en=16.0, sf=-4.0, ef=-22.0,
    hn=3.0, kn=4.0, hf=-4.0, kf=6.0,
    gun=True, knife=True, gun_ang=18.0, knife_ang=-24.0,
    fist_near=False, fist_far=False,
)


def pose(**kw):
    p = dict(DEFAULT)
    p.update(kw)
    return p


class Rig:
    def __init__(self, canvas=CANVAS, axis=AXIS, ss=SUPERSAMPLE):
        self.w, self.h = canvas
        self.ax, self.ay = axis
        self.ss = ss
        self.size = (self.w * ss, self.h * ss)

    # -- coordinate helpers ----------------------------------------------
    def P(self, p):
        return ((self.ax + p[0]) * self.ss, (self.ay + p[1]) * self.ss)

    def S(self, v):
        return v * self.ss

    # -- skeleton ---------------------------------------------------------
    def joints(self, p):
        drop = 44.0 * p["crouch"]
        hip = (p["hx"], HIP_Y + drop)
        lean = p["lean"]
        chest = _add(hip, _up(lean), HIP_Y - CHEST_Y)
        neck = _add(chest, _up(lean), CHEST_Y - NECK_Y)
        headc = _add(neck, _up(lean + p["head"]), NECK_Y - HEAD_Y)

        sh_near = (chest[0] + SHOULDER_HALF * 0.86, chest[1] + 6)
        sh_far = (chest[0] - SHOULDER_HALF * 0.92, chest[1] + 10)

        el_near = _add(sh_near, _d(p["sn"]), UPPER_ARM)
        wr_near = _add(el_near, _d(p["sn"] + p["en"]), FORE_ARM)
        el_far = _add(sh_far, _d(p["sf"]), UPPER_ARM)
        wr_far = _add(el_far, _d(p["sf"] + p["ef"]), FORE_ARM)

        hip_near = (hip[0] + HIP_HALF * 0.5, hip[1])
        hip_far = (hip[0] - HIP_HALF * 0.58, hip[1])
        k_near = _add(hip_near, _d(p["hn"]), THIGH)
        a_near = _add(k_near, _d(p["hn"] + p["kn"]), SHIN)
        k_far = _add(hip_far, _d(p["hf"]), THIGH)
        a_far = _add(k_far, _d(p["hf"] + p["kf"]), SHIN)

        return dict(hip=hip, chest=chest, neck=neck, head=headc,
                    sh_near=sh_near, el_near=el_near, wr_near=wr_near,
                    sh_far=sh_far, el_far=el_far, wr_far=wr_far,
                    hip_near=hip_near, k_near=k_near, a_near=a_near,
                    hip_far=hip_far, k_far=k_far, a_far=a_far)

    # -- drawing primitives ----------------------------------------------
    def _capsule(self, img, p0, p1, r0, r1, base, lit, shade):
        A, B = self.P(p0), self.P(p1)
        r0, r1 = self.S(r0), self.S(r1)
        d = math.hypot(B[0] - A[0], B[1] - A[1]) or 1.0
        nx, ny = -(B[1] - A[1]) / d, (B[0] - A[0]) / d

        mask = Image.new("L", self.size, 0)
        md = ImageDraw.Draw(mask)
        md.polygon([(A[0] + nx * r0, A[1] + ny * r0),
                    (B[0] + nx * r1, B[1] + ny * r1),
                    (B[0] - nx * r1, B[1] - ny * r1),
                    (A[0] - nx * r0, A[1] - ny * r0)], fill=255)
        md.ellipse([A[0] - r0, A[1] - r0, A[0] + r0, A[1] + r0], fill=255)
        md.ellipse([B[0] - r1, B[1] - r1, B[0] + r1, B[1] + r1], fill=255)

        body = Image.new("RGBA", self.size, base + (255,))
        body.putalpha(mask)
        img.alpha_composite(body)

        off = max(2.0, r1 * 0.55)
        sh = Image.new("L", self.size, 0)
        sd = ImageDraw.Draw(sh)
        sd.polygon([(A[0] - nx * r0 + off * 0.6, A[1] - ny * r0 + off * 0.6),
                    (B[0] - nx * r1 + off * 0.6, B[1] - ny * r1 + off * 0.6),
                    (B[0] - nx * r1 * 0.2, B[1] - ny * r1 * 0.2),
                    (A[0] - nx * r0 * 0.2, A[1] - ny * r0 * 0.2)], fill=150)
        sh = sh.filter(ImageFilter.GaussianBlur(r1 * 0.5))
        layer = Image.new("RGBA", self.size, shade + (255,))
        layer.putalpha(sh)
        masked = Image.new("RGBA", self.size, (0, 0, 0, 0))
        masked.paste(layer, (0, 0), mask)
        img.alpha_composite(masked)

        rl = Image.new("L", self.size, 0)
        rd = ImageDraw.Draw(rl)
        rd.polygon([(A[0] + nx * r0 * 0.8, A[1] + ny * r0 * 0.8),
                    (B[0] + nx * r1 * 0.8, B[1] + ny * r1 * 0.8),
                    (B[0] + nx * r1 * 0.15, B[1] + ny * r1 * 0.15),
                    (A[0] + nx * r0 * 0.15, A[1] + ny * r0 * 0.15)], fill=140)
        rl = rl.filter(ImageFilter.GaussianBlur(r1 * 0.42))
        layer = Image.new("RGBA", self.size, lit + (255,))
        layer.putalpha(rl)
        masked = Image.new("RGBA", self.size, (0, 0, 0, 0))
        masked.paste(layer, (0, 0), mask)
        img.alpha_composite(masked)

    def _poly(self, img, pts, base, lit=None, shade=None, blur=6, light=(-6, -8)):
        mask = Image.new("L", self.size, 0)
        ImageDraw.Draw(mask).polygon([self.P(q) for q in pts], fill=255)
        body = Image.new("RGBA", self.size, base + (255,))
        body.putalpha(mask)
        img.alpha_composite(body)
        if shade:
            sm = Image.new("L", self.size, 0)
            ImageDraw.Draw(sm).polygon(
                [self.P((q[0] + 9, q[1] + 10)) for q in pts], fill=160)
            sm = sm.filter(ImageFilter.GaussianBlur(blur))
            layer = Image.new("RGBA", self.size, shade + (255,))
            layer.putalpha(sm)
            masked = Image.new("RGBA", self.size, (0, 0, 0, 0))
            masked.paste(layer, (0, 0), mask)
            img.alpha_composite(masked)
        if lit:
            lm = Image.new("L", self.size, 0)
            ImageDraw.Draw(lm).polygon(
                [self.P((q[0] + light[0], q[1] + light[1])) for q in pts], fill=130)
            lm = lm.filter(ImageFilter.GaussianBlur(blur))
            layer = Image.new("RGBA", self.size, lit + (255,))
            layer.putalpha(lm)
            masked = Image.new("RGBA", self.size, (0, 0, 0, 0))
            masked.paste(layer, (0, 0), mask)
            img.alpha_composite(masked)

    # -- body parts -------------------------------------------------------
    def head(self, img, sk, p):
        c = self.P(sk["head"])
        s = self.ss
        rw, rh = 23 * s, 28 * s

        self._capsule(img, _add(sk["neck"], (0, 4)), _add(sk["chest"], (0, -4)),
                      13, 16, SKIN_SH, SKIN, SKIN_DEEP)

        jaw = [(c[0] - rw * 0.82, c[1] - rh * 0.30),
               (c[0] - rw * 0.66, c[1] + rh * 0.40),
               (c[0] - rw * 0.20, c[1] + rh * 0.86),
               (c[0] + rw * 0.44, c[1] + rh * 0.76),
               (c[0] + rw * 0.86, c[1] + rh * 0.18),
               (c[0] + rw * 0.80, c[1] - rh * 0.58)]
        self._poly(img, jaw, SKIN, SKIN_LIT, SKIN_SH, blur=5,
                   light=(-4 * s, -6 * s))

        d = ImageDraw.Draw(img)
        d.line([(c[0] - 6 * s, c[1] - 8 * s), (c[0] + 14 * s, c[1] - 10 * s)],
               fill=HAIR_DARK + (255,), width=int(4 * s))
        d.line([(c[0] - 4 * s, c[1] + 1 * s), (c[0] + 2 * s, c[1] + 6 * s),
                (c[0] + 9 * s, c[1] + 2 * s)], fill=SKIN_DEEP + (170,),
               width=int(2.4 * s))
        for dx, dy in ((4, -4), (12, -4)):
            d.ellipse([c[0] + dx * s, c[1] + dy * s,
                       c[0] + (dx + 7) * s, c[1] + (dy + 4) * s],
                      fill=(250, 250, 248, 255))
            d.ellipse([c[0] + (dx + 2) * s, c[1] + (dy + 1) * s,
                       c[0] + (dx + 5) * s, c[1] + (dy + 4) * s],
                      fill=(64, 108, 152, 255))
        d.line([(c[0] + 2 * s, c[1] + 17 * s), (c[0] + 15 * s, c[1] + 15 * s)],
               fill=(152, 96, 76, 255), width=int(2.6 * s))
        d.line([(c[0] + 15 * s, c[1] + 15 * s), (c[0] + 17 * s, c[1] + 17 * s)],
               fill=(132, 82, 64, 255), width=int(2 * s))

        hair = [(c[0] - rw * 0.95, c[1] - rh * 0.22),
                (c[0] - rw * 0.86, c[1] - rh * 0.92),
                (c[0] - rw * 0.12, c[1] - rh * 1.14),
                (c[0] + rw * 0.58, c[1] - rh * 1.02),
                (c[0] + rw * 0.90, c[1] - rh * 0.50),
                (c[0] + rw * 0.66, c[1] - rh * 0.18),
                (c[0] + rw * 0.12, c[1] - rh * 0.44),
                (c[0] - rw * 0.42, c[1] - rh * 0.30)]
        self._poly(img, hair, HAIR, HAIR_LIT, HAIR_DARK, blur=4,
                   light=(-3 * s, -5 * s))
        d.polygon([(c[0] - rw * 0.95, c[1] - rh * 0.1),
                   (c[0] - rw * 1.12, c[1] + rh * 1.05),
                   (c[0] - rw * 0.55, c[1] + rh * 1.28),
                   (c[0] - rw * 0.35, c[1] + rh * 0.30)],
                  fill=HAIR_DARK + (255,))
        for i in range(5):
            t = i / 4.0
            d.line([(c[0] - rw * (0.55 - 0.3 * t), c[1] - rh * 0.95),
                    (c[0] - rw * (0.2 - 0.15 * t), c[1] - rh * (0.55 + 0.2 * t))],
                   fill=HAIR_LIT + (150,), width=int(1.6 * s))

    def torso(self, img, sk, p):
        hip, chest = sk["hip"], sk["chest"]
        s = self.ss
        self._poly(img, [(chest[0] - 34, chest[1] - 6), (chest[0] + 34, chest[1] - 8),
                         (chest[0] + 30, chest[1] + 26), (chest[0] - 30, chest[1] + 26)],
                   SKIN, SKIN_LIT, SKIN_SH, blur=7)

        wt, wm, wb = 30.0, 26.0, 23.0
        y0 = chest[1] - 2
        y1 = hip[1] + 8
        ymid = y0 + (y1 - y0) * 0.52
        top = [(hip[0] - wt, y0 + 4), (hip[0] - wt * 0.34, y0 - 10),
               (hip[0] + wt * 0.40, y0 - 12), (hip[0] + wt * 0.98, y0 + 2),
               (hip[0] + wm + 4, ymid), (hip[0] + wb, y1),
               (hip[0] - wb, y1), (hip[0] - wm - 3, ymid)]
        self._poly(img, top, TANK, TANK_LIT, TANK_SH, blur=6, light=(-5, -7))

        d = ImageDraw.Draw(img)
        d.line([(hip[0] - 18, y0 + 6), (hip[0] - 2, y0 + 22), (hip[0] + 16, y0 + 3)],
               fill=TANK_DEEP + (220,), width=int(3 * s))
        d.line([(hip[0] - 22, y0 + 4), (hip[0] - 26, y0 + 18)],
               fill=TANK_DEEP + (160,), width=int(2 * s))
        for dx, y in ((-14, ymid - 6), (8, ymid + 2), (16, y1 - 12)):
            d.line([(hip[0] + dx, y), (hip[0] + dx + 6, y + 14)],
                   fill=TANK_SH + (150,), width=int(1.6 * s))

        cx, cy = hip[0] + 2, y0 + 46
        d.ellipse([cx - 17, cy - 17, cx + 16, cy + 16], fill=(216, 150, 160, 255))
        d.polygon([(cx, cy - 15), (cx + 11, cy - 5), (cx + 9, cy + 11),
                   (cx, cy + 17), (cx - 9, cy + 11), (cx - 11, cy - 5)],
                  fill=(150, 178, 118, 255))
        d.line([(cx - 8, cy - 3), (cx - 2, cy - 3)], fill=INK + (255,),
               width=int(3 * s))
        d.line([(cx + 2, cy - 3), (cx + 8, cy - 3)], fill=INK + (255,),
               width=int(3 * s))
        d.line([(cx, cy + 4), (cx, cy + 10)], fill=(96, 44, 44, 255),
               width=int(3 * s))
        for sgn in (-1, 1):
            d.line([(cx + sgn * 6, cy - 14), (cx + sgn * 9, cy - 21)],
                   fill=(120, 150, 96, 255), width=int(2.6 * s))

        d.rectangle([hip[0] - wb - 2, y1 - 4, hip[0] + wb + 2, y1 + 4],
                    fill=(62, 42, 26, 255))
        d.rectangle([hip[0] - 7, y1 - 5, hip[0] + 7, y1 + 5],
                    fill=(184, 158, 100, 255))

    def leg(self, img, hipj, knee, ankle, near=True):
        r0, r1, r2 = (23, 17, 13) if near else (22, 16, 12.5)
        self._capsule(img, hipj, knee, r0, r1, DENIM, DENIM_LIT, DENIM_SH)
        self._capsule(img, knee, ankle, r1, r2, DENIM, DENIM_LIT, DENIM_SH)
        d = ImageDraw.Draw(img)
        s = self.ss
        a, b = self.P(knee), self.P(ankle)
        d.line([(a[0] - 3 * s, a[1]), (b[0] - 2 * s, b[1] - 4 * s)],
               fill=DENIM_SEAM + (170,), width=int(2 * s))
        d.line([(b[0] - r2 * s, b[1]), (b[0] + r2 * s, b[1] - 2 * s)],
               fill=DENIM_DEEP + (210,), width=int(3 * s))

    def boot(self, img, knee, ankle):
        s = self.ss
        self._capsule(img, _add(knee, (0, -4)), ankle, 20, 15,
                      BOOT, BOOT_LIT, BOOT_SH)
        A = self.P(ankle)
        d = ImageDraw.Draw(img)
        d.ellipse([A[0] - 15 * s, A[1] - 12 * s, A[0] + 26 * s, A[1] + 12 * s],
                  fill=BOOT + (255,))
        d.ellipse([A[0] - 12 * s, A[1] - 10 * s, A[0] + 22 * s, A[1] + 6 * s],
                  fill=BOOT_LIT + (255,))
        d.line([(A[0] - 14 * s, A[1] + 9 * s), (A[0] + 26 * s, A[1] + 9 * s)],
               fill=BOOT_SH + (255,), width=int(4 * s))
        K = self.P(knee)
        d.line([(K[0] - 10 * s, K[1] + 8 * s), (A[0] - 8 * s, A[1] - 6 * s)],
               fill=BOOT_SH + (140,), width=int(2 * s))
        for i in range(3):
            t = 0.2 + i * 0.24
            x = K[0] + (A[0] - K[0]) * t
            y = K[1] + (A[1] - K[1]) * t
            d.line([(x - 8 * s, y), (x + 9 * s, y - 2 * s)],
                   fill=(208, 184, 118, 255), width=int(2.4 * s))

    def hand(self, img, wrist, near=True, fist=False):
        w = self.P(wrist)
        s = self.ss
        d = ImageDraw.Draw(img)
        r = 10 * s
        d.ellipse([w[0] - r, w[1] - r, w[0] + r, w[1] + r],
                  fill=(SKIN if near else SKIN_SH) + (255,))
        d.ellipse([w[0] - r * 0.7, w[1] - r * 0.8, w[0] + r * 0.4, w[1] + r * 0.2],
                  fill=SKIN_LIT + (200,))
        if not fist:
            d.line([(w[0] - 2 * s, w[1] + 3 * s), (w[0] + 6 * s, w[1] + 2 * s)],
                   fill=SKIN_DEEP + (170,), width=int(1.6 * s))
        return w

    def pistol(self, img, hand, ang):
        s = self.ss
        a = math.radians(ang - 90)
        ca, sa = math.cos(a), math.sin(a)

        def T(x, y):
            return (hand[0] + (x * ca - y * sa) * s, hand[1] + (x * sa + y * ca) * s)

        d = ImageDraw.Draw(img)
        d.polygon([T(-2, -6), T(34, -6), T(36, -1), T(4, 0), T(3, 13),
                   T(-7, 13), T(-9, 2)], fill=METAL + (255,))
        d.polygon([T(1, -6), T(34, -6), T(34, -3), T(1, -3)],
                  fill=METAL_LIT + (255,))
        d.polygon([T(2, 1), T(6, 1), T(4, 13), T(-4, 13)],
                  fill=(38, 38, 44, 255))
        d.line([T(8, -2), T(30, -2)], fill=(28, 28, 32, 255), width=int(1.6 * s))

    def knife(self, img, hand, ang):
        s = self.ss
        a = math.radians(ang - 90)
        ca, sa = math.cos(a), math.sin(a)

        def T(x, y):
            return (hand[0] + (x * ca - y * sa) * s, hand[1] + (x * sa + y * ca) * s)

        d = ImageDraw.Draw(img)
        d.polygon([T(-16, -3), T(-2, -4), T(-1, 4), T(-16, 3)],
                  fill=(66, 42, 24, 255))
        d.polygon([T(-2, -7), T(2, -7), T(2, 7), T(-2, 7)],
                  fill=STEEL_SH + (255,))
        d.polygon([T(2, -4), T(26, -3), T(34, 0), T(26, 3), T(2, 4)],
                  fill=STEEL + (255,))
        d.polygon([T(2, -4), T(26, -3), T(29, -1), T(2, -1)],
                  fill=STEEL_LIT + (255,))

    # -- render -----------------------------------------------------------
    def render(self, p):
        img = Image.new("RGBA", self.size, (0, 0, 0, 0))
        sk = self.joints(p)

        self.leg(img, sk["hip_far"], sk["k_far"], sk["a_far"], near=False)
        self.boot(img, sk["k_far"], sk["a_far"])
        self._capsule(img, sk["sh_far"], sk["el_far"], 18, 15,
                      SKIN_SH, SKIN, SKIN_DEEP)
        self._capsule(img, sk["el_far"], sk["wr_far"], 15, 12,
                      SKIN_SH, SKIN, SKIN_DEEP)
        hf = self.hand(img, sk["wr_far"], near=False, fist=p["fist_far"])
        if p["knife"]:
            self.knife(img, hf, p["knife_ang"])

        self.leg(img, sk["hip_near"], sk["k_near"], sk["a_near"])
        self.boot(img, sk["k_near"], sk["a_near"])
        self.torso(img, sk, p)
        self.head(img, sk, p)
        self._capsule(img, sk["sh_near"], sk["el_near"], 20, 16,
                      SKIN, SKIN_LIT, SKIN_SH)
        self._capsule(img, sk["el_near"], sk["wr_near"], 16, 12.5,
                      SKIN, SKIN_LIT, SKIN_SH)
        hn = self.hand(img, sk["wr_near"], fist=p["fist_near"])
        if p["gun"]:
            self.pistol(img, hn, p["gun_ang"])

        sh = Image.new("RGBA", self.size, (0, 0, 0, 0))
        cx = self.P((sk["hip"][0], 0))[0]
        sw = self.S(46)
        ImageDraw.Draw(sh).ellipse([cx - sw, self.S(self.ay - 2), cx + sw,
                                    self.S(self.ay + 4)], fill=(0, 0, 0, 96))
        sh = sh.filter(ImageFilter.GaussianBlur(4 * self.ss))
        out = Image.alpha_composite(sh, img)
        return out.resize((self.w, self.h), Image.LANCZOS)


def frame(p, canvas=CANVAS, axis=AXIS):
    return Rig(canvas, axis).render(p)


class JackRig(Rig):
    """Refined pass: proper skull, short thick neck, fitted tank, slimmer boots,
    plus a dark contour so the figure reads against a busy stage."""

    def head(self, img, sk, p):
        c = self.P(sk["head"])
        s = self.ss
        rw, rh = 26 * s, 30 * s

        # neck: short and thick, from the collar to the jaw
        self._capsule(img, _add(sk["neck"], (2, 10)), _add(sk["chest"], (0, -8)),
                      16, 19, SKIN_SH, SKIN, SKIN_DEEP)

        # skull + jaw
        jaw = [(c[0] - rw * 0.76, c[1] - rh * 0.44),
               (c[0] - rw * 0.72, c[1] + rh * 0.18),
               (c[0] - rw * 0.40, c[1] + rh * 0.72),
               (c[0] + rw * 0.02, c[1] + rh * 0.98),
               (c[0] + rw * 0.48, c[1] + rh * 0.80),
               (c[0] + rw * 0.78, c[1] + rh * 0.26),
               (c[0] + rw * 0.74, c[1] - rh * 0.42),
               (c[0] + rw * 0.30, c[1] - rh * 0.78),
               (c[0] - rw * 0.28, c[1] - rh * 0.80)]
        self._poly(img, jaw, SKIN, SKIN_LIT, SKIN_SH, blur=6,
                   light=(-5 * s, -7 * s))

        d = ImageDraw.Draw(img)
        # cheekbone + jaw shading
        d.arc([c[0] - rw * 0.5, c[1] + rh * 0.05, c[0] + rw * 0.5, c[1] + rh * 0.95],
              20, 150, fill=SKIN_SH + (150,), width=int(3 * s))
        # brow ridge
        d.line([(c[0] + 1 * s, c[1] - 9 * s), (c[0] + 15 * s, c[1] - 11 * s)],
               fill=HAIR_DARK + (255,), width=int(5 * s))
        d.line([(c[0] - 8 * s, c[1] - 8 * s), (c[0] - 1 * s, c[1] - 9 * s)],
               fill=HAIR_DARK + (230,), width=int(4 * s))
        # nose
        d.line([(c[0] + 6 * s, c[1] - 4 * s), (c[0] + 11 * s, c[1] + 6 * s),
                (c[0] + 4 * s, c[1] + 8 * s)], fill=SKIN_SH + (170,),
               width=int(2.6 * s))
        # eyes
        for dx in (0, 11):
            d.ellipse([c[0] + (dx + 2) * s, c[1] - 5 * s,
                       c[0] + (dx + 9) * s, c[1] + 1 * s],
                      fill=(250, 250, 248, 255))
            d.ellipse([c[0] + (dx + 4) * s, c[1] - 4 * s,
                       c[0] + (dx + 7) * s, c[1] + 0.5 * s],
                      fill=(62, 106, 150, 255))
        # smirk
        d.line([(c[0] + 1 * s, c[1] + 15 * s), (c[0] + 13 * s, c[1] + 13 * s)],
               fill=(146, 92, 72, 255), width=int(2.8 * s))
        d.line([(c[0] + 13 * s, c[1] + 13 * s), (c[0] + 16 * s, c[1] + 15 * s)],
               fill=(126, 78, 60, 255), width=int(2.2 * s))
        # stubble
        for i in range(10):
            a = -0.4 + i / 13.0
            d.point([(c[0] + 4 * s + math.cos(a) * rw * 0.42,
                      c[1] + rh * 0.62 + math.sin(a) * rh * 0.12)],
                    fill=(120, 82, 62, 120))

        # hair: cap over the crown, fringe over the brow, mullet down the back
        crown = [(c[0] - rw * 0.86, c[1] - rh * 0.34),
                 (c[0] - rw * 0.78, c[1] - rh * 0.92),
                 (c[0] - rw * 0.18, c[1] - rh * 1.16),
                 (c[0] + rw * 0.52, c[1] - rh * 1.10),
                 (c[0] + rw * 0.84, c[1] - rh * 0.72),
                 (c[0] + rw * 0.88, c[1] - rh * 0.24),
                 (c[0] + rw * 0.60, c[1] - rh * 0.44),
                 (c[0] + rw * 0.10, c[1] - rh * 0.62),
                 (c[0] - rw * 0.40, c[1] - rh * 0.52)]
        self._poly(img, crown, HAIR, HAIR_LIT, HAIR_DARK, blur=4,
                   light=(-4 * s, -6 * s))
        mullet = [(c[0] - rw * 0.60, c[1] - rh * 0.70),
                  (c[0] - rw * 1.02, c[1] + rh * 0.26),
                  (c[0] - rw * 1.18, c[1] + rh * 1.34),
                  (c[0] - rw * 0.62, c[1] + rh * 1.62),
                  (c[0] - rw * 0.28, c[1] + rh * 0.80),
                  (c[0] - rw * 0.10, c[1] - rh * 0.20)]
        self._poly(img, mullet, HAIR_DARK, HAIR, HAIR_DARK, blur=3)
        for i in range(4):
            t = i / 3.0
            d.line([(c[0] - rw * (0.42 + 0.3 * t), c[1] - rh * 0.92),
                    (c[0] - rw * (0.10 + 0.28 * t), c[1] - rh * (0.30 - 0.1 * t))],
                   fill=HAIR_LIT + (160,), width=int(1.8 * s))

    def torso(self, img, sk, p):
        hip, chest = sk["hip"], sk["chest"]
        s = self.ss
        # trapezius and lats
        self._poly(img, [(chest[0] - 38, chest[1] - 4), (chest[0] + 38, chest[1] - 8),
                         (chest[0] + 33, chest[1] + 34), (chest[0] - 33, chest[1] + 34)],
                   SKIN, SKIN_LIT, SKIN_SH, blur=7)
        wt, wm, wb = 34.0, 27.0, 24.0
        y0 = chest[1] - 4
        y1 = hip[1] + 10
        ymid = y0 + (y1 - y0) * 0.55
        top = [(hip[0] - wt, y0 + 6), (hip[0] - wt * 0.36, y0 - 12),
               (hip[0] + wt * 0.42, y0 - 14), (hip[0] + wt * 0.99, y0 + 4),
               (hip[0] + wm + 3, ymid), (hip[0] + wb, y1),
               (hip[0] - wb, y1), (hip[0] - wm - 2, ymid)]
        self._poly(img, top, TANK, TANK_LIT, TANK_SH, blur=6, light=(-6, -8))

        d = ImageDraw.Draw(img)
        # scoop neckline
        d.arc([hip[0] - 20, y0 + 2, hip[0] + 20, y0 + 30], 200, 340,
              fill=TANK_DEEP + (235,), width=int(3.2 * s))
        # pec shading and folds
        for dx, dy in ((-12, 30), (10, 28)):
            d.arc([hip[0] + dx - 10, y0 + dy - 8, hip[0] + dx + 12, y0 + dy + 12],
                  20, 160, fill=TANK_SH + (140,), width=int(2 * s))
        for dx, y in ((-16, ymid + 2), (6, ymid + 10), (18, y1 - 14)):
            d.line([(hip[0] + dx, y), (hip[0] + dx + 5, y + 16)],
                   fill=TANK_SH + (140,), width=int(1.8 * s))
        # chest graphic
        cx, cy = hip[0] + 2, y0 + 54
        d.ellipse([cx - 19, cy - 19, cx + 18, cy + 18], fill=(214, 148, 158, 255))
        d.polygon([(cx, cy - 17), (cx + 12, cy - 6), (cx + 10, cy + 12),
                   (cx, cy + 19), (cx - 10, cy + 12), (cx - 12, cy - 6)],
                  fill=(148, 176, 116, 255))
        d.line([(cx - 9, cy - 3), (cx - 2, cy - 3)], fill=INK + (255,), width=int(3.4 * s))
        d.line([(cx + 2, cy - 3), (cx + 9, cy - 3)], fill=INK + (255,), width=int(3.4 * s))
        d.line([(cx, cy + 5), (cx, cy + 11)], fill=(96, 44, 44, 255), width=int(3 * s))
        for sgn in (-1, 1):
            d.line([(cx + sgn * 7, cy - 15), (cx + sgn * 10, cy - 23)],
                   fill=(118, 148, 94, 255), width=int(2.8 * s))
        # belt
        d.rectangle([hip[0] - wb - 2, y1 - 5, hip[0] + wb + 2, y1 + 5],
                    fill=(62, 42, 26, 255))
        d.rectangle([hip[0] - 8, y1 - 6, hip[0] + 8, y1 + 6],
                    fill=(184, 158, 100, 255))

    def leg(self, img, hipj, knee, ankle, near=True):
        r0, r1, r2 = (20, 15, 12) if near else (19, 14, 11.5)
        self._capsule(img, hipj, knee, r0, r1, DENIM, DENIM_LIT, DENIM_SH)
        self._capsule(img, knee, ankle, r1, r2, DENIM, DENIM_LIT, DENIM_SH)
        d = ImageDraw.Draw(img)
        s = self.ss
        a, b = self.P(knee), self.P(ankle)
        d.line([(a[0] - 3 * s, a[1]), (b[0] - 2 * s, b[1] - 4 * s)],
               fill=DENIM_SEAM + (160,), width=int(2 * s))
        # knee crease
        d.arc([a[0] - 9 * s, a[1] - 8 * s, a[0] + 9 * s, a[1] + 8 * s], 200, 340,
              fill=DENIM_DEEP + (150,), width=int(2 * s))

    def boot(self, img, knee, ankle):
        s = self.ss
        self._capsule(img, _add(knee, (0, -2)), _add(ankle, (0, -4)), 17, 13,
                      BOOT, BOOT_LIT, BOOT_SH)
        A = self.P(ankle)
        d = ImageDraw.Draw(img)
        d.ellipse([A[0] - 13 * s, A[1] - 10 * s, A[0] + 21 * s, A[1] + 10 * s],
                  fill=BOOT + (255,))
        d.ellipse([A[0] - 10 * s, A[1] - 8 * s, A[0] + 17 * s, A[1] + 4 * s],
                  fill=BOOT_LIT + (255,))
        d.line([(A[0] - 12 * s, A[1] + 8 * s), (A[0] + 21 * s, A[1] + 8 * s)],
               fill=BOOT_SH + (255,), width=int(3.4 * s))
        K = self.P(knee)
        # cuff
        d.line([(K[0] - 16 * s, K[1] + 6 * s), (K[0] + 16 * s, K[1] + 4 * s)],
               fill=BOOT_LIT + (255,), width=int(3 * s))
        for i in range(3):
            t = 0.22 + i * 0.24
            x = K[0] + (A[0] - K[0]) * t
            y = K[1] + (A[1] - K[1]) * t
            d.line([(x - 7 * s, y), (x + 8 * s, y - 2 * s)],
                   fill=(206, 182, 116, 255), width=int(2.2 * s))

    def render(self, p):
        base = super().render(p)
        # contour: dilate the alpha, keep the ring outside the figure
        alpha = base.split()[3]
        grown = alpha.filter(ImageFilter.MaxFilter(5))
        ring = Image.eval(Image.merge("L", (grown,)), lambda v: 0) if False else grown
        ring = Image.composite(Image.new("L", base.size, 210), Image.new("L", base.size, 0), grown)
        ring = ring.point(lambda v: 210 if v else 0)
        inner = alpha.point(lambda v: 210 if v else 0)
        import PIL.ImageChops as C
        edge = C.subtract(ring, inner)
        ink = Image.new("RGBA", base.size, (22, 16, 14, 255))
        ink.putalpha(edge)
        return Image.alpha_composite(ink, base)


def frame(p, canvas=CANVAS, axis=AXIS):
    return JackRig(canvas, axis).render(p)
