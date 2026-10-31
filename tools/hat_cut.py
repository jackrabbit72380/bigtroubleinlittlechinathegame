"""Cut Lightning's hat out of the HD render and restyle it for the sprite rig.

Every other part of Lightning is drawn by ``lightning_art.py``, but the hat is
the one piece that should come from the source art: it is a 3D render of the
real hat, and at hat size the banded weave and the straw fan survive the
reduction better than a redrawn copy did.

The render sits on a white plate, so the background is keyed out by how close a
pixel is to white, the result is cropped to the hat, scaled down, and then
snapped onto a short ramp of the same straw tones the rest of the art uses so
it sits next to the hand-drawn robe instead of looking pasted on. The blue
veins running over the weave are kept on their own small blue ramp.

Run:  python3 tools/hat_cut.py           (writes the cut and a size check)
      python3 tools/lightning_art.py     (uses it for the head)
"""

from __future__ import annotations

import os
import sys

from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "concept_art", "fighters", "lightning", "hat_hd7.png")
CUT = os.path.join(ROOT, "art_src", "chars", "lightning", "hat_cut.png")

# The straw ramp, darkest first. The last two tones are the lit top of the
# brim; the first two are the shadowed weave under the crown.
STRAW_RAMP = [
    (36, 26, 18),
    (74, 56, 34),
    (110, 86, 54),
    (146, 120, 80),
    (176, 152, 108),
    (206, 184, 140),
    (232, 214, 172),
]
# Where the lightning veins land: deep blue through to white-hot.
BOLT_RAMP = [
    (28, 62, 112),
    (52, 108, 176),
    (96, 164, 224),
    (168, 214, 248),
    (232, 248, 255),
]


def load_source():
    if not os.path.exists(SOURCE):
        raise SystemExit("hat source missing: %s" % SOURCE)
    return Image.open(SOURCE).convert("RGBA")


def matte(im):
    """Drop the white plate the hat was rendered on."""
    w, h = im.size
    px = im.load()
    mask = Image.new("L", (w, h), 0)
    mp = mask.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 8:
                continue
            # Straw is saturated; the plate is not. Anything whose darkest
            # channel is nearly white is background.
            if min(r, g, b) > 232:
                continue
            mp[x, y] = a
    # A pixel of erosion kills the pale halo the render left around the brim.
    mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.6))
    out = im.copy()
    out.putalpha(mask)
    return out


def cut(im=None):
    """Keyed, cropped hat at source resolution."""
    im = matte(im or load_source())
    box = im.getchannel("A").getbbox()
    if box is None:
        raise SystemExit("nothing left after keying the source")
    return im.crop(box)


def restyle(im):
    """Snap the render onto the sprite palette, keeping the veins blue."""
    w, h = im.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    src = im.load()
    dst = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = src[x, y]
            if a < 24:
                continue
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if b - r > 26 and b > 96:                       # lightning vein
                t = min(1.0, max(0.0, (lum - 90) / 140))
                ramp = BOLT_RAMP
            else:                                            # straw
                t = min(1.0, max(0.0, (lum - 34) / 200))
                ramp = STRAW_RAMP
            dst[x, y] = ramp[round(t * (len(ramp) - 1))] + (a,)
    return out


def hat(max_w, max_h):
    """The hat scaled to fit a box, bottom of the brim on the box's bottom.

    Returns an RGBA image at most ``max_w`` wide and ``max_h`` tall, with the
    hat's own proportions kept. Used by ``lightning_art.head``.
    """
    im = cut()
    scale = min(max_w / im.width, max_h / im.height)
    size = (max(1, round(im.width * scale)), max(1, round(im.height * scale)))
    small = im.resize(size, Image.LANCZOS)
    return restyle(small)


CONCEPT = os.path.join(ROOT, "concept_art", "fighters", "lightning",
                       "juan-ruiz-03.jpg")
ARC_CACHE = {}


def blue_mask(im):
    """Pixels that belong to the painted lightning: blue, and clearly bluer
    than the paper, the straw and the charcoal cloth around it."""
    w, h = im.size
    src = im.load()
    mask = bytearray(w * h)
    for y in range(h):
        row = y * w
        for x in range(w):
            r, g, b, a = src[x, y]
            if a < 8:
                continue
            if b - r > 34 and b > 96 and b - g > 6:
                mask[row + x] = 1
    return mask, w, h


def tint(piece):
    """Luminance onto the bolt ramp, so a cut arc matches the drawn effects."""
    w, h = piece.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    src, dst = piece.load(), out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = src[x, y]
            if a < 12:
                continue
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            t = min(1.0, max(0.0, (lum - 60) / 150))
            dst[x, y] = BOLT_RAMP[round(t * (len(BOLT_RAMP) - 1))] + (a,)
    return out


def arcs(count=4, min_pixels=90):
    """The lightning as it is painted in the concept, cut out of the picture.

    The arcs there are thin blue strokes over the figure; keying them by colour
    and keeping the connected strokes preserves the hand-drawn taper and the
    forked spurs that a redrawn polyline loses at sprite size. Each piece comes
    back recoloured onto the same bolt ramp the hat's veins use, so it sits in
    the same light as the rest of him.
    """
    key = (count, min_pixels)
    if key in ARC_CACHE:
        return ARC_CACHE[key]
    im = Image.open(CONCEPT).convert("RGBA")
    mask, w, h = blue_mask(im)
    seen = bytearray(w * h)
    comps = []
    neighbours = ((1, 0), (-1, 0), (0, 1), (0, -1),
                  (1, 1), (1, -1), (-1, 1), (-1, -1))
    for start in range(w * h):
        if not mask[start] or seen[start]:
            continue
        stack = [start]
        seen[start] = 1
        pts = []
        while stack:
            i = stack.pop()
            pts.append(i)
            x, y = i % w, i // w
            for dx, dy in neighbours:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    j = ny * w + nx
                    if mask[j] and not seen[j]:
                        seen[j] = 1
                        stack.append(j)
        if len(pts) >= min_pixels:
            comps.append(pts)
    comps.sort(key=len, reverse=True)
    out = []
    for pts in comps[:count]:
        xs = [i % w for i in pts]
        ys = [i // w for i in pts]
        box = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)
        m = Image.new("L", (w, h), 0)
        mp = m.load()
        for i in pts:
            mp[i % w, i // w] = 255
        piece = im.copy()
        piece.putalpha(m)
        out.append(tint(piece.crop(box)))
    ARC_CACHE[key] = out
    return out


if __name__ == "__main__":
    im = load_source()
    print("source", im.size, "alpha range",
          im.getchannel("A").getextrema())
    c = cut(im)
    print("cut", c.size, "aspect %.2f" % (c.width / c.height))
    c.save(CUT)
    print("wrote", os.path.relpath(CUT, ROOT))
    # size check: the hat at three widths, on a ground line, next to nothing
    tiles = []
    for w in (110, 132, 150):
        h = round(w * c.height / c.width)
        t = restyle(c.resize((w, h), Image.LANCZOS))
        tiles.append(t)
    pad = 8
    sheet = Image.new("RGBA", (sum(t.width for t in tiles) + pad * 4,
                               max(t.height for t in tiles) + pad * 2),
                      (24, 26, 33, 255))
    x = pad
    for t in tiles:
        sheet.alpha_composite(t, (x, sheet.height - pad - t.height))
        x += t.width + pad
    sheet.save(os.path.join(ROOT, "artifacts", "hat_cut_check.png"))
    print("wrote artifacts/hat_cut_check.png")
