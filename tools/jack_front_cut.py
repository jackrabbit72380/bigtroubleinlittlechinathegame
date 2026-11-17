"""Cut Jack Burton's forward-facing render into the front rig's parts.

The front set is what the win pose is drawn from, and it used to be one view
cropped out of a four-view turnaround: a figure holding a pistol, arms half out,
a few hundred pixels tall, with a neighbour's hand leaking into the crop. The art
is now a dedicated forward-facing render on transparency (jack_faceing_farward1)
and this tool measures THAT figure instead of re-using coordinates that were
fitted to the old one.

Nothing is hand-typed about the body except proportions a human figure cannot
avoid (where a knee falls between hip and floor). Every joint comes from the art:

  * the neck is the narrowest row in the top quarter,
  * the shoulders are the row just under it,
  * the belt is the first row that is denim,
  * the crotch is the first row below the belt where the denim splits in two,
  * the arm sockets are the shoulder ends of the bare skin left and right of the
    tank top.

Run:  python3 tools/jack_front_cut.py
      python3 tools/char_rig.py --sheet jackburton
"""

from __future__ import annotations

import json
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import jack_cut as jc  # matte, components, constants for the props

ROOT = jc.ROOT
CHAR = jc.CHAR
SOURCE = os.path.join(ROOT, "concept_art", "fighters", "jack_burton",
                      "jack_faceing_farward1.png")
OUT = jc.OUT
WORK = jc.WORK

FRAME_H = 607          # every game sprite of this fighter is this tall


def masks(art):
    """Skin, tank top, denim and boot leather, from colour alone."""
    w, h = art.size
    skin = Image.new("L", (w, h), 0)
    vest = Image.new("L", (w, h), 0)
    denim = Image.new("L", (w, h), 0)
    boot = Image.new("L", (w, h), 0)
    sp = art.load()
    sk, ve, de, bo = skin.load(), vest.load(), denim.load(), boot.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = sp[x, y]
            if a < 200:
                continue
            if r > 120 and r - b > 30 and r - g > 8:
                sk[x, y] = 255
            elif b - r > 28 and b > 80 and g > 45:
                de[x, y] = 255
            elif r > 80 and r > g + 14 and g > b and b < 120:
                bo[x, y] = 255
            elif min(r, g, b) > 145 and max(r, g, b) - min(r, g, b) < 34:
                ve[x, y] = 255
    return dict(skin=skin, vest=vest, denim=denim, boot=boot)


def profile(mask, y, thr=3):
    """(min_x, max_x, count) of a mask on one row."""
    w = mask.size[0]
    px = mask.load()
    xs = [x for x in range(w) if px[x, y] > 128]
    if len(xs) < thr:
        return None
    return xs[0], xs[-1], len(xs)


