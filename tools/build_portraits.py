"""Generate the select-screen portraits the screenpack asks for.

The pre-match screens read every fighter's portrait out of its own SFF:
sprite 9000,0 for the roster cell and 9000,1 for the big VS art (system.def
[Select Info] ``portrait.spr``). A character baked straight from the puppet rig
has no portraits at all - its SFF only holds poses - so its cell and its VS art
come up as the engine's "?" placeholder. This renders them from the fighter's
own standing frame, at the same sizes and axis as the rest of the roster, and
mirrors each stage's 9000,1 preview to 9000,0 so either index resolves.

Run:  python3 tools/build_portraits.py
"""

from __future__ import annotations

import glob
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Same shapes the engine's own roster uses: a 25x25 cell and a 120x140 VS art,
# with the axis at the sprite's top-left (as the engine art is).
# The cell art is painted at the grid cell size so it can be drawn at scale 1
# with the axis at the sprite corner, which is how the engine lays out its own
# 25x25 portraits in a 24px cell.
CELL = (120, 120)
BUST = 100                 # the bust sits inside the cell bevel
SIDE = (300, 520)          # the tall art shown beside the grid
BIG = (120, 140)
AXIS = (0, 0)


def standing_frame(d, sprites, palettes):
    """The fighter's own idle art: the largest sprite in group 0."""
    best = None
    for sp in sprites:
        if sp["group"] != 0:
            continue
        if best is None or sp["w"] * sp["h"] > best["w"] * best["h"]:
            best = sp
    if best is None:
        return None
    img = sff.decode_sprite(d, best, palettes)
    box = img.getchannel("A").getbbox()
    return img.crop(box) if box else None


def fit(img, size, head=False):
    """Contain ``img`` in ``size``, bottom-aligned, on a transparent canvas."""
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    if head:
        # the cell is a bust shot: take the top of the figure
        keep = max(1, int(img.height * 0.45))
        img = img.crop((0, 0, img.width, keep))
    k = min(size[0] / float(img.width), size[1] / float(img.height))
    img = img.resize((max(1, int(round(img.width * k))),
                      max(1, int(round(img.height * k)))), Image.LANCZOS)
    out.alpha_composite(img, ((size[0] - img.width) // 2, size[1] - img.height))
    return out


def cell_art(img):
    """The roster cell: a head-and-shoulders crop centred on the cell plate."""
    out = Image.new("RGBA", CELL, (0, 0, 0, 0))
    bust = img.crop((0, 0, img.width, max(1, int(img.height * 0.52))))
    k = min(BUST / float(bust.width), BUST / float(bust.height))
    bust = bust.resize((max(1, int(round(bust.width * k))),
                        max(1, int(round(bust.height * k)))), Image.LANCZOS)
    out.alpha_composite(bust, ((CELL[0] - bust.width) // 2,
                               (CELL[1] - bust.height) // 2))
    return out


def patch_character(path):
    """Rebuild the cell and VS portraits from the idle frame.

    They are rewritten every build rather than only when missing: the cell size
    lives in the screenpack, so a portrait left over from an older cell size is
    worse than no portrait at all.
    """
    d, sprites, palettes = sff.read_sff(path)
    standing = standing_frame(d, sprites, palettes)
    if standing is None:
        print(f"  {os.path.relpath(path, ROOT)}: no group-0 art, skipped")
        return False

    # Pick a source with real pixels. The base roster is a recoloured copy of
    # Kung Fu Man, whose own portrait is pristine PNG8 art, so it is decoded
    # with this fighter's palette. Anything that already has a portrait of its
    # own (the rig fighters) uses its standing frame instead.
    base_sff = os.path.join(ROOT, "chars", "kfm", "kfm.sff")
    source = None
    if len(palettes) > 1 and os.path.isfile(base_sff) and \
            os.path.abspath(base_sff) != os.path.abspath(path):
        bd, base_sprites, _bp = sff.read_sff(base_sff)
        rec = {(sp["group"], sp["number"]): sp
               for sp in base_sprites}.get((9000, 1))
        if rec is not None:
            source = sff.decode_sprite(bd, rec, palettes).convert("RGBA")
    if source is None:
        source = standing
    box = source.getchannel("A").getbbox()
    if box:
        source = source.crop(box)

    cell = cell_art(source)
    side = fit(source, SIDE)
    out = [{"group": sp["group"], "number": sp["number"], "raw": sp["raw"],
            "format": sp["format"], "depth": sp["depth"], "w": sp["w"],
            "h": sp["h"], "axis": sp["axis"], "pal": sp["pal"],
            "link": sp["link"]}
           for sp in sprites
           if (sp["group"], sp["number"]) not in ((9000, 0), (9000, 1))]
    out.append({"group": 9000, "number": 0, "image": cell, "axis": AXIS})
    out.append({"group": 9000, "number": 1, "image": fit(source, BIG),
                "axis": AXIS})
    out.append({"group": 9000, "number": 2, "image": side, "axis": AXIS})

    blob = sff.write_sff(out, [p["rgba"] for p in palettes] if palettes else [])
    with open(path + ".tmp", "wb") as f:
        f.write(blob)
    os.replace(path + ".tmp", path)
    print(f"  portraits rebuilt in {os.path.relpath(path, ROOT)}")
    return True


def patch_stage(path):
    """Mirror a stage's 9000,1 preview to 9000,0, which some motifs ask for."""
    d, sprites, palettes = sff.read_sff(path)
    have = {(sp["group"], sp["number"]): sp for sp in sprites}
    if (9000, 1) not in have or (9000, 0) in have:
        return False

    preview = sff.decode_sprite(d, have[(9000, 1)], palettes)
    out = [{"group": sp["group"], "number": sp["number"], "raw": sp["raw"],
            "format": sp["format"], "depth": sp["depth"], "w": sp["w"],
            "h": sp["h"], "axis": sp["axis"], "pal": sp["pal"],
            "link": sp["link"]} for sp in sprites]
    out.append({"group": 9000, "number": 0, "image": preview,
                "axis": have[(9000, 1)]["axis"]})
    blob = sff.write_sff(out, [p["rgba"] for p in palettes] if palettes else [])
    with open(path + ".tmp", "wb") as f:
        f.write(blob)
    os.replace(path + ".tmp", path)
    print(f"  mirrored 9000,1 -> 9000,0 in {os.path.relpath(path, ROOT)}")
    return True


def main():
    changed = 0
    for path in sorted(glob.glob(os.path.join(ROOT, "chars", "*", "*.sff"))):
        changed += bool(patch_character(path))
    for path in sorted(glob.glob(os.path.join(ROOT, "stages", "*.sff"))):
        changed += bool(patch_stage(path))
    print(f"portraits: {changed} file(s) updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
