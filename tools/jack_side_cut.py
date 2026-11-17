"""Cut Jack's SIDE-VIEW part set from the hand-cut profile render.

``side_parts.py`` cuts the old side set from the third panel of the photographic
turnaround by knocking a studio background out of a JPEG. That art is gone: the
fighters are built from the new renders now, and the render that faces right
(``jack faceing right.png``) arrives as RGBA with the alpha already painted,
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
                   "jack faceing right.png")
OUT = os.path.join(ROOT, "art_src", "chars", "jackburton", "parts_side")

# Joints in the cut's own pixels, read off the grid over the cut.
NECK = (493, 230)
# The arm's socket, measured INSIDE the deltoid rather than on its outer edge.
# The skeleton hangs the arm from this point and the piece pivots on it, so it
# has to be both a plausible joint and the point the art draws the arm around:
# taken out on the deltoid's rim it is neither, and the arm then swings its own
# shoulder away from the body, leaving a wedge of air at the armpit.
SHOULDER_N = (598, 285)          # raised arm, image right, drawn right of centre
ELBOW_N = (743, 495)             # its elbow, at the bottom of the biceps
WRIST_N = (728, 395)             # the crease under the fist, not the knuckles
SHOULDER_F = (238, 285)          # the arm across the chest, image left
HIP_N = (563, 695)
KNEE_N = (738, 1000)
ANKLE_N = (708, 1285)
HIP_F = (353, 695)
KNEE_F = (238, 995)
ANKLE_F = (113, 1295)
SOLE = 1517
HIP_MID = (458, 695)

# A part box clips one limb out of the cut; the joint is where it hangs from.
# How far a shin laps over its knee, in art pixels. A shin box starts a little
# above the joint so the two pieces overlap at rest, and that overlap is a
# straight edge cut through the jeans: they are the same pixels in the same
# place while the leg stands as drawn, so nothing shows, but a bent knee swings
# the thigh's cut and the shin's cut apart and the thigh's face of the cut
# stands out behind the knee as a flat tab of denim. A disc centred ON the joint
# is the one shape a rotation about that joint cannot move, so the shin's own
# denim covers the fold at every angle a pose can ask for.
# How far the thigh stops short of the knee, in art pixels, so that the shin's
# lap (which is the bigger circle) covers its edge. See _thigh_mask.
KNEE_CUT = 38
KNEE_LAP = 46


BOXES = {
    # stops under the chin: the tank strap starts around y=286 and a head part
    # that clips it pastes a vest shoulder under his jaw when the head turns
    "head": (298, 0, 568, 250),
    # The box takes the near shoulder cap with it (out to 760), and starts above
    # the collar (180) so the trapezius is the body's: stopping at the near arm's
    # inner edge left a hole at the armpit the moment the arm swung forward, and
    # starting at 240 left a notch of background behind the jaw, because the head
    # part stops at the throat.
    # right edge past the whole deltoid: at 628 the box cut the shoulder cap in
    # half, and the arm - which swings around that cap - left the cut showing as
    # a gap of background between his vest and his own bicep.
    "torso": (0, 0, 895, 695),
    # THROUGH the shoulder cap, so the piece owns the deltoid it swings from. Cut
    # under the cap the arm had nothing over its socket, and every pose that
    # swung it out left the bicep floating beside a bare shoulder.
    "arm_n": (528, 230, 808, 555),
    # The hip band, kept INSIDE the denim. A box wide enough to take the body's
    # own outline at this height also takes his fists - they hang at his hips -
    # and the piece then has wings that are not his body at all. Cut inside the
    # denim instead, every edge of the piece is a seam on jeans of the same
    # colour, and it cannot stick out of the hip when a leg swings away.
    "pelvis": (308, 650, 608, 752),
    # Leg boxes lap upwards past their joint. The two drawn legs are not the
    # same length (the stance is three-quarter, so the far one is foreshortened)
    # and the skeleton carries one thigh and one shin for both, so the piece
    # that ends short has to be covered by the piece below it, not left with a
    # gap. They start at the hip line, not at the waist: a thigh that carried
    # the belt swung it out of the hip on every step.
    "thigh_n": (448, 685, 798, 1025),
        # x1 covers the whole toe: the boot reaches x=890 and the old edge at 808 cut
    # the front of the foot off square, which read as a boot with no toes.
    # The top stops KNEE_LAP above the knee, because the piece carries a disc of
    # that radius on the joint (see _shin_mask).
    "shin_n": (608, KNEE_N[1] - KNEE_LAP, 892, 1531),
    "thigh_f": (158, 685, 478, 1025),
    # The far leg is the wide one below the knee: its inner edge is still at
    # x=304 on row 985 and does not come in past 268 until well down the shin.
    # Cut at 268 the shin could not cover the bottom corner of the thigh piece,
    # which laps down to y=1025 with a square cut - so that corner stuck out
    # past the shin as a flat blue tab of denim behind his knee.
    "shin_f": (3, KNEE_F[1] - KNEE_LAP, 310, 1531),
}

JOINTS = {
    "head": NECK,
    "torso": (HIP_MID[0], 695),
    "arm_n": SHOULDER_N,
    "pelvis": (455, 640),
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
CROTCH_X = 428

# Rig units per art pixel. The old side set drew the figure about 550 rig units
# tall on a 640x780 canvas from a 648px crop; this art is 1485px tall, so the
# same size on screen needs about this much per pixel.
SCALE = 0.368

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
    # Real white only: saturation under 26 and every channel over 150. The old
    # test took anything merely neutral, which is most of the lit skin of a neck,
    # and punched holes in it - the torso's copy of that skin showed through them
    # slightly displaced and the seam came out as brickwork of pale rectangles.
    for y in range(int(h * 0.60), h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a and max(r, g, b) - min(r, g, b) < 26 and min(r, g, b) > 150:
                px[x, y] = (0, 0, 0, 0)
    return part


def _arm_mask(cut, box):
    """The arm inside its box, taken by its own colour.

    The arm is the only warm thing in its box: the tank top, the print and the
    background are all cool or neutral. Taking the arm as "everything that is not
    vest" is how this used to work, and on this render a slab of the vest that is
    not joined to the box's edge survived the walk - the piece then carried a
    flat pale shape that swung out with the arm as a ghost of it.

    Warm is r - b >= 18, which the arm's own highlights pass (they are lit skin,
    not lit cloth) and the vest cannot. Dark pixels are kept only when they are
    not blue, so the outline comes with the arm and the blue print does not.
    """
    x0, y0, x1, y1 = box
    m = Image.new("L", cut.size, 0)
    mp = m.load()
    px = cut.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b, a = px[x, y]
            if a < 40:
                continue
            warm = r - b >= 18
            # A dark pixel is only the arm's own outline if it is still WARM. The
            # old test allowed near-neutral darks, and the tank top's shadowed
            # folds are exactly that: they joined the arm's mask, and because the
            # mask lives in a box, every one of them dragged the box's straight
            # edges with it as a slab of chest across the vest when the arm moved.
            dark = max(r, g, b) < 120 and r > b + 8
            if warm or dark:
                mp[x, y] = 255
    # Grow over the antialiased outline, then stay inside the box.
    m = m.filter(ImageFilter.MaxFilter(5))
    inside = Image.new("L", cut.size, 0)
    ImageDraw.Draw(inside).rectangle([x0, y0, x1 - 1, y1 - 1], fill=255)
    return ImageChops.multiply(m, inside)


def _warm_mask(cut, box):
    """Skin in the box: the arm's own flesh, without the cloth it was cut with."""
    x0, y0, x1, y1 = box
    m = Image.new("L", cut.size, 0)
    mp = m.load()
    px = cut.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b, a = px[x, y]
            if a >= 40 and r - b >= 18:
                mp[x, y] = 255
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


