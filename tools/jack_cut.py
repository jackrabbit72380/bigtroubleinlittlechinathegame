"""Cut Jack Burton's concept turnaround into rig parts.

The turnaround (four views on a flat studio background) is the only source with
the whole figure and the boots in frame, so the puppet parts come from its
front view. Nothing is generated here: every part is a masked crop of the art,
which is why the in-game result inherits the concept art's paint.

Joint coordinates below were measured off a 50px grid overlay of the cutout
(see art_src/chars/jackburton/work/front_grid.png); all values are pixels in
that cutout, origin at its top-left.

Run:  python3 tools/jack_cut.py
      python3 tools/char_rig.py --sheet jackburton
"""

from __future__ import annotations

import json
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAR = "jackburton"
SOURCE = os.path.join(ROOT, "concept_art", "fighters", "jack_burton",
                      "bernardo-mercurio-jack-turnable.jpg")
OUT = os.path.join(ROOT, "art_src", "chars", CHAR, "parts")
WORK = os.path.join(ROOT, "art_src", "chars", CHAR, "work")

# The front view sits in the second of four equally spaced poses.
CROP = (0.26, 0.56)

# --- measured joints (cutout pixels) -----------------------------------------
NECK = (300, 116)
HIP = (300, 292)
SHOULDER = {"f": (268, 148), "n": (348, 148)}   # measured on the grid
SHOULDER_F = (222, 150)      # screen left = far side
SHOULDER_N = (344, 150)      # screen right = near side
ELBOW_F = (178, 196)
ELBOW_N = (392, 196)
WRIST_F = (138, 212)
WRIST_N = (446, 212)
HIP_F = (278, 296)
HIP_N = (326, 296)
KNEE_F = (266, 436)
KNEE_N = (338, 436)
ANKLE_F = (260, 572)
ANKLE_N = (344, 572)
FOOT_Y = 575

HEAD_BOX = (254, 2, 352, 120)
TORSO_POLY = [(212, 150), (240, 126), (272, 112), (328, 112),
              (360, 126), (388, 150), (368, 296), (236, 296)]
PELVIS_POLY = [(238, 258), (362, 258), (352, 336), (248, 336)]
# The boot shaft belongs to the shin; the foot crop starts below the ankle,
# because overlapping the two duplicated the boot in every pose.
FOOT_N_BOX = (316, 574, 452, 616)
FOOT_F_BOX = (232, 574, 356, 616)
GUN_BOX = (14, 66, 152, 170)
GUN_GRIP = (120, 168)
GUN_MUZZLE = (24, 78)
KNIFE_BOX = (462, 176, 516, 262)
KNIFE_GRIP = (479, 188)


def matte(img, bg, soft=14, hard=42):
    """Flat-background knockout with a soft edge."""
    out = Image.new("RGBA", img.size)
    sp, op = img.load(), out.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b = sp[x, y]
            d = max(abs(r - bg[0]), abs(g - bg[1]), abs(b - bg[2]))
            if d < soft:
                a = 0
            elif d < hard:
                a = int(255 * (d - soft) / max(1, hard - soft))
            else:
                a = 255
            op[x, y] = (r, g, b, a)
    return out


