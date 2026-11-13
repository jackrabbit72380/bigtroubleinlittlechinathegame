"""Cut the 3-D Lab's own picture for the select screen out of its concept render.

The concept art ships one 1280x960 render of the room with two cartoon stand-ins
standing on the floor as scale references. A card is 3:1, so the wall either
crops that render through the middle - which slices the stand-ins in half and
shows their heads and shoulders at the card's edges - or it uses a band chosen
on purpose. This cuts the band above them: the tanks, the reactor and the
ceiling panels, which is the room the fighters stand in.

The crop is found, not guessed: the stand-ins are the only strongly pink thing
in a red-and-steel room, so the band ends ten pixels above the first row that
carries them, and runs three-to-one back from there.

Run: python3 tools/build_lab3d_preview.py && python3 tools/build_stage_wall.py
(part of tools/build_all.py)
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "concept_art", "stages", "lab3dstage", "LAB.sff")
TARGET = os.path.join(ROOT, "stages", "lab3d.sff")
PORTRAIT = ((9000, 1), (9000, 0))


def stand_ins_top(img):
    """The first row that carries the cartoon stand-ins, or None if none do."""
    w, h = img.size
    px = img.load()
    for y in range(h):
        hits = 0
        for x in range(0, w, 4):
            r, g, b = px[x, y][:3]
            if r > 190 and 90 < g < 200 and 100 < b < 210 and r - g > 45 and r - b > 30:
                hits += 1
                if hits > 3:
                    return y
    return None


def main():
    data, sprites, pals = sff.read_sff(SOURCE)
    source = [s for s in sprites if (s["group"], s["number"]) == (9000, 1)]
    if not source:
        raise SystemExit("lab3d: %s has no 9000,1 to cut the card from" % SOURCE)
    full = sff.decode_sprite(data, source[0], pals).convert("RGBA")
    w, h = full.size
    band = w // 3
    top_of_stand_ins = stand_ins_top(full)
    bottom = (top_of_stand_ins - 10) if top_of_stand_ins else h
    y1 = max(band, min(bottom, h))
    y0 = max(0, y1 - band)
    card = full.crop((0, y0, w, y0 + band))

    _old, target_sprites, target_pals = sff.read_sff(TARGET)
    out, replaced = [], set()
    for sp in target_sprites:
        key = (sp["group"], sp["number"])
        if key in PORTRAIT:
            out.append({"group": key[0], "number": key[1], "image": card})
            replaced.add(key)
        else:
            out.append(sp)
    for key in PORTRAIT:
        if key not in replaced:
            out.append({"group": key[0], "number": key[1], "image": card})
    blob = sff.write_sff(out, [q["rgba"] for q in (target_pals or [])])
    if blob[:12] != sff.SIG:
        raise SystemExit("lab3d: refusing to write a sprite sheet with no signature")
    with open(TARGET + ".tmp", "wb") as handle:
        handle.write(blob)
    os.replace(TARGET + ".tmp", TARGET)
    print("  lab3d: card picture %dx%d cut from %dx%d at row %d"
          % (card.width, card.height, w, h, y0))


if __name__ == "__main__":
    main()