def _torso_mask(cut, head_mask=None):
    """The body from the shoulders down to the waistband, no further.

    The top edge used to be a straight line across the chest at the collar, and
    that line is the cut the eye finds: it runs across his neck and shoulder,
    where the body carries on above it, so the moment the torso leans it swings
    out from under the head as a cut corner on his chest. The piece now starts up
    at the shoulders and is shaped by the head's own mask instead - the head part
    draws exactly that shape, so at rest the seam is nothing, and small head
    angles slide inside its overlap.

    The bottom is cut at the waist for the same reason: the torso LEANS, and a
    wedge of hip denim below this line swung out of his belt as a hard edged flap
    on every step. The waistband is the piece there, cut from the same denim.
    """
    x0, y0, x1, y1 = BOXES["torso"]
    cut_at = 738
    m = Image.new("L", cut.size, 0)
    ImageDraw.Draw(m).rectangle([x0, y0, x1 - 1, cut_at - 1], fill=255)
    # The body keeps its own head, and the head piece is drawn over it. Cutting a
    # head shaped hole in the body was tried twice - exact, and with a lap - and
    # both leave something: the hole shows as a black crescent at the nape the
    # moment he turns his head, and growing the head to cover it drags the art's
    # shadow ring with it. Skin over skin is invisible; a hole in him is not.
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


