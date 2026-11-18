"""Write every sprite a fighter draws out as a PNG, ready to open in Photoshop.

A fighter's art is not a picture on disk: it is packed into the fighter's .sff,
and the .air decides which sprite goes where with ``group, index, x, y, time``
inside each ``[Begin Action N]``. This unpacks those sprites so they can be
looked at, and writes a manifest of which action draws which file and where.

With no arguments it dumps the roster in data/select.def - the fighters the game
actually plays. Name a folder to dump just that one.

Usage:

    python3 tools/dump_fighter_art.py                    # the whole roster
    python3 tools/dump_fighter_art.py jackburton_rig     # one fighter
    python3 tools/dump_fighter_art.py jackburton_rig lopan_rig

Output goes to artifacts/fighter_art/<fighter folder>/:

    g0_0.png, g20_0.png, ...   one PNG per sprite, named <group>_<index>
    actions.txt                every action, its frames, offsets and timings

On Windows, "Dump Fighter Art.bat" in the project root runs this and opens the
folder for you, so it can be double-clicked from Explorer.

Sprites are written at their native size with their transparency intact, so a
frame can be painted at that size and dropped into art_src/ for the rebuild.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARS = os.path.join(ROOT, "chars")
SELECT = os.path.join(ROOT, "data", "select.def")
OUT = os.path.join(ROOT, "artifacts", "fighter_art")

ROSTER_ENTRY = re.compile(r"^([A-Za-z0-9_]+)/([A-Za-z0-9_]+\.def)")
ACTION = re.compile(r"^\[Begin Action\s+(\d+)\]", re.I)
FRAME = re.compile(r"^(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)")
CLSN = re.compile(r"^Clsn(\d)", re.I)


def roster():
    """The [Characters] entries in select.def: (folder, def name) pairs."""
    text = open(SELECT, encoding="utf-8", errors="replace").read()
    if "[Characters]" not in text:
        raise SystemExit("data/select.def has no [Characters] section")
    block = text.split("[Characters]", 1)[1].split("\n[", 1)[0]
    out = []
    for raw in block.splitlines():
        line = raw.split(";", 1)[0].strip()
        m = ROSTER_ENTRY.match(line)
        if m and (m.group(1), m.group(2)) not in out:
            out.append((m.group(1), m.group(2)))
    if not out:
        raise SystemExit("data/select.def names no fighters")
    return out


def resolve(argv):
    """(folder, def name) for each argument, or the whole roster for none."""
    if not argv:
        return roster()
    out = []
    for arg in argv:
        arg = arg.replace("\\", "/").strip("/")
        folder, _, named = arg.partition("/")
        base = os.path.join(CHARS, folder)
        if not os.path.isdir(base):
            raise SystemExit("no such fighter folder: %s\nfighters: %s"
                             % (arg, ", ".join(f for f, _ in roster())))
        if not named:
            defs = sorted(f for f in os.listdir(base) if f.endswith(".def"))
            named = folder + ".def" if folder + ".def" in defs else (defs[0] if defs else "")
        if not named or not os.path.isfile(os.path.join(base, named)):
            raise SystemExit("%s has no character .def" % arg)
        out.append((folder, named))
    return out


def files(def_path):
    """The sprite and animation file a .def names, relative to its folder."""
    text = open(def_path, encoding="utf-8", errors="replace").read()
    if "[Files]" not in text:
        raise SystemExit("%s has no [Files] section" % def_path)
    block = text.split("[Files]", 1)[1].split("\n[", 1)[0]
    found = {}
    for m in re.finditer(r"(?im)^\s*(sprite|anim)\s*=\s*([^;\r\n]+)", block):
        found[m.group(1).lower()] = m.group(2).strip()
    missing = [k for k in ("sprite", "anim") if k not in found]
    if missing:
        raise SystemExit("%s has no %s line in [Files]"
                         % (def_path, " or ".join(missing)))
    return found["sprite"], found["anim"]


def actions(air_path):
    """Every [Begin Action] with its frames, collision boxes and timing."""
    text = open(air_path, encoding="utf-8-sig", errors="replace").read()
    out, cur = [], None
    for raw in text.splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        m = ACTION.match(line)
        if m:
            cur = {"number": int(m.group(1)), "frames": [], "clsn": {}}
            out.append(cur)
            continue
        if cur is None:
            continue
        c = CLSN.match(line)
        if c:
            key = line.split("=", 1)[0].strip()
            cur["clsn"][key] = cur["clsn"].get(key, 0) + 1
            continue
        f = FRAME.match(line)
        if f:
            cur["frames"].append({
                "group": int(f.group(1)), "index": int(f.group(2)),
                "x": int(f.group(3)), "y": int(f.group(4)),
                "time": int(f.group(5)),
            })
    return out


def dump_fighter(folder, def_name, out_root):
    base = os.path.join(CHARS, folder)
    def_path = os.path.join(base, def_name)
    sprite_name, anim_name = files(def_path)
    raw, sprites, palettes = sff.read_sff(os.path.join(base, sprite_name))
    acts = actions(os.path.join(base, anim_name))

    out_dir = os.path.join(out_root, folder)
    os.makedirs(out_dir, exist_ok=True)

    written = {}
    for sp in sprites:
        key = (sp["group"], sp["number"])
        if key in written:
            continue                 # a second copy of a slot paints the same art
        img = sff.decode_sprite(raw, sp, palettes)
        name = "g%d_%d.png" % key
        img.save(os.path.join(out_dir, name))
        written[key] = (name, img.width, img.height, sp["axis"])

    lines = [
        "# %s/%s - animations and the sprites they draw" % (folder, def_name),
        "# %d sprites, %d actions, all at native size with transparency intact."
        % (len(written), len(acts)),
        "# offset is the frame's position from the sprite's axis; time is in"
        " ticks (60 a second).",
        "",
    ]
    missing = 0
    for act in acts:
        total = sum(f["time"] for f in act["frames"])
        head = "[Action %d] %d frame%s, %d tick%s" % (
            act["number"], len(act["frames"]),
            "" if len(act["frames"]) == 1 else "s", total,
            "" if total == 1 else "s")
        if act["clsn"]:
            head += "  (" + ", ".join("%s x%d" % (k, v)
                                      for k, v in sorted(act["clsn"].items())) + ")"
        lines.append(head)
        for i, f in enumerate(act["frames"], 1):
            if f["group"] < 0:
                where = "%-16s" % "(keeps the previous sprite)"
            else:
                hit = written.get((f["group"], f["index"]))
                if hit is None:
                    missing += 1
                    where = "%-16s" % ("MISSING g%d_%d" % (f["group"], f["index"]))
                else:
                    where = "%-16s" % hit[0]
            lines.append("  frame %2d  %s offset %4d,%4d  time %2d"
                         % (i, where, f["x"], f["y"], f["time"]))
        lines.append("")

    with open(os.path.join(out_dir, "actions.txt"), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write("\n".join(lines))

    print("  %-22s %3d sprites, %3d actions%s -> %s"
          % (folder, len(written), len(acts),
             ", %d missing" % missing if missing else "",
             os.path.relpath(out_dir, ROOT)))
    return len(written), missing


def main(argv):
    if not os.path.isdir(CHARS):
        raise SystemExit("chars/ is missing - run this from the project")
    picks = resolve(argv)
    total = missing = 0
    for folder, def_name in picks:
        n, m = dump_fighter(folder, def_name, OUT)
        total += n
        missing += m
    print("%d sprites from %d fighter(s) in %s%s"
          % (total, len(picks), os.path.relpath(OUT, ROOT),
             ", %d frame(s) name a sprite the file does not hold" % missing
             if missing else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
