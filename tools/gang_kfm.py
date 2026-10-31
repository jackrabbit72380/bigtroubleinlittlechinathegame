"""Gang fighters built from the real Kung Fu Man art instead of drawn parts.

The base sprites in chars/kfm are 32-colour indexed art, 47x106 for the idle
frame. Every gang member is that same art, recoloured by rewriting the palette
roles (gi cloth, trousers, headband and belt, hair, skin) and then upscaled to
the roster's 318px height. That keeps Kung Fu Man's real anatomy and shading -
the thing the painted puppet bodies could not fake - while still giving each
member his own cloth tone, headband colour and weapon.

Weapons are painted in after the recolour: the lead fist is found by its skin
colour, and the staff or machete is drawn out of that grip, so the frames that
ship are the frames that hold the weapon.

Run:  python3 tools/gang_kfm.py --sheet
"""

from __future__ import annotations

import colorsys
import math
import os
import sys

import re

from PIL import Image, ImageDraw, ImageFilter, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "chars", "kfm")
SCALE = 3                      # 106px base -> 318px, the roster height
PAD_X, PAD_Y = 78, 46          # room around the figure for staff and machete

# Every colour Kung Fu Man uses in palette 0, with the role it plays. The base
# wears a white gi, pale baggy trousers, a blue headband/belt/shoes and black
# hair; recolouring by role keeps each shading ramp intact, so highlights stay
# highlights and the figure keeps its volume.
ROLE = {
    (0x00, 0x00, 0x00): "outline",
    (0x31, 0x31, 0x31): "hair",
    (0x5a, 0x5a, 0x63): "hair_h",
    (0x42, 0x63, 0xa5): "trim_d",
    (0x80, 0x94, 0xc4): "trim",
    (0xa5, 0xb5, 0xde): "trim_l",
    (0x84, 0x42, 0x31): "skin_d2",
    (0x84, 0x6b, 0x5a): "skin_d",
    (0xa5, 0x90, 0x7d): "wrap_d",
    (0xbd, 0x73, 0x5a): "skin_2",
    (0xce, 0xb5, 0xa5): "wrap",
    (0xd4, 0x83, 0x63): "skin_3",
    (0xe7, 0x94, 0x73): "skin_4",
    (0xe7, 0xd6, 0xc6): "gi_s",
    (0xef, 0xbd, 0x9c): "skin_h",
    (0xf7, 0xef, 0xe7): "gi",
    (0xf7, 0xf7, 0xf7): "gi_h",
}

SKIN = {
    "skin_d2": (0x84, 0x42, 0x31),
    "skin_d": (0x84, 0x6b, 0x5a),
    "skin_2": (0xbd, 0x73, 0x5a),
    "skin_3": (0xd4, 0x83, 0x63),
    "skin_4": (0xe7, 0x94, 0x73),
    "skin_h": (0xef, 0xbd, 0x9c),
}

# Chang Sing: tan gi and trousers over black underclothes, black sash, gold band.
CHANG = {
    "gi_s": (0x8e, 0x78, 0x50), "gi": (0xc2, 0xa9, 0x7c), "gi_h": (0xdc, 0xc6, 0x99),
    "wrap_d": (0x6d, 0x5c, 0x3d), "wrap": (0x99, 0x83, 0x5b),
    "hair": (0x14, 0x12, 0x10), "hair_h": (0x2c, 0x28, 0x24),
    "outline": (0x08, 0x07, 0x06),
    "trim_d": (0x7a, 0x5a, 0x14), "trim": (0xc8, 0x95, 0x2f), "trim_l": (0xe6, 0xbb, 0x5c),
}

# Wing Kong: black gi and trousers, red trim and band.
WING = {
    "gi_s": (0x12, 0x12, 0x17), "gi": (0x22, 0x22, 0x2b), "gi_h": (0x31, 0x31, 0x3c),
    "wrap_d": (0x0e, 0x0e, 0x12), "wrap": (0x1b, 0x1b, 0x22),
    "hair": (0x0d, 0x0d, 0x10), "hair_h": (0x22, 0x22, 0x28),
    "outline": (0x06, 0x06, 0x08),
    "trim_d": (0x6d, 0x16, 0x1b), "trim": (0xa8, 0x22, 0x28), "trim_l": (0xcf, 0x38, 0x3c),
}