def _close_mask(m):
    """Fill the holes inside a mask.

    The arm mask is grown by walking the vest in from the box's border, and a
    bright highlight on the forearm passes for vest: the walk eats into the arm
    and leaves islands of BACKGROUND inside it. Those holes are not vest, they
    are arm - left unfilled, the pixels inside them stay in the torso, and the
    drawn guard arm hangs there as a ghost of its own forearm on every punch.
    Only holes are closed, so the mask's outer edge is untouched.
    """
    w, h = m.size
    px = m.load()
    seen = bytearray(w * h)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if px[x, y] < 128 and not seen[y * w + x]:
                seen[y * w + x] = 1
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if px[x, y] < 128 and not seen[y * w + x]:
                seen[y * w + x] = 1
                q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < w and 0 <= ny < h):
                continue
            i = ny * w + nx
            if seen[i] or px[nx, ny] >= 128:
                continue
            seen[i] = 1
            q.append((nx, ny))
    out = m.copy()
    op = out.load()
    for y in range(h):
        for x in range(w):
            if not seen[y * w + x] and px[x, y] < 128:
                op[x, y] = 255
    return out


def _head_mask(cut, grow=0):
    """The head, the mullet and the throat - and nothing that is cloth.

    The box runs left past the jaw to keep the hair, which also takes in the top
    of the trapezius, the collar and the strap of the vest. Left in, they hung off
    the skull and turned with it: a slab of shoulder and tank top beside his jaw,
    which is most of what "his head is cut off" looks like.
    """
    x0, y0, x1, y1 = BOXES["head"]
    m = Image.new("L", cut.size, 0)
    d = ImageDraw.Draw(m)
    # Above the jaw, the whole box: skull, face and the sweep of the mullet.
    d.rectangle([x0, y0, x1 - 1, 211], fill=255)
    # Below it, a band that follows the throat back from the chin. The head has to
    # keep the throat - it is the only art that reaches from the jaw down into the
    # body, and cutting at the jaw line leaves the skull floating over a gap - but
    # a full width rectangle here also took the collar and the front of the vest.
    d.polygon([(x0, 211), (512, 211), (472, NECK[1] + 8), (x0, NECK[1] + 8)],
              fill=255)
    # Skin, hair and outline only, over the whole head: the vest is neutral and
    # passes neither test, so no fabric can swing with his head. Eyes and teeth
    # fail the test as well, so holes INSIDE that skin-and-hair shape are closed -
    # but only those. Closing the box shape instead filled the air under his jaw
    # right across to the shoulder, which came out as a slab of neck on his chest.
    flesh = Image.new("L", cut.size, 0)
    px = cut.load()
    fp = flesh.load()
    for y in range(y0, min(NECK[1] + 9, cut.height)):
        for x in range(x0, min(x1, cut.width)):
            r, g, b, a = px[x, y]
            if a > 40 and (r - b >= 18 or (max(r, g, b) < 120 and r > b + 8)):
                fp[x, y] = 255
    flesh = _close_mask(flesh)
    # The head laps over the body's own cut: the body is cut away in the shape of
    # this mask, so at rest the seam is nothing, but the head turns a couple of
    # degrees in most poses and the body does not, which is enough to open a
    # crescent of background along his jaw. Grown by a few pixels the head covers
    # the edge of the hole at any small angle, and the ring it gains is skin and
    # hair either way, because only those pass the test. `grow` is 0 for the hole
    # the body is cut with, so the body is never cut away further than the head
    # itself reaches - that left a dark tab of background at the nape.
    if grow:
        m = m.filter(ImageFilter.MaxFilter(grow))
    # No feather on the bottom edge. It used to fade from y=196 - the MOUTH - so
    # the chin and the whole throat came out half transparent and his head ended
    # at the jaw: a hard cut across the neck is exactly what that looked like.
    # The band stops inside the body's own neck instead, on solid skin.
    return ImageChops.multiply(m, flesh)


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
    # From ABOVE the hip line, so the piece runs up behind the hip band. Cut 40px
    # below the joint it started where the band ends, and the strip between them
    # was the stage: his legs read as two pieces floating under his jeans.
    d.rectangle([box[0], hip[1] - 26, box[2], box[3]], fill=255)
    # the lap: a disc on the joint. A band above the joint turns with the leg
    # and swings a corner of denim out of the hip; a disc is unchanged by any
    # rotation about its own centre, so it can only ever cover the seam.
    # The near hip is the one the torso's waistband cut runs across, so its lap
    # is a full palm wide: the band must not be left to cover that seam alone,
    # or it is the band's static denim that shows when the leg swings.
    lap = 30 if name == "thigh_n" else 24
    d.ellipse([hip[0] - lap, hip[1] - lap, hip[0] + lap, hip[1] + lap], fill=255)
    # The bottom is a circle about the KNEE, not the straight line of the box.
    # That line is a cut across the jeans: hidden behind the shin while the leg
    # stands as drawn, but a bent knee swings the two cuts apart and the thigh's
    # face of it is a flat slab of denim standing out behind the knee - the
    # blue paint he had in the crouch. A circle about the knee cannot move when
    # the shin turns about that same point, and the shin laps over it with a
    # bigger one (KNEE_LAP), so the seam stays under denim at every angle.
    knee = JOINTS["shin_" + name[-1]]
    d.ellipse([knee[0] - KNEE_CUT, knee[1] - KNEE_CUT,
               knee[0] + KNEE_CUT, knee[1] + KNEE_CUT], fill=0)
    if name == "thigh_n":
        d.rectangle([0, 0, CROTCH_X, cut.height], fill=0)
    else:
        d.rectangle([CROTCH_X, 0, cut.width, cut.height], fill=0)
    return m