def limb_poly(p0, p1, r0, r1, pad0=16, pad1=16):
    """Tapered quad along a limb, extended past both joints to hide seams."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    length = math.hypot(dx, dy) or 1.0
    ux, uy = dx / length, dy / length
    ax, ay = p0[0] - ux * pad0, p0[1] - uy * pad0
    bx, by = p1[0] + ux * pad1, p1[1] + uy * pad1
    px, py = -uy, ux
    return [(ax + px * r0, ay + py * r0), (bx + px * r1, by + py * r1),
            (bx - px * r1, by - py * r1), (ax - px * r0, ay - py * r0)]


def rotate_about(img, pivot, delta_cw):
    """Rotate an image and carry the pivot with it (screen-clockwise degrees)."""
    pil = -delta_cw
    out = img.rotate(pil, resample=Image.BICUBIC, expand=True)
    cx, cy = img.width / 2.0, img.height / 2.0
    dx, dy = pivot[0] - cx, pivot[1] - cy
    th = math.radians(pil)
    rx = dx * math.cos(th) - dy * math.sin(th)
    ry = dx * math.sin(th) + dy * math.cos(th)
    return out, (out.width / 2.0 + rx, out.height / 2.0 + ry)


def skin_mask(img):
    """Bare skin: warm, mid-bright, and not the tank top or the denim."""
    mask = Image.new("L", img.size, 0)
    sp, mp = img.load(), mask.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = sp[x, y]
            if a < 200:
                continue
            if r > 120 and r - b > 26 and r - g > 6 and g > 70 and b < 215:
                mp[x, y] = 255
    return mask


def components(mask, min_area=600):
    """8-connected components of a mask, as lists of pixels."""
    w, h = mask.size
    px = mask.load()
    seen = bytearray(w * h)
    out = []
    for y in range(h):
        for x in range(w):
            i = y * w + x
            if seen[i] or px[x, y] < 128:
                continue
            stack = [(x, y)]
            seen[i] = 1
            pix = []
            while stack:
                cx, cy = stack.pop()
                pix.append((cx, cy))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            j = ny * w + nx
                            if not seen[j] and px[nx, ny] >= 128:
                                seen[j] = 1
                                stack.append((nx, ny))
            if len(pix) >= min_area:
                out.append(pix)
    return out


def principal_axis(pix):
    """(centre, unit direction, projection range) of a pixel cloud."""
    n = len(pix)
    mx = sum(p[0] for p in pix) / n
    my = sum(p[1] for p in pix) / n
    sxx = sum((p[0] - mx) ** 2 for p in pix)
    syy = sum((p[1] - my) ** 2 for p in pix)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pix)
    ang = 0.5 * math.atan2(2 * sxy, sxx - syy)
    ux, uy = math.cos(ang), math.sin(ang)
    ts = [((p[0] - mx) * ux + (p[1] - my) * uy) for p in pix]
    return (mx, my), (ux, uy), (min(ts), max(ts))


def cut(source, polygon=None, box=None, ellipse=False):
    """Mask the art to a shape and crop it, returning (image, offset)."""
    mask = Image.new("L", source.size, 0)
    d = ImageDraw.Draw(mask)
    if polygon:
        d.polygon(polygon, fill=255)
    else:
        if ellipse:
            d.ellipse(box, fill=255)
        else:
            d.rectangle(box, fill=255)
    part = Image.new("RGBA", source.size, (0, 0, 0, 0))
    part.paste(source, (0, 0), mask)
    bbox = part.getbbox()
    if not bbox:
        raise SystemExit("cut produced an empty part")
    return part.crop(bbox), (bbox[0], bbox[1])


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)

    src = Image.open(SOURCE).convert("RGB")
    W, H = src.size
    view = src.crop((int(W * CROP[0]), 0, int(W * CROP[1]), H))
    bg = view.getpixel((3, 3))
    figure = matte(view, bg)
    bbox = figure.getbbox()
    art = figure.crop(bbox)
    art.save(os.path.join(WORK, "front.png"))
    print(f"front cutout {art.size}, background {bg}")

    parts, pivots, angles = {}, {}, {}
    metrics = {}

    def emit(name, image, pivot, angle=None, mirror=False):
        if mirror:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
            pivot = (image.width - pivot[0], pivot[1])
        image.save(os.path.join(OUT, f"{name}.png"))
        parts[name] = image.size
        pivots[name] = [round(pivot[0], 1), round(pivot[1], 1)]
        if angle is not None:
            angles[name] = round(angle, 2)

    def emit_shape(name, pivot, polygon=None, box=None, ellipse=False,
                   angle=None, mirror=False, rotate_to=None):
        img, off = cut(art, polygon=polygon, box=box, ellipse=ellipse)
        piv = (pivot[0] - off[0], pivot[1] - off[1])
        if rotate_to is not None:
            img, piv = rotate_about(img, piv, rotate_to)
        emit(name, img, piv, angle, mirror)

    # --- body ---------------------------------------------------------------
    emit_shape("head", NECK, box=HEAD_BOX, ellipse=True, angle=0.0)
    emit_shape("torso", HIP, polygon=TORSO_POLY, angle=0.0)
    emit_shape("pelvis", (300, 264), polygon=PELVIS_POLY, angle=0.0)

    def mean_colour(img, band=0.35):
        h = max(1, int(img.height * band))
        px = list(img.crop((0, 0, img.width, h)).convert("RGBA").resize((8, 8), Image.BOX).getdata())
        tot, n = [0, 0, 0], 0
        for r, g, b, a in px:
            if a > 100:
                tot[0] += r
                tot[1] += g
                tot[2] += b
                n += 1
        if not n:
            return (210, 165, 135)
        return tuple(v // n for v in tot)

    def part_from_pixels(name, pix, pivot, angle, cap=0):
        """Mask the art to exactly these pixels and crop to them.

        ``cap`` paints a disc of the arm's own colour UNDER the art at the
        pivot, so rotating the limb cannot tear a hole at the shoulder.
        """
        mask = Image.new("L", art.size, 0)
        mp = mask.load()
        for x, y in pix:
            mp[x, y] = 255
        piece = Image.new("RGBA", art.size, (0, 0, 0, 0))
        piece.paste(art, (0, 0), mask)
        bbox = piece.getbbox()
        img = piece.crop(bbox)
        piv = (pivot[0] - bbox[0], pivot[1] - bbox[1])
        if cap:
            # Fill ONLY the transparent gap around the pivot. Painting a solid
            # disc over the limb is what showed up as a second ghost arm.
            shape = Image.new("L", img.size, 0)
            ImageDraw.Draw(shape).ellipse(
                [piv[0] - cap, piv[1] - cap, piv[0] + cap, piv[1] + cap], fill=255)
            shape = ImageChops.multiply(shape,
                                        ImageChops.invert(img.getchannel("A")))
            disc = Image.new("RGBA", img.size, mean_colour(img) + (0,))
            disc.putalpha(shape)
            img = Image.alpha_composite(img, disc)
        emit(name, img, piv, angle)

    def auto_arm(side, centre_x=300):
        """Mask each arm to its OWN art, and nothing else.

        The arms are the biggest bare-skin blobs left and right of the body,
        but the bare chest sits ~2px from both bounding boxes, so a proximity
        merge dragged a slab of chest into each crop - that slab was the
        rectangle across the torso and the second arm in every pose. Groups
        are only merged when they are on the arm's own side of the body AND
        actually adjacent, which picks up a fist separated from its arm by a
        held prop, and never the chest.
        """
        def bbox(pix):
            xs = [p[0] for p in pix]
            ys = [p[1] for p in pix]
            return min(xs), min(ys), max(xs), max(ys)

        groups = []
        for pix in components(skin_mask(art)):
            cx = sum(p[0] for p in pix) / len(pix)
            cy = sum(p[1] for p in pix) / len(pix)
            if cy > 300:                        # a leg, not an arm
                continue
            if abs(cx - centre_x) < 30:         # the bare chest / neckline
                continue
            if (side == "f" and cx >= centre_x) or (side == "n" and cx <= centre_x):
                continue
            groups.append(pix)
        if not groups:
            raise SystemExit(f"no {side} arm found in the art")

        groups.sort(key=len, reverse=True)
        best = list(groups[0])
        ax0, ay0, ax1, ay1 = bbox(best)
        for g in groups[1:]:
            bx0, by0, bx1, by1 = bbox(g)
            gap = max(0, max(ax0, bx0) - min(ax1, bx1))
            if gap <= 20:                       # a fist beside its own forearm
                best.extend(g)

        # Pivot = the TOP of the arm where it meets the shoulder, i.e. the arm
        # pixel nearest the torso's upper corner on that side. Picking the
        # nearest pixel to the body's mid-line landed on the ARMPIT, so the
        # deltoid was pasted above the shoulder joint and every arm looked
        # pinned on and raised.
        torso_top = min(y for _x, y in TORSO_POLY)
        torso_half = (max(x for x, _y in TORSO_POLY)
                      - min(x for x, _y in TORSO_POLY)) / 2.0
        sign = 1 if side == "n" else -1
        corner = (centre_x + sign * torso_half, torso_top + 2)
        sh = min(best, key=lambda q: (q[0] - corner[0]) ** 2 + (q[1] - corner[1]) ** 2)
        tip = max(best, key=lambda q: (q[0] - sh[0]) ** 2 + (q[1] - sh[1]) ** 2)
        a_up = math.degrees(math.atan2(tip[0] - sh[0], tip[1] - sh[1]))

        # Bridge non-skin pixels that belong to the arm. The leather wristband
        # is dark, so a skin-only mask leaves the fist floating beside the
        # forearm in every frame. Grow the mask a little and keep non-white
        # art: the tank top is white, so the shirt stays out while the band,
        # the grip and the fist come in.
        sel = Image.new("L", art.size, 0)
        sp = sel.load()
        for x, y in best:
            sp[x, y] = 255
        grown = sel.filter(ImageFilter.MaxFilter(29))
        alpha = art.getchannel("A").point(lambda v: 255 if v > 128 else 0)
        solid = Image.new("L", art.size, 0)
        dp = solid.load()
        ap = art.load()
        for yy in range(art.height):
            for xx in range(art.width):
                r, g, b, a = ap[xx, yy]
                if a > 128 and not (r > 196 and g > 196 and b > 196
                                    and max(r, g, b) - min(r, g, b) < 26):
                    dp[xx, yy] = 255
        keep = ImageChops.multiply(ImageChops.multiply(grown, alpha), solid)
        kp = keep.load()
        best = [(xx, yy) for yy in range(art.height) for xx in range(art.width)
                if kp[xx, yy] > 128]

        part_from_pixels(f"arm_{side}", best, sh, a_up, cap=0)

        length = math.hypot(tip[0] - sh[0], tip[1] - sh[1])
        ux, uy = (tip[0] - sh[0]) / length, (tip[1] - sh[1]) / length

        def at(t):
            return (sh[0] + ux * t, sh[1] + uy * t)

        return dict(shoulder=sh, elbow=at(length * 0.55), wrist=at(length * 0.90))

    arms = {"f": auto_arm("f"), "n": auto_arm("n")}

    def leg(side, hip, knee, ankle):
        a1 = math.degrees(math.atan2(knee[0] - hip[0], knee[1] - hip[1]))
        a2 = math.degrees(math.atan2(ankle[0] - knee[0], ankle[1] - knee[1]))
        emit_shape(f"thigh_{side}", hip,
                   polygon=limb_poly(hip, knee, 32, 29, pad0=10, pad1=10),
                   angle=a1)
        # A tapered polygon clipped the boot narrower than the art, leaving a
        # gap above the sole. A box around the leg keeps the boot continuous.
        x0 = min(knee[0], ankle[0]) - 40
        x1 = max(knee[0], ankle[0]) + 40
        emit_shape(f"shin_{side}", knee, box=(x0, knee[1], x1, ankle[1] + 8),
                   angle=a2)
        return a1, a2

    leg("f", HIP_F, KNEE_F, ANKLE_F)
    leg("n", HIP_N, KNEE_N, ANKLE_N)

    # No separate foot parts: the boot art already includes the toe and sole
    # down to the ground, so cutting a foot as well pasted a SECOND shoe
    # beside each boot in every pose. The shin carries the whole boot.

    # --- props --------------------------------------------------------------
    barrel = math.degrees(math.atan2(GUN_MUZZLE[0] - GUN_GRIP[0],
                                     GUN_MUZZLE[1] - GUN_GRIP[1]))
    emit_shape("prop", GUN_GRIP, box=GUN_BOX, angle=0.0,
               rotate_to=90.0 - barrel)
    emit_shape("prop_knife", KNIFE_GRIP, box=KNIFE_BOX, angle=0.0)

    # --- skeleton, in the art's own pixels ----------------------------------
    # The cut parts are the ONLY source of truth for the skeleton. Bone
    # lengths and the shoulder line come from the pivots the extractor
    # measured; mixing them with typed-in constants put the arms 20px below
    # their own sockets.
    hip_abs = 607 - HIP[1]
    sh_n, sh_f = arms["n"]["shoulder"], arms["f"]["shoulder"]
    el_n, wr_n = arms["n"]["elbow"], arms["n"]["wrist"]
    shoulder_abs = 607 - (sh_n[1] + sh_f[1]) / 2.0
    # The shoulder joint is the TOP OF THE TORSO ART, not a fitted arm axis:
    # measuring it from the arm put the socket ~35px low, which left a gap at
    # every shoulder and made the arms look pinned on from the outside.
    torso_len = float(pivots["torso"][1])
    metrics.update(
        hip_y=-round(hip_abs, 1),
        shoulder_y=-round(hip_abs + torso_len, 1),
        neck_y=-round(hip_abs + torso_len + 8, 1),
        knee_y=-(607 - KNEE_N[1]),
        ankle_y=-(607 - ANKLE_N[1]),
        torso_len=round(torso_len, 1),
        neck_len=8.0,
        uarm=round(math.hypot(el_n[0] - sh_n[0], el_n[1] - sh_n[1]), 1),
        farm=round(math.hypot(wr_n[0] - el_n[0], wr_n[1] - el_n[1]), 1),
        hand=34.0,
        thigh=round(math.hypot(KNEE_N[0] - HIP_N[0], KNEE_N[1] - HIP_N[1]), 1),
        shin=round(math.hypot(ANKLE_N[0] - KNEE_N[0], ANKLE_N[1] - KNEE_N[1]), 1),
        shoulder_half=round(abs(sh_n[0] - sh_f[0]) / 2.0, 1),
        hip_half=round((HIP_N[0] - HIP_F[0]) / 2.0, 1),
    )

    rig = dict(
        scale=1.0,
        canvas=[640, 780],
        axis=[300, 700],
        metrics=metrics,
        pivots=pivots,
        angles=angles,
    )
    with open(os.path.join(OUT, "rig.json"), "w", encoding="utf-8") as f:
        json.dump(rig, f, indent=2)
        f.write("\n")

    for name in sorted(parts):
        w, h = parts[name]
        print(f"  {name:12} {w:4}x{h:<4} pivot {pivots[name]}"
              + (f"  art {angles[name]:+.1f} deg" if name in angles else ""))
    # Remove parts this run did not produce. A stale PNG is loaded by the rig
    # and drawn on top of the fresh one, which is how a deleted foot part kept
    # showing up as a second shoe beside every boot.
    for fname in sorted(os.listdir(OUT)):
        if not fname.endswith(".png"):
            continue
        if fname[:-4] not in parts:
            os.remove(os.path.join(OUT, fname))
            print(f"  removed stale part {fname}")
    print(f"wrote {len(parts)} parts + rig.json to {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    raise SystemExit(main())
