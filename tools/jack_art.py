"""Jack Burton sprite renderer.

The roster's fighters are palette-swapped Kung Fu Man, which cannot look like
Jack Burton no matter what colours are picked. This module draws him instead:
a jointed figure in a white tank top, denim jeans and knee-high boots, with the
pistol in his right hand and the knife in his left.

Authoring units are pixels at 2x the base character's scale (Jack stands 212px
tall at 1x). Every frame is drawn at 2x that again and downsampled, so the
result is anti-aliased rather than pixel-stepped. The sprites are written as
true-colour PNG32, so there is no palette to fight.

Poses are plain dictionaries of joint angles in degrees, 0 = hanging straight
down, positive = swung towards the enemy (right side of the screen).
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFilter

# --------------------------------------------------------------------- metrics
H = 212.0                    # standing height, feet at y = 0
HIP_Y = -106.0
SHOULDER_Y = -158.0
NECK_Y = -168.0
HEAD_Y = -186.0
SHOULDER_X = 24.0
HIP_X = 14.0
UPPER_ARM = 40.0
FORE_ARM = 36.0
THIGH = 50.0
SHIN = 46.0
SUPERSAMPLE = 2

# ---------------------------------------------------------------------- colours
SKIN = (226, 178, 146)
SKIN_LIT = (245, 204, 172)
SKIN_MID = (206, 156, 124)
SKIN_DARK = (166, 116, 88)
TANK = (246, 246, 244)
TANK_SHADE = (206, 208, 212)
TANK_DARK = (166, 170, 178)
DENIM = (96, 126, 158)
DENIM_LIT = (132, 162, 194)
DENIM_DARK = (62, 86, 112)
DENIM_DEEP = (44, 62, 82)
BOOT = (78, 52, 32)
BOOT_LIT = (108, 76, 48)
BOOT_DARK = (48, 30, 18)
HAIR = (104, 68, 38)
HAIR_LIT = (140, 96, 56)
HAIR_DARK = (62, 38, 20)
STEEL = (188, 196, 206)
STEEL_DARK = (108, 118, 130)
STEEL_LIT = (226, 232, 240)
GUNMETAL = (58, 60, 66)
GUNMETAL_LIT = (96, 100, 108)


def _p(base, ang, length):
    """Point `length` away from `base` at angle `ang` (0 = straight down)."""
    a = math.radians(ang)
    return (base[0] + math.sin(a) * length, base[1] + math.cos(a) * length)


def _poly(img, pts, colour):
    ImageDraw.Draw(img).polygon(pts, fill=colour)


def _mask(w, h):
    return Image.new("L", (w, h), 0)


def _limb(size, p0, p1, r0, r1, base, lit, dark):
    """Tapered capsule with a lit edge and a shadow edge."""
    w, h = size
    d = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) or 1.0
    nx, ny = -(p1[1] - p0[1]) / d, (p1[0] - p0[0]) / d

    img = Image.new("RGBA", size, (0, 0, 0, 0))
    mask = _mask(*size)
    md = ImageDraw.Draw(mask)
    md.polygon([(p0[0] + nx * r0, p0[1] + ny * r0),
                (p1[0] + nx * r1, p1[1] + ny * r1),
                (p1[0] - nx * r1, p1[1] - ny * r1),
                (p0[0] - nx * r0, p0[1] - ny * r0)], fill=255)
    md.ellipse([p0[0] - r0, p0[1] - r0, p0[0] + r0, p0[1] + r0], fill=255)
    md.ellipse([p1[0] - r1, p1[1] - r1, p1[0] + r1, p1[1] + r1], fill=255)
    img.paste(Image.new("RGBA", size, base + (255,)), (0, 0), mask)

    # shade: darken the far edge, light the near edge
    shade = _mask(*size)
    sd = ImageDraw.Draw(shade)
    sd.polygon([(p0[0] - nx * r0, p0[1] - ny * r0),
                (p1[0] - nx * r1, p1[1] - ny * r1),
                (p1[0] - nx * r1 * 0.15, p1[1] - ny * r1 * 0.15),
                (p0[0] - nx * r0 * 0.15, p0[1] - ny * r0 * 0.15)], fill=120)
    shade = shade.filter(ImageFilter.GaussianBlur(r1 * 0.32))
    darklayer = Image.new("RGBA", size, dark + (255,))
    darklayer.putalpha(shade)
    img = Image.alpha_composite(img, Image.composite(
        darklayer, Image.new("RGBA", size, (0, 0, 0, 0)), mask))

    glint = _mask(*size)
    gd = ImageDraw.Draw(glint)
    gd.polygon([(p0[0] + nx * r0 * 0.55, p0[1] + ny * r0 * 0.55),
                (p1[0] + nx * r1 * 0.55, p1[1] + ny * r1 * 0.55),
                (p1[0] + nx * r1 * 0.1, p1[1] + ny * r1 * 0.1),
                (p0[0] + nx * r0 * 0.1, p0[1] + ny * r0 * 0.1)], fill=110)
    glint = glint.filter(ImageFilter.GaussianBlur(r1 * 0.3))
    litlayer = Image.new("RGBA", size, lit + (255,))
    litlayer.putalpha(glint)
    img = Image.alpha_composite(img, Image.composite(
        litlayer, Image.new("RGBA", size, (0, 0, 0, 0)), mask))
    return img


def _shape(size, pts, base, lit, dark, lit_offset=(-5, -6), blur=4, shade=110):
    """Flat polygon with a soft top-left light and a bottom-right shadow."""
    mask = _mask(*size)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    img = Image.new("RGBA", size, base + (255,))
    img.putalpha(mask)

    darkm = _mask(*size)
    ImageDraw.Draw(darkm).polygon(
        [(x + 6, y + 7) for x, y in pts], fill=shade)
    darkm = darkm.filter(ImageFilter.GaussianBlur(blur))
    dl = Image.new("RGBA", size, dark + (255,))
    dl.putalpha(darkm)
    img = Image.alpha_composite(img, Image.composite(
        dl, Image.new("RGBA", size, (0, 0, 0, 0)), mask))

    litm = _mask(*size)
    ImageDraw.Draw(litm).polygon(
        [(x + lit_offset[0], y + lit_offset[1]) for x, y in pts], fill=120)
    litm = litm.filter(ImageFilter.GaussianBlur(blur))
    ll = Image.new("RGBA", size, lit + (255,))
    ll.putalpha(litm)
    img = Image.alpha_composite(img, Image.composite(
        ll, Image.new("RGBA", size, (0, 0, 0, 0)), mask))
    return img


# ------------------------------------------------------------------------ pose
BASE_POSE = dict(
    lean=2.0, head=0.0, head_x=0.0, hip_x=0.0,
    sh_near=8.0, el_near=18.0, sh_far=-6.0, el_far=-24.0,
    hip_near=4.0, knee_near=6.0, foot_near=0.0,
    hip_far=-5.0, knee_far=8.0, foot_far=-6.0,
    gun=True, knife=True, crouch=0.0,
)


def pose(**kw):
    p = dict(BASE_POSE)
    p.update(kw)
    return p


class Figure:
    """Draws one pose onto a transparent canvas, feet at the sprite axis."""

    def __init__(self, size=(260, 260), origin=(120, 244)):
        self.size = size
        self.origin = origin
        self.w, self.h = size
        self.s = SUPERSAMPLE

    # -- geometry ---------------------------------------------------------
    def P(self, x, y):
        """Authoring point -> supersampled pixel."""
        return (self.origin[0] * self.s + x * self.s,
                self.origin[1] * self.s + y * self.s)

    def skeleton(self, p):
        drop = 26.0 * p["crouch"]
        hip = (p["hip_x"], HIP_Y + drop)
        lean = p["lean"]
        chest = _p(hip, 180 + lean, HIP_Y - SHOULDER_Y + drop * 0.2)
        neck = _p(chest, 180 + lean, NECK_Y - SHOULDER_Y)
        head = _p(neck, 180 + lean + p["head"], HEAD_Y - NECK_Y)
        head = (head[0] + p["head_x"], head[1])

        sh_near = (chest[0] + SHOULDER_X * 0.6, chest[1] + 4)
        sh_far = (chest[0] - SHOULDER_X * 0.75, chest[1] + 6)
        el_near = _p(sh_near, p["sh_near"], UPPER_ARM)
        hand_near = _p(el_near, p["sh_near"] + p["el_near"], FORE_ARM)
        el_far = _p(sh_far, p["sh_far"], UPPER_ARM)
        hand_far = _p(el_far, p["sh_far"] + p["el_far"], FORE_ARM)

        hip_near = (hip[0] + HIP_X * 0.5, hip[1])
        hip_far = (hip[0] - HIP_X * 0.6, hip[1])
        knee_near = _p(hip_near, p["hip_near"], THIGH)
        ankle_near = _p(knee_near, p["hip_near"] + p["knee_near"], SHIN)
        knee_far = _p(hip_far, p["hip_far"], THIGH)
        ankle_far = _p(knee_far, p["hip_far"] + p["knee_far"], SHIN)
        return dict(hip=hip, chest=chest, neck=neck, head=head,
                    sh_near=sh_near, el_near=el_near, hand_near=hand_near,
                    sh_far=sh_far, el_far=el_far, hand_far=hand_far,
                    hip_near=hip_near, knee_near=knee_near, ankle_near=ankle_near,
                    hip_far=hip_far, knee_far=knee_far, ankle_far=ankle_far,
                    foot_near=p["foot_near"], foot_far=p["foot_far"])

    # -- parts ------------------------------------------------------------
    def _boot(self, img, knee, ankle, toe, colour=(BOOT, BOOT_LIT, BOOT_DARK)):
        s = self.s
        kn = self.P(*knee)
        an = self.P(*ankle)
        toe = self.P(*toe)
        leg = _limb((self.w * s, self.h * s), kn, an, 12.5 * s, 9.0 * s, *colour)
        img.alpha_composite(leg)
        d = ImageDraw.Draw(img)
        # sole and toe box
        d.ellipse([toe[0] - 9 * s, toe[1] - 7 * s, toe[0] + 10 * s, toe[1] + 6 * s],
                  fill=BOOT_DARK + (255,))
        d.ellipse([an[0] - 11 * s, an[1] - 12 * s, an[0] + 12 * s, an[1] + 10 * s],
                  fill=colour[0] + (255,))
        # buckles
        for i in range(3):
            t = 0.28 + i * 0.2
            x = kn[0] + (an[0] - kn[0]) * t
            y = kn[1] + (an[1] - kn[1]) * t
            d.line([(x - 5 * s, y), (x + 5 * s, y - 1 * s)],
                   fill=(196, 176, 120, 255), width=int(1.6 * s))
        d.line([(kn[0], kn[1]), (an[0], an[1])], fill=BOOT_DARK + (150,),
               width=int(1.4 * s))

    def _jeans(self, img, hip, knee, ankle, near=True):
        s = self.s
        h = self.P(*hip)
        k = self.P(*knee)
        a = self.P(*ankle)
        r0, r1, r2 = (14.0, 11.0, 9.0) if near else (13.0, 10.0, 8.5)
        img.alpha_composite(_limb((self.w * s, self.h * s), h, k, r0 * s, r1 * s,
                                  DENIM, DENIM_LIT, DENIM_DARK))
        img.alpha_composite(_limb((self.w * s, self.h * s), k, a, r1 * s, r2 * s,
                                  DENIM, DENIM_LIT, DENIM_DARK))
        d = ImageDraw.Draw(img)
        # crease and hem
        d.line([(k[0] - 2 * s, k[1]), (a[0] - 1 * s, a[1] - 3 * s)],
               fill=DENIM_LIT + (150,), width=int(1.5 * s))
        d.line([(a[0] - r2 * s, a[1]), (a[0] + r2 * s, a[1])],
               fill=DENIM_DEEP + (190,), width=int(2.2 * s))

    def _torso(self, img, sk, p):
        s = self.s
        chest = self.P(*sk["chest"])
        hip = self.P(*sk["hip"])
        wtop = 20 * s
        wmid = 17 * s
        wbot = 15 * s
        y0, y1 = chest[1] - 4 * s, hip[1] + 6 * s
        ymid = (y0 + y1) * 0.55
        # bare shoulders / arms socket mass behind the vest
        img.alpha_composite(_shape(
            (self.w * s, self.h * s),
            [(chest[0] - wtop - 4 * s, y0 - 2 * s),
             (chest[0] + wtop + 4 * s, y0 - 2 * s),
             (chest[0] + wtop, ymid), (chest[0] - wtop, ymid)],
            SKIN_MID, SKIN_LIT, SKIN_DARK, blur=5))
        # tank top
        top = [(chest[0] - wtop, y0 + 2 * s), (chest[0] - wtop * 0.35, y0 - 5 * s),
               (chest[0] + wtop * 0.42, y0 - 6 * s), (chest[0] + wtop, y0 + 3 * s),
               (chest[0] + wmid, ymid), (chest[0] + wbot, y1),
               (chest[0] - wbot, y1), (chest[0] - wmid, ymid)]
        img.alpha_composite(_shape((self.w * s, self.h * s), top,
                                   TANK, (255, 255, 255), TANK_SHADE, blur=5))
        d = ImageDraw.Draw(img)
        # neckline
        d.line([(chest[0] - wtop * 0.6, y0 + 3 * s),
                (chest[0] - 2 * s, y0 + 13 * s),
                (chest[0] + wtop * 0.55, y0 + 2 * s)],
               fill=TANK_DARK + (210,), width=int(2.2 * s))
        # belt
        d.rectangle([chest[0] - wbot - 1 * s, y1 - 4 * s,
                     chest[0] + wbot + 1 * s, y1 + 2 * s],
                    fill=(58, 40, 26, 255))
        d.rectangle([chest[0] - 4 * s, y1 - 4 * s, chest[0] + 4 * s, y1 + 2 * s],
                    fill=(176, 154, 96, 255))
        self._chest_print(img, chest[0], y0 + 26 * s)
        # waistband below the belt
        d.rectangle([chest[0] - wbot - 1 * s, y1 + 2 * s,
                     chest[0] + wbot + 1 * s, y1 + 9 * s],
                    fill=DENIM + (255,))

    def _chest_print(self, img, cx, cy):
        """The shirt graphic: pink sun behind a green demon mask."""
        s = self.s
        d = ImageDraw.Draw(img)
        r = 11 * s
        d.ellipse([cx - r, cy - r, cx + r * 0.9, cy + r * 0.92],
                  fill=(214, 148, 158, 255))
        # mask
        d.polygon([(cx, cy - 9 * s), (cx + 7 * s, cy - 3 * s),
                   (cx + 6 * s, cy + 7 * s), (cx, cy + 11 * s),
                   (cx - 6 * s, cy + 7 * s), (cx - 7 * s, cy - 3 * s)],
                  fill=(150, 178, 120, 255))
        d.line([(cx - 5 * s, cy - 2 * s), (cx - 1 * s, cy - 2 * s)],
               fill=(30, 30, 30, 255), width=int(2 * s))
        d.line([(cx + 1 * s, cy - 2 * s), (cx + 5 * s, cy - 2 * s)],
               fill=(30, 30, 30, 255), width=int(2 * s))
        d.line([(cx, cy + 2 * s), (cx, cy + 6 * s)], fill=(90, 40, 40, 255),
               width=int(2 * s))
        # horns
        d.line([(cx - 4 * s, cy - 9 * s), (cx - 6 * s, cy - 13 * s)],
               fill=(120, 150, 96, 255), width=int(2 * s))
        d.line([(cx + 4 * s, cy - 9 * s), (cx + 6 * s, cy - 13 * s)],
               fill=(120, 150, 96, 255), width=int(2 * s))

    def _head(self, img, sk, p):
        s = self.s
        c = self.P(*sk["head"])
        rw, rh = 13.5 * s, 16.5 * s
        skin = _shape((self.w * s, self.h * s),
                      [(c[0] - rw * 0.86, c[1] - rh * 0.5),
                       (c[0] - rw * 0.7, c[1] + rh * 0.42),
                       (c[0] - rw * 0.2, c[1] + rh * 0.92),
                       (c[0] + rw * 0.55, c[1] + rh * 0.78),
                       (c[0] + rw * 0.9, c[1] + rh * 0.1),
                       (c[0] + rw * 0.8, c[1] - rh * 0.62)],
                      SKIN, SKIN_LIT, SKIN_DARK, blur=4)
        img.alpha_composite(skin)
        d = ImageDraw.Draw(img)
        # neck
        d.polygon([(c[0] - 6 * s, c[1] + rh * 0.6), (c[0] + 6 * s, c[1] + rh * 0.6),
                   (c[0] + 7 * s, c[1] + rh * 1.5), (c[0] - 7 * s, c[1] + rh * 1.5)],
                  fill=SKIN_MID + (255,))
        # hair: swept-back mullet
        hair = [(c[0] - rw * 1.02, c[1] - rh * 0.24),
                (c[0] - rw * 0.9, c[1] - rh * 0.95),
                (c[0] - rw * 0.2, c[1] - rh * 1.18),
                (c[0] + rw * 0.62, c[1] - rh * 1.05),
                (c[0] + rw * 0.92, c[1] - rh * 0.55),
                (c[0] + rw * 0.7, c[1] - rh * 0.2),
                (c[0] + rw * 0.2, c[1] - rh * 0.42),
                (c[0] - rw * 0.4, c[1] - rh * 0.3)]
        img.alpha_composite(_shape((self.w * s, self.h * s), hair,
                                   HAIR, HAIR_LIT, HAIR_DARK, blur=3))
        d.polygon([(c[0] - rw * 1.0, c[1] - rh * 0.1),
                   (c[0] - rw * 1.15, c[1] + rh * 0.9),
                   (c[0] - rw * 0.62, c[1] + rh * 1.15),
                   (c[0] - rw * 0.45, c[1] + rh * 0.35)],
                  fill=HAIR_DARK + (255,))
        d.line([(c[0] - rw * 0.55, c[1] - rh * 0.95),
                (c[0] + rw * 0.4, c[1] - rh * 1.02)],
               fill=HAIR_LIT + (220,), width=int(2.4 * s))
        # brow, eye, smirk
        d.line([(c[0] - 1 * s, c[1] - 2 * s), (c[0] + 7 * s, c[1] - 3 * s)],
               fill=HAIR_DARK + (255,), width=int(2.1 * s))
        d.ellipse([c[0] + 1 * s, c[1] - 1 * s, c[0] + 5 * s, c[1] + 2 * s],
                  fill=(250, 250, 250, 255))
        d.ellipse([c[0] + 2.6 * s, c[1] - 0.6 * s,
                   c[0] + 4.6 * s, c[1] + 1.6 * s], fill=(70, 110, 150, 255))
        d.line([(c[0] - 1 * s, c[1] + 7 * s), (c[0] + 6 * s, c[1] + 6 * s)],
               fill=(150, 96, 78, 255), width=int(1.8 * s))
        d.point([(c[0] + 6 * s, c[1] + 7 * s)], fill=(120, 70, 56, 255))
        # stubble
        st = Image.new("RGBA", (self.w * s, self.h * s), (0, 0, 0, 0))
        sd = ImageDraw.Draw(st)
        for i in range(14):
            a = -0.5 + i / 18.0
            sd.point([(c[0] + math.cos(a) * rw * 0.55 + s,
                       c[1] + rh * 0.55 + math.sin(a) * rh * 0.2)],
                     fill=(120, 82, 62, 90))
        img.alpha_composite(st.filter(ImageFilter.GaussianBlur(1)))

    def _hand(self, img, wrist, ang, near=True):
        s = self.s
        w = self.P(*wrist)
        d = ImageDraw.Draw(img)
        d.ellipse([w[0] - 5.5 * s, w[1] - 5 * s, w[0] + 6 * s, w[1] + 6 * s],
                  fill=SKIN_LIT if near else SKIN_MID)
        d.arc([w[0] - 5 * s, w[1] - 5 * s, w[0] + 5 * s, w[1] + 5 * s],
              200, 340, fill=SKIN_DARK + (160,), width=int(1.4 * s))
        return w

    def _pistol(self, img, hand, ang):
        """Beretta-ish pistol pointing along `ang` (0 = up)."""
        s = self.s
        a = math.radians(ang - 90)
        ca, sa = math.cos(a), math.sin(a)

        def T(x, y):
            return (hand[0] + (x * ca - y * sa) * s,
                    hand[1] + (x * sa + y * ca) * s)

        poly = [T(0, -3), T(26, -3), T(27, 1), T(4, 2), T(2, 9), T(-5, 9), T(-6, 2)]
        ImageDraw.Draw(img).polygon(poly, fill=GUNMETAL + (255,))
        ImageDraw.Draw(img).polygon([T(1, -3), T(26, -3), T(26, -1), T(1, -1)],
                                    fill=GUNMETAL_LIT + (255,))
        ImageDraw.Draw(img).polygon([T(1, 3), T(5, 3), T(3, 9), T(-3, 9)],
                                    fill=GUNMETAL + (255,))

    def _knife(self, img, hand, ang):
        s = self.s
        a = math.radians(ang - 90)
        ca, sa = math.cos(a), math.sin(a)

        def T(x, y):
            return (hand[0] + (x * ca - y * sa) * s,
                    hand[1] + (x * sa + y * ca) * s)

        ImageDraw.Draw(img).polygon(
            [T(-12, -2), T(-2, -3), T(-1, 3), T(-12, 2)], fill=(70, 44, 26, 255))
        ImageDraw.Draw(img).polygon(
            [T(-2, -5), T(1, -5), T(1, 5), T(-2, 5)], fill=STEEL_DARK + (255,))
        ImageDraw.Draw(img).polygon(
            [T(1, -3), T(20, -2), T(26, 0), T(20, 2), T(1, 2)],
            fill=STEEL + (255,))
        ImageDraw.Draw(img).polygon(
            [T(1, -3), T(20, -2), T(22, -0.5), T(1, -0.5)],
            fill=STEEL_LIT + (255,))

    # -- render -----------------------------------------------------------
    def render(self, p):
        s = self.s
        size = (self.w * s, self.h * s)
        sk = self.skeleton(p)
        img = Image.new("RGBA", size, (0, 0, 0, 0))

        # far limbs first
        self._jeans(img, sk["hip_far"], sk["knee_far"], sk["ankle_far"], near=False)
        self._boot(img, sk["knee_far"], sk["ankle_far"],
                   (sk["ankle_far"][0] + 12, 0))
        img.alpha_composite(_limb(size, self.P(*sk["sh_far"]), self.P(*sk["el_far"]),
                                  10.5 * s, 8.5 * s, SKIN_MID, SKIN_LIT, SKIN_DARK))
        img.alpha_composite(_limb(size, self.P(*sk["el_far"]), self.P(*sk["hand_far"]),
                                  8.5 * s, 6.5 * s, SKIN_MID, SKIN_LIT, SKIN_DARK))
        hand_far = self._hand(img, sk["hand_far"], p["sh_far"] + p["el_far"], near=False)
        if p["knife"]:
            self._knife(img, hand_far, p["sh_far"] + p["el_far"] + 18)

        # near leg, torso, head
        self._jeans(img, sk["hip_near"], sk["knee_near"], sk["ankle_near"])
        self._boot(img, sk["knee_near"], sk["ankle_near"],
                   (sk["ankle_near"][0] + 13, 0))
        self._torso(img, sk, p)
        self._head(img, sk, p)

        # near arm on top
        img.alpha_composite(_limb(size, self.P(*sk["sh_near"]), self.P(*sk["el_near"]),
                                  11.5 * s, 9.0 * s, SKIN, SKIN_LIT, SKIN_DARK))
        img.alpha_composite(_limb(size, self.P(*sk["el_near"]), self.P(*sk["hand_near"]),
                                  9.0 * s, 6.8 * s, SKIN, SKIN_LIT, SKIN_DARK))
        hand_near = self._hand(img, sk["hand_near"], p["sh_near"] + p["el_near"])
        if p["gun"]:
            self._pistol(img, hand_near, p["sh_near"] + p["el_near"] + 22)

        # contact shadow
        shadow = Image.new("RGBA", size, (0, 0, 0, 0))
        ImageDraw.Draw(shadow).ellipse(
            [self.P(sk["hip"][0] - 34, 0)[0], self.P(0, -2)[1],
             self.P(sk["hip"][0] + 34, 0)[0], self.P(0, 4)[1]],
            fill=(0, 0, 0, 90))
        shadow = shadow.filter(ImageFilter.GaussianBlur(3 * s))
        out = Image.alpha_composite(shadow, img)
        return out.resize((self.w, self.h), Image.LANCZOS)


def frame(p, size=(260, 260), origin=(120, 244)):
    return Figure(size, origin).render(p)


# --------------------------------------------------------------- pose library
STANCE = pose()

WALK = [pose(lean=3, hip_near=22, knee_near=-8, hip_far=-16, knee_far=16,
             sh_near=14, el_near=26, sh_far=-14, el_far=-30),
        pose(lean=2, hip_near=4, knee_near=6, hip_far=-4, knee_far=6,
             sh_near=8, el_near=20, sh_far=-8, el_far=-26),
        pose(lean=3, hip_near=-16, knee_near=16, hip_far=22, knee_far=-8,
             sh_near=2, el_near=22, sh_far=-2, el_far=-28),
        pose(lean=2, hip_near=-4, knee_near=6, hip_far=4, knee_far=6,
             sh_near=8, el_near=20, sh_far=-8, el_far=-26)]

CROUCH = pose(crouch=1.0, lean=16, hip_near=48, knee_near=-72, hip_far=26,
              knee_far=-60, sh_near=24, el_near=44, sh_far=10, el_far=-38,
              head=-6)

JUMP = pose(lean=8, hip_near=34, knee_near=-52, hip_far=-6, knee_far=-18,
            sh_near=52, el_near=40, sh_far=-26, el_far=-52, head=-4)

PUNCH_MID = pose(lean=6, sh_near=46, el_near=42, sh_far=-18, el_far=-46,
                 hip_near=10, knee_near=4, hip_far=-10, knee_far=10)
PUNCH_OUT = pose(lean=10, sh_near=88, el_near=92, sh_far=-24, el_far=-54,
                 hip_near=18, knee_near=2, hip_far=-16, knee_far=12)

GUN_UP = pose(lean=2, sh_near=20, el_near=74, sh_far=-8, el_far=-30,
              hip_near=6, knee_near=4, hip_far=-6, knee_far=8)
GUN_FIRE = pose(lean=-2, sh_near=16, el_near=70, sh_far=-10, el_far=-32,
                hip_near=4, knee_near=6, hip_far=-8, knee_far=10)

KNIFE_BACK = pose(lean=-4, sh_near=6, el_near=20, sh_far=-38, el_far=-64,
                  hip_near=2, knee_near=6, hip_far=-8, knee_far=8)
KNIFE_THROW = pose(lean=8, sh_near=18, el_near=26, sh_far=58, el_far=40,
                   hip_near=12, knee_near=4, hip_far=-12, knee_far=10)

HIT = pose(lean=-10, head=-8, sh_near=-16, el_near=34, sh_far=14, el_far=20,
           hip_near=-6, knee_near=12, hip_far=8, knee_far=14)

GUARD = pose(lean=4, sh_near=28, el_near=96, sh_far=6, el_far=-84,
             hip_near=8, knee_near=8, hip_far=-8, knee_far=10)

DOWN = pose(crouch=1.6, lean=76, head=6, hip_near=84, knee_near=-16,
            hip_far=70, knee_far=-10, sh_near=-30, el_near=60,
            sh_far=-46, el_far=40)

KIOSK = dict(
    stance=STANCE, walk=WALK, crouch=CROUCH, jump=JUMP,
    punch_mid=PUNCH_MID, punch_out=PUNCH_OUT,
    gun_up=GUN_UP, gun_fire=GUN_FIRE,
    knife_back=KNIFE_BACK, knife_throw=KNIFE_THROW,
    hit=HIT, guard=GUARD, down=DOWN,
)