def _shin_mask(cut, name):
    """The shin from its knee down, lapped over the knee with a disc.

    See KNEE_LAP: the box alone is a straight cut across the jeans, and a bent
    knee opens it. The disc is centred on the joint the piece pivots on, so it
    turns with the shin and still covers exactly the same ground.
    """
    box = BOXES[name]
    knee = JOINTS[name]
    m = Image.new("L", cut.size, 0)
    d = ImageDraw.Draw(m)
    d.rectangle([box[0], box[1], box[2] - 1, box[3] - 1], fill=255)
    d.ellipse([knee[0] - KNEE_LAP, knee[1] - KNEE_LAP,
               knee[0] + KNEE_LAP, knee[1] + KNEE_LAP], fill=255)
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

    # Only fill where there is BODY to fill. The arm is cut out of the torso, and
    # the arm sticks out past his ribs - so the hole is arm-shaped and reaches
    # into air where the body never was. Filled, that overhang is a pale ghost of
    # the arm hanging off his chest in every pose that throws the arm forward.
    # The body's own span on each row - its leftmost and rightmost solid pixel
    # that is NOT arm - is where the filling may go: the arm's protrusion lies
    # outside that span, the chest behind the arm lies inside it.
    spans = {}
    for y in range(y0, y1):
        xs = [x for x in range(x0, x1)
              if sp[x, y][3] > 40 and hp[x, y] < 128]
        if xs:
            spans[y] = (min(xs), max(xs))
    holes = {(x, y) for x, y in holes
             if y in spans and spans[y][0] <= x <= spans[y][1]}
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
    # Blur the hole to lose the ruled edge, but keep the blur INSIDE the hole. A
    # six pixel blur also paints cloth six pixels outside the arm's footprint,
    # i.e. over the shoulder art beside it, which is the pale haze that made his
    # far shoulder look cut off from his neck.
    limit = mask.filter(ImageFilter.MaxFilter(5))
    mask = ImageChops.darker(mask.filter(ImageFilter.GaussianBlur(6)), limit)

    shade = Image.new("RGBA", src.size, cloth + (255,))
    spx = shade.load()
    # Row by row, take the cloth the vest has on that same row to the left of the
    # hole: the light falls across his chest, so a single flat tone reads as a
    # card however well its average matches. Darker where the row is darker.
    row_col = {}
    for y in rows:
        tot, n = [0, 0, 0], 0
        for x in range(x0, min(x1, x0 + 440), 3):
            if (x, y) in holes or not solid(x, y):
                continue
            r, g, b, a = sp[x, y]
            if min(r, g, b) > 120 and max(r, g, b) - min(r, g, b) < 60:
                tot[0] += r
                tot[1] += g
                tot[2] += b
                n += 1
        row_col[y] = tuple(v // n for v in tot) if n >= 4 else cloth
    for x, y in holes:
        c = row_col[y]
        spx[x, y] = (c[0], c[1], c[2], 255)
    # Feathering the mask pushes its soft edge past the body's own outline, so
    # the fill would paint cloth into the air beside his chest - a pale smear
    # along his ribs in every pose. Clip it to the silhouette it is filling.
    mask = ImageChops.multiply(mask, src.getchannel("A"))
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
    if mask is not None:
        # ... and keep the mask's own softness. The island mask is a threshold, so
        # on its own it re-hardens a feathered cut into a staircase edge.
        alpha = ImageChops.multiply(alpha, mask.crop(box))
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


# No alignment offset: the coordinates below are measured on THIS render, off a
# grid laid over it. They were once the previous render's, and that render drew a
# much larger head, so every joint above the waist sat about a hundred pixels too
# low - the head cut through his chest and the neck cut reached his sternum.
ALIGN = (0, 0)


def build():
    cut = Image.open(ART).convert("RGBA")
    # Trim on a real threshold: the render carries a few rows of near-transparent
    # fringe, and getbbox() on raw alpha counts it, so the frame's origin would
    # drift with the fringe instead of sitting on the figure.
    bb = cut.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox()
    if bb:
        cut = cut.crop(bb)
    if ALIGN != (0, 0):
        frame = Image.new("RGBA", (cut.width + ALIGN[0], cut.height + ALIGN[1]),
                          (0, 0, 0, 0))
        frame.alpha_composite(cut, ALIGN)
        cut = frame

    # The arm is cut out of the body, not copied on top of it: a body that kept
    # its own copy showed a second bicep on the chest wherever the arm swung
    # away, and painting that copy over with cloth only traded it for a pale
    # patch with a hard edge. He has air there, and the arm is drawn into it.
    arm = _close_mask(_arm_mask(cut, BOXES["arm_n"]))
    # A round pad of his own shoulder skin, centred ON the socket. The piece is
    # rotated about that point, so a disc there is unchanged by any rotation: it
    # covers the joint at every angle. Without it the arm's drawn shoulder cap
    # swings away from the body's and leaves a gap between bicep and vest on every
    # punch, which is what made the arm look pinned on rather than joined.
    PAD = 104
    pad = Image.new("L", cut.size, 0)
    ImageDraw.Draw(pad).ellipse([SHOULDER_N[0] - PAD, SHOULDER_N[1] - PAD,
                                 SHOULDER_N[0] + PAD, SHOULDER_N[1] + PAD],
                                fill=255)
    pad = ImageChops.multiply(
        pad, _warm_mask(cut, (SHOULDER_N[0] - PAD, SHOULDER_N[1] - PAD,
                              SHOULDER_N[0] + PAD, SHOULDER_N[1] + PAD)))
    # The piece is not clipped down to the limb. It was, while the arm rotated:
    # anything above the socket turned with it and dragged a slab of trapezius on
    # to his chest. The arm is held at its drawn angle now, so the piece is the
    # arm as drawn - and clipping it here only put a straight edge across his
    # collar, where the arm's shoulder cap meets the vest.
    arm = ImageChops.lighter(arm, pad)
    # The body the arm is drawn over does not exist in the photo, so the torso is
    # cut from a copy of the art whose arm has been replaced by the fabric around
    # it. The arm part still covers its own hole exactly at rest.
    # Only the arm's SKIN is taken out of the body, not the cloth it was cut
    # with: the vest under his arm is still there in the picture, and cutting the
    # arm's whole silhouette out of the torso left a hole shaped exactly like an
    # arm - filled flat, it read as a pale ghost of the arm pasted on his chest
    # every time the real one reached out.
    # ... and only the arm BELOW its socket: the deltoid stays on the body. The
    # arm piece carries the cap too, so at rest the two are the same pixels in the
    # same place - but when the arm swings forward the body still has a shoulder
    # there instead of a hole the arm had to cover.
    skin = ImageChops.multiply(arm, _warm_mask(cut, BOXES["arm_n"]))
    ax0, ay0, ax1, ay1 = BOXES["arm_n"]
    below = Image.new("L", cut.size, 0)
    ImageDraw.Draw(below).rectangle([ax0, SHOULDER_N[1] + 96, ax1, ay1], fill=255)
    skin = ImageChops.multiply(skin, below)
    # And then actually take it out. This said "no fill" and cut the torso from
    # the untouched art, so the body kept the drawing of the arm underneath the
    # arm - at rest the two were the same pixels in the same place, and the moment
    # the arm moved he had one and a half arms: the swinging piece plus its own
    # sleeve still lying on his chest. Erased with the same mask the arm piece
    # carries, so the hole and the piece are one shape and the piece fills it
    # exactly at rest; where the arm swings away, the air that is left is the gap
    # a punching arm actually has between the bicep and the vest.
    # Not erased. Erasing the arm out of the body was tried and it cannot be made
    # to look like anything: the art has no paint behind the arm, so whatever
    # fills the hole is invented - a blurred smudge, or a hard edged strip of
    # vest - and it only shows when the arm moves anyway. The arm is drawn as part
    # of the body instead and the poses hold it still, so the two drawings are
    # always the same pixels in the same place and there is nothing to ghost.
    body = cut

    head_cut = _head_mask(cut)               # the part
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
            mask = head_cut
        elif name in ("thigh_n", "thigh_f"):
            mask = _thigh_mask(cut, name)
        elif name in ("shin_n", "shin_f"):
            mask = _shin_mask(cut, name)
        src = body if name == "torso" else cut
        parts[name], pivots[name], offsets[name] = _part(src, name, mask)

    # The knife sprite the old set produced is still drawn by the Knife Toss
    # state; the new art's hands are empty, so there is nothing to re-cut.
    for keep in ("prop_knife.png",):
        if os.path.isfile(os.path.join(OUT, keep)):
            parts["prop_knife"] = Image.open(os.path.join(OUT, keep)).convert("RGBA")
            pivots["prop_knife"] = [round(parts["prop_knife"].width * 0.55, 1),
                                    round(parts["prop_knife"].height * 0.08, 1)]
    # No arm part. It is drawn on the body, and a rigid arm on a body that leans
    # cannot be a separate piece: the same angle about the hip (the body) and
    # about the socket (the arm) are the same rotation around two different
    # points, which is a rotation plus a slide - so the piece sat a few pixels off
    # its own copy and the two upper arms showed at once. What is left is nothing
    # to draw: the body already has him.
    parts["arm_n"] = Image.new("RGBA", (2, 2), (0, 0, 0, 0))
    pivots["arm_n"] = [1, 1]
    # No head part either. A head on a body it is welded to is either doubled -
    # the piece turned a few degrees off its own drawn face - or cut with a hole
    # that shows as black at the nape. Drawn as one piece with the body, his head
    # is simply his head, and it cannot be cut off at the neck because nothing
    # cuts it.
    parts["head"] = Image.new("RGBA", (2, 2), (0, 0, 0, 0))
    pivots["head"] = [1, 1]
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
        "torso_len": round((JOINTS["torso"][1] - 236) * SCALE, 1),
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
        # NO arm_joints: the arm is cut and posed as ONE piece. Cut at the elbow
        # it came apart - the forearm piece drew pale over the bicep on every
        # extended punch - and the drawn guard already has the elbow bent, so a
        # second joint buys nothing the art does not already show.
        "arm_joints": None,
        "one_piece_arms": True,
        "hand_pieces": HAND_PIECES,
        # Both thighs are cut with a lap disc on their own hip and the hip band
        # sits between them, so the hip joints have no air to weld: welded, the
        # capsule is a dark stripe across the jeans every time he leans. The
        # shoulder is the same story from the other side: the arm's art already
        # covers its own socket, so the weld has no air to close and instead
        # washes a skin tinted sash over the soft edge of his vest.
        # The head's throat column already reaches up under the jaw and the torso
        # keeps its own collar, so the neck has no air to weld either: the capsule
        # is a skin-tinted wedge that hangs beside his throat and swings with his
        # head - the translucent spike that read as his head coming off.
        # The arm is one continuous piece of art cut at the elbow, so the weld
        # across that cut has nothing to fill - and welded it paints a pale
        # capsule over the joint that stretches into a ghost of the arm the
        # moment the elbow bends.
        # The shins are off too. A weld is a capsule through the joint filled
        # with the limb's own colour, and for a shin that capsule runs down past
        # the ankle; clipped to the air around the boot it painted a rounded pad
        # of boot leather under the sole and out past the toe. Jack's boot is
        # drawn whole - knee to sole in one piece - so there is no seam for a
        # weld to close, and the pad was the second boot standing behind his.
        "welds_off": ["thigh_n", "thigh_f", "shin_n", "shin_f", "head", "torso",
                      "arm_n", "arm_f", "uarm_n", "farm_n", "uarm_f", "farm_f"],
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
        "_note": ("Side set cut from jack faceing right.png, the right-facing "
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
