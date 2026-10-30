"""A 2D puppet rig: poses painted body parts instead of drawing a body.

The roster's fighters are 106px tall, drawn from Kung Fu Man. To reach HD they
have to be drawn at 3x (~318px) *and* look painted. Drawing 250 frames by hand
per fighter is not happening, and a 3D model is out of scope, so this uses the
technique 2D fighters actually ship with: the body is authored **once**, cut into
parts (head, torso, upper/lower arm, hand, thigh, shin, foot, props), and every
animation frame is those parts rotated about their joints.

That means the quality of a fighter is the quality of the painted parts. This
tool never invents anatomy - it only articulates art you put in
``art_src/chars/<id>/parts/``.

    art_src/chars/jackburton/parts/
        torso.png          92px tall, drawn upward from the hip
        head.png           42px, drawn upward from the neck
        uarm_n.png  ...    limbs drawn vertically, hanging DOWN from the pivot
        foot_n.png         drawn pointing RIGHT (+x), flat on the ground
        prop_gun.png       drawn pointing right, pivot at the grip
        rig.json           optional pivot/metric overrides

Part convention: each PNG is the part at rest, and its pivot is the point that
sits on the joint. ``rig.json`` may override any pivot; without it the pivot is
the top-centre for limbs, bottom-centre for the torso, and the bottom-centre of
the left edge for the foot.

Run:
    python3 tools/char_rig.py --demo          # stand-in parts, pose sheet
    python3 tools/char_rig.py --sheet jackburton
    python3 tools/char_rig.py --template jackburton
"""

from __future__ import annotations

import json
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS_DIR = os.path.join(ROOT, "art_src", "chars")
OUT_DIR = os.path.join(ROOT, "artifacts")

# --------------------------------------------------------------------- metrics
# Body-space pixels at 3x, feet on y=0, up is negative y. A 106px fighter
# scaled 3x is 318px; these are the joints that match that height.
METRICS = dict(
    ankle_y=-14.0,
    knee_y=-91.0,
    hip_y=-165.0,
    shoulder_y=-257.0,
    neck_y=-275.0,
    head_y=-317.0,
    shoulder_half=48.0,
    hip_half=20.0,
    torso_len=92.0,       # hip -> shoulder
    neck_len=18.0,        # shoulder -> neck
    uarm=62.0,
    farm=52.0,
    hand=30.0,
    thigh=74.0,
    shin=77.0,
)
M = METRICS

# Part pixels, canvas pixels and the metrics below are ONE unit system: an
# author draws a 62px upper arm and the skeleton's upper arm is 62 units. The
# art is already at 3x, so there is nothing to supersample.
CANVAS = (360, 400)
AXIS = (180, 372)         # ground contact point inside the canvas
SUPERSAMPLE = 1

# Draw order, back to front. Far limbs sit behind the torso, near ones in front.
ORDER = ["cape", "thigh_f", "shin_f", "foot_f", "arm_f",
         "uarm_f", "farm_f", "hand_f",
         "pelvis", "torso", "head",
         "thigh_n", "shin_n", "foot_n", "arm_n",
         "uarm_n", "farm_n", "hand_n", "prop"]

# Parts whose art is not drawn hanging straight down.
BASE_ANGLE = {"foot_f": 90.0, "foot_n": 90.0, "prop": 90.0}

# The arms are cut as ONE bent piece each, in the guard the concept art draws.
# A bent arm rotated from an absolute angle swings its forearm across the
# chest, so arm angles in POSES are offsets from that drawn guard (0 = as
# drawn). Everything else is absolute.
RELATIVE = ("arm_n", "arm_f")

# Parts that get a joint socket disc. A one-piece arm is deliberately not
# here: its shoulder is already covered by the torso's own shoulder cap and
# the disc sat on top of that as a grey ball, which made the fighters read as
# mannequins with ball joints.
SOCKETED = ("uarm_", "farm_", "hand_", "thigh_", "shin_", "foot_")

LIMB_LEN = {
    "uarm_n": M["uarm"], "uarm_f": M["uarm"],
    "farm_n": M["farm"], "farm_f": M["farm"],
    "hand_n": M["hand"], "hand_f": M["hand"],
    "thigh_n": M["thigh"], "thigh_f": M["thigh"],
    "shin_n": M["shin"], "shin_f": M["shin"],
    "foot_n": 40.0, "foot_f": 40.0,
    "torso": M["torso_len"], "head": M["head_y"] - M["neck_y"],
    "pelvis": 34.0, "prop": 40.0,
}


# ------------------------------------------------------------------- painting
def _profile_shape(size, profile):
    """Rasterise a vertical taper: profile = [(t, halfwidth), ...], t in 0..1."""
    w, h = size
    mask = Image.new("L", size, 0)
    d = ImageDraw.Draw(mask)
    rows = []
    for i in range(h):
        t = i / max(1, h - 1)
        hw = _interp(profile, t)
        rows.append(hw * w * 0.5)
    for i in range(h):
        hw = rows[i]
        d.line([(w * 0.5 - hw, i), (w * 0.5 + hw, i)], fill=255)
    # round the caps so joints look like flesh, not cut paper
    for idx, sign in ((0, 1), (h - 1, -1)):
        hw = rows[idx]
        r = hw
        d.ellipse([w * 0.5 - hw, idx - r, w * 0.5 + hw, idx + r], fill=255)
    return mask


