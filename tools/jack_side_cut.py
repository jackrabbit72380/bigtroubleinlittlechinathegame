"""Cut Jack's SIDE-VIEW part set from the hand-cut profile render.

``side_parts.py`` cuts the old side set from the third panel of the photographic
turnaround by knocking a studio background out of a JPEG. That art is gone: the
fighters are built from the new renders now, and the render that faces right
(``jack faceing right_cut.png``) arrives as RGBA with the alpha already painted,
so nothing has to be keyed - the cut is taken straight from the alpha channel.

Boxes and joints below are measured on this file in its own pixels (1021x1526
after the empty margin is trimmed), read off a 100px grid laid over the cut and
checked against the mask: the boot tops, the crotch, the arms' elbows and the
sole are all where the art puts them.  Every pivot is a joint of the drawn body,
so the rig rotates the art around the same point the artist drew it around.

The art is a three-quarter guard rather than a flat profile: both shoulders and
both hips are visible, so this set keeps a ``shoulder_half`` and a ``hip_half``
that the old profile set had to zero, and the near arm and near leg are cut on
their own side of the body instead of being hidden behind each other.

Three things this cut has to get right, because each one was a visible fault:

*   **The near arm's elbow.** ``arm_joints`` below states where the elbow and
    the wrist are DRAWN, in part pixels, so ``char_rig`` can cut the arm there
    and bend it. Without it the arm fell back to the front-view joints, which
    land on the biceps of a 251px piece - a dark band across the elbow that no
    pose could bend, so the arm swung from the shoulder like a plank.
*   **The far arm stays on the torso.** It is drawn across the chest, and the
    part of it that is over his body is the only place his chest is covered from
    the shoulder down: cutting it out and rebuilding that chest read as a pale
    slab with a hard edge wherever the arm left it, and the rebuilt cloth never
    matched the print under the fist. He keeps the guard the art draws, and the
    near arm - the one that reaches out - carries the punches.
*   **The near arm is cut OUT of the body.** ``torso.png`` has a notch where the
    raised arm is drawn, because the arm is its own part now and is drawn back
    into that notch in every pose. Keeping the body's copy instead left a second
    bicep painted on his chest the moment the arm reached forward.
*   **The legs.** A thigh box that reached up to the waist carried the belt and
    the other leg with it, and swinging it tore a flap of denim out of the hip.
    Each thigh now keeps only its own leg plus a lap over its hip joint.

Run:  python3 tools/jack_side_cut.py
"""

from __future__ import annotations

import json
import math
import os
from collections import deque

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ART = os.path.join(ROOT, "concept_art", "fighters", "jack_burton",
                   "jack faceing right_cut.png")
OUT = os.path.join(ROOT, "art_src", "chars", "jackburton", "parts_side")

# Joints in the cut's own pixels, read off the grid over the cut.
NECK = (566, 336)
# The arm's socket, measured INSIDE the deltoid rather than on its outer edge.
# The skeleton hangs the arm from this point and the piece pivots on it, so it
# has to be both a plausible joint and the point the art draws the arm around:
# taken out on the deltoid's rim it is neither, and the arm then swings its own
# shoulder away from the body, leaving a wedge of air at the armpit.
SHOULDER_N = (680, 320)          # raised arm, image right, drawn right of centre
ELBOW_N = (800, 545)             # its elbow, at the bottom of the biceps
WRIST_N = (830, 445)             # the crease under the fist, not the knuckles
SHOULDER_F = (330, 300)          # the arm across the chest, image left
HIP_N = (620, 780)
KNEE_N = (806, 980)
ANKLE_N = (828, 1420)
HIP_F = (462, 780)
KNEE_F = (330, 1050)
ANKLE_F = (170, 1425)
SOLE = 1522
HIP_MID = (541, 780)

