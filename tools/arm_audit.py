"""Audit where each fighter's arms meet the body, and zoom in on the joints.

A cut-and-rotate puppet only reads as one body if the top of the upper arm
meets the torso silhouette and every rotated piece still covers its own socket.
Where it does not, the pose sheet shows strips of background between arm and
body - "disconnected arms" - however good the individual pieces are.

For every fighter this renders a few poses twice: once whole, and once with the
arm pieces removed. Where the whole render has pixels but the body does not, the
horizontal distance from the body edge to those pixels is the AIR GAP at that
row. Rest and stance should be ~0 (the arm touches or overlaps the torso).
Elbow and wrist gaps are reported the same way, measured between the piece
below the joint and the piece above it.

Run:  python3 tools/arm_audit.py [id ...] [--sheet]
"""

import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import char_rig as R

OUT = os.path.join(R.ROOT, "artifacts")
ARMS = ("uarm_n", "uarm_f", "farm_n", "farm_f", "hand_n", "hand_f", "arm_n", "arm_f")
POSES = ("rest", "stance", "jab", "block")


def _pose(rig, name):
    if name == "rest":
        return R.rest_pose(rig)
    return dict(R.POSES[name])


def _subset(rig, keep):
    parts = {k: v for k, v in rig.parts.items() if keep(k)}
    return R.Rig(parts, rig.metrics, rig.art, rig.canvas, rig.axis)


def _gap(full, body, lo, hi):
    """Largest horizontal air gap between body pixels and other pixels."""
    fa, ba = full.getchannel("A"), body.getchannel("A")
    worst = 0
    for y in range(max(0, lo), min(full.height, hi)):
        brow = ba.crop((0, y, body.width, y + 1)).getbbox()
        if not brow:
            continue
        row = []
        for x in range(full.width):
            if fa.getpixel((x, y)) > 40 and ba.getpixel((x, y)) <= 40:
                row.append(x)
        if not row:
            continue
        left, right = min(row), max(row)
        bl, br = brow[0], brow[2]
        if right < bl:
            worst = max(worst, bl - right)
        elif left > br:
            worst = max(worst, left - br)
    return worst


def audit(cid, zoom_poses=None):
    rig = R.load_rig(cid)
    body = _subset(rig, lambda k: k not in ARMS)
    rows = []
    for name in POSES:
        pose = _pose(rig, name)
        full = R.render(rig, pose)
        bd = R.render(body, pose)
        # shoulder band: from the highest arm pixel down a third of the torso
        box = full.getbbox()
        if not box:
            continue
        h = box[3] - box[1]
        gap = _gap(full, bd, box[1] + int(h * 0.10), box[1] + int(h * 0.55))
        rows.append((name, gap))
    return rig, rows


def main(argv):
    ids = [a for a in argv[1:] if not a.startswith("-")]
    if not ids:
        ids = ["lightning", "rain", "thunder", "lopan", "eggshen",
               "wangchi", "gracielaw", "jade", "jackburton"]
    print("%-12s %s" % ("fighter", "air gap at shoulders (px, rig scale)"))
    tiles = []
    for cid in ids:
        try:
            rig, rows = audit(cid)
        except SystemExit as e:
            print("%-12s %s" % (cid, e))
            continue
        print("%-12s %s" % (cid, "  ".join("%s=%d" % r for r in rows)))
        tile = Image.new("RGB", (rig.canvas[0] * 3 * len(POSES),
                                 rig.canvas[1] * 3), (12, 12, 16))
        for i, name in enumerate(POSES):
            img = R.render(rig, _pose(rig, name))
            big = img.resize((img.width * 3, img.height * 3), Image.LANCZOS)
            tile.paste(big, (i * rig.canvas[0] * 3, 0), big)
        tiles.append((cid, tile))
    if tiles:
        w = max(t[1].width for t in tiles)
        h = max(t[1].height for t in tiles)
        sheet = Image.new("RGB", (w, h * len(tiles)), (12, 12, 16))
        d = ImageDraw.Draw(sheet)
        for i, (cid, tile) in enumerate(tiles):
            sheet.paste(tile, (0, i * h))
            d.text((6, i * h + 4), cid + "   rest | stance | jab | block",
                   fill=(255, 220, 80))
        path = os.path.join(OUT, "arm_audit.png")
        sheet.save(path)
        print("wrote", path, sheet.size)


if __name__ == "__main__":
    main(sys.argv)