def _interp(profile, t):
    if t <= profile[0][0]:
        return profile[0][1]
    for i in range(len(profile) - 1):
        t0, v0 = profile[i]
        t1, v1 = profile[i + 1]
        if t0 <= t <= t1:
            f = (t - t0) / max(1e-6, t1 - t0)
            return v0 + (v1 - v0) * f
    return profile[-1][1]


def _shade(mask, base, lit, dark, light_from=0.12):
    """Colour a mask with a left-to-right light and a soft rim."""
    w, h = mask.size
    ramp = Image.linear_gradient("L").resize((w, h), Image.BILINEAR)
    ramp = ramp.point(lambda v: 255 - v)              # bright at the left
    lit_img = Image.new("RGBA", (w, h), lit + (255,))
    dark_img = Image.new("RGBA", (w, h), dark + (255,))
    body = Image.composite(lit_img, dark_img, ramp)
    base_img = Image.new("RGBA", (w, h), base + (255,))
    body = Image.blend(base_img, body, 0.85)
    # rim light on the lit edge, matching the soft studio look of the refs
    edge = ImageChops.subtract(mask, mask.filter(ImageFilter.MinFilter(5)))
    rim = Image.new("RGBA", (w, h), lit + (0,))
    rim.putalpha(edge.point(lambda v: min(255, int(v * 0.5))))
    body = Image.alpha_composite(body, rim)
    # dark contour so the part reads against a busy stage
    ink = ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(3)), mask)
    line = Image.new("RGBA", (w, h), (24, 16, 12, 0))
    line.putalpha(ink.point(lambda v: min(190, v)))
    body = Image.alpha_composite(line, body)
    # Mask the result back down to the shape. Every composite above produces
    # an opaque image, so without this the part (and every joint socket drawn
    # from it) is a solid rectangle of its bounding box.
    body.putalpha(ImageChops.lighter(mask, ink))
    _ = light_from
    return body


# ----------------------------------------------------------------- load/rig
class Rig:
    def __init__(self, parts, metrics=None, art_angles=None, canvas=None, axis=None):
        self.metrics = dict(METRICS)
        if metrics:
            self.metrics.update(metrics)
        self.parts = parts            # name -> dict(image=, pivot=)
        # Art authored at a different scale than the default canvas needs its
        # own canvas/ground point; rig.json carries them.
        self.canvas = tuple(canvas) if canvas else CANVAS
        self.axis = tuple(axis) if axis else AXIS
        # art_angles: the angle each part is DRAWN at in the source art. A
        # figure cut from an A-pose has upper arms at ~45 deg, not hanging
        # down, and without this the whole arm would be 45 deg out in every
        # pose. Values use the same convention as POSES.
        self.art = dict(art_angles or {})

    @property
    def m(self):
        return self.metrics


def load_rig(char_id):
    folder = os.path.join(PARTS_DIR, char_id, "parts")
    if not os.path.isdir(folder):
        raise SystemExit(f"no parts at {os.path.relpath(folder, ROOT)}")
    cfg = {}
    cfg_path = os.path.join(folder, "rig.json")
    if os.path.isfile(cfg_path):
        with open(cfg_path, encoding="utf-8") as f:
            cfg = json.load(f)

    parts = {}
    default_pivots = cfg.get("pivots", {})
    for name in ORDER:
        path = os.path.join(folder, f"{name}.png")
        if not os.path.isfile(path):
            continue
        img = Image.open(path).convert("RGBA")
        s = float(cfg.get("scale", 1.0))
        if s != 1.0:
            img = img.resize((max(1, round(img.width * s)),
                              max(1, round(img.height * s))), Image.LANCZOS)
        if name in default_pivots:
            px, py = default_pivots[name]
        elif name == "torso" or name == "head" or name == "pelvis":
            px, py = img.width * 0.5, img.height
        else:
            px, py = img.width * 0.5, 0.0
        parts[name] = dict(image=img, pivot=(px * s, py * s))
    # A rig may supply one piece per arm (arm_n / arm_f) instead of the three
    # segments, so only complain about a segment when its single piece is absent.
    missing = []
    for n in ORDER:
        if n in ("prop", "cape") or n in parts:
            continue
        if n.startswith(("uarm_", "farm_", "hand_")) and ("arm_" + n[-1]) in parts:
            continue
        if n.startswith("foot_"):
            continue
        missing.append(n)
    if missing:
        raise SystemExit(f"{char_id}: missing parts: {', '.join(missing)}")
    return Rig(parts, cfg.get("metrics"), cfg.get("angles"),
               cfg.get("canvas"), cfg.get("axis"))


def _place(dst, part, angle_deg, joint):
    """Rotate a part about its pivot and paste the pivot onto ``joint``."""
    img = part["image"]
    px, py = part["pivot"]
    base = part.get("base", 0.0)
    # Positive angles swing the limb toward the enemy (+x in the skeleton's
    # seg()), and a downward-hanging part rotated toward +x turns CLOCKWISE on
    # screen, which is rotate() with a negative angle. This had the sign the
    # other way, so every limb left its joint in the opposite direction: a
    # 26-degree thigh put the art's knee at x=287 while the skeleton's knee was
    # at 362, and the boot hung 70px away from the leg it belonged to.
    rot = angle_deg - base
    if abs(rot) > 0.01:
        out = img.rotate(rot, resample=Image.BICUBIC, expand=True)
        cx, cy = img.width * 0.5, img.height * 0.5
        dx, dy = px - cx, py - cy
        th = math.radians(rot)
        # PIL rotates the CONTENT counter-clockwise, so a point of the image
        # moves by the inverse of the rotation matrix written the usual way.
        # With the forward matrix here the pivot orbited the image centre: a
        # 10-degree joint slid the part 25px off its socket and a 30-degree one
        # threw it 72px away, which is why every posed limb looked detached
        # while the rest pose (0 degrees, no rotation) was perfect.
        rx = dx * math.cos(th) + dy * math.sin(th)
        ry = -dx * math.sin(th) + dy * math.cos(th)
        opx, opy = out.width * 0.5 + rx, out.height * 0.5 + ry
        geo = (out, opx, opy)
    else:
        geo = (img, px, py)
    src, opx, opy = geo
    dst.alpha_composite(src, (round(joint[0] - opx), round(joint[1] - opy)))


