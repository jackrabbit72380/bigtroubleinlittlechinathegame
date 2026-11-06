"""Put leather on the boot reference renders.

The boot art arrives as untextured clay: boots_front.png is 8-bit grey, and
boots_back.png is RGB but measures rgb(67,67,67) across the frame, so neither
carries any leather. The colour is not invented - it is sampled off the boot in
the new Jack render, where the leather sits at rgb(66,39,27), its highlights at
rgb(110,73,56) and its shadows at rgb(49,28,19).

Every clay pixel keeps its own shading - the pebbled grain, the stitched seams,
the button caps, the treaded sole - and is mapped onto that ramp. Each render's
own tonal range is stretched first, because a clay render is mostly mid-grey and
a straight mapping would land nearly every pixel on the same leather tone and
flatten the boot back out.

Written beside the originals under art_src/chars/jackburton/ref/, and the same
ramp is what tools/jack_parts.py paints the in-game boots with, so the reference
and the rig agree on the colour.

Run:  python3 tools/boot_paint.py
"""

import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SRC = os.path.join(ROOT, "concept_art", "fighters", "jack_burton")
OUT = os.path.join(ROOT, "art_src", "chars", "jackburton", "ref")

# leather, sampled from the boot in jack_faceing_farward.png (t, rgb)
RAMP = [(0.00, (26, 14, 9)),
        (0.18, (49, 28, 19)),
        (0.45, (66, 39, 27)),
        (0.75, (110, 73, 56)),
        (1.00, (150, 108, 80))]


def _ramp(t):
    t = max(0.0, min(1.0, t))
    for i in range(1, len(RAMP)):
        t0, c0 = RAMP[i - 1]
        t1, c1 = RAMP[i]
        if t <= t1:
            k = (t - t0) / (t1 - t0 or 1.0)
            return tuple(int(round(c0[j] + (c1[j] - c0[j]) * k)) for j in range(3))
    return RAMP[-1][1]


def paint(path):
    clay = Image.open(path).convert("L")
    w, h = clay.size
    px = list(clay.getdata())
    solid = sorted(px)
    lo = solid[int(len(solid) * 0.02)]
    hi = solid[int(len(solid) * 0.98)] or (lo + 1)
    span = float(max(1, hi - lo))
    out = Image.new("RGB", (w, h))
    out.putdata([_ramp((v - lo) / span) for v in px])
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    for name in ("boots_front.png", "boots_back.png"):
        src = os.path.join(SRC, name)
        if not os.path.isfile(src):
            print(f"  {name}: not in the concept folder, skipped")
            continue
        img = paint(src)
        dest = os.path.join(OUT, name)
        img.save(dest)
        print(f"  {name}: {img.width}x{img.height} -> {os.path.relpath(dest, ROOT)}")


if __name__ == "__main__":
    main()