# A part box clips one limb out of the cut; the joint is where it hangs from.
BOXES = {
    # stops under the chin: the tank strap starts around y=286 and a head part
    # that clips it pastes a vest shoulder under his jaw when the head turns
    "head": (420, 0, 690, 340),
    # The box takes the near shoulder cap with it (out to 760), and starts above
    # the collar (180) so the trapezius is the body's: stopping at the near arm's
    # inner edge left a hole at the armpit the moment the arm swung forward, and
    # starting at 240 left a notch of background behind the jaw, because the head
    # part stops at the throat.
    "torso": (200, 180, 760, 800),
    "arm_n": (640, 200, 940, 660),
    # The hip band, kept INSIDE the denim. A box wide enough to take the body's
    # own outline at this height also takes his fists - they hang at his hips -
    # and the piece then has wings that are not his body at all. Cut inside the
    # denim instead, every edge of the piece is a seam on jeans of the same
    # colour, and it cannot stick out of the hip when a leg swings away.
    "pelvis": (430, 720, 780, 792),
    # Leg boxes lap upwards past their joint. The two drawn legs are not the
    # same length (the stance is three-quarter, so the far one is foreshortened)
    # and the skeleton carries one thigh and one shin for both, so the piece
    # that ends short has to be covered by the piece below it, not left with a
    # gap. They start at the hip line, not at the waist: a thigh that carried
    # the belt swung it out of the hip on every step.
    "thigh_n": (540, 745, 880, 1010),
    "shin_n": (720, 960, 1015, 1526),
    "thigh_f": (235, 745, 585, 1080),
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

# Where the near arm is drawn bent. Part pixels, the same space as the pivots,
# because ``char_rig`` cuts the arm image at these numbers. Both points are
# stated: the elbow is where the knife goes, and the wrist is what tells the rig
# which way the forearm runs - a cut with no wrist has to guess the direction from
# the piece's bounding box, and on a bent arm that guess lands on the far corner,
# which leaves the forearm attached to the bicep and the arm rigid at the
# shoulder.
ARM_JOINTS = {"n": [[ELBOW_N, WRIST_N]]}

# The fist is drawn as knuckles on a wrist bone, not as a hand with a silhouette
# of its own. Cut free at the wrist it hangs in the air ahead of the forearm on
# every extended punch, so it rides the forearm here and the wrist joint only
# gives it its direction.
HAND_PIECES = False

# The far arm is cut by following the skin it is painted with: a seed inside its
# forearm, then the connected skin around it. The art's outline is dark and the
# fist is a shade off the biceps, so the mask is grown before the walk and
# shrunk back after it.
CROTCH_X = 590

# Rig units per art pixel. The old side set drew the figure about 550 rig units
# tall on a 640x780 canvas from a 648px crop; this art is 1485px tall, so the
# same size on screen needs about this much per pixel.
SCALE = 0.371

# Draw order for this rig only. The far arm is painted ACROSS the chest in this
# guard, so it has to be drawn after the torso - behind it, the fist would be
# swallowed by the body it is held against. The far leg stays behind, and the
# near arm in front of everything. Both the one-piece and the cut names are
# listed: char_rig keeps whichever pair the set actually supplies.
ORDER = ["cape", "thigh_f", "shin_f", "foot_f", "pelvis", "torso", "head",
         "thigh_n", "shin_n", "foot_n",
         "arm_n", "uarm_n", "farm_n", "hand_n", "prop"]


def _trim_white_collar(part):
    """Drop the tank top the head box clips in under the jaw.

    The head box runs down past the chin so the mullet and the throat survive.
    Near-white fabric in its bottom corner would pivot with the head and paste a
    second vest shoulder under the chin - the white blob the old set shipped.
    Only near-white, low-saturation pixels go, which leaves the hair alone.
    """
    px = part.load()
    w, h = part.size
    for y in range(int(h * 0.60), h):
        for x in range(w):
            r, g, b, a = px[x, y]
            # Fabric, not hair: the vest is neutral grey-white in both its lit
            # and its shaded parts, the hair is warm and the throat is skin.
            if a and max(r, g, b) - min(r, g, b) < 46 and min(r, g, b) > 60:
                px[x, y] = (0, 0, 0, 0)
    return part


def _arm_mask(cut, box):
    """The arm inside its box, with the vest it is raised in front of taken out.

    The box also clips the vest's shoulder and the edge of the print, and both
    travelled with the arm: a slab of cloth turning at the shoulder, a sliver of
    print at the elbow. The vest is the only neutral-bright thing that reaches
    the box's edge, so it is walked in from the border - which leaves the arm's
    own white specular highlights alone, since they sit inside the arm and the
    walk cannot reach them.
    """
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    px = cut.load()
    m = Image.new("L", cut.size, 0)
    mp = m.load()
    vest = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x + x0, y + y0]
            if a < 40:
                continue
            if min(r, g, b) > 140 and max(r, g, b) - min(r, g, b) < 45:
                vest[y * w + x] = 1
            else:
                mp[x + x0, y + y0] = 255
    seen = bytearray(w * h)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if vest[y * w + x] and not seen[y * w + x]:
                seen[y * w + x] = 1
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if vest[y * w + x] and not seen[y * w + x]:
                seen[y * w + x] = 1
                q.append((x, y))
    while q:
        x, y = q.popleft()
        mp[x + x0, y + y0] = 0
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < w and 0 <= ny < h):
                continue
            i = ny * w + nx
            if seen[i] or not vest[i]:
                continue
            seen[i] = 1
            q.append((nx, ny))
    return m


