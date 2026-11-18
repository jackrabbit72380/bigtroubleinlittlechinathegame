"""Cut Lightning's concept render into the parts ``char_rig`` hangs on its joints.

He is the one fighter whose art is a photograph of a person rather than a
painting, so he cannot be painted with the shared ``*_art.py`` helpers: the
cuirass is quilted, the hat is woven and the cloak is velvet, and every attempt
to flatten that into flat shapes read as a different costume.  What does work is
to lift his own pixels into the rig.

How the cut works
-----------------
The earlier version of this tool laid a capsule over each guessed limb and
pasted whatever landed inside it.  That fails on a photograph: the capsule is
only as good as the guess, sleeves and baggy trousers stick out of it, and the
pieces end up the wrong size and length, so the arm hangs two hands' worth below
its own shoulder and the hand floats free of the wrist.

Instead the joints are decided first and every opaque pixel is then given to the
bone it is nearest to.  The pieces therefore TILE the figure: nothing is lost at
a seam, nothing overlaps by accident, and a piece can only ever be as large as
its own bone reaches - the shoulder cut lands halfway between the shoulder and
the elbow, exactly where a sleeve changes, and both pieces include the joint.
A limb cannot be cut too long, because its length is the bone it was given.

The joints come from the render, measured once below (``JOINTS``).  The bones
come from ``char_rig``'s own skeleton, built here with the same formulas the
renderer uses, so the pivots and the metrics agree with it by construction and
the rest pose reproduces the drawing - ``char_rig.py --rest lightning`` is the
check.

The cloak is not cut by distance: it hangs behind the shoulders across the legs,
so every bone would claim a piece of it.  It is lifted out first by its colour
(crimson is the one hue nothing else on him has) and becomes one piece hinged at
the shoulders.

Run:  python3 tools/lightning_cut.py
"""

import json
import math
import os

from PIL import Image

try:
    import numpy as np
except ImportError:  # pragma: no cover - the art tools all need numpy
    raise SystemExit("needs numpy")

try:
    from scipy import ndimage
except ImportError:  # pragma: no cover
    ndimage = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "concept_art", "fighters", "lightning",
                   "lighting faceing right.png")
OUT = os.path.join(ROOT, "art_src", "chars", "lightning", "parts")

# He stands 371 units from the sole of the boot to the top of the hat in the
# game (bake_char fits the drawn figure to the same height), and the render is
# that same figure a few times larger.
TARGET_HEIGHT = 371.0

# Joints in render pixels, read off the drawing: hip, knee, ankle and toe for
# each leg, shoulder, elbow, wrist and fingertips for each arm, the neck, and
# the top of the hat.  "n" is the limb nearer the camera.
JOINTS = dict(
    hip_mid=(610, 800),
    hip_n=(700, 800), hip_f=(520, 800),
    knee_n=(780, 1030), knee_f=(420, 1030),
    ankle_n=(870, 1265), ankle_f=(300, 1265),
    toe_n=(1080, 1350), toe_f=(210, 1350),
    sh_n=(700, 330), sh_f=(575, 345),
    elbow_n=(800, 500), elbow_f=(480, 505),
    wrist_n=(930, 395), wrist_f=(400, 585),
    tip_n=(975, 300), tip_f=(375, 610),
    neck=(575, 315), head_top=(560, 150),
    # The brim is 580 pixels wide and the neck it hangs on is 160: measured from
    # the neck alone its two ends are nearer the shoulders and the raised hand,
    # so the hat was being sliced into three fighters' parts.  A second bone
    # across the brim keeps the whole hat on the head, where it belongs.
    hat_l=(275, 150), hat_r=(835, 150),
)

# Where the figure sits in the part canvas.  bake_char re-fits the finished
# sprite, so this only has to leave room round him.
CANVAS = (400, 420)
AXIS = (200, 380)


def _load():
    img = Image.open(ART).convert("RGBA")
    a = np.asarray(img.getchannel("A")).astype(np.float32) / 255.0
    bbox = Image.fromarray((a * 255).astype(np.uint8)).getbbox()
    return img, a, bbox


def _scale(bbox):
    """Render pixels -> rig units: one factor, so his proportions are the photo's.

    The canvas, the parts and the metrics are one unit system: an upper arm cut
    62 units long hangs on a 62-unit bone.  Scaling by the figure's own height
    keeps his in-game height identical to every other fighter's.
    """
    return TARGET_HEIGHT / float(bbox[3] - bbox[1])


