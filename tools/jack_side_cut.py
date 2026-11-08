"""Cut Jack's SIDE-VIEW part set from the hand-cut profile render.

``side_parts.py`` cuts the old side set from the third panel of the photographic
turnaround by knocking a studio background out of a JPEG. That art is gone: the
fighters are built from the new renders now, and the render that faces right
(``jack faceing right_cut.png``) arrives as RGBA with the alpha already painted,
so nothing has to be keyed - the cut is taken straight from the alpha channel.

Boxes and joints below are measured on this file in its own pixels (1021x1526
after the empty margin is trimmed), read off a 100px grid laid over the cut and
checked against the mask: the boot tops, the crotch, the arm's elbow and the
sole are all where the art puts them.
Every pivot is a joint of the drawn body, so the rig rotates the art around the
same point the artist drew it around.

The art is a three-quarter guard rather than a flat profile: both shoulders and
both hips are visible, so this set keeps a ``shoulder_half`` and a ``hip_half``
that the old profile set had to zero, and the near arm and near leg are cut on
their own side of the body instead of being hidden behind each other.

Run:  python3 tools/jack_side_cut.py
"""

from __future__ import annotations

import json
import math
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ART = os.path.join(ROOT, "concept_art", "fighters", "jack_burton",
                   "jack faceing right_cut.png")
OUT = os.path.join(ROOT, "art_src", "chars", "jackburton", "parts_side")

# Joints in the cut's own pixels, read off the grid over the cut. The ankles
# sit inside the boots near the heel, not at the boot tops: stated at the tops
# the ankle offset came out at -119 rig units and the bake could not lay out the
# shin sprite at all. The rig draws
# the near limb on the RIGHT of centre and the far one on the left, so "near"
# here is the figure's image-right leg. Assigning them the other way round drew
# each leg on its neighbour's hip, and the two crossed.
NECK = (566, 336)
SHOULDER_N = (716, 352)          # raised arm, image right, drawn right of centre
HIP_N = (620, 780)
KNEE_N = (806, 980)
ANKLE_N = (828, 1420)
HIP_F = (462, 780)
KNEE_F = (330, 1050)
ANKLE_F = (170, 1425)
SOLE = 1522
HIP_MID = (541, 780)

# A part box clips one limb out of the cut; the joint is where it hangs from.
# Boxes overlap on purpose - the tank sits under both arms, and the arm is
# drawn over the torso, which is how the old set handled the same overlap.
BOXES = {
    # stops under the chin: the tank strap starts around y=286 and a head part
    # that clips it pastes a vest shoulder under his jaw when the head turns
    "head": (420, 0, 690, 336),
    # the box reaches left past the chest so the far forearm, which is drawn
    # across the body in this guard, stays painted on the torso: cutting it out
    # would leave a forearm-shaped hole in the chest once the arm swings away
    "torso": (200, 240, 700, 800),
    "arm_n": (650, 290, 910, 600),
    "pelvis": (380, 730, 700, 880),
    # Leg boxes lap upwards past their joint. The two drawn legs are not the same
    # length (the stance is three-quarter, so the far one is foreshortened) and
    # the skeleton carries one thigh and one shin for both, so the piece that
    # ends short has to be covered by the piece below it, not left with a gap.
    "thigh_n": (540, 760, 860, 1010),
    "shin_n": (720, 960, 1015, 1526),
    "thigh_f": (250, 760, 560, 1080),
    "shin_f": (95, 1030, 400, 1526),
}

JOINTS = {
    "head": NECK,
    "torso": (HIP_MID[0], 780),
    "arm_n": SHOULDER_N,
    "pelvis": (555, 704),
    "thigh_n": HIP_N,
    "shin_n": KNEE_N,
    "thigh_f": HIP_F,
    "shin_f": KNEE_F,
}

# Rig units per art pixel. The old side set drew the figure about 550 rig units
# tall on a 640x780 canvas from a 648px crop; this art is 1485px tall, so the
# same size on screen needs about this much per pixel.
SCALE = 0.371


