"""Cut a SIDE-VIEW part set for char_rig from the concept turnaround.

Fighters have to face each other, which the front-facing part set cannot do:
it was cut from the frontal panel of the turnaround, so every pose looked at
the camera. Panel 3 of the same turnaround holds Jack in profile facing right
(that is the only panel with a true side view - panels 1 and 2 are front and
three-quarter, and the left figure of panel 3 is a back view).

This writes ``art_src/chars/<id>/parts_side/`` with the same part names the rig
already uses, so ``char_rig.load_rig`` can read it once it learns about the
``parts_side`` folder. Output is deterministic from the committed concept art,
so the PNGs are not checked in.

Run:  python3 tools/side_parts.py            (jackburton)
"""

from __future__ import annotations

import json
import os

from PIL import Image, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ART = os.path.join(ROOT, "concept_art", "fighters", "jack_burton",
                   "bernardo-mercurio-jack-turnable.jpg")
OUT = os.path.join(ROOT, "art_src", "chars", "jackburton", "parts_side")

# The profile figure is the right-hand figure of the third panel.
PANEL = 2
CROP = (280, 0, 640, 648)

# Boxes in the 360x648 profile crop. The drawn arm sits in front of the chest,
# so the torso keeps that overlap and only the pistol is cut out of it, at a box
# that starts to the right of the tank strap.
GUN = (172, 128, 268, 292)
KNIFE = (140, 178, 218, 282)  # kept for the unused-holster notes below
BOXES = {
    "head": (30, 12, 138, 130),
    "torso": (25, 112, 190, 312),
    "arm_n": (100, 118, 268, 278),
    "pelvis": (25, 272, 152, 402),
    "thigh_n": (30, 342, 142, 502),
    "shin_n": (22, 478, 178, 648),
    "prop_knife": (140, 178, 218, 282),
}

# Which joint each part hangs from, as a fraction of its own bounding box.
PIVOT = {
    "head": (0.42, 1.0),
    "torso": (0.46, 1.0),
    "pelvis": (0.50, 0.0),
    "arm_n": (0.08, 0.24),
    "thigh_n": (0.55, 0.0),
    "shin_n": (0.45, 0.0),
    "prop_knife": (0.55, 0.08),
}

# Scale that makes the cut parts the same length as the rig's skeleton
# segments, plus the profile skeleton: the near and far limbs share one line,
# so shoulder_half / hip_half are zero and the far limb hides behind the near.
SCALE = 0.86
# hip_y / knee_y / ankle_y are the ground-relative joints; the bone lengths are
# filled in from the cut art in build(), because they were typed in by hand and
# the torso bone (180) was longer than the scaled torso art (172). The rig hangs
# the head off shoulder + neck_len, so those 8 phantom pixels plus an 8px neck
# put a visible gap under Jack's chin.
METRICS = {
    "hip_y": -315, "knee_y": -171, "ankle_y": -35,
    "torso_len": 0.0, "neck_len": -10.0,
    "uarm": 86.7, "farm": 55.2, "hand": 34.0,
    "thigh": 140.5, "shin": 136.1,
    "shoulder_half": 0.0, "hip_half": 0.0,
}


def _mask(crop, bg, box, thr=18):
    p = crop.crop(box)
    px = p.load()
    w, h = p.size
    m = Image.new("L", (w, h), 0)
    mp = m.load()
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            d = max(abs(r - bg[0]), abs(g - bg[1]), abs(b - bg[2]))
            mp[x, y] = 0 if d < thr else (
                255 if d > thr + 16 else int((d - thr) / 16 * 255))
    return m


def _clean_edge(img, bg, floor=90):
    """Pull the studio background out of the matte edge.

    The knockout leaves a ramp of partially covered pixels, and each one still
    carries the colour of the white studio background. Pasted on a dark stage
    that ramp is a white halo around the head, the shoulders and the gun - the
    glow that made the rig look pasted off the internet. Un-mix the background
    out of every partially covered pixel, then drop what is left of the ramp.
    """
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if a < floor:
                px[x, y] = (0, 0, 0, 0)
                continue
            if a < 255:
                f = a / 255.0
                r = max(0, min(255, int((r - bg[0] * (1 - f)) / f)))
                g = max(0, min(255, int((g - bg[1] * (1 - f)) / f)))
                b = max(0, min(255, int((b - bg[2] * (1 - f)) / f)))
            px[x, y] = (r, g, b, a)
    return img


# NOTE: do not try to strip the pale rim off the silhouette here. The white
# tank top IS the silhouette along his chest and shoulder, so a rim strip that
# removes background-coloured edge pixels removes the vest with it - it ate the
# strap and left black bites out of the chest. Decontaminating the alpha ramp in
# _clean_edge is as far as this can safely go.


