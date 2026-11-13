"""Put the 3D stages' own preview picture back in their sprite sheets.

The three Storms stages ship with a preview sprite (9000,1) drawn from the same
scene they play in: the floating island, the chained arch and the blue medallion.
An earlier pass painted a flat sea horizon over it, and when the stages went back
to their 3D models the wall kept showing that horizon - pictures of a map that no
longer exists.

So the pack's own picture comes back, written into all three sheets because the
rain pass is the same island under a different sky. The card the wall draws is
baked from this sprite by tools/build_stage_wall.py, so run that afterwards.

Run: python3 tools/build_stage3d_previews.py && python3 tools/fit_stage_previews.py
     && python3 tools/build_stage_wall.py

The fitter is not optional: this writes the pack's 240x100 picture back, which is
the wrong shape for the VS screen's 1215x398 card, and the fitter is what refits
it. tools/build_all.py runs both.
"""

from __future__ import annotations

import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "art_src", "stages", "third_heights_preview.png")
STAGES = ("stage3d", "stage3d_outline", "stage3d_rain")
PREVIEW = ((9000, 1), (9000, 0))


def main():
    src = Image.open(SOURCE).convert("RGBA")
    for name in STAGES:
        path = os.path.join(ROOT, "stages", name + ".sff")
        _data, sprites, pals = sff.read_sff(path)
        out, replaced = [], set()
        for sp in sprites:
            key = (sp["group"], sp["number"])
            if key in PREVIEW:
                out.append({"group": key[0], "number": key[1], "image": src})
                replaced.add(key)
            else:
                out.append(sp)
        for key in PREVIEW:
            if key not in replaced:
                out.append({"group": key[0], "number": key[1], "image": src})
        with open(path, "wb") as handle:
            handle.write(sff.write_sff(out, pals))
        print("%s: preview sprite set from %s" % (name, os.path.basename(SOURCE)))


if __name__ == "__main__":
    main()