STAFF = dict(wood=(0x6b, 0x4a, 0x2a), wood_hi=(0x8f, 0x66, 0x3b),
             cap=(0xc8, 0x95, 0x2f), edge=(0x2b, 0x1d, 0x10))
BLADE = dict(steel=(0x9a, 0xa3, 0xb0), steel_hi=(0xdc, 0xe2, 0xea),
             spine=(0x3a, 0x40, 0x4c), grip=(0x8c, 0x1c, 0x22),
             edge=(0x51, 0x59, 0x66))

# id, gang, cloth tone, skin tone, headband tone, weapon, build scale, weapon length
MEMBERS = [
    ("changsing_bo", "chang", 1.02, 1.00, 1.00, "staff", 1.05, 214),
    ("changsing_lin", "chang", 0.88, 1.06, 0.70, "staff", 0.96, 196),
    ("changsing_shi", "chang", 1.12, 0.94, 1.00, "staff", 1.10, 208),
    ("changsing_han", "chang", 0.80, 0.88, 0.55, "staff", 0.93, 230),
    ("changsing_wei", "chang", 1.16, 1.02, 1.15, "staff", 0.98, 186),
    ("changsing_tam", "chang", 0.94, 0.98, 0.40, "staff", 1.02, 222),
    ("wingkong_gou", "wing", 1.00, 1.00, 1.00, "machete", 1.08, 124),
    ("wingkong_ma", "wing", 0.86, 1.06, 1.12, "machete", 0.97, 112),
    ("wingkong_zhao", "wing", 1.12, 0.92, 0.70, "machete", 1.12, 132),
    ("wingkong_lu", "wing", 0.78, 1.00, 0.45, "machete", 0.94, 104),
    ("wingkong_shen", "wing", 1.18, 0.96, 1.18, "machete", 1.01, 118),
    ("wingkong_bai", "wing", 0.92, 1.04, 0.30, "machete", 1.05, 128),
]


def _shade(c, k):
    """Scale a colour's brightness, keeping it inside 0..255."""
    return tuple(max(0, min(255, int(v * k))) for v in c[:3])


def _warm(c, k):
    """Nudge a skin colour warm or cool without leaving the skin ramp."""
    r, g, b = c[:3]
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    h = (h + (k - 1.0) * 0.05) % 1.0
    s = max(0.0, min(1.0, s * (1.0 + (k - 1.0) * 0.6)))
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return (int(r * 255), int(g * 255), int(b * 255))


def colour_map(gang, cloth=1.0, skin=1.0, band=1.0):
    """old RGB -> new RGB for one member."""
    base = CHANG if gang == "chang" else WING
    out = {}
    for rgb, role in ROLE.items():
        if role.startswith("skin"):
            out[rgb] = _warm(SKIN[role], skin)
        elif role.startswith("trim"):
            out[rgb] = _shade(base[role], band)
        elif role.startswith("gi"):
            out[rgb] = _shade(base[role], cloth)
        else:
            out[rgb] = base.get(role, rgb)
    return out


def recolour(img, mapping):
    """Rewrite a decoded sprite's colours through ``mapping``."""
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a:
                c = mapping.get((r, g, b))
                if c:
                    px[x, y] = (c[0], c[1], c[2], a)
    return img


def upscale(img, scale=SCALE):
    """Take the 1990s sprite up to roster height, clean, then re-sharpen.

    The transparent pixels of the base art still carry a light colour, and a
    plain LANCZOS pass bleeds it onto every silhouette edge - that is what the
    white fringe was. Clearing the hidden colour first and dropping the faint
    half-pixels afterwards leaves an edge that reads as drawn, not cut out.
    """
    w, h = img.size
    empty = Image.new("RGBA", img.size, (0, 0, 0, 0))
    img = Image.composite(img, empty, img.split()[3])
    big = img.resize((w * scale, h * scale), Image.LANCZOS)
    big.putalpha(big.split()[3].point(lambda v: 255 if v >= 140 else 0))
    return big.filter(ImageFilter.UnsharpMask(radius=1.2, percent=45, threshold=3))


