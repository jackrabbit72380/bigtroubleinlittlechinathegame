"""Write every sprite a stage draws out as a PNG, ready to open in Photoshop.

A stage's art is not a picture on disk: it is packed into stages/<id>.sff, and
stages/<id>.def decides which sprite goes where with ``spriteno = group,index``
inside each ``[BG ...]`` section. This unpacks those sprites so they can be
edited, and writes a manifest of which layer uses which file and where it sits.

Usage:

    python3 tools/dump_stage_art.py                     # every stage
    python3 tools/dump_stage_art.py porkchop_express    # one stage
    python3 tools/dump_stage_art.py lopans_throne chinatown_alley

Output goes to artifacts/stage_art/<stage id>/:

    g0_0.png, g14_0.png, ...   one PNG per sprite, named <group>_<index>
    layers.txt                 the layer list: sprite, position, layer order

On Windows, "Dump Stage Art.bat" in the project root runs this and opens the
folder for you, so it can be double-clicked from Explorer.

Sprites are written at their native size with their transparency intact, so a
layer can be painted and packed back into the stage without rescaling it.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGES = os.path.join(ROOT, "stages")
OUT = os.path.join(ROOT, "artifacts", "stage_art")

# A [BG ...] block: its key = value lines, in file order.
BLOCK = re.compile(r"^\[(?P<header>[^\]]+)\][ \t]*$", re.MULTILINE)
FIELD = re.compile(r"^[ \t]*(?P<key>[A-Za-z0-9_.]+)[ \t]*=[ \t]*(?P<value>[^;\r\n]*)",
                   re.MULTILINE)


def stage_ids(argv):
    """Every stage with a .def and a .sff, or just the ones asked for."""
    have = sorted(f[:-4] for f in os.listdir(STAGES) if f.endswith(".def"))
    if not argv:
        return [s for s in have
                if os.path.isfile(os.path.join(STAGES, s + ".sff"))]
    missing = [a for a in argv if a not in have]
    if missing:
        raise SystemExit("no such stage: " + ", ".join(missing)
                         + "\nstages: " + ", ".join(have))
    return list(argv)


def layers(def_path):
    """The [BG ...] blocks, each as a dict of its own keys."""
    text = open(def_path, encoding="utf-8", errors="replace").read()
    heads = list(BLOCK.finditer(text))
    out = []
    for i, head in enumerate(heads):
        header = head.group("header").strip().lower()
        if not header.startswith("bg") or header == "bgdef":
            continue
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        body = text[head.end():end]
        keys = {m.group("key").lower(): m.group("value").strip()
                for m in FIELD.finditer(body)}
        out.append({"name": head.group("header").strip(), **keys})
    return out


def dump_stage(sid, out_root):
    sff_path = os.path.join(STAGES, sid + ".sff")
    raw, sprites, palettes = sff.read_sff(sff_path)
    out_dir = os.path.join(out_root, sid)
    os.makedirs(out_dir, exist_ok=True)

    by_id = {(sp["group"], sp["number"]): sp for sp in sprites}
    written = {}
    for key, sp in by_id.items():
        img = sff.decode_sprite(raw, sp, palettes)
        name = "g%d_%d.png" % key
        img.save(os.path.join(out_dir, name))
        written[key] = (name, img.width, img.height)

    rows = []
    for layer in layers(os.path.join(STAGES, sid + ".def")):
        sprite = layer.get("spriteno", "")
        match = re.match(r"\s*(\d+)\s*,\s*(\d+)", sprite)
        key = (int(match.group(1)), int(match.group(2))) if match else None
        if key is None or key not in written:
            rows.append((layer["name"], sprite or "(none)", "", "", "",
                         "MISSING"))
            continue
        name, w, h = written[key]
        rows.append((layer["name"], sprite, name, layer.get("start", ""),
                     layer.get("layerno", "0"),
                     "%dx%d" % (w, h)))

    with open(os.path.join(out_dir, "layers.txt"), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write("# %s - sprites and the layers that draw them\n" % sid)
        fh.write("# start is the sprite's top-left in stage space; layerno 0 is\n"
                 "# behind the fighters, 1 or 2 in front of them.\n")
        fh.write("%-22s %-10s %-12s %-18s %-8s %s\n"
                 % ("layer", "spriteno", "file", "start", "layerno", "size"))
        for row in rows:
            fh.write("%-22s %-10s %-12s %-18s %-8s %s\n" % row)

    print("  %-20s %2d sprites -> %s"
          % (sid, len(written), os.path.relpath(out_dir, ROOT)))
    return len(written)


def main(argv):
    if not os.path.isdir(STAGES):
        raise SystemExit("stages/ is missing - run this from the project")
    ids = stage_ids(argv)
    total = 0
    for sid in ids:
        total += dump_stage(sid, OUT)
    print("%d sprites from %d stage(s) in %s"
          % (total, len(ids), os.path.relpath(OUT, ROOT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