def _angle(a, b):
    """Direction of a joint pair in rig degrees: 0 hangs straight down.

    ``char_rig._seg`` walks a bone as ``(x + sin a, y + cos a)``, so the
    direction from one joint to the next is ``atan2(dx, dy)`` with y running
    down the image.  This is the number the rig states as a part's drawn angle.
    """
    return math.degrees(math.atan2(b[0] - a[0], b[1] - a[1]))


def _length(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _skeleton(S, bbox):
    """The rig's joints, built with ``char_rig``'s own formulas.

    ``render`` puts the hip on the canvas axis, the shoulder ``torso_len``
    straight up from it, the neck ``neck_len`` above that, the shoulders
    ``shoulder_half`` either side of the torso (the far one 0.92 as far out, a
    three-quarter concession), and walks each limb from those joints at the
    drawn angle.  Doing the same arithmetic here means the cut is made on the
    joints the renderer will actually use - which is the only way the pieces can
    meet in the rest pose and stay met in a pose.
    """
    J = {k: (v[0] * S, v[1] * S) for k, v in JOINTS.items()}
    hat_l, hat_r = J["hat_l"], J["hat_r"]
    # The hip's height is solved from the legs (both boots on the floor); with
    # the drawn leg angles the ankle sits exactly one leg-drop below it.
    drops = []
    for side in ("n", "f"):
        drops.append(J["knee_" + side][1] - J["hip_" + side][1]
                     + J["ankle_" + side][1] - J["knee_" + side][1])
    hip_y = -max(drops)
    axis = AXIS
    hip = (axis[0], axis[1] + hip_y)
    # Translate the drawing so its hip lands on the canvas hip.
    ox = hip[0] - J["hip_mid"][0]
    oy = hip[1] - J["hip_mid"][1]
    J = {k: (v[0] + ox, v[1] + oy) for k, v in J.items()}

    shoulder_half = J["sh_n"][0] - hip[0]
    torso_len = hip[1] - J["sh_n"][1]
    shoulder = (hip[0], hip[1] - torso_len)
    neck_len = shoulder[1] - J["neck"][1]
    neck = (shoulder[0], shoulder[1] - neck_len)
    sh_n = (shoulder[0] + shoulder_half, shoulder[1])
    sh_f = (shoulder[0] - shoulder_half * 0.92, shoulder[1])
    hip_half = J["hip_n"][0] - hip[0]
    hip_n = (hip[0] + hip_half, hip[1])
    hip_f = (hip[0] - hip_half, hip[1])

    a_thigh_n = _angle(J["hip_n"], J["knee_n"])
    a_shin_n = _angle(J["knee_n"], J["ankle_n"])
    a_thigh_f = _angle(J["hip_f"], J["knee_f"])
    a_shin_f = _angle(J["knee_f"], J["ankle_f"])
    thigh_n = _length(J["hip_n"], J["knee_n"])
    shin_n = _length(J["knee_n"], J["ankle_n"])
    thigh_f = _length(J["hip_f"], J["knee_f"])
    shin_f = _length(J["knee_f"], J["ankle_f"])
    a_uarm_n = _angle(J["sh_n"], J["elbow_n"])
    a_farm_n = _angle(J["elbow_n"], J["wrist_n"])
    a_hand_n = _angle(J["wrist_n"], J["tip_n"])
    a_uarm_f = _angle(J["sh_f"], J["elbow_f"])
    a_farm_f = _angle(J["elbow_f"], J["wrist_f"])
    a_hand_f = _angle(J["wrist_f"], J["tip_f"])
    uarm = (_length(J["sh_n"], J["elbow_n"]) + _length(J["sh_f"], J["elbow_f"])) / 2
    farm = (_length(J["elbow_n"], J["wrist_n"]) + _length(J["elbow_f"], J["wrist_f"])) / 2
    hand = (_length(J["wrist_n"], J["tip_n"]) + _length(J["wrist_f"], J["tip_f"])) / 2

    def seg(o, a, n):
        r = math.radians(a)
        return (o[0] + math.sin(r) * n, o[1] + math.cos(r) * n)

    elb_n, elb_f = seg(sh_n, a_uarm_n, uarm), seg(sh_f, a_uarm_f, uarm)
    wri_n, wri_f = seg(elb_n, a_farm_n, farm), seg(elb_f, a_farm_f, farm)
    tip_n, tip_f = seg(wri_n, a_hand_n, hand), seg(wri_f, a_hand_f, hand)
    kn_n, kn_f = seg(hip_n, a_thigh_n, thigh_n), seg(hip_f, a_thigh_f, thigh_f)
    ank_n = seg(kn_n, a_shin_n, shin_n)
    ank_f = seg(kn_f, a_shin_f, shin_f)
    toe_len = _length(J["ankle_n"], J["toe_n"])
    toe_n = (ank_n[0] + toe_len, ank_n[1])
    toe_f = (ank_f[0] + toe_len, ank_f[1])
    head_len = max(40.0, neck[1] - J["head_top"][1])

    bones = {
        "torso": (hip, shoulder),
        "head": [(neck, (neck[0], neck[1] - head_len)),
                 ((hat_l[0], hat_l[1]), (hat_r[0], hat_r[1]))],
        "pelvis": (hip_f, hip_n),
        "uarm_n": (sh_n, elb_n), "farm_n": (elb_n, wri_n), "hand_n": (wri_n, tip_n),
        "uarm_f": (sh_f, elb_f), "farm_f": (elb_f, wri_f), "hand_f": (wri_f, tip_f),
        "thigh_n": (hip_n, kn_n), "shin_n": (kn_n, ank_n), "foot_n": (ank_n, toe_n),
        "thigh_f": (hip_f, kn_f), "shin_f": (kn_f, ank_f), "foot_f": (ank_f, toe_f),
    }
    anchors = {
        "cape": shoulder, "pelvis": hip, "torso": hip, "head": neck,
        "uarm_n": sh_n, "farm_n": elb_n, "hand_n": wri_n,
        "uarm_f": sh_f, "farm_f": elb_f, "hand_f": wri_f,
        "thigh_n": hip_n, "shin_n": kn_n, "foot_n": ank_n,
        "thigh_f": hip_f, "shin_f": kn_f, "foot_f": ank_f,
    }
    angles = {
        "torso": 0.0, "head": 0.0, "pelvis": 0.0,
        "uarm_n": a_uarm_n, "farm_n": a_farm_n, "hand_n": a_hand_n,
        "uarm_f": a_uarm_f, "farm_f": a_farm_f, "hand_f": a_hand_f,
        "thigh_n": a_thigh_n, "shin_n": a_shin_n, "foot_n": 0.0,
        "thigh_f": a_thigh_f, "shin_f": a_shin_f, "foot_f": 0.0,
    }
    metrics = dict(
        hip_y=round(hip_y, 1), ankle_y=0.0,
        knee_y=round(hip_y + thigh_n * math.cos(math.radians(a_thigh_n)), 1),
        shoulder_y=round(hip_y - torso_len, 1),
        neck_y=round(hip_y - torso_len - neck_len, 1),
        head_y=round(hip_y - torso_len - neck_len - head_len, 1),
        shoulder_half=round(shoulder_half, 1), hip_half=round(hip_half, 1),
        torso_len=round(torso_len, 1), neck_len=round(neck_len, 1),
        uarm=round(uarm, 1), farm=round(farm, 1), hand=round(hand, 1),
        thigh=round(thigh_n, 1), shin=round(shin_n, 1),
        thigh_f=round(thigh_f, 1), shin_f=round(shin_f, 1),
    )
    return bones, anchors, angles, metrics, (ox, oy)


def _cape_mask(rgb, alpha):
    """The cloak, by the one colour nothing else on him wears.

    Crimson only: the brass lion is far redder in green than this rule allows
    and the black robe has no red bias at all, so both stay with the body.
    """
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    # The boots are brown leather: redder than the armour, but nowhere near the
    # cloak's crimson.  Asking for a strong red bias AND a wide red-over-green
    # gap keeps them out, or both boots become cloak and walk off with the hem.
    m = (alpha > 0.25) & (r > 70) & (r > 1.7 * g) & (r > 1.3 * b) & (r - g > 45)
    if ndimage is not None:
        m = ndimage.binary_closing(m, np.ones((7, 7)))
        lab, n = ndimage.label(m)
        if n:
            sizes = ndimage.sum(m, lab, range(1, n + 1))
            keep = [i + 1 for i, s in enumerate(sizes) if s > 1500]
            m = np.isin(lab, keep) if keep else m
    return m


def _dist_to_seg(px, py, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 < 1e-6:
        return np.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / L2
    t = np.clip(t, 0.0, 1.0)
    return np.hypot(px - (ax + t * dx), py - (ay + t * dy))


# A bone's reach is multiplied by its weight, so a weight BELOW one lets a short
# bone hold cloth that hangs further off it than the next bone along does.  The
# head needs it: the brim is 580 pixels wide on a 165-pixel neck, and at an even
# weight each end of the hat is nearer the shoulder or the raised hand.
WEIGHT = {"head": 0.42, "torso": 0.9, "pelvis": 0.9}


def _partition(img, alpha, bones, S, origin):
    """Give every opaque pixel to the nearest bone, so the pieces tile him."""
    W, H = img.size
    # the bones are in rig units; ask where each render pixel sits in those
    px, py = np.meshgrid((np.arange(W, dtype=np.float32) + 0.5) * S + origin[0],
                         (np.arange(H, dtype=np.float32) + 0.5) * S + origin[1])
    cape = _cape_mask(np.asarray(img.convert("RGB")).astype(np.float32), alpha)
    body = (alpha > 0.25) & ~cape
    best = np.full((H, W), 1e9, dtype=np.float32)
    label = np.full((H, W), "", dtype=object)
    for name, segs in bones.items():
        if len(segs) == 2 and all(isinstance(v, (int, float)) for v in segs[0]):
            segs = [segs]
        d = None
        for a, b in segs:
            dd = _dist_to_seg(px, py, a, b)
            d = dd if d is None else np.minimum(d, dd)
        d = d * WEIGHT.get(name, 1.0)
        d = np.where(body, d, 1e9)
        take = d < best
        best = np.where(take, d, best)
        label = np.where(take, name, label)
    # One piece per bone, no island surgery: ``char_rig`` bridges separate
    # islands inside a part with a painted line, which on this art drew a long
    # red bar across the cuirass, so the rig is told not to (``join_off``).
    pieces = {}
    for name in list(bones) + ["cape"]:
        m = cape if name == "cape" else label == name
        if m.any():
            pieces[name] = m
    return pieces, cape


def _part(img, mask, pivot, S):
    """Crop one piece out at the figure's scale and put its pivot on the joint."""
    ys, xs = np.where(mask)
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    crop = img.crop((x0, y0, x1, y1))
    sub = mask[y0:y1, x0:x1]
    a = np.asarray(crop.getchannel("A")).astype(np.float32) / 255.0
    a = a * sub.astype(np.float32)
    crop.putalpha(Image.fromarray((a * 255.0 + 0.5).astype(np.uint8)))
    w = max(1, int(round(crop.width * S)))
    h = max(1, int(round(crop.height * S)))
    # RGBA resize in premultiplied space, or every edge fringe goes dark
    crop = crop.convert("RGBa").resize((w, h), Image.LANCZOS).convert("RGBA")
    return crop, ((pivot[0] - x0) * S, (pivot[1] - y0) * S)


def build():
    img, alpha, bbox = _load()
    S = _scale(bbox)
    bones, anchors, angles, metrics, origin = _skeleton(S, bbox)
    pieces, cape = _partition(img, alpha, bones, S, origin)

    os.makedirs(OUT, exist_ok=True)
    # A part set is whatever is in the folder, and the rig draws a one-piece
    # arm (arm_n) in place of the three segments whenever the file is there.
    # The previous painted pass left those files behind, so the cut arms were
    # silently ignored and a smudge of the old sleeve sat over the new one.
    for old in os.listdir(OUT):
        if old.endswith(".png") and old[:-4] not in pieces:
            os.remove(os.path.join(OUT, old))
            print("  dropped stale part %s" % old)
    written = {}
    to_px = lambda p: ((p[0] - origin[0]) / S, (p[1] - origin[1]) / S)
    for name, mask in pieces.items():
        part, pivot = _part(img, mask, to_px(anchors[name]), S)
        part.save(os.path.join(OUT, name + ".png"))
        written[name] = [round(pivot[0], 1), round(pivot[1], 1)]
        print("  %-8s %3dx%-3d pivot %s" % (name, part.width, part.height,
                                            written[name]))
    cfg = dict(
        pivots=written,
        # The pieces already tile him, so there is no hole at a joint for a weld
        # to fill.  Left on, the rig paints a capsule of the limb's own colour
        # from the socket into the chest - on this photo that came out as a red
        # bar across the cuirass and a black slab over his belly.
        welds_off=sorted(written),
        join_off=sorted(written),
        contact_off=sorted(written),
        angles={k: round(v, 2) for k, v in angles.items()},
        metrics=metrics,
        canvas=list(CANVAS),
        axis=list(AXIS),
    )
    with open(os.path.join(OUT, "rig.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    print("wrote %d parts and rig.json (scale %.4f)" % (len(written), S))


if __name__ == "__main__":
    build()