def _avg_rgb(img):
    small = img.convert("RGBA").resize((10, 10), Image.BOX)
    px = list(small.getdata())
    tot = [0, 0, 0]
    n = 0
    for r, g, b, a in px:
        if a > 120:
            tot[0] += r
            tot[1] += g
            tot[2] += b
            n += 1
    if not n:
        return (200, 160, 130)
    return tuple(v // n for v in tot)


def _socket(dst, part, joint, scale=0.11):
    """A colour-matched disc at a limb's own socket.

    Rotated parts leave a visible gap or a hard step at the joint; a disc
    sampled from the part itself reads as the joint and closes the seam. This
    is the difference between a paper doll and an articulated figure.
    """
    img = part["image"]
    # Thickness, not length: a bent arm's part is as wide as it is long, and
    # sizing the disc from that painted a dinner-plate over the chest.
    r = max(4, min(12, int(min(img.width, img.height) * scale)))
    col = _avg_rgb(img)
    lit = tuple(min(255, c + 30) for c in col)
    dark = tuple(int(c * 0.70) for c in col)
    mask = Image.new("L", (r * 2, r * 2), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, r * 2 - 1, r * 2 - 1], fill=255)
    dst.alpha_composite(_shade(mask, col, lit, dark),
                        (int(joint[0] - r), int(joint[1] - r)))


def _seg(origin, angle_deg, length):
    a = math.radians(angle_deg)
    return (origin[0] + math.sin(a) * length, origin[1] + math.cos(a) * length)


def _seg_up(origin, angle_deg, length):
    a = math.radians(angle_deg)
    return (origin[0] + math.sin(a) * length, origin[1] - math.cos(a) * length)


def rest_pose(rig):
    """Every part at the angle it was DRAWN at, i.e. zero rotation.

    Compositing this has to reproduce the source art exactly. If it does not,
    the pivots or the skeleton are wrong and no animated pose can be trusted -
    this is the check that catches joint errors before poses hide them.
    """
    a = rig.art
    return dict(
        lean=0.0, head=0.0, lift=0.0, shift=0.0,
        arm_n=(0.0, 0.0, 0.0),
        arm_f=(0.0, 0.0, 0.0),
        leg_n=(a.get("thigh_n", 0.0), a.get("shin_n", 0.0), 90.0),
        leg_f=(a.get("thigh_f", 0.0), a.get("shin_f", 0.0), 90.0),
    )


