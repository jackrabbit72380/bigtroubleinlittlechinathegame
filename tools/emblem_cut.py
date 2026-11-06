"""Cut Jack's chest emblem to a flat RGBA file the rig can paint from.

The source is the flat, high-resolution graphic in the concept folder: the
emblem on its own, transparent background, no fabric behind it. That is the art
the fighter is meant to be wearing, so all this does is trim it to its own
pixels and save it where tools/jack_parts.py and tools/jack_cut.py look for it.

Earlier this tool keyed the same design off a tank-top mock-up, because that was
the only copy in the repo; it needed a colour-based mask and a hole fill to get
a clean edge. None of that is needed now that the flat art exists, and it is
deliberately not kept: a key that is not used is a key that rots.

Output: art_src/chars/jackburton/ref/emblem.png
"""

import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SRC = os.path.join(ROOT, "concept_art", "fighters", "jack_burton",
                   "The emblem flat, on its own, at high resolution.png")
OUT = os.path.join(ROOT, "art_src", "chars", "jackburton", "ref", "emblem.png")


def cut():
    art = Image.open(SRC).convert("RGBA")
    box = art.getchannel("A").getbbox()
    if box:
        art = art.crop(box)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    art.save(OUT)
    return art


if __name__ == "__main__":
    im = cut()
    print(f"  emblem: {im.width}x{im.height} -> {os.path.relpath(OUT, ROOT)}")