def lead_fist(img, skin_rgb):
    """Centre of the hand that is furthest forward, so a weapon has a grip."""
    w, h = img.size
    px = img.load()
    best = None
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a and (r, g, b) in skin_rgb:
                reach = x + y * 0.15        # forward and a little low wins
                if best is None or reach > best[0]:
                    best = (reach, x, y)
    if not best:
        return None
    _, bx, by = best
    xs, ys, n = 0, 0, 0
    for y in range(max(0, by - 9), min(h, by + 10)):
        for x in range(max(0, bx - 9), min(w, bx + 10)):
            r, g, b, a = px[x, y]
            if a and (r, g, b) in skin_rgb:
                xs, ys, n = xs + x, ys + y, n + 1
    return (xs / n, ys / n)


def draw_staff(d, grip, length=210.0, angle=-0.14):
    """A six-foot staff held out in front, butt behind the fist."""
    gx, gy = grip
    dx, dy = math.cos(angle), math.sin(angle)
    x0, y0 = gx - dx * length * 0.20, gy - dy * length * 0.20
    x1, y1 = gx + dx * length * 0.80, gy + dy * length * 0.80
    d.line([(x0, y0), (x1, y1)], fill=STAFF["edge"], width=9)
    d.line([(x0, y0), (x1, y1)], fill=STAFF["wood"], width=7)
    d.line([(x0 - dy * 1.5, y0 + dx * 1.5), (x1 - dy * 1.5, y1 + dx * 1.5)],
           fill=STAFF["wood_hi"], width=2)
    for t in (0.0, 1.0):
        cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=STAFF["cap"])


def draw_machete(d, grip, length=120.0, angle=-0.12):
    """A heavy chopper held out front: wrapped grip, guard, broad blade."""
    gx, gy = grip
    dx, dy = math.cos(angle), math.sin(angle)
    nx, ny = -dy, dx

    # wrapped grip running through the fist, pommel behind it
    d.line([(gx - dx * 22, gy - dy * 22), (gx + dx * 8, gy + dy * 8)],
           fill=BLADE["edge"], width=14)
    d.line([(gx - dx * 20, gy - dy * 20), (gx + dx * 7, gy + dy * 7)],
           fill=BLADE["grip"], width=9)

    # small guard between fist and blade
    d.line([(gx + dx * 8 + nx * 11, gy + dy * 8 + ny * 11),
            (gx + dx * 8 - nx * 11, gy + dy * 8 - ny * 11)],
           fill=BLADE["spine"], width=5)

    # broad chopper: spine along the top, deep belly hanging below it, and the
    # hilt end buried in the fist so there is never a gap to read as floating
    bx, by = gx + dx * 2, gy + dy * 2
    tipx, tipy = gx + dx * length, gy + dy * length
    quad = [(bx - nx * 6, by - ny * 6), (tipx - nx * 3, tipy - ny * 3),
            (tipx + nx * 24, tipy + ny * 24), (bx + nx * 17, by + ny * 17)]
    d.polygon(quad, fill=BLADE["edge"])
    inner = [(bx - nx * 4, by - ny * 4), (tipx - nx * 1, tipy - ny * 1),
             (tipx + nx * 21, tipy + ny * 21), (bx + nx * 14, by + ny * 14)]
    d.polygon(inner, fill=BLADE["steel"])
    d.line([(bx - nx * 4, by - ny * 4), (tipx - nx * 1, tipy - ny * 1)],
           fill=BLADE["spine"], width=4)
    d.line([(bx + nx * 15, by + ny * 15), (tipx + nx * 22, tipy + ny * 22)],
           fill=BLADE["steel_hi"], width=3)