def render(rig, pose, canvas=None, axis=None, ss=SUPERSAMPLE):
    """Render one pose to an RGBA canvas."""
    canvas = canvas or rig.canvas
    axis = axis or rig.axis
    m = rig.m
    W, H = canvas[0] * ss, canvas[1] * ss

    lean = pose.get("lean", 0.0)
    head_a = pose.get("head", 0.0)
    lift = pose.get("lift", 0.0)
    if pose.get("ground", True):
        # Solve the hip height from whichever leg is planted, so a crouch,
        # lunge or kick never sinks into the floor or floats above it.
        spans = []
        for key in ("leg_n", "leg_f"):
            angles = pose.get(key, (0, 0, 88))
            a1 = math.radians(angles[0])
            a2 = math.radians(angles[1])
            spans.append(m["thigh"] * math.cos(a1) + m["shin"] * math.cos(a2))
        span = max(spans)
        lift = (m["ankle_y"] - m["hip_y"]) - span
    shift = pose.get("shift", 0.0)

    hip = (axis[0] * ss + shift * ss, (axis[1] + m["hip_y"] + lift) * ss)
    torso_dir = lean
    shoulder = _seg_up(hip, torso_dir, m["torso_len"] * ss)
    neck = _seg_up(shoulder, torso_dir * 0.7, m["neck_len"] * ss)

    # shoulders ride the torso's perpendicular
    pa = math.radians(torso_dir)
    perp = (math.cos(pa), math.sin(pa))
    sh_n = (shoulder[0] + perp[0] * m["shoulder_half"] * ss,
            shoulder[1] + perp[1] * m["shoulder_half"] * ss)
    sh_f = (shoulder[0] - perp[0] * m["shoulder_half"] * ss * 0.92,
            shoulder[1] - perp[1] * m["shoulder_half"] * ss * 0.92)
    hip_n = (hip[0] + m["hip_half"] * ss, hip[1])
    hip_f = (hip[0] - m["hip_half"] * ss, hip[1])

    arm_n = pose.get("arm_n", (0, 0, 0))
    arm_f = pose.get("arm_f", (0, 0, 0))
    leg_n = pose.get("leg_n", (0, 0, 88))
    leg_f = pose.get("leg_f", (0, 0, 88))

    def arm(joint, angles):
        a1 = angles[0] + torso_dir
        elbow = _seg(joint, a1, m["uarm"] * ss)
        a2 = angles[1] + torso_dir
        wrist = _seg(elbow, a2, m["farm"] * ss)
        a3 = angles[2] + torso_dir if len(angles) > 2 else a2
        tip = _seg(wrist, a3, m["hand"] * ss)
        return elbow, wrist, tip

    def leg(joint, angles):
        a1 = angles[0]
        knee = _seg(joint, a1, m["thigh"] * ss)
        a2 = angles[1]
        ankle = _seg(knee, a2, m["shin"] * ss)
        a3 = angles[2] if len(angles) > 2 else 88
        return knee, ankle, a3

    elb_f, wri_f, tip_f = arm(sh_f, arm_f)
    kn_f, ank_f, fa_f = leg(hip_f, leg_f)
    kn_n, ank_n, fa_n = leg(hip_n, leg_n)
    elb_n, wri_n, tip_n = arm(sh_n, arm_n)

    joints = {
        "hip": hip, "hip_n": hip_n, "hip_f": hip_f,
        "torso": hip, "head": neck, "pelvis": hip,
        "arm_n": sh_n, "arm_f": sh_f,
        "uarm_n": sh_n, "farm_n": elb_n, "hand_n": wri_n,
        "uarm_f": sh_f, "farm_f": elb_f, "hand_f": wri_f,
        "thigh_n": hip_n, "shin_n": kn_n, "foot_n": ank_n,
        "thigh_f": hip_f, "shin_f": kn_f, "foot_f": ank_f,
    }
    angles = {
        "torso": torso_dir, "head": torso_dir * 0.4 + head_a, "pelvis": 0.0,
        "arm_n": arm_n[0] + torso_dir, "arm_f": arm_f[0] + torso_dir,
        "uarm_n": arm_n[0] + torso_dir, "farm_n": arm_n[1] + torso_dir,
        "hand_n": (arm_n[2] + torso_dir) if len(arm_n) > 2 else arm_n[1] + torso_dir,
        "uarm_f": arm_f[0] + torso_dir, "farm_f": arm_f[1] + torso_dir,
        "hand_f": (arm_f[2] + torso_dir) if len(arm_f) > 2 else arm_f[1] + torso_dir,
        "thigh_n": leg_n[0], "shin_n": leg_n[1], "foot_n": fa_n,
        "thigh_f": leg_f[0], "shin_f": leg_f[1], "foot_f": fa_f,
    }

    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    order = []
    for nm in ORDER:
        if nm.startswith(("uarm_", "farm_", "hand_")):
            single = "arm_" + nm[-1]
            if single in rig.parts:          # rig supplies a one-piece arm
                if single not in order:
                    order.append(single)
                continue
        order.append(nm)

    for name in order:
        if name == "prop":
            which = pose.get("prop_part", "prop")
            if which in rig.parts and pose.get("prop"):
                part = dict(rig.parts[which])
                part["name"] = "prop"
                part["base"] = BASE_ANGLE.get("prop", 0.0) + rig.art.get(which, 0.0)
                _place(out, part, pose.get("prop_angle", 0.0), wri_n)
            continue
        # A cloak hangs from the shoulders, behind everything else, and only
        # partly follows the torso: it drapes, so it rides 35% of the lean.
        if name == "cape":
            if "cape" in rig.parts:
                part = dict(rig.parts["cape"])
                part["name"] = "cape"
                part["base"] = 0.0
                _place(out, part, torso_dir * 0.35 + pose.get("cape", 0.0),
                       shoulder)
            continue
        if name not in rig.parts or name not in joints:
            continue
        part = dict(rig.parts[name])
        part["name"] = name
        part["base"] = BASE_ANGLE.get(name, 0.0) + (
            0.0 if name in RELATIVE else rig.art.get(name, 0.0))
        # Socket FIRST, limb over it: the disc exists to fill the gap the
        # rotation opens at the joint, so it must never paint over the art.
        if name.startswith(SOCKETED):
            turned = abs((angles.get(name, 0.0) - part["base"]) % 360.0)
            if min(turned, 360.0 - turned) > 6.0:
                _socket(out, part, joints[name])
        _place(out, part, angles.get(name, 0.0), joints[name])

    if ss != 1:
        out = out.resize(canvas, Image.LANCZOS)
    return out