def _pelvis_mask(cut):
    """The waistband: the whole hip band, minus the skin in it.

    The band has to reach past the torso's own bottom edge - a cut through the
    jeans leaves a hard ledge wherever the hips do not cover it - and a box that
    wide also takes his fists, which hang at his hips in this guard. Skin is warm
    and jeans are not, so the fists are the only thing that has to go.
    """
    x0, y0, x1, y1 = BOXES["pelvis"]
    m = Image.new("L", cut.size, 0)
    ImageDraw.Draw(m).rectangle([x0, y0, x1 - 1, y1 - 1], fill=255)
    px = cut.load()
    mp = m.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b, a = px[x, y]
            if a > 40 and r > b + 12 and max(r, g, b) - min(r, g, b) > 40:
                mp[x, y] = 0
    return m


def _torso_mask(cut):
    """The body down to the waistband, no further.

    The torso box runs to the hip line, so the piece carries a wedge of hip
    denim below the vest - and the torso LEANS, so that wedge swings out of his
    waist as a hard edged flap on every step. Below this line the waistband is
    the piece, cut from the same denim, so the seam has nothing to show.
    """
    x0, y0, x1, y1 = BOXES["torso"]
    cut_at = 772
    m = Image.new("L", cut.size, 0)
    ImageDraw.Draw(m).rectangle([x0, y0, x1 - 1, cut_at - 1], fill=255)
    # Fade the last few rows instead of stopping dead: a hard cut through denim
    # is a one pixel bright seam across his belt in every pose.
    feather = 6
    px = m.load()
    for i in range(feather):
        y = cut_at + i
        if y < m.height:
            v = int(255 * (1.0 - (i + 1) / float(feather + 1)))
            for x in range(x0, x1):
                px[x, y] = v
    return m


def _head_mask(cut):
    """The head, the mullet and the throat - not the shoulder it stands on.

    The box runs left past the jaw to keep the hair, which also takes in the top
    of the trapezius and the vest strap. Left in, they hung off the side of the
    skull and turned with it.
    """
    x0, y0, x1, y1 = BOXES["head"]
    m = Image.new("L", cut.size, 0)
    d = ImageDraw.Draw(m)
    d.polygon([(x0, y0), (x1 - 1, y0), (x1 - 1, y1 - 1), (NECK[0] - 46, y1 - 1),
               (x0, NECK[1] - 81)], fill=255)
    return m