def _trim_white_collar(part):
    """Drop the tank top the head box clips in under the jaw.

    The head box runs down past the chin so the mullet and the throat survive.
    Near-white fabric in its bottom corner would pivot with the head and paste a
    second vest shoulder under the chin - the white blob the old set shipped.
    Only near-white, low-saturation pixels go, which leaves the hair alone.
    """
    px = part.load()
    w, h = part.size
    for y in range(int(h * 0.70), h):
        for x in range(0, int(w * 0.66)):
            r, g, b, a = px[x, y]
            if a and min(r, g, b) > 168 and max(r, g, b) - min(r, g, b) < 34:
                px[x, y] = (0, 0, 0, 0)
    return part


def _clean_alpha(img):
    """Drop alpha crumbs the hand cut left behind, then re-crop.

    A few isolated specks survive a hand mask, and a 1px speck 300px from the
    body stretches the part's bounding box - which moves its pivot off the
    joint. Anything under 40px of coverage goes.
    """
    a = img.getchannel("A").point(lambda v: 255 if v > 40 else 0)
    px, ap = img.load(), a.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            if ap[x, y] == 0:
                px[x, y] = (0, 0, 0, 0)
    bb = a.getbbox()
    return img.crop(bb) if bb else img


def _part(cut, name):
    box = BOXES[name]
    joint = JOINTS[name]
    raw = cut.crop(box)
    # The trim offset has to be measured BEFORE _clean_alpha crops the piece to
    # its own content. Reading the bbox afterwards always gives (0, 0, ...), so
    # every part whose content did not start at the box corner was pasted that
    # many pixels off its joint - an 8px bite out of the torso's back and a 12px
    # step on the far boot.
    bb = raw.getchannel("A").point(
        lambda v: 255 if v > 40 else 0).getbbox() or (0, 0, 1, 1)
    piece = _clean_alpha(raw)
    # pivot relative to the part, i.e. the joint in part-local pixels
    px = joint[0] - box[0] - bb[0]
    py = joint[1] - box[1] - bb[1]
    if name == "head":
        piece = _trim_white_collar(piece)
    return piece, (max(0, min(piece.width - 1, px)),
                   max(0, min(piece.height - 1, py)))


def _dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _ang(a, b):
    """Angle of a bone in the rig's convention: 0 is straight down, +x is +90.

    The rig rotates a limb by (pose angle - this), so stating the angle the art
    is DRAWN at makes the rest pose reproduce the cut exactly. Leaving it at
    zero rotated every leg by a whole stance on top of the pose: the knees swung
    out sideways and the boots hung away from the shins.
    """
    return round(math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])), 2)