# --------------------------------------------------------------------- poses
POSES = {
    # Arms are single bent pieces: only the shoulder value does anything, and
    # it is a swing away from the drawn guard. Legs are absolute.
    "stance": dict(lean=4, head=-2,
                   arm_n=(6, 0, 0), arm_f=(-6, 0, 0),
                   leg_n=(12, -10, 88), leg_f=(-14, 6, 92)),
    "breath": dict(lean=3, head=-3, lift=1,
                   arm_n=(9, 0, 0), arm_f=(-5, 0, 0),
                   leg_n=(12, -10, 88), leg_f=(-14, 6, 92)),
    "walk_a": dict(lean=7, head=-4, shift=1,
                   arm_n=(13, 0, 0), arm_f=(-14, 0, 0),
                   leg_n=(26, -18, 92), leg_f=(-22, 4, 86)),
    "walk_b": dict(lean=6, head=-3, shift=-1,
                   arm_n=(2, 0, 0), arm_f=(-4, 0, 0),
                   leg_n=(-16, 2, 84), leg_f=(24, -20, 96)),
    "crouch": dict(lean=16, head=8,
                   arm_n=(18, 0, 0), arm_f=(8, 0, 0),
                   leg_n=(44, -44, 86), leg_f=(30, -56, 94)),
    "jump": dict(lean=8, head=-4, lift=-20, ground=False,
                 arm_n=(26, 0, 0), arm_f=(-20, 0, 0),
                 leg_n=(38, -74, 70), leg_f=(8, 26, 96)),
    "jab": dict(lean=8, shift=3, head=-2,
                arm_n=(30, 0, 0), arm_f=(8, 0, 0),
                leg_n=(20, -14, 88), leg_f=(-18, 8, 92)),
    "cross": dict(lean=14, shift=5, head=-5,
                  arm_n=(32, 0, 0), arm_f=(-12, 0, 0),
                  leg_n=(30, -20, 88), leg_f=(-24, 10, 94)),
    "upper": dict(lean=-8, lift=-14, shift=3, head=4,
                  arm_n=(30, 0, 0), arm_f=(-14, 0, 0),
                  leg_n=(38, -46, 90), leg_f=(-30, 24, 92)),
    "boot": dict(lean=-14, head=6, shift=-6,
                 arm_n=(-20, 0, 0), arm_f=(-22, 0, 0),
                 leg_n=(84, -6, 60), leg_f=(-16, 10, 92)),
    "low_kick": dict(lean=-6, head=4, lift=-24,
                     arm_n=(-18, 0, 0), arm_f=(16, 0, 0),
                     leg_n=(72, -4, 78), leg_f=(-24, 30, 94)),
    "gun_aim": dict(lean=6, head=-2,
                    arm_n=(34, 0, 0), arm_f=(10, 0, 0),
                    leg_n=(16, -14, 88), leg_f=(-16, 8, 92),
                    prop=True, prop_angle=78),
    "gun_fire": dict(lean=2, head=-4, shift=-3,
                     arm_n=(28, 0, 0), arm_f=(8, 0, 0),
                     leg_n=(18, -16, 88), leg_f=(-18, 10, 92),
                     prop=True, prop_angle=72),
    "knife": dict(lean=10, head=-3,
                  arm_n=(-14, 0, 0), arm_f=(12, 0, 0),
                  leg_n=(18, -14, 88), leg_f=(-18, 8, 92),
                  prop=True, prop_part="prop_knife", prop_angle=-58),
    "knife_throw": dict(lean=18, shift=4, head=-6,
                        arm_n=(34, 0, 0), arm_f=(-10, 0, 0),
                        leg_n=(26, -18, 88), leg_f=(-22, 10, 92),
                        prop=True, prop_part="prop_knife", prop_angle=-40),
    # Lightning's specials: hands charged, then hurled forward. The cloak
    # trails the lean instead of swinging with the arms.
    "cast": dict(lean=-6, head=3, shift=-2, cape=-12,
                 arm_n=(26, 0, 0), arm_f=(18, 0, 0),
                 leg_n=(14, -10, 88), leg_f=(-18, 10, 92)),
    "cast_release": dict(lean=11, shift=4, head=-4, cape=9,
                         arm_n=(44, 0, 0), arm_f=(-4, 0, 0),
                         leg_n=(24, -16, 88), leg_f=(-20, 10, 92)),
    "block": dict(lean=-4, lift=-4, head=6,
                  arm_n=(24, 0, 0), arm_f=(20, 0, 0),
                  leg_n=(6, -4, 88), leg_f=(-10, 6, 92)),
    "hit": dict(lean=-16, head=14, shift=-5,
                arm_n=(-24, 0, 0), arm_f=(-30, 0, 0),
                leg_n=(-10, 12, 88), leg_f=(-26, 18, 92)),
    "win": dict(lean=-4, head=-6,
                arm_n=(26, 0, 0), arm_f=(-24, 0, 0),
                leg_n=(14, -10, 88), leg_f=(-18, 8, 92)),
}

SHEET_ORDER = ["stance", "breath", "walk_a", "walk_b", "crouch", "jump",
               "jab", "cross", "upper", "boot", "low_kick", "block",
               "gun_aim", "gun_fire", "knife", "cast", "cast_release",
               "hit", "win"]


# ------------------------------------------------------------- demo part art
SKIN = (226, 176, 142)
SKIN_LIT = (250, 214, 184)
SKIN_DK = (176, 122, 92)
TANK = (244, 244, 242)
TANK_LIT = (255, 255, 255)
TANK_DK = (198, 200, 206)
DENIM = (104, 132, 164)
DENIM_LIT = (150, 178, 206)
DENIM_DK = (62, 82, 108)
BOOT = (82, 54, 34)
BOOT_LIT = (126, 88, 56)
BOOT_DK = (44, 28, 16)
HAIR = (104, 68, 40)
HAIR_LIT = (150, 104, 62)
HAIR_DK = (54, 32, 16)


def _part(size, profile, base, lit, dark):
    mask = _profile_shape(size, profile)
    return _shade(mask, base, lit, dark)