def first_row(mask, start, stop, thr):
    for y in range(start, stop):
        p = profile(mask, y, thr)
        if p:
            return y, p
    return None, None


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)

    src = Image.open(SOURCE)
    if src.mode != "RGBA":
        src = src.convert("RGBA")
    figure = src.crop(src.getbbox())
    scale = FRAME_H / float(figure.height)
    figure = figure.resize(
        (max(1, int(round(figure.width * scale))), FRAME_H), Image.LANCZOS)
    art = Image.new("RGBA", (figure.width + 40, FRAME_H), (0, 0, 0, 0))
    art.paste(figure, (20, 0))
    art.save(os.path.join(WORK, "front.png"))
    print(f"front cutout {art.size} (figure {figure.size}, scale {scale:.3f})")

    W, H = art.size
    alpha = art.getchannel("A")
    m = masks(art)

    # --- the figure's own rows -------------------------------------------------
    def width_at(y):
        p = profile(alpha, y, 2)
        return (p[1] - p[0] + 1) if p else 0

    # neck: the narrowest row between the top of the head and the shoulders.
    # The chin and the hair are wider than the neck, so the minimum is the neck.
    cand = [(width_at(y), y) for y in range(int(H * 0.10), int(H * 0.30))]
    cand = [c for c in cand if c[0] > 0]
    neck_y = min(cand)[1]
    neck_x = sum(profile(alpha, neck_y)[:2]) / 2.0
    shoulder_y = neck_y + int(round(H * 0.055))

    # head: everything above the neck, as wide as the hair goes
    head_rows = [profile(alpha, y, 2) for y in range(0, neck_y + 4)]
    head_rows = [r for r in head_rows if r]
    hx0 = min(r[0] for r in head_rows)
    hx1 = max(r[1] for r in head_rows)

    # Belt: the first row with a WIDE run of denim. Counting scattered blue
    # pixels found the print on his shirt - the emblem is blue and its rock is
    # blue - which put the waist halfway up his chest and cut the torso to a
    # strip. Only a run of denim as wide as the body is the waistband.
    fig_w = max(width_at(y) for y in range(shoulder_y, H))
    belt_y = None
    counts = []
    px = m["denim"].load()
    for y in range(H):
        counts.append(sum(1 for x in range(W) if px[x, y] > 128))
    need = fig_w * 0.18
    for y in range(shoulder_y + int(H * 0.10), H - 5):
        # five rows in a row, so a single seam or a blue pocket stud cannot pass
        if all(counts[y + i] >= need for i in range(5)):
            belt_y = y
            break
    if belt_y is None:
        raise SystemExit("no denim found - is the art the forward render?")

    # The body's width is the figure's own span at the shoulder row. It used to
    # be taken from the tank top's white pixels, and the print on that shirt is
    # half the vest - the "body" came out 69px wide on a 383px figure, which cut
    # the torso to a ribbon and put both arm sockets inside his chest.
    bp = profile(alpha, shoulder_y, 8)
    if not bp:
        raise SystemExit("no body found at the shoulder row")
    vest_l, vest_r = bp[0] + 5, bp[1] - 5
    chest_x = (vest_l + vest_r) / 2.0
    body_half = (vest_r - vest_l) / 2.0

    # crotch: the first row below the belt where the denim is in two pieces
    crotch_y, crotch_x = belt_y + int(H * 0.12), chest_x
    for y in range(belt_y + int(H * 0.03), int(H * 0.75)):
        px = m["denim"].load()
        runs, cur = [], None
        for x in range(W):
            if px[x, y] > 128:
                if cur is None:
                    cur = [x, x]
                else:
                    cur[1] = x
            elif cur is not None:
                if cur[1] - cur[0] > 10:
                    runs.append(cur)
                cur = None
        if cur is not None and cur[1] - cur[0] > 10:
            runs.append(cur)
        if len(runs) >= 2 and runs[-1][0] - runs[0][1] > 6:
            crotch_y = y
            crotch_x = (runs[0][1] + runs[-1][0]) / 2.0
            break

    hip_y = belt_y
    knee_y = int(round(hip_y + (H - hip_y) * 0.52))
    ankle_y = int(round(H - H * 0.045))

    # --- parts -----------------------------------------------------------------
    parts, pivots, angles = {}, {}, {}

    def cut(name, box=None, polygon=None, pivot=None, angle=None, only=None,
            exclude=None):
        mask = Image.new("L", art.size, 0)
        d = ImageDraw.Draw(mask)
        if polygon:
            d.polygon(polygon, fill=255)
        else:
            d.rectangle(box, fill=255)
        if exclude is not None:
            mask = ImageChops.multiply(mask, ImageChops.invert(exclude))
        if only is not None:
            # ... and only inside that material. The legs are cut as boxes as tall
            # as the hip, and his hands hang at exactly that height: without this
            # each thigh carried a piece of the near hand and pasted it over the
            # arm, which is the doubled arm that stood beside him.
            mask = ImageChops.multiply(mask, only)
        piece = Image.new("RGBA", art.size, (0, 0, 0, 0))
        piece.paste(art, (0, 0), mask)
        bb = piece.getbbox()
        if not bb:
            raise SystemExit(f"{name}: cut produced an empty part")
        img = piece.crop(bb)
        piv = (pivot[0] - bb[0], pivot[1] - bb[1])
        img.save(os.path.join(OUT, f"{name}.png"))
        parts[name] = img.size
        pivots[name] = [round(piv[0], 1), round(piv[1], 1)]
        if angle is not None:
            angles[name] = round(angle, 2)
        return img, piv

    # head: hair and face, down to just under the jaw
    cut("head", box=(hx0 - 2, 0, hx1 + 2, neck_y + 6),
        pivot=(neck_x, neck_y + 2), angle=0.0)

    # torso: the tank top and the skin inside the shoulder line. A box, not a
    # traced outline - the arms are drawn over it, so the only silhouette that
    # shows is the vest's own, and its alpha is the art's alpha.
    # Torso stops inside the arms. The shoulder row's span INCLUDES them (they
    # hang at his sides and touch the body), so a box that wide put a copy of both
    # arms in the torso as well as in the arm parts - the doubled, ghosted arm.
    cut("torso", box=(int(chest_x - body_half * 0.68), neck_y + 4,
                      int(chest_x + body_half * 0.68), belt_y + 12),
        pivot=(chest_x, belt_y), angle=0.0)

    # pelvis: the waistband, behind the torso
    # The waistband only: starting above the belt took in the hem of the tank top,
    # and that hem swung out of his waist as a white flap whenever he moved.
    cut("pelvis", box=(int(crotch_x - body_half * 0.9), belt_y + 2,
                       int(crotch_x + body_half * 0.9), crotch_y + 30),
        pivot=(crotch_x, belt_y), angle=0.0)

    hip_half = max(14.0, (vest_r - vest_l) * 0.16)
    sh_half = max(18.0, (vest_r - vest_l) * 0.30)

    # --- arms ------------------------------------------------------------------
    arm_metrics = {}
    arm_masks = {}
    arm_joints = {}
    for side, sign in (("f", -1), ("n", 1)):
        # bare skin on that side of the tank top, from the shoulder down to the
        # hand: no props in this render, so the arm is one clean island
        skin = m["skin"]
        sel = Image.new("L", art.size, 0)
        sp, dp = skin.load(), sel.load()
        for y in range(shoulder_y - 10, H):
            for x in range(W):
                if sp[x, y] > 128 and ((x < vest_l - 2) if sign < 0 else (x > vest_r + 2)):
                    dp[x, y] = 255
        blobs = jc.components(sel, min_area=400)
        if not blobs:
            raise SystemExit(f"no {side} arm found")
        arm_px = max(blobs, key=len)

        sh = (vest_l - 4 if sign < 0 else vest_r + 4, shoulder_y + 2)
        tip = max(arm_px, key=lambda q: (q[0] - sh[0]) ** 2 + (q[1] - sh[1]) ** 2)
        a_up = math.degrees(math.atan2(tip[0] - sh[0], tip[1] - sh[1]))

        keep = Image.new("L", art.size, 0)
        kp = keep.load()
        for x, y in arm_px:
            kp[x, y] = 255
        # the leather wristband and the fist are darker than skin; grow a little
        # and keep non-white art so they come with the arm
        grow = keep.filter(ImageFilter.MaxFilter(9))
        solid = Image.new("L", art.size, 0)
        sd, ap = solid.load(), art.load()
        for y in range(art.size[1]):
            for x in range(W):
                r, g, b, a = ap[x, y]
                if a > 128 and not (r > 198 and g > 198 and b > 198
                                    and max(r, g, b) - min(r, g, b) < 24):
                    sd[x, y] = 255
        arm_mask = ImageChops.multiply(ImageChops.multiply(grow, alpha), solid)

        arm_masks[side] = arm_mask
        piece = Image.new("RGBA", art.size, (0, 0, 0, 0))
        piece.paste(art, (0, 0), arm_mask)
        bb = piece.getbbox()
        img = piece.crop(bb)
        piv = (sh[0] - bb[0], sh[1] - bb[1])
        img.save(os.path.join(OUT, f"arm_{side}.png"))
        parts[f"arm_{side}"] = img.size
        pivots[f"arm_{side}"] = [round(piv[0], 1), round(piv[1], 1)]
        angles[f"arm_{side}"] = round(a_up, 2)

        length = math.hypot(tip[0] - sh[0], tip[1] - sh[1])
        ux = (tip[0] - sh[0]) / length
        uy = (tip[1] - sh[1]) / length
        elb = (sh[0] + ux * length * 0.55, sh[1] + uy * length * 0.55)
        wr = (sh[0] + ux * length * 0.90, sh[1] + uy * length * 0.90)
        arm_joints[side] = [
            [round(elb[0] - bb[0], 1), round(elb[1] - bb[1], 1)],
            [round(wr[0] - bb[0], 1), round(wr[1] - bb[1], 1)],
        ]
        arm_metrics[side] = dict(
            shoulder=sh,
            elbow=(sh[0] + ux * length * 0.55, sh[1] + uy * length * 0.55),
            wrist=(sh[0] + ux * length * 0.90, sh[1] + uy * length * 0.90),
            length=length,
        )

    # Each leg's own denim/boot extent on its own side of the crotch. Cutting a
    # fixed 120px swath either side made each part twice as wide as the leg, and a
    # part's width sets its joint radius - so the leg welds inflated into big
    # brown capsules standing beside the boots.
    # His fists hang level with the top of the legs, and shadowed skin beside
    # denim passes a denim test - so every leg box took a piece of hand with it
    # and pasted a blue-grey hand onto each hip. The arms are already cut by then,
    # so the legs are simply told not to take their pixels.
    arms_all = Image.new("L", art.size, 0)
    for _mask in arm_masks.values():
        arms_all = ImageChops.lighter(arms_all, _mask)
    cloth = ImageChops.lighter(m["denim"], m["boot"]).filter(
        ImageFilter.MaxFilter(5))
    legs = {}
    for side, sign in (("f", -1), ("n", 1)):
        # measured on the shin, where the leg is at its own width: over every row
        # the union also catches the flare of the boot and, on the near side, the
        # other leg, and a part's width is what sizes its joint radius
        px = ImageChops.lighter(m["denim"], m["boot"]).load()
        row = int((knee_y + ankle_y) / 2)
        xs = [x for y in range(row - 6, row + 6) for x in range(W)
              if px[x, y] > 128 and ((x < crotch_x) if sign < 0 else (x > crotch_x))]
        if not xs:
            raise SystemExit(f"no {side} leg found")
        legs[side] = (min(xs), max(xs))

    for side, sign in (("f", -1), ("n", 1)):
        hx = crotch_x + sign * hip_half
        lx0, lx1 = legs[side]
        pad = 8
        # From just under the crotch: his fists hang at hip height, and a box that
        # started at the belt took the hand in with the denim - and shadowed skin
        # beside denim passes for denim - which pasted a blue-grey hand onto each
        # hip. The waistband above the crotch is the pelvis part's job.
        if side == "f":
            box = (lx0 - pad, crotch_y - 8, int(crotch_x + 2), knee_y + 10)
        else:
            box = (int(crotch_x - 2), crotch_y - 8, lx1 + pad, knee_y + 10)
        a = math.degrees(math.atan2(0.0, 1.0))
        cut(f"thigh_{side}", box=box, pivot=(hx, belt_y - 12), angle=a,
            only=cloth, exclude=arms_all)

        if side == "f":
            sbox = (lx0 - pad, knee_y - 12, int(crotch_x + 2), H)
        else:
            sbox = (int(crotch_x - 2), knee_y - 12, lx1 + pad, H)
        cut(f"shin_{side}", box=sbox, pivot=(hx, knee_y), angle=a, only=cloth,
            exclude=arms_all)

    # --- props -----------------------------------------------------------------
    # Still cut from the turnaround: the forward render has him empty-handed.
    raw = Image.open(jc.PROP_SOURCE).convert("RGB")
    pw, ph = raw.size
    view = raw.crop((int(pw * jc.PROP_CROP[0]), 0,
                     int(pw * jc.PROP_CROP[1]), ph))
    matted = jc.matte(view, view.getpixel((3, 3)))
    prop_art = matted.crop(matted.getbbox())
    spare = art
    for name, mission in (("prop", "gun"), ("prop_knife", "knife")):
        box = jc.GUN_BOX if mission == "gun" else jc.KNIFE_BOX
        grip = jc.GUN_GRIP if mission == "gun" else jc.KNIFE_GRIP
        mask = Image.new("L", prop_art.size, 0)
        ImageDraw.Draw(mask).rectangle(box, fill=255)
        piece = Image.new("RGBA", prop_art.size, (0, 0, 0, 0))
        piece.paste(prop_art, (0, 0), mask)
        bb = piece.getbbox()
        if not bb:
            continue
        img = piece.crop(bb)
        if mission == "gun":
            barrel = math.degrees(math.atan2(jc.GUN_MUZZLE[0] - jc.GUN_GRIP[0],
                                             jc.GUN_MUZZLE[1] - jc.GUN_GRIP[1]))
            img = img.rotate(-(90.0 - barrel), resample=Image.BICUBIC, expand=True)
            grip_local = (grip[0] - bb[0], grip[1] - bb[1])
            cx, cy = (bb[2] - bb[0]) / 2.0, (bb[3] - bb[1]) / 2.0
            th = math.radians(-(90.0 - barrel))
            dx, dy = grip_local[0] - cx, grip_local[1] - cy
            rx = dx * math.cos(th) - dy * math.sin(th)
            ry = dx * math.sin(th) + dy * math.cos(th)
            grip_local = (img.width / 2.0 + rx, img.height / 2.0 + ry)
        else:
            grip_local = (grip[0] - bb[0], grip[1] - bb[1])
        img.save(os.path.join(OUT, f"{name}.png"))
        parts[name] = img.size
        pivots[name] = [round(grip_local[0], 1), round(grip_local[1], 1)]
        angles[name] = 0.0

    # --- skeleton, from the measurements ---------------------------------------
    hip_abs = H - hip_y
    torso_len = float(belt_y - (shoulder_y - 6))
    sh_n = arm_metrics["n"]["shoulder"]
    sh_f = arm_metrics["f"]["shoulder"]
    el_n, wr_n = arm_metrics["n"]["elbow"], arm_metrics["n"]["wrist"]
    metrics = dict(
        hip_y=-round(hip_abs, 1),
        shoulder_y=-round(hip_abs + torso_len, 1),
        neck_y=-round(hip_abs + torso_len + 8, 1),
        knee_y=-(H - knee_y),
        ankle_y=-(H - ankle_y),
        torso_len=round(torso_len, 1),
        neck_len=8.0,
        uarm=round(math.hypot(el_n[0] - sh_n[0], el_n[1] - sh_n[1]), 1),
        farm=round(math.hypot(wr_n[0] - el_n[0], wr_n[1] - el_n[1]), 1),
        hand=round(arm_metrics["n"]["length"] * 0.14, 1),
        thigh=round(knee_y - hip_y, 1),
        shin=round(ankle_y - knee_y, 1),
        shoulder_half=round(abs(sh_n[0] - sh_f[0]) / 2.0, 1),
        hip_half=round(hip_half, 1),
    )

    rig = dict(
        scale=1.0,
        canvas=[640, 780],
        axis=[300, 700],
        metrics=metrics,
        pivots=pivots,
        angles=angles,
        # Where THIS art bends its arms, in part pixels. Without its own table
        # the loader falls back to the joints measured on the profile art and
        # slices the front arm at the wrong place - which came out as a pale
        # second arm standing behind the real one.
        arm_joints=arm_joints,
        hand_pieces=False,
        # No joint welds. This render is one continuous figure - arm to body, shin
        # to thigh - so there is no air at any joint to fill. The welds only added
        # a fat capsule of invented skin beside each arm and each boot, which read
        # as a second ghost limb.
        welds_off=["arm_n", "arm_f", "thigh_n", "thigh_f",
                   "shin_n", "shin_f"],
        _note=("Front set cut from jack_faceing_farward1.png by "
               "tools/jack_front_cut.py. The forward render has both arms at his "
               "sides and no props, so each arm is its own clean island; the "
               "pistol and knife are still cut from the turnaround."),
    )
    with open(os.path.join(OUT, "rig.json"), "w", encoding="utf-8") as f:
        json.dump(rig, f, indent=2)
        f.write("\n")

    for fname in sorted(os.listdir(OUT)):
        if fname.endswith(".png") and fname[:-4] not in parts:
            os.remove(os.path.join(OUT, fname))
            print(f"  removed stale part {fname}")

    print(f"neck y={neck_y} shoulder y={shoulder_y} belt y={belt_y} "
          f"crotch ({crotch_x:.0f},{crotch_y}) knee y={knee_y} ankle y={ankle_y}")
    for name in sorted(parts):
        w, h = parts[name]
        print(f"  {name:12} {w:4}x{h:<4} pivot {pivots[name]}"
              + (f"  art {angles[name]:+.1f} deg" if name in angles else ""))
    print(f"wrote {len(parts)} parts + rig.json to {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    raise SystemExit(main())