def _thigh_mask(cut, name):
    """This leg only: its own side of the crotch, plus a lap over its hip.

    The box alone carried the belt and the other leg's hip with it, and a step
    swung that denim out of the waist as a flap.
    """
    hip = JOINTS[name]
    box = BOXES[name]
    m = Image.new("L", cut.size, 0)
    d = ImageDraw.Draw(m)
    # The cut starts well below the joint: a thigh box is 340 art px wide, so a
    # cut skimming the hip swings out as a slab of denim the moment the leg moves,
    # and the far one swings it across the near leg. Below the joint the cut is
    # inside the leg's own silhouette, and at the joint itself only the disc -
    # whose shape no rotation changes - is ever on show.
    d.rectangle([box[0], hip[1] + 40, box[2], box[3]], fill=255)
    # the lap: a disc on the joint. A band above the joint turns with the leg
    # and swings a corner of denim out of the hip; a disc is unchanged by any
    # rotation about its own centre, so it can only ever cover the seam.
    # The near hip is the one the torso's waistband cut runs across, so its lap
    # is a full palm wide: the band must not be left to cover that seam alone,
    # or it is the band's static denim that shows when the leg swings.
    lap = 38 if name == "thigh_n" else 30
    d.ellipse([hip[0] - lap, hip[1] - lap, hip[0] + lap, hip[1] + lap], fill=255)
    if name == "thigh_n":
        d.rectangle([0, 0, CROTCH_X, cut.height], fill=0)
    else:
        d.rectangle([CROTCH_X, 0, cut.width, cut.height], fill=0)
    return m


def _fill_hole(cut, hole, box):
    """Paint the body where the near arm is drawn over it.

    The arm is its own part, so the body cannot keep the arm's pixels - swing the
    arm and a second bicep stays painted on his chest. But the photo has no chest
    under that arm either, so cut out it leaves a hole the stage shows through on
    every punch. Behind the arm is his tank top: the gap between the straps is
    above it and the print is to its left, so the hole is filled with the colour
    of the cloth AROUND it - weighed on the rim, where the vest is lit the way it
    is beside the arm - and that fill is blended into the art through a feathered
    mask, because a fill with its own edges reads as a card pasted on him.
    """
    img = cut.copy()
    src = img.copy()
    px = img.load()
    sp = src.load()
    hp = hole.load()
    x0, y0, x1, y1 = box

    def solid(x, y):
        return 0 <= x < src.width and 0 <= y < src.height and sp[x, y][3] > 40

    holes = {(x, y) for y in range(y0, y1) for x in range(x0, x1)
             if hp[x, y] > 127 and sp[x, y][3] > 40}
    if not holes:
        return img

    # The cloth on the rim of the hole: bright and neutral, i.e. the tank top.
    rim = []
    for x, y in holes:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n in holes or not solid(*n):
                continue
            r, g, b, a = sp[n]
            if min(r, g, b) > 120 and max(r, g, b) - min(r, g, b) < 60:
                rim.append((r + g + b, r, g, b))
    if rim:
        rim.sort()
        # Lit end of the rim, not the middle: the rim's darker half is the arm's
        # own shadow, and filling with it left a grey cloud on a white vest.
        _, r, g, b = rim[int(len(rim) * 0.75)]
        cloth = (r, g, b)
    else:
        cloth = (190, 188, 184)

    # The body's own side, above and below the arm, carried across it: the raised
    # arm sticks out past his ribs, so the fill may not run out where the arm did.
    rows = sorted({y for _, y in holes})
    top_row, bot_row = rows[0] - 1, rows[-1] + 1
    def side(y):
        for x in range(x1 - 1, x0 - 1, -1):
            if hp[x, y] < 128 and solid(x, y):
                return x
        return None
    x_top, x_bot = side(max(y0, top_row)), side(min(y1 - 1, bot_row))
    clip_from = 470
    if x_top is not None and x_bot is not None and bot_row > top_row:
        for y in rows:
            if y < clip_from:
                continue
            edge = x_top + (x_bot - x_top) * (y - top_row) / float(bot_row - top_row)
            for x in range(int(edge) + 1, x1):
                holes.discard((x, y))

    # Composite it: a mask of the hole, blurred, over the art. The blur is what
    # takes the ruled edge off both the fill and the body's cut side.
    mask = Image.new("L", src.size, 0)
    mp = mask.load()
    for x, y in holes:
        mp[x, y] = 255
    mask = mask.filter(ImageFilter.GaussianBlur(6))

    shade = Image.new("RGBA", src.size, cloth + (255,))
    spx = shade.load()
    for x, y in holes:
        # A little darker into the armpit, lit along the ribs: a flat tone reads
        # as paper even when the colour is right.
        t = max(0.0, min(1.0, (y - rows[0]) / 220.0))
        k = 0.86 + 0.14 * t
        spx[x, y] = (int(cloth[0] * k), int(cloth[1] * k), int(cloth[2] * k), 255)
    shade.putalpha(ImageChops.multiply(shade.getchannel("A"), mask))
    return Image.alpha_composite(img, shade)


