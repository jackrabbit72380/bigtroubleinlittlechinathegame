"""Cut Jack's chest emblem out of the concept art.

The demon-in-the-pink-sun graphic only exists in the repo printed on a white
tank-top mock-up (concept_art/fighters/jack_burton), so it has to be keyed off
the fabric before it can be put on the puppet rig's chest.

A brightness key does not work: the shirt is shaded across its folds and has
JPEG noise in it, so any threshold loose enough to keep the print's pale cyan
leaves a grey rectangle of shirt behind it. What actually separates the two is
colour, not lightness - every part of the print is either saturated (pink sun,
cyan robe, jade dragons) or near-black ink, while every part of the shirt is
neutral. The mask is built on that, then cleaned up:

* specks smaller than MIN_AREA are dropped, which takes the JPEG mottling out
  of the shirt without touching the print;
* light areas fully enclosed by the print are put back, so the pale panels
  inside the graphic (the mask's face, the ear plates) stay solid.

Output is art_src/chars/jackburton/ref/emblem.png, which tools/jack_parts.py
picks up for the torso. Deterministic from the committed mock-up.
"""

import os
from collections import deque

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SRC = os.path.join(ROOT, "concept_art", "fighters", "jack_burton",
                   "il_1588xN.2963586700_ro5b.jpg")
OUT = os.path.join(ROOT, "art_src", "chars", "jackburton", "ref", "emblem.png")

# The print, in pixels of the 1588x1588 mock-up. Generous on every side; the
# alpha bounding box trims it afterwards.
BOX = (498, 488, 1068, 1122)

SAT_MIN = 30        # a pixel this colourful is print, whatever its lightness
INK_MAX = 110       # a pixel this dark is line work, whatever its colour
MIN_AREA = 400      # connected specks smaller than this are shirt mottling


def _mask(px, w, h):
    """Print or shirt, per pixel, on colour rather than brightness."""
    keep = bytearray(w * h)
    for y in range(h):
        row = y * w
        for x in range(w):
            r, g, b = px[x, y]
            if max(r, g, b) - min(r, g, b) >= SAT_MIN or max(r, g, b) <= INK_MAX:
                keep[row + x] = 1
    return keep


def _drop_specks(keep, w, h):
    """Zero every connected run of keep-pixels below MIN_AREA."""
    seen = bytearray(w * h)
    for start in range(w * h):
        if not keep[start] or seen[start]:
            continue
        run, dq = [], deque([start])
        seen[start] = 1
        while dq:
            i = dq.popleft()
            run.append(i)
            y, x = divmod(i, w)
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < w and 0 <= ny < h:
                    j = ny * w + nx
                    if keep[j] and not seen[j]:
                        seen[j] = 1
                        dq.append(j)
        if len(run) < MIN_AREA:
            for i in run:
                keep[i] = 0
    return keep


def _fill_enclosed(keep, w, h):
    """Put back light areas the print closes around: reach them from the
    border; anything the border cannot reach is inside the graphic."""
    outside = bytearray(w * h)
    dq = deque()
    for x in range(w):
        for y in (0, h - 1):
            i = y * w + x
            if not keep[i] and not outside[i]:
                outside[i] = 1
                dq.append(i)
    for y in range(h):
        for x in (0, w - 1):
            i = y * w + x
            if not keep[i] and not outside[i]:
                outside[i] = 1
                dq.append(i)
    while dq:
        i = dq.popleft()
        y, x = divmod(i, w)
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h:
                j = ny * w + nx
                if not keep[j] and not outside[j]:
                    outside[j] = 1
                    dq.append(j)
    for i in range(w * h):
        if not outside[i]:
            keep[i] = 1
    return keep


def cut():
    src = Image.open(SRC).convert("RGB").crop(BOX)
    w, h = src.size
    px = src.load()
    keep = _fill_enclosed(_drop_specks(_mask(px, w, h), w, h), w, h)
    out = src.convert("RGBA")
    op = out.load()
    for y in range(h):
        row = y * w
        for x in range(w):
            if not keep[row + x]:
                op[x, y] = (0, 0, 0, 0)
    box = out.getbbox()
    if box:
        out = out.crop(box)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out.save(OUT)
    return out


if __name__ == "__main__":
    im = cut()
    print(f"  emblem: {im.width}x{im.height} cut from "
          f"{os.path.relpath(SRC, ROOT)} -> {os.path.relpath(OUT, ROOT)}")
