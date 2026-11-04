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
import re
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
# The grid's cell is 74px now that the roster is ten across, and the standing
# art beside it gets a 222px column; painting the art at the column width is
# what keeps the whole fighter visible instead of cropped by the frame.
CELL = (74, 74)            # the grid's cell, in build_select_grid.py
BUST = 66                  # the bust sits inside the cell bevel
SIDE = (214, 600)          # the tall art shown beside the grid
BIG = (120, 140)
AXIS = (0, 0)

# [Info] localcoord of the screenpack these portraits are drawn in.
MOTIF_LOCALCOORD = 1280


def char_localcoord(def_path):
    """The character's own coordinate space; MUGEN's default is 320x240."""
    try:
        body = open(def_path, encoding="utf-8", errors="replace").read()
    except OSError:
        return 320
    found = re.search(r"^\s*localcoord\s*=\s*(\d+)", body, re.M | re.I)
    return int(found.group(1)) if found else 320


def portrait_sizes(sff_path):
    """Sprite sizes that land on the intended on-screen size.

    The engine multiplies a portrait's scale by motif.localcoord / the
    character's localcoord (src/motif.go: Scale = cfg.Scale * portraitscale *
    motif.Localcoord[0] / char.localcoord[0]). Painting every fighter at 120px
    therefore drew the 320x240 base roster at 4x - 480px cells and 1200px side
    art, blowing far outside their boxes - while the 960x720 rigs only reached
    1.33x. The art has to be painted at target / factor so both end up the same
    size on screen.
    """
    factor = MOTIF_LOCALCOORD / float(char_localcoord(sff_path[:-4] + ".def"))

    def scaled(size):
        return (max(1, int(round(size[0] / factor))),
                max(1, int(round(size[1] / factor))))

    return scaled(CELL), scaled(BIG), scaled(SIDE)


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
    """Scale by height, crop width: every fighter ends up the same size.

    Containing the figure in the box (the old behaviour) made the apparent size
    depend on how wide the fighter happened to be: Lo Pan's cape and the
    Chings' shoulder props are much wider than Jack, so ``min(w/W, h/H)``
    shrank them and the grid showed a row of characters at different sizes.
    Scaling to the box height and cropping the surplus width keeps the heads
    and bodies identical from fighter to fighter, which is what a roster grid
    is for. Only the sides are ever cropped, and the figure is centred first.
    """
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    if head:
        # the cell is a bust shot: take the top of the figure
        keep = max(1, int(img.height * 0.45))
        img = img.crop((0, 0, img.width, keep))
    if img.width < 1 or img.height < 1:
        return out
    k = size[1] / float(img.height)
    keep = min(img.width, max(1, int(round(size[0] / k))))
    left = (img.width - keep) // 2
    img = img.crop((left, 0, left + keep, img.height))
    img = img.resize((max(1, int(round(img.width * k))), size[1]), Image.LANCZOS)
    out.alpha_composite(img, ((size[0] - img.width) // 2, 0))
    return out


def cell_art(img, cell=CELL):
    """The roster cell: a head-and-shoulders crop centred on the cell plate.

    Same height rule as fit(): the bust fills the plate vertically so no head
    in the grid is smaller than its neighbour.
    """
    bust_target = max(1, int(round(cell[0] * BUST / float(CELL[0]))))
    bust = img.crop((0, 0, img.width, max(1, int(img.height * 0.52))))
    art = fit(bust, (bust_target, bust_target))
    # the sprite itself stays the size of the grid cell: the engine draws it at
    # scale 1, so a 63px canvas would land 84px on screen instead of the 84 the
    # cell is. It used to be 100, which is 16px wider than the cell it is
    # clipped to and is why every portrait hung over its neighbour's frame.
    out = Image.new("RGBA", cell, (0, 0, 0, 0))
    out.alpha_composite(art, ((cell[0] - art.width) // 2,
                              (cell[1] - art.height) // 2))
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
    # A rig character cut from a turnaround leaves its whole figure in
    # art_src/<id>/work/front.png. That figure has no seams, so portraits are
    # painted from it rather than from a reassembled idle frame whose limb
    # joints can show as notches.
    char_id = os.path.basename(os.path.dirname(path)).replace("_rig", "")
    front = os.path.join(ROOT, "art_src", "chars", char_id, "work", "front.png")
    source = None
    if os.path.isfile(front):
        source = Image.open(front).convert("RGBA")
    # Every fighter paints its portraits from its own art now. There used to be
    # a branch here that took Kung Fu Man's 9000,1 and decoded it with this
    # fighter's palette, which was right while the roster *was* recoloured Kung
    # Fu Man - the engine's portrait is pristine PNG8 art, better than a
    # reassembled idle frame. It stopped being right when the roster was rebaked
    # from the puppet rig, and nothing caught it because the branch fires for
    # every fighter carrying more than one palette, i.e. all of them. Every cell
    # in the grid was Kung Fu Man wearing a different outfit, which is what
    # "all the character pictures are gone" looks like on screen.
    if source is None:
        source = standing
    box = source.getchannel("A").getbbox()
    if box:
        source = source.crop(box)

    cell_size, big_size, side_size = portrait_sizes(path)
    cell = cell_art(source, cell_size)
    side = fit(source, side_size)
    out = [{"group": sp["group"], "number": sp["number"], "raw": sp["raw"],
            "format": sp["format"], "depth": sp["depth"], "w": sp["w"],
            "h": sp["h"], "axis": sp["axis"], "pal": sp["pal"],
            "link": sp["link"]}
           for sp in sprites
           if (sp["group"], sp["number"]) not in ((9000, 0), (9000, 1), (9000, 2))]
    out.append({"group": 9000, "number": 0, "image": cell, "axis": AXIS})
    out.append({"group": 9000, "number": 1, "image": fit(source, big_size),
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
