"""Cut Jack's new forward-view render out of its backdrop, for the portraits.

The new concept renders (concept_art/fighters/jack_burton/jack_faceing_*.png)
arrive as flat RGB with a painted scene behind the figure, not as transparent
PNGs on a studio sweep, so they cannot be used the way the old turnaround was.
The forward render separates cleanly: its backdrop is a smooth dark gradient and
the figure is brightly rim-lit, which is exactly what GrabCut is good at.

The right-facing render does *not* separate, and this tool deliberately does not
pretend otherwise - its rock field is rgb(6,7,11) while Jack's jeans in shadow
are rgb(27,33,47) and his boot shadow is rgb(24,13,10). Background, jeans and
boots are the same value, so no colour or graph rule can tell them apart; that
view needs an upload with a transparent or plain background before the fight
poses are rebuilt from it.

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
    im = cv2.imread(path)
    h, w = im.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    rect = (int(w * 0.05), int(h * 0.01), int(w * 0.90), int(h * 0.96))
    cv2.grabCut(im, mask, rect, bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
    keep = np.where((mask == 2) | (mask == 0), 0, 1).astype(np.uint8)
    lab, n = ndimage.label(keep)
    if n:
        sizes = ndimage.sum(keep, lab, range(1, n + 1))
        keep = (lab == (np.argmax(sizes) + 1)).astype(np.uint8)
    keep = ndimage.binary_fill_holes(keep).astype(np.uint8)
    keep = ndimage.binary_closing(keep, np.ones((3, 3))).astype(np.uint8)
    alpha = (ndimage.gaussian_filter(keep.astype(np.float32), 0.7) * 255)
    alpha = alpha.clip(0, 255).astype(np.uint8)
    rgb = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
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