def demo_parts():
    """Stand-in parts so the rig can be tested before real art exists.

    These are deliberately flat: they prove the articulation, not the paint.
    """
    ss = 1
    parts = {}

    uw, fw = 34 * ss, 28 * ss
    parts["uarm_n"] = dict(image=_skin_part(uw, int(62 * ss)), pivot=(uw / 2, 0), name="uarm_n")
    parts["uarm_f"] = dict(image=_skin_part(uw, int(62 * ss)), pivot=(uw / 2, 0), name="uarm_f")
    parts["farm_n"] = dict(image=_skin_part(fw, int(52 * ss)), pivot=(fw / 2, 0), name="farm_n")
    parts["farm_f"] = dict(image=_skin_part(fw, int(52 * ss)), pivot=(fw / 2, 0), name="farm_f")
    hand = _hand_part(30, 30)
    parts["hand_n"] = dict(image=hand, pivot=(hand.width / 2, 0), name="hand_n")
    parts["hand_f"] = dict(image=hand.copy(), pivot=(hand.width / 2, 0), name="hand_f")

    tw, sw = 42 * ss, 34 * ss
    parts["thigh_n"] = dict(image=_denim_part(tw, int(74 * ss)), pivot=(tw / 2, 0), name="thigh_n")
    parts["thigh_f"] = dict(image=_denim_part(tw, int(74 * ss)), pivot=(tw / 2, 0), name="thigh_f")
    parts["shin_n"] = dict(image=_shin_boot_part(sw, int(77 * ss)), pivot=(sw / 2, 0), name="shin_n")
    parts["shin_f"] = dict(image=_shin_boot_part(sw, int(77 * ss)), pivot=(sw / 2, 0), name="shin_f")
    foot = _foot_part(44 * ss, 36 * ss)
    parts["foot_n"] = dict(image=foot, pivot=(foot.width * 0.20, foot.height * 0.62), name="foot_n")
    parts["foot_f"] = dict(image=foot.copy(), pivot=(foot.width * 0.20, foot.height * 0.62), name="foot_f")

    torso = _torso_part(104 * ss, 110 * ss)
    parts["torso"] = dict(image=torso, pivot=(torso.width / 2, torso.height), name="torso")
    pelvis = _denim_part(62 * ss, 38 * ss)
    parts["pelvis"] = dict(image=pelvis, pivot=(pelvis.width / 2, pelvis.height * 0.25), name="pelvis")
    head = _head_part(62 * ss, 48 * ss)
    parts["head"] = dict(image=head, pivot=(head.width / 2, head.height), name="head")
    parts["prop"] = dict(image=_gun_part(52 * ss, 30 * ss),
                         pivot=(7 * ss, 21 * ss), name="prop")
    return Rig(parts)


def _skin_part(w, h):
    return _part((w, h), [(0.0, 0.82), (0.18, 1.0), (0.55, 0.82), (1.0, 0.7)],
                 SKIN, SKIN_LIT, SKIN_DK)


def _denim_part(w, h):
    return _part((w, h), [(0.0, 0.8), (0.2, 1.0), (0.7, 0.86), (1.0, 0.74)],
                 DENIM, DENIM_LIT, DENIM_DK)


def _hand_part(w, h):
    img = _part((w, h), [(0.0, 0.7), (0.3, 1.0), (1.0, 0.8)], SKIN, SKIN_LIT, SKIN_DK)
    d = ImageDraw.Draw(img)
    d.line([(w * 0.3, h * 0.5), (w * 0.72, h * 0.5)], fill=(150, 100, 74, 110), width=2)
    return img


def _shin_boot_part(w, h):
    """The calf, in a tall strapped boot.

    From the boot references: the shaft is tall enough to cover the calf, so it
    belongs on the SHIN, which moves with the knee - not on the ankle. Denim
    above the cuff, leather below, stitched panel, buckle straps down the
    outer edge, welted sole follows on the foot part.
    """
    body = _profile_shape((w, h), [(0.0, 0.80), (0.24, 1.0), (0.72, 0.94), (1.0, 0.88)])
    leather = _shade(body, BOOT, BOOT_LIT, BOOT_DK)

    cuff = max(2, int(h * 0.30))
    denim_mask = Image.new("L", (w, h), 0)
    denim_mask.paste(body.crop((0, 0, w, cuff)), (0, 0))
    img = Image.alpha_composite(leather,
                                _shade(denim_mask, DENIM, DENIM_LIT, DENIM_DK))

    d = ImageDraw.Draw(img)
    d.line([(w * 0.05, cuff), (w * 0.95, cuff)], fill=BOOT_DK + (240,), width=3)
    d.line([(w * 0.05, cuff - 2), (w * 0.95, cuff - 2)], fill=BOOT_LIT + (110,), width=1)
    d.line([(w * 0.52, cuff + 3), (w * 0.45, h * 0.97)], fill=BOOT_DK + (130,), width=2)

    span = h - cuff
    for i in range(5):
        y = cuff + span * (0.07 + i * 0.185)
        band = y + span * 0.075
        d.rectangle([w * 0.50, y, w * 0.98, band], fill=BOOT_LIT + (68,))
        d.rectangle([w * 0.50, y, w * 0.98, band], outline=BOOT_DK + (175,), width=1)
        d.rectangle([w * 0.77, y - 1, w * 0.96, band + 1],
                    fill=(160, 162, 166, 212), outline=(50, 36, 22, 232))
    return img


