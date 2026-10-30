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
METRICS = {
    "hip_y": -315, "shoulder_y": -495.0, "neck_y": -503.0,
    "knee_y": -171, "ankle_y": -35,
    "torso_len": 180.0, "neck_len": 8.0,
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
    return col


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

    # The near arm already covers the far one, and the pistol is baked into it,
    # so both the far arm and the separate prop are empty on purpose.
    parts["arm_f"] = Image.new("RGBA", (2, 2), (0, 0, 0, 0))
    parts["prop"] = Image.new("RGBA", (2, 2), (0, 0, 0, 0))
    parts["thigh_f"] = _darken(parts["thigh_n"], 0.62)
    parts["shin_f"] = _darken(parts["shin_n"], 0.62)

    os.makedirs(OUT, exist_ok=True)
    for name, img in parts.items():
        img.save(os.path.join(OUT, name + ".png"))

    pivots = {}
    for name, (fx, fy) in PIVOT.items():
        pw, ph = parts[name].size
        pivots[name] = [round(pw * fx, 1), round(ph * fy, 1)]
    pivots["arm_f"] = [1, 1]
    pivots["prop"] = [1, 1]
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
                   "thigh_n": 0.0, "shin_n": 0.0, "prop": 0.0},
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