def _largest_blob(alpha):
    """Keep the biggest connected piece of a part's alpha.

    A part is one limb. Where the arm's skin was cut out of the chest, the lit
    rim along the arm is neither skin nor outline and stayed behind as bars
    floating in the air; where the fist is drawn against the print, a swirl came
    away with the knuckles. Both are small islands beside the real piece, and
    both are gone once only the biggest island is kept.
    """
    w, h = alpha.size
    px = alpha.load()
    seen = bytearray(w * h)
    best = []
    for sy in range(h):
        for sx in range(w):
            if px[sx, sy] < 128 or seen[sy * w + sx]:
                continue
            q = deque([(sx, sy)])
            seen[sy * w + sx] = 1
            comp = []
            while q:
                x, y = q.popleft()
                comp.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < w and 0 <= ny < h):
                        continue
                    i = ny * w + nx
                    if seen[i] or px[nx, ny] < 128:
                        continue
                    seen[i] = 1
                    q.append((nx, ny))
            if len(comp) > len(best):
                best = comp
    out = Image.new("L", (w, h), 0)
    op = out.load()
    for x, y in best:
        op[x, y] = 255
    return out


def _part(cut, name, mask=None):
    """Cut one part; return it, its pivot and its offset in the cut."""
    box = BOXES[name]
    joint = JOINTS[name]
    raw = cut.crop(box)
    # The art's OWN alpha, not a threshold of it: the render's cut carries a soft
    # drop shadow under the arm and along the boots, and flattening alpha to 0/255
    # turned that shadow into a hard black triangle painted on his chest.
    soft = raw.getchannel("A")
    solid = soft.point(lambda v: 255 if v > 40 else 0)
    if mask is not None:
        solid = ImageChops.multiply(solid, mask.crop(box))
    # Keep only the biggest island, then put the art's soft edge back inside it.
    alpha = ImageChops.multiply(soft, _largest_blob(solid))
    bb = alpha.getbbox() or (0, 0, 1, 1)
    # The joint has to stay inside the piece or its pivot cannot be expressed in
    # part pixels; a lap that starts above the joint would otherwise be clamped
    # to the top edge, which is the bug that put a 12px step on the far boot.
    jx, jy = joint[0] - box[0], joint[1] - box[1]
    bb = (min(bb[0], jx), min(bb[1], jy), max(bb[2], jx + 1), max(bb[3], jy + 1))
    piece = raw.crop(bb)
    piece.putalpha(alpha.crop(bb))
    if name == "head":
        piece = _trim_white_collar(piece)
    pivot = (joint[0] - box[0] - bb[0], joint[1] - box[1] - bb[1])
    return piece, pivot, (box[0] + bb[0], box[1] + bb[1])


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

    # The arm is cut out of the body, not copied on top of it: a body that kept
    # its own copy showed a second bicep on the chest wherever the arm swung
    # away, and painting that copy over with cloth only traded it for a pale
    # patch with a hard edge. He has air there, and the arm is drawn into it.
    arm = _arm_mask(cut, BOXES["arm_n"])
    # The body the arm is drawn over does not exist in the photo, so the torso is
    # cut from a copy of the art whose arm has been replaced by the fabric around
    # it. The arm part still covers its own hole exactly at rest.
    body = _fill_hole(cut, arm.filter(ImageFilter.MaxFilter(7)), BOXES["torso"])

    parts, pivots, offsets = {}, {}, {}
    for name in BOXES:
        mask = None
        if name == "arm_n":
            mask = arm
        elif name == "torso":
            mask = _torso_mask(cut)
        elif name == "pelvis":
            mask = _pelvis_mask(cut)
        elif name == "head":
            mask = _head_mask(cut)
        elif name in ("thigh_n", "thigh_f"):
            mask = _thigh_mask(cut, name)
        src = body if name == "torso" else cut
        parts[name], pivots[name], offsets[name] = _part(src, name, mask)

    # The knife sprite the old set produced is still drawn by the Knife Toss
    # state; the new art's hands are empty, so there is nothing to re-cut.
    for keep in ("prop_knife.png",):
        if os.path.isfile(os.path.join(OUT, keep)):
            parts["prop_knife"] = Image.open(os.path.join(OUT, keep)).convert("RGBA")
            pivots["prop_knife"] = [round(parts["prop_knife"].width * 0.55, 1),
                                    round(parts["prop_knife"].height * 0.08, 1)]
    parts["prop"] = Image.new("RGBA", (2, 2), (0, 0, 0, 0))
    pivots["prop"] = [1, 1]

    # The near arm's joints, moved from the cut's pixels into its own part.
    arm_joints = {}
    aox, aoy = offsets["arm_n"]
    # Only the elbow. The fist is drawn as knuckles on the wrist, not as a hand
    # with its own silhouette, so cutting it off at the wrist left a fist hanging
    # in the air ahead of the forearm on every extended punch.
    arm_joints["n"] = [[round(ELBOW_N[0] - aox, 1), round(ELBOW_N[1] - aoy, 1)],
                       [round(WRIST_N[0] - aox, 1), round(WRIST_N[1] - aoy, 1)]]

    metrics = {
        # pivot to the top of the piece: that is the torso bone. Taking the whole
        # piece height instead put the bone past the pivot once the box ran below
        # the hip line, and the rig's shoulder-line probe went off the top.
        # pivot to the SHOULDER LINE in the art (y=240), not to the top of the
        # piece: the box now starts above the collar, and measuring to the box
        # would lift the whole skeleton 60px up his chest.
        "torso_len": round((JOINTS["torso"][1] - 240) * SCALE, 1),
        "neck_len": 0.0,
        "uarm": round(_dist(SHOULDER_N, ELBOW_N) * SCALE, 1),
        "farm": round(_dist(ELBOW_N, WRIST_N) * SCALE, 1),
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
        # Where the sleeve hangs, measured from the hip: the skeleton's shoulder
        # line is the top of the SHORT neck at the collar, and the arm's joint is
        # a whole deltoid below it. Stating it keeps the head on the neck and the
        # arm on its own shoulder instead of trading one for the other.
        "arm_socket": [round((SHOULDER_N[0] - HIP_MID[0]) * SCALE, 1),
                       round((HIP_MID[1] - SHOULDER_N[1]) * SCALE, 1)],
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
        "arm_joints": arm_joints,
        "hand_pieces": HAND_PIECES,
        # Both thighs are cut with a lap disc on their own hip and the hip band
        # sits between them, so the hip joints have no air to weld: welded, the
        # capsule is a dark stripe across the jeans every time he leans. The
        # shoulder is the same story from the other side: the arm's art already
        # covers its own socket, so the weld has no air to close and instead
        # washes a skin tinted sash over the soft edge of his vest.
        "welds_off": ["thigh_n", "thigh_f", "uarm_n"],
        "order": ORDER,
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
                  "joints carry a half-width. The near arm is cut at the elbow "
                  "and wrist it is DRAWN bent at (arm_joints), so it folds and "
                  "reaches; the far one is painted across the chest by the "
                  "artist and stays part of torso.png, since the chest behind "
                  "it only exists as that arm."),
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
    print("arm_joints " + json.dumps(arm_joints))


if __name__ == "__main__":
    build()
