"""Cut Jack's new forward-view render out of its backdrop, for the portraits.

The new concept renders (concept_art/fighters/jack_burton/jack_faceing_*.png)
arrive on a painted backdrop, not as transparent PNGs on a studio sweep, so they
cannot be used the way the old turnaround was.

The cut that comes out clean is a plain rectangle initialisation: GrabCut is
told the figure is inside a tight box and nothing outside it is, and it finds
the silhouette itself. Two leaner variants were tried and both failed - seeding
GrabCut with the art's alpha as probable-foreground kept the smoky backdrop and
the metal floor (the backdrop is blue-leaning in exactly the way the floor is,
so a colour rule cannot tell them apart), and seeding from the border model ate
Jack's shadowed legs. So the rectangle does the segmenting, and the alpha the
art carries is then applied last, as a straight cut: it clears only the gap
between his legs, which is the one place GrabCut fills in and should not.

The right-facing render does not separate at all: its rock field is rgb(6,7,11),
Jack's shadowed jeans are rgb(27,33,47) and his boot shadow rgb(24,13,10). That
view needs the same treatment this one got before the fight poses are rebuilt.

Output: art_src/chars/jackburton/work/portrait.png (alpha cut, trimmed to the
figure). tools/build_portraits.py prefers it over work/front.png.

Run:  python3 tools/jack_portrait_cut.py
"""

import os

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SRC = os.path.join(ROOT, "concept_art", "fighters", "jack_burton",
                   "jack_faceing_farward.png")
OUT = os.path.join(ROOT, "art_src", "chars", "jackburton", "work", "portrait.png")


def matte(path):
    bgr = cv2.imread(path)
    raw = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    h, w = bgr.shape[:2]
    given = raw[:, :, 3] if raw.shape[2] == 4 else np.full((h, w), 255, np.uint8)

    mask = np.zeros((h, w), np.uint8)
    rect = (int(w * 0.05), int(h * 0.01), int(w * 0.90), int(h * 0.96))
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(bgr, mask, rect, bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
    keep = np.where((mask == 1) | (mask == 3), 1, 0).astype(np.uint8)

    lab, n = ndimage.label(keep)
    if n:
        sizes = ndimage.sum(keep, lab, range(1, n + 1))
        keep = (lab == (np.argmax(sizes) + 1)).astype(np.uint8)
    keep = ndimage.binary_fill_holes(keep).astype(np.uint8)
    keep = ndimage.binary_closing(keep, np.ones((3, 3))).astype(np.uint8)
    # the artist's own cut, applied after the hole filling it would undo
    keep[given < 20] = 0
    alpha = (ndimage.gaussian_filter(keep.astype(np.float32), 0.7) * 255)
    alpha = alpha.clip(0, 255).astype(np.uint8)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(np.dstack([rgb, alpha]), "RGBA")


def cut():
    art = matte(SRC)
    box = art.getchannel("A").getbbox()
    if box:
        art = art.crop(box)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    art.save(OUT)
    return art


if __name__ == "__main__":
    im = cut()
    print(f"  portrait cut {im.width}x{im.height} -> {os.path.relpath(OUT, ROOT)}")