def _trim_collar(img):
    """Drop the tank top the head box clips in at the collar.

    The profile head box runs down past the jaw, so the white vest shoulder
    lands in its bottom-left corner. Pivoting the head with that patch on it
    pasted a second vest corner under his chin - the white blob he had instead
    of a throat. Only near-white pixels go, so the mullet at the back survives.
    """
    w, h = img.size
    px = img.load()
    for y in range(int(h * 0.70), h):
        for x in range(0, int(w * 0.58)):
            r, g, b, a = px[x, y]
            if a and min(r, g, b) > 172 and max(r, g, b) - min(r, g, b) < 34:
                px[x, y] = (0, 0, 0, 0)
    return img


def _build(crop, bg, box, subtract=()):
    m = _mask(crop, bg, box)
    for sbox in subtract:
        sm = _mask(crop, bg, sbox)
        canvas = Image.new("L", (box[2] - box[0], box[3] - box[1]), 0)
        canvas.paste(sm, (sbox[0] - box[0], sbox[1] - box[1]))
        m = ImageChops.subtract(m, canvas)
    bb = m.getbbox()
    m = m.crop(bb)
    col = crop.crop((box[0] + bb[0], box[1] + bb[1],
                     box[0] + bb[2], box[1] + bb[3])).convert("RGBA")
    col.putalpha(m)
    return _clean_edge(col, bg)


def _darken(im, factor):
    out = im.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            px[x, y] = (int(r * factor), int(g * factor), int(b * factor), a)
    return out


def build():
    sheet = Image.open(ART).convert("RGBA")
    w = sheet.width // 3
    panel = sheet.crop((PANEL * w, 0, (PANEL + 1) * w, sheet.height))
    crop = panel.crop(CROP)
    bg = crop.getpixel((2, 2))

    parts = {}
    for name, box in BOXES.items():
        subtract = (GUN,) if name == "torso" else ()
        parts[name] = _build(crop, bg, box, subtract)

    # NOTE: the pistol stays in his hand in this art, and cutting it out is not
    # a way to holster it - the hand is painted around the grip, so removing the
    # gun leaves a hole straight through the arm and the chest. Holstering him
    # needs source art of that hand empty (or a redrawn fist). Until then the
    # gun is drawn where the art has it.

    # The near arm already covers the far one, and the pistol is baked into it,
    # so both the far arm and the separate prop are empty on purpose.
    parts["arm_f"] = Image.new("RGBA", (2, 2), (0, 0, 0, 0))
    parts["prop"] = Image.new("RGBA", (2, 2), (0, 0, 0, 0))
    parts["thigh_f"] = _darken(parts["thigh_n"], 0.62)
    parts["shin_f"] = _darken(parts["shin_n"], 0.62)

    os.makedirs(OUT, exist_ok=True)
    # Delete parts this run did not produce. A stale PNG left behind is loaded by
    # the rig and drawn into every pose - that is how an abandoned holster ended
    # up hanging off his hip.
    for stale in os.listdir(OUT):
        if stale.endswith(".png") and stale[:-4] not in parts:
            os.remove(os.path.join(OUT, stale))
            print("  removed stale " + stale)
    for name, img in parts.items():
        img.save(os.path.join(OUT, name + ".png"))

    # Bone lengths come from the art that was just cut, scaled the same way the
    # rig scales it. Typed-in numbers only ever approximate this set.
    METRICS["torso_len"] = round(parts["torso"].height * SCALE, 1)
    METRICS["shoulder_y"] = round(METRICS["hip_y"] - METRICS["torso_len"], 1)
    METRICS["neck_y"] = round(METRICS["shoulder_y"] + METRICS["neck_len"], 1)

    pivots = {}
    for name, (fx, fy) in PIVOT.items():
        pw, ph = parts[name].size
        pivots[name] = [round(pw * fx, 1), round(ph * fy, 1)]
    pivots["arm_f"] = [1, 1]
    pivots["prop"] = [1, 1]
    _trim_collar(parts["head"]).save(os.path.join(OUT, "head.png"))
    for name in ("thigh_f", "shin_f"):
        pw, ph = parts[name].size
        px, py = PIVOT[name.replace("_f", "_n")]
        pivots[name] = [round(pw * px, 1), round(ph * py, 1)]

    cfg = {
        "scale": SCALE,
        "canvas": [640, 780],
        "axis": [300, 700],
        "metrics": METRICS,
        "pivots": pivots,
        "angles": {"head": 0.0, "torso": 0.0, "pelvis": 0.0,
                   "arm_f": 0.0, "arm_n": 0.0,
                   "thigh_f": 0.0, "shin_f": 0.0,
                   "thigh_n": 0.0, "shin_n": 0.0, "prop": 0.0,
                   "holster_gun": -28.0, "holster_knife": 172.0},
        "_note": ("Side set cut from the profile panel of the turnaround so the "
                  "fighters face each other. The drawn arm overlaps the torso "
                  "on purpose; only the pistol is masked out of the chest. Far "
                  "limbs sit exactly behind the near ones and are darkened."),
    }
    with open(os.path.join(OUT, "rig.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    print("wrote " + os.path.relpath(OUT, ROOT))
    for name, img in sorted(parts.items()):
        print(f"  {name:11s} {img.size[0]:>3d}x{img.size[1]:<3d} pivot {pivots.get(name)}")


if __name__ == "__main__":
    build()