def build():
    cut = Image.open(ART).convert("RGBA")
    bb = cut.getchannel("A").getbbox()
    if bb:
        cut = cut.crop(bb)

    parts, pivots = {}, {}
    for name in BOXES:
        parts[name], pivots[name] = _part(cut, name)

    # The new art has empty hands: no pistol and no knife are drawn into it, so
    # there is no prop to cut. Keep the knife sprite the old set produced - the
    # Knife Toss state still draws it - instead of leaving that action empty.
    for keep in ("prop_knife.png",):
        if os.path.isfile(os.path.join(OUT, keep)):
            parts["prop_knife"] = Image.open(os.path.join(OUT, keep)).convert("RGBA")
            pivots["prop_knife"] = [round(parts["prop_knife"].width * 0.55, 1),
                                    round(parts["prop_knife"].height * 0.08, 1)]
    # Only one arm is cut: the raised near arm. The far arm is drawn across the
    # chest and is part of the torso art, so the rig needs an empty placeholder
    # (load_rig requires the part to exist) rather than a second limb.
    parts["arm_f"] = Image.new("RGBA", (2, 2), (0, 0, 0, 0))
    pivots["arm_f"] = [1, 1]
    parts["prop"] = Image.new("RGBA", (2, 2), (0, 0, 0, 0))
    pivots["prop"] = [1, 1]

    metrics = {
        # pivot to the top of the piece: that is the torso bone. Taking the whole
        # piece height instead put the bone past the pivot once the box ran below
        # the hip line, and the rig's shoulder-line probe went off the top.
        "torso_len": round((JOINTS["torso"][1] - BOXES["torso"][1]) * SCALE, 1),
        "neck_len": 0.0,
        "uarm": round(_dist(SHOULDER_N, (800, 545)) * SCALE, 1),
        "farm": round(_dist((800, 545), (860, 340)) * SCALE, 1),
        "hand": 34.0,
        # The skeleton carries ONE thigh and ONE shin, and the near leg is the
        # one the rig actually animates in every pose, so its drawn lengths win:
        # the far leg is foreshortened by the three-quarter stance and its pieces
        # lap over the joints that the shared bones place for it.
        "thigh": round(_dist(HIP_N, KNEE_N) * SCALE, 1),
        "shin": round(_dist(KNEE_N, ANKLE_N) * SCALE, 1),
        "ankle_y": round(-(SOLE - ANKLE_N[1]) * SCALE, 1),
        # both hips and both shoulders are drawn, so the joints sit off centre
        # a distance: the sign would put the near leg on the far hip
        "hip_half": round(abs(HIP_N[0] - HIP_F[0]) * 0.5 * SCALE, 1),
        "shoulder_half": round((SHOULDER_N[0] - HIP_MID[0]) * SCALE, 1),
    }
    metrics["ankle_y"] = round(metrics["ankle_y"], 1)
    metrics["knee_y"] = round(metrics["ankle_y"] - metrics["shin"], 1)
    metrics["hip_y"] = round(metrics["knee_y"] - metrics["thigh"], 1)
    metrics["shoulder_y"] = round(metrics["hip_y"] - metrics["torso_len"], 1)
    metrics["neck_y"] = round(metrics["shoulder_y"] + metrics["neck_len"], 1)

    cfg = {
        "scale": SCALE,
        "canvas": [640, 780],
        "axis": [300, 700],
        "metrics": metrics,
        "pivots": {k: [round(v[0], 1), round(v[1], 1)] for k, v in pivots.items()},
        "angles": {"head": 0.0, "torso": 0.0, "pelvis": 0.0,
                   "arm_f": 0.0, "arm_n": 0.0,
                   # the bones as the art draws them, in rig units
                   "thigh_n": _ang(HIP_N, KNEE_N),
                   "shin_n": _ang(KNEE_N, ANKLE_N),
                   "thigh_f": _ang(HIP_F, KNEE_F),
                   "shin_f": _ang(KNEE_F, ANKLE_F),
                   "prop": 0.0,
                   "holster_gun": -28.0, "holster_knife": 172.0},
        "_note": ("Side set cut from jack faceing right_cut.png, the hand-cut "
                  "profile render. Both hips and shoulders are drawn, so the "
                  "joints carry a half-width. The art's hands are empty: no "
                  "pistol or knife is painted in, and the knife sprite kept "
                  "from the old set is only the thrown prop."),
    }

    os.makedirs(OUT, exist_ok=True)
    for stale in os.listdir(OUT):
        if stale.endswith(".png") and stale[:-4] not in parts:
            os.remove(os.path.join(OUT, stale))
            print("  removed stale " + stale)
    for name, img in parts.items():
        img.save(os.path.join(OUT, name + ".png"))
    with open(os.path.join(OUT, "rig.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")

    print("wrote " + os.path.relpath(OUT, ROOT))
    for name in sorted(parts):
        w, h = parts[name].size
        print(f"  {name:11s} {w:>3d}x{h:<4d} pivot {cfg['pivots'][name]}")
    print("metrics " + json.dumps(metrics))


if __name__ == "__main__":
    build()