def _foot_part(w, h):
    """The shoe below the ankle: TOE RIGHT, welted sole, tread, toe cap."""
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(w * 0.06, h * 0.14), (w * 0.64, h * 0.08), (w * 0.99, h * 0.50),
               (w * 0.99, h * 0.78), (w * 0.06, h * 0.84)], fill=255)
    d.ellipse([w * 0.04, h * 0.08, w * 0.50, h * 0.82], fill=255)
    img = _shade(mask, BOOT, BOOT_LIT, BOOT_DK)

    d = ImageDraw.Draw(img)
    d.rectangle([w * 0.03, h * 0.74, w * 1.0, h * 0.90], fill=(184, 180, 170, 235))
    for i in range(9):
        x = w * (0.05 + i * 0.105)
        d.rectangle([x, h * 0.84, x + w * 0.042, h * 0.96], fill=(94, 90, 84, 225))
    d.arc([w * 0.68, h * 0.16, w * 1.0, h * 0.80], 250, 110,
          fill=BOOT_DK + (155,), width=2)
    d.rectangle([w * 0.14, h * 0.26, w * 0.42, h * 0.44], fill=BOOT_LIT + (78,),
                outline=BOOT_DK + (160,))
    return img


def _torso_part(w, h):
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    # shoulders wide, waist tucked, deltoid caps rounded
    d.polygon([(w * 0.09, h * 0.14), (w * 0.91, h * 0.14),
               (w * 0.74, h * 0.56), (w * 0.69, h * 1.0),
               (w * 0.31, h * 1.0), (w * 0.26, h * 0.56)], fill=255)
    d.ellipse([w * 0.02, 0, w * 0.98, h * 0.34], fill=255)
    d.ellipse([w * 0.20, h * 0.30, w * 0.80, h * 0.98], fill=255)
    img = _shade(mask, TANK, TANK_LIT, TANK_DK)
    d = ImageDraw.Draw(img)
    # bare chest at the neckline
    d.polygon([(w * 0.40, 0), (w * 0.60, 0), (w * 0.56, h * 0.20),
               (w * 0.50, h * 0.26), (w * 0.44, h * 0.20)], fill=SKIN + (255,))
    d.arc([w * 0.36, h * 0.02, w * 0.64, h * 0.30], 20, 160, fill=SKIN_DK + (140,), width=2)
    # the shirt graphic, as a placeholder smudge
    d.ellipse([w * 0.32, h * 0.44, w * 0.62, h * 0.66], fill=(206, 120, 130, 120))
    d.ellipse([w * 0.40, h * 0.50, w * 0.56, h * 0.62], fill=(70, 120, 90, 90))
    return img


def _head_part(w, h):
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([w * 0.22, h * 0.06, w * 0.78, h * 0.66], fill=255)   # cranium
    d.polygon([(w * 0.28, h * 0.44), (w * 0.72, h * 0.44),
               (w * 0.68, h * 0.80), (w * 0.50, h * 0.98),
               (w * 0.32, h * 0.80)], fill=255)                       # jaw
    d.rectangle([w * 0.40, h * 0.86, w * 0.60, h], fill=255)          # neck stub
    img = _shade(mask, SKIN, SKIN_LIT, SKIN_DK)
    d = ImageDraw.Draw(img)
    # hair: swept top plus mullet at the back
    d.polygon([(w * 0.16, h * 0.34), (w * 0.28, h * 0.08), (w * 0.56, h * 0.00),
               (w * 0.84, h * 0.16), (w * 0.80, h * 0.40), (w * 0.70, h * 0.22),
               (w * 0.40, h * 0.24), (w * 0.30, h * 0.44)], fill=HAIR + (255,))
    d.polygon([(w * 0.16, h * 0.34), (w * 0.26, h * 0.58), (w * 0.22, h * 0.80),
               (w * 0.34, h * 0.62), (w * 0.34, h * 0.38)], fill=HAIR + (255,))
    d.line([(w * 0.30, h * 0.26), (w * 0.46, h * 0.14)], fill=HAIR_LIT + (180,), width=3)
    # brows, eyes, nose, mouth, stubble
    d.line([(w * 0.30, h * 0.47), (w * 0.45, h * 0.45)], fill=(58, 38, 24, 235), width=3)
    d.line([(w * 0.56, h * 0.45), (w * 0.70, h * 0.47)], fill=(58, 38, 24, 235), width=3)
    d.ellipse([w * 0.33, h * 0.51, w * 0.43, h * 0.56], fill=(238, 238, 240, 255))
    d.ellipse([w * 0.57, h * 0.51, w * 0.67, h * 0.56], fill=(238, 238, 240, 255))
    d.ellipse([w * 0.365, h * 0.515, w * 0.405, h * 0.555], fill=(46, 104, 160, 255))
    d.ellipse([w * 0.605, h * 0.515, w * 0.645, h * 0.555], fill=(46, 104, 160, 255))
    d.line([(w * 0.50, h * 0.54), (w * 0.47, h * 0.66)], fill=SKIN_DK + (150,), width=2)
    d.line([(w * 0.42, h * 0.76), (w * 0.58, h * 0.75)], fill=(120, 66, 54, 200), width=2)
    d.ellipse([w * 0.26, h * 0.70, w * 0.74, h * 0.92], fill=(96, 58, 40, 60))
    d.arc([w * 0.34, h * 0.62, w * 0.66, h * 0.92], 200, 340, fill=(96, 58, 40, 90), width=2)
    return img


def _gun_part(w, h):
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.rectangle([0, h * 0.10, w, h * 0.34], fill=255)          # slide
    d.polygon([(0, h * 0.30), (w * 0.22, h * 0.30), (w * 0.16, h * 1.0),
               (w * 0.02, h * 1.0)], fill=255)                   # grip
    img = _shade(mask, (60, 62, 68), (112, 116, 124), (26, 28, 32))
    d = ImageDraw.Draw(img)
    d.rectangle([0, h * 0.10, w * 0.16, h * 0.34], fill=(38, 40, 44, 255))
    return img