def paint_weapon(img, gang, skin_rgb, kind, length=210.0):
    """Draw the gang's weapon out of the lead fist."""
    grip = lead_fist(img, skin_rgb)
    if not grip:
        return img
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if kind == "staff":
        draw_staff(d, grip, length)
    else:
        draw_machete(d, grip, length)
    return Image.alpha_composite(img, layer)


def member_sprite(cid, group=0, number=0, weapon=True):
    gang, cloth, skin, band, kind, build_scale, length = next(
        m for m in MEMBERS if m[0] == cid)[1:]
    raw, sprites, pal = sff.read_sff(os.path.join(BASE, "kfm.sff"))
    sp = next(s for s in sprites if s["group"] == group and s["number"] == number)
    img = sff.decode_sprite(raw, sp, pal, 0)
    img = upscale(recolour(img, colour_map(gang, cloth, skin, band)))
    img = ImageOps.expand(img, (PAD_X, PAD_Y, PAD_X, PAD_Y), fill=(0, 0, 0, 0))
    if weapon:
        skins = {_warm(SKIN[r], skin) for r in SKIN}
        img = paint_weapon(img, gang, skins, kind, length)
    if build_scale != 1.0:
        img = img.resize((max(1, round(img.width * build_scale)),
                          max(1, round(img.height * build_scale))), Image.LANCZOS)
    return img


def sheet(path="artifacts/kfm_gang_proto.png"):
    from PIL import ImageDraw as Draw
    from PIL import ImageFont

    def font(size):
        try:
            return ImageFont.load_default(size=size)
        except Exception:
            return ImageFont.load_default()

    raw, sprites, pal = sff.read_sff(os.path.join(BASE, "kfm.sff"))
    sp = next(s for s in sprites if s["group"] == 0 and s["number"] == 0)
    original_big = upscale(sff.decode_sprite(raw, sp, pal, 0))

    cw, ch, pad = 300, 430, 30
    cols = 7
    img_sheet = Image.new("RGB", (cw * cols, ch * 3), (24, 26, 33))
    d = Draw.Draw(img_sheet)
    d.text((10, 12), "", fill=(226, 228, 238))

    cells = [("Kung Fu Man (base, 3x)", original_big, 0, 0)]
    for i, m in enumerate(MEMBERS[:6]):
        cells.append((m[0].replace("_", " ").title(), member_sprite(m[0]), i + 1, 0))
    for i, m in enumerate(MEMBERS[6:]):
        cells.append((m[0].replace("_", " ").title(), member_sprite(m[0]), i, 1))

    # action row: the same member across the animation set, weapon following
    picks = [sprites[40], sprites[120], sprites[200]]
    for i, p in enumerate(picks):
        g, n = p["group"], p["number"]
        cells.append((f"changsing_bo {g},{n}", member_sprite("changsing_bo", g, n), i, 2))

    for name, img, col, row in cells:
        x = col * cw + cw // 2 - img.width // 2
        y = row * ch + ch - pad - img.height
        img_sheet.paste(img, (x, y), img)
        d.text((col * cw + 10, row * ch + 10), name, font=font(15), fill=(226, 228, 238))
        d.line([(col * cw, row * ch), (col * cw, row * ch + ch)], fill=(44, 48, 58))
    img_sheet.save(path)
    print("wrote", path, img_sheet.size)


def scale_air(text, k):
    """Scale every frame offset and collision box in an AIR file."""
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.lower().startswith("clsn") and "=" in line:
            head, vals = line.split("=", 1)
            nums = re.findall(r"-?\d+", vals)
            if len(nums) == 4:
                out.append(head.strip() + " = " + ", ".join(
                    str(int(round(int(n) * k))) for n in nums))
                continue
        m = re.match(r"^(\d+)\s*,\s*(\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)$",
                     line)
        if m:
            g, n, x, y, t = (int(m.group(i)) for i in range(1, 6))
            out.append(f"{g},{n}, {int(round(x * k))},{int(round(y * k))}, {t}")
            continue
        out.append(raw.rstrip())
    return "\n".join(out) + "\n"