# ------------------------------------------------------------------ contact sheet
def sheet(rig, order, path, cols=6, cell=None, label=True):
    from PIL import ImageFont
    cell = cell or rig.canvas
    rows = (len(order) + cols - 1) // cols
    pad_top = 26 if label else 0
    W, H = cell[0] * cols, (cell[1] + pad_top) * rows
    out = Image.new("RGBA", (W, H), (30, 32, 38, 255))
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
    except OSError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(out)
    for i, name in enumerate(order):
        frame = render(rig, POSES[name], cell)
        cx, cy = (i % cols) * cell[0], (i // cols) * (cell[1] + pad_top)
        out.alpha_composite(frame, (cx, cy + pad_top))
        if label:
            d.text((cx + 8, cy + 6), name, font=font, fill=(210, 214, 222, 255))
        d.rectangle([cx, cy, cx + cell[0] - 1, cy + pad_top + cell[1] - 1],
                    outline=(52, 56, 66, 255))
    out.convert("RGB").save(path, quality=92)
    return path


TEMPLATE = """# {char} - part art for the puppet rig

Drop these PNGs in `art_src/chars/{char}/parts/`, then run
`python3 tools/char_rig.py --sheet {char}`. Each part is drawn ONCE, at rest,
and the rig rotates it about its pivot for every animation frame.

Draw at 2x the sizes below and add `{{"scale": 0.5}}` to `rig.json`; the rig
downsamples with LANCZOS.

| file | size (px) | drawn as | pivot |
|---|---|---|---|
| torso.png | 104 x 110 | upright, head end at the top | bottom centre (the hip) |
| pelvis.png | 62 x 38 | upright | 25% down, centre |
| head.png | 62 x 48 | upright, crown at the top | bottom centre (the neck) |
| uarm_n.png / uarm_f.png | 34 x 62 | hanging straight DOWN | top centre (the shoulder) |
| farm_n.png / farm_f.png | 28 x 52 | hanging straight DOWN | top centre (the elbow) |
| hand_n.png / hand_f.png | 30 x 30 | fingers down | top centre (the wrist) |
| thigh_n.png / thigh_f.png | 42 x 74 | hanging straight DOWN | top centre (the hip) |
| shin_n.png / shin_f.png | 34 x 77 | hanging straight DOWN | top centre (the knee) |
| foot_n.png / foot_f.png | 44 x 36 | TOE POINTING RIGHT, sole flat | 34% across, 62% down (the heel) |
| prop.png | 52 x 30 | pointing +x | the grip |

`_n` is the near (screen-left of the enemy) limb, `_f` the far one.

Pivots can be overridden in `rig.json`:

```json
{{
  "scale": 1.0,
  "pivots": {{"foot_n": [10, 20], "head": [33, 60]}},
  "metrics": {{"hip_y": -165}},
  "angles": {{"uarm_n": 45, "uarm_f": 45, "farm_n": 20, "farm_f": 20}}
}}
```

`angles` says how far each part is rotated in the source art, so an A-pose
figure (arms out at 45 deg) still bends correctly: cut the arm as drawn and
declare the angle it sits at instead of redrawing it straight down.

Keep the joint ends of each part full-bleed to the edge of its canvas - the rig
overlaps them at the joint, so a soft or empty edge shows as a gap when a limb
bends hard.

Animation frames the rig drives (poses in `POSES`, `tools/char_rig.py`):
{poses}
"""


def write_template(char_id):
    folder = os.path.join(PARTS_DIR, char_id)
    os.makedirs(os.path.join(folder, "parts"), exist_ok=True)
    path = os.path.join(folder, "README.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(TEMPLATE.format(char=char_id,
                                poses=", ".join(SHEET_ORDER)))
    return path


def main(argv):
    os.makedirs(OUT_DIR, exist_ok=True)
    if "--template" in argv:
        which = [a for a in argv if not a.startswith("-")] or ["jackburton"]
        for cid in which:
            print("wrote", os.path.relpath(write_template(cid), ROOT))
        return 0

    if "--sheet" in argv:
        cid = [a for a in argv if not a.startswith("-")][0]
        rig = load_rig(cid)
        out = sheet(rig, SHEET_ORDER, os.path.join(OUT_DIR, f"{cid}_poses.png"))
        print("wrote", os.path.relpath(out, ROOT))
        return 0

    if "--demo" in argv:
        rig = demo_parts()
        out = sheet(rig, SHEET_ORDER, os.path.join(OUT_DIR, "char_rig_poses.png"))
        print("wrote", os.path.relpath(out, ROOT))
        write_template("jackburton")
        return 0

    if "--rest" in argv:
        cid = [a for a in argv if not a.startswith("-")][0]
        rig = load_rig(cid)
        made = render(rig, rest_pose(rig))
        src_path = os.path.join(ROOT, "art_src", "chars", cid, "work", "front.png")
        path = os.path.join(OUT_DIR, f"{cid}_rest.png")
        if os.path.isfile(src_path):
            ref = Image.open(src_path).convert("RGBA")
            sheet_img = Image.new("RGBA", (ref.width + made.width + 24,
                                           max(ref.height, made.height)),
                                  (30, 32, 38, 255))
            sheet_img.alpha_composite(ref, (0, 0))
            sheet_img.alpha_composite(made, (ref.width + 24, 0))
        else:
            sheet_img = made
        sheet_img.convert("RGB").save(path)
        print("wrote", os.path.relpath(path, ROOT))
        return 0

    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