def member_palette(gang, cloth=1.0, skin=1.0, band=1.0):
    """One 256-colour palette for a member: index 0 transparent, then his art."""
    colours = []
    for rgb in list(colour_map(gang, cloth, skin, band).values()) + [
            STAFF["wood"], STAFF["wood_hi"], STAFF["cap"], STAFF["edge"],
            BLADE["steel"], BLADE["steel_hi"], BLADE["spine"], BLADE["grip"],
            BLADE["edge"]]:
        rgb = tuple(rgb[:3])
        if rgb not in colours:
            colours.append(rgb)
    flat = [255, 0, 255]                    # index 0: the SFF's transparent entry
    for rgb in colours[:255]:
        flat.extend(rgb)
    flat += [0] * (768 - len(flat))

    pal_bytes = bytearray()
    for i in range(256):
        r, g, b = flat[i * 3:i * 3 + 3]
        pal_bytes += bytes((r, g, b, 0 if i == 0 else 255))
    pal_img = Image.new("P", (1, 1))
    pal_img.putpalette(flat)
    return bytes(pal_bytes), pal_img


def build(cid):
    """Bake one gang member: recoloured, upscaled, armed Kung Fu Man art."""
    gang, cloth, skin, band, kind, build_scale, length = next(
        m for m in MEMBERS if m[0] == cid)[1:]
    raw, sprites, pal = sff.read_sff(os.path.join(BASE, "kfm.sff"))
    cmap = colour_map(gang, cloth, skin, band)
    skins = {_warm(SKIN[r], skin) for r in SKIN}
    pal_bytes, pal_img = member_palette(gang, cloth, skin, band)

    out = []
    for sp in sprites:
        if sp["group"] >= 9000:
            continue          # portraits are rendered fresh by build_portraits
        img = sff.decode_sprite(raw, sp, pal, 0)
        img = upscale(recolour(img, cmap))
        img = ImageOps.expand(img, (PAD_X, PAD_Y, PAD_X, PAD_Y), fill=(0, 0, 0, 0))
        img = paint_weapon(img, gang, skins, kind, length)
        if build_scale != 1.0:
            img = img.resize((max(1, round(img.width * build_scale)),
                              max(1, round(img.height * build_scale))), Image.LANCZOS)

        # 8-bit on the member's own palette: same art, a tenth of the bytes.
        indexed = img.convert("RGB").quantize(palette=pal_img,
                                              dither=Image.Dither.NONE)
        flat_p = Image.new("P", img.size, 0)
        flat_p.putpalette(indexed.getpalette())
        flat_p.paste(indexed, (0, 0),
                     img.split()[3].point(lambda a: 255 if a > 0 else 0))

        ax, ay = sp["axis"]
        out.append({"group": sp["group"], "number": sp["number"],
                    "image": flat_p,
                    "axis": (round(ax * SCALE * build_scale) + PAD_X,
                             round(ay * SCALE * build_scale) + PAD_Y)})

    d = os.path.join(ROOT, "chars", cid + "_rig")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, cid + ".sff"), "wb") as f:
        f.write(sff.write_sff(out, [pal_bytes]))

    air_src = open(os.path.join(BASE, "kfm.air"), encoding="utf-8-sig").read()
    with open(os.path.join(d, cid + ".air"), "w", encoding="utf-8") as f:
        f.write(scale_air(air_src, SCALE))

    def_path = os.path.join(d, cid + ".def")
    if os.path.isfile(def_path):
        with open(def_path, encoding="utf-8") as f:
            text = f.read().replace(' (rig)"', '"')
        with open(def_path, "w", encoding="utf-8") as f:
            f.write(text)
    print(f"{cid}: {len(out)} sprites -> chars/{cid}_rig")


if __name__ == "__main__":
    if "--sheet" in sys.argv:
        sheet()
    elif "--build" in sys.argv:
        for cid in (sys.argv[sys.argv.index("--build") + 1].split(",")
                    if len(sys.argv) > sys.argv.index("--build") + 1 else [m[0] for m in MEMBERS]):
            build(cid)
    else:
        print("usage: python3 tools/gang_kfm.py [--sheet | --build [id,id,...]]")
