"""Offline validation for the game data, so a typo does not wait for a playtest.

Checks, without launching the engine:
  * every select.def character and stage resolves to real files
  * character DEFs reference files that exist, and their SFF loads
  * every animation frame in each .air resolves to a sprite in the .sff
  * stage DEFs reference sprites that exist in their .sff, plus preview sprite
  * optional: roster palettes differ from the base character
  * the Windows launchers parse, and the rules that read them still fire

Run:  python3 tools/validate.py
"""

from __future__ import annotations

import re

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sff

def _portrait_sizes():
    import os, re
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "build_portraits.py"), encoding="utf-8") as f:
        body = f.read()
    def size(name):
        m = re.search(r"^%s = \((\d+), (\d+)\)" % name, body, re.M)
        return (int(m.group(1)), int(m.group(2)))
    return size("CELL"), size("BIG"), size("SIDE")


def _grid_cell():
    """The roster cell size, read from the grid generator.

    It was typed in here as 74 and stayed 74 when the grid was repainted, so a
    cell change failed validation on every fighter instead of checking anything.
    """
    import os, re
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "build_select_grid.py"), encoding="utf-8") as f:
        m = re.search(r"^CELL(?:, CELL_H)? = (\d+)(?:, (\d+))?", f.read(), re.M)
    return int(m.group(1)), int(m.group(2) or m.group(1))


CELL, CELL_H = _grid_cell()


def _grid_shape():
    """COLS and ROWS, read from the generator that lays the wall out."""
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "build_select_grid.py"), encoding="utf-8") as f:
        src = f.read()
    m = re.search(r"(?m)^COLS,\s*ROWS\s*=\s*(\d+),\s*(\d+)", src)
    if m is None:
        return 10, 5
    return int(m.group(1)), int(m.group(2))


COLS, ROWS = _grid_shape()
CELL_SIZE, BIG_SIZE, SIDE_SIZE = _portrait_sizes()
MOTIF_WIDTH = int(re.search(r"^\s*localcoord\s*=\s*(\d+)",
                  open(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir,
                       "data", "ikemen1", "system.def"), encoding="utf-8").read(),
                  re.M).group(1))



ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors = []
notes = []


def err(msg):
    errors.append(msg)


def read(path):
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        return f.read()


def ini_sections(text):
    """Very small INI reader: {section_lower: [(key_lower, value)]}."""
    out, cur = {}, None
    for raw in text.splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            cur = line[1:-1].strip().lower()
            out.setdefault(cur, [])
        elif "=" in line and cur:
            k, v = line.split("=", 1)
            out[cur].append((k.strip().lower(), v.strip()))
    return out


def resolve_char(entry):
    """'kfm' / 'kfm/alt.def' / 'zip.zip' -> (def path, folder)."""
    if entry.endswith(".zip"):
        return None, os.path.join(ROOT, "chars", entry)
    if "/" in entry:
        folder, name = entry.split("/", 1)
        return os.path.join(ROOT, "chars", folder, name), os.path.join(ROOT, "chars", folder)
    return (os.path.join(ROOT, "chars", entry, f"{entry}.def"),
            os.path.join(ROOT, "chars", entry))


def parse_roster(text):
    """Read [Characters] / [ExtraStages]: both are bare comma-separated lines."""
    section = None
    chars, stages = [], []
    for raw in text.splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            continue
        if line in ("{", "}") or line.lower().startswith(("slot", "skipslot", "dummyslot")):
            continue
        if section == "characters":
            if line.lower() == "randomselect":
                continue
            parts = [p.strip() for p in line.split(",")]
            chars.append((parts[0], parts[1] if len(parts) > 1 else ""))
        elif section == "extrastages":
            stages.append(line.split(",")[0].strip())
    return chars, stages


def check_select():
    text = read(os.path.join(ROOT, "data", "select.def"))
    chars, stages = parse_roster(text)

    if not chars:
        err("select.def: no characters found")
    for name, stage in chars:
        def_path, folder = resolve_char(name)
        if def_path is None:
            if not os.path.isdir(folder):
                err(f"select.def: missing zipped character {name}")
            continue
        if not os.path.isfile(def_path):
            err(f"select.def: missing character DEF {def_path}")
        if stage and stage != "random" and not os.path.isfile(os.path.join(ROOT, stage)):
            err(f"select.def: missing stage {stage} for {name}")

    for stage in stages:
        if not os.path.isfile(os.path.join(ROOT, stage)):
            err(f"select.def: missing extra stage {stage}")
    notes.append(f"select.def: {len(chars)} characters, {len(stages)} extra stages")
    return chars


def check_character(def_path, folder):
    text = read(def_path)
    secs = ini_sections(text)
    files = dict(secs.get("files", []))
    label = os.path.basename(def_path)

    for key in ("sprite", "anim", "cmd", "cns"):
        if key not in files:
            err(f"{label}: [Files] missing '{key}'")
            continue
        target = os.path.join(folder, files[key])
        if not os.path.isfile(target):
            err(f"{label}: {key} file missing: {files[key]}")

    sprite_name = files.get("sprite")
    anim_name = files.get("anim")
    if not (sprite_name and anim_name):
        return

    sff_path = os.path.join(folder, sprite_name)
    if not os.path.isfile(sff_path):
        return
    try:
        _d, sprites, palettes = sff.read_sff(sff_path)
    except Exception as exc:                              # noqa: BLE001
        err(f"{label}: cannot read {sprite_name}: {exc}")
        return
    have = {(sp["group"], sp["number"]) for sp in sprites}
    if not sprites:
        err(f"{label}: {sprite_name} has no sprites")
    if not palettes:
        err(f"{label}: {sprite_name} has no palettes (indexed art needs one)")

    # every animation frame must exist
    air_path = os.path.join(folder, anim_name)
    missing = set()
    frames = 0
    for raw in read(air_path).splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line or line.startswith("[") or line.lower().startswith("clsn"):
            continue
        m = re.match(r"^\s*(-?\d+)\s*,\s*(-?\d+)", line)
        if not m:
            continue
        frames += 1
        key = (int(m.group(1)), int(m.group(2)))
        # negative groups are engine placeholders (no sprite expected)
        if key[0] >= 0 and key not in have:
            missing.add(key)
    if missing:
        sample = ", ".join(f"{g},{n}" for g, n in sorted(missing)[:6])
        err(f"{label}: {len(missing)} animation sprites missing from {sprite_name} "
            f"(e.g. {sample})")
    notes.append(f"{label}: {len(sprites)} sprites, {len(palettes)} palettes, "
                 f"{frames} frame refs OK")
    return palettes


def check_stage(def_path):
    label = os.path.basename(def_path)
    text = read(def_path)
    secs = ini_sections(text)
    if "bgdef" not in secs:
        err(f"{label}: no [BGdef]")
        return
    files = dict(secs["bgdef"])
    spr = files.get("spr")
    if not spr:
        err(f"{label}: [BGdef] missing spr")
        return
    sff_path = os.path.join(os.path.dirname(def_path), spr)
    if not os.path.isfile(sff_path):
        err(f"{label}: sprite file missing: {spr}")
        return
    try:
        _d, sprites, _p = sff.read_sff(sff_path)
    except Exception as exc:                              # noqa: BLE001
        err(f"{label}: cannot read {spr}: {exc}")
        return
    have = {(sp["group"], sp["number"]) for sp in sprites}

    # A 3D stage has no sprite layers at all: the whole background is a
    # model file, so counting [BG*] spriteno sections says nothing about it.
    # Recognise the model and check that instead, or every 3D stage reads as
    # a stage with no background.
    model = files.get("model")
    layers = 0
    for section, entries in secs.items():
        if not section.startswith("bg"):
            continue
        opts = dict(entries)
        if "spriteno" not in opts:
            continue
        layers += 1
        g, n = [int(v.strip()) for v in opts["spriteno"].split(",")[:2]]
        if (g, n) not in have:
            err(f"{label}: [{section}] spriteno {g},{n} missing from {spr}")
    if (9000, 1) not in have:
        err(f"{label}: select-screen preview sprite 9000,1 missing")
    if model:
        model_path = os.path.join(os.path.dirname(def_path), model.strip())
        if not os.path.isfile(model_path):
            err(f"{label}: 3D model missing: {model.strip()}")
        notes.append(f"{label}: 3D stage ({model.strip()}), {len(sprites)} sprites")
    else:
        if layers == 0:
            err(f"{label}: no background layers defined")
        notes.append(f"{label}: {layers} layers, {len(sprites)} sprites")


def check_select_screen(chars):
    """The portrait grid painted by tools/build_select_grid.py."""
    def_text = read(os.path.join(ROOT, "data", "ikemen1", "system.def"))
    parts = def_text.split("[Select Info]", 1)
    if len(parts) < 2:
        err("system.def: no [Select Info] block")
        return
    body = parts[1].split("\n[", 1)[0]
    opts = {}
    for line in body.splitlines():
        if "=" in line and not line.strip().startswith(";"):
            key, value = line.split("=", 1)
            opts[key.strip().lower()] = value.split(";")[0].strip()

    if opts.get("rows") != str(ROWS) or opts.get("columns") != str(COLS):
        err("select screen: grid is %s rows by %s columns, expected %d by %d "
            "(%d cells for the whole cast plus the random box)"
            % (opts.get("rows"), opts.get("columns"), ROWS, COLS, ROWS * COLS))
    if opts.get("cell.size") != "%d,%d" % (CELL, CELL_H):
        err("select screen: cell.size is %r, expected %d,%d"
            % (opts.get("cell.size"), CELL, CELL_H))
    # Every roster line must land on the one page, or fighters exist but cannot
    # be picked.
    try:
        rows = int(opts.get("rows", 0))
        cols = int(opts.get("columns", 0))
        sel = read(os.path.join(ROOT, "data", "select.def"))
        entries = [ln for ln in sel.split("[Characters]", 1)[-1].split("[", 1)[0]
                   .splitlines()
                   if ln.strip() and not ln.strip().startswith(";")
                   and not ln.strip().startswith("def")]
        if rows and cols and len(entries) > rows * cols:
            err("select screen: %d roster lines but only %d cells, so %d "
                "character(s) cannot be selected"
                % (len(entries), rows * cols, len(entries) - rows * cols))
    except OSError:
        pass
    # start.lua's f_animGet indexes params.scale as a table for every portrait
    # group it loads, and the engine leaves scale nil for a group the screenpack
    # never defines - so a missing done/random/loading scale is a hard crash on
    # the key that draws it (selecting a fighter took the engine down at
    # start.lua:755), not a cosmetic default. Any group that exists must carry
    # a scale.
    for side in (1, 2):
        for base in ("face", "face2"):
            for state in ("done", "random", "loading", "slot"):
                prefix = "p%d.%s.%s." % (side, base, state)
                if (any(k.startswith(prefix) for k in opts)
                        and prefix + "scale" not in opts):
                    err("select screen: %s has no scale, and start.lua's "
                        "f_animGet indexes that as a table - it crashes the "
                        "engine when the group is drawn" % (prefix + "scale"))
            if "p%d.%s.scale" % (side, base) not in opts:
                err("select screen: p%d.%s.scale is missing" % (side, base))
    if opts.get("portrait.spr") != "9000,0":
        err("select screen: portrait.spr is %r, expected 9000,0" % opts.get("portrait.spr"))
    if "p1.face.window" not in opts or "p2.face.window" not in opts:
        err("select screen: the big side portraits have no window")

    # The VS screen loads its portraits the same way, out of its own section:
    # start.lua:4427 hands the player table itself to f_animGet as the animation
    # params, and hands the same table over again as the velocity source, then
    # swaps in pX.done once the order is confirmed. Every field that function
    # indexes therefore has to exist there too - choosing VS MODE took the
    # engine down at start.lua:755 because p1.done carried only its anim.
    vs_parts = def_text.split("[VS Screen]", 1)
    if len(vs_parts) < 2:
        err("system.def: no [VS Screen] block")
    else:
        vs = {}
        for line in vs_parts[1].split("\n[", 1)[0].splitlines():
            if "=" in line and not line.strip().startswith(";"):
                key, value = line.split("=", 1)
                vs[key.strip().lower()] = value.split(";")[0].strip()
        # Every group handed to f_animGet as `params` needs the drawing fields.
        # The groups handed over as `velParams` (the player table and face2)
        # need the motion tables as well: f_animGet indexes those on the
        # velocity source, not on the anim params.
        portrait_fields = ("scale", "facing", "xshear", "angle", "xangle",
                           "yangle", "projection", "focallength", "window",
                           "layerno")
        motion_fields = ("velocity", "maxdist", "accel", "friction")
        for side in ("p1", "p2"):
            for group in (side, side + ".done", side + ".face2",
                          side + ".face2.done"):
                for field in portrait_fields:
                    if "%s.%s" % (group, field) not in vs:
                        err("vs screen: %s.%s is missing, and start.lua's f_animGet "
                            "indexes it as a table when VS MODE builds the "
                            "portraits" % (group, field))
            # face2 has no motion tables to require: this build rejects
            # face2.velocity/maxdist/accel/friction at load, so the motif never
            # carried them and start.lua's pair() covers the nil.
            for group in (side,):
                for field in motion_fields:
                    if "%s.%s" % (group, field) not in vs:
                        err("vs screen: %s.%s is missing, and start.lua's f_animGet "
                            "indexes it on the velocity source when VS MODE "
                            "builds the portraits" % (group, field))
            for group in (side + ".face2", side + ".face2.done"):
                for field in ("anim", "spr"):
                    if "%s.%s" % (group, field) not in vs:
                        err("vs screen: %s.%s is missing, so start.lua indexes a "
                            "nil portrait group when VS MODE builds them"
                            % (group, field))

    # The "?" and loading art are drawn in the portrait panels; sharing the
    # panel window is what keeps them from spilling onto the grid.
    for side in ("p1", "p2"):
        panel = opts.get(side + ".face2.window")
        for state in ("random", "loading"):
            win = opts.get("%s.face2.%s.window" % (side, state))
            if panel and win != panel:
                err("select screen: %s.face2.%s.window is %r, expected the panel "
                    "window %r" % (side, state, win, panel))

    sff_path = os.path.join(ROOT, "data", "ikemen1", "system.sff")
    if not os.path.isfile(sff_path):
        err("select screen: data/ikemen1/system.sff is missing")
        return
    _d, sprites, _p = sff.read_sff(sff_path)
    have = {(sp["group"], sp["number"]): sp for sp in sprites}

    # The "?" and the loading art stand in for the big side portraits, so they
    # must draw inside the portrait rect. The engine scales a sprite's axis with
    # it, which is what pushed the stock 5x "?" out past the panel and left it
    # showing around the preview art.
    # 9000,2 covers the panel exactly: it is painted at twice SIDE_SIZE
    # (build_portraits.SIDE_RES) and drawn at face2.scale 0.5, so the screen
    # rect is SIDE_SIZE whichever way round the two numbers are.
    portrait = (float(SIDE_SIZE[0]), float(SIDE_SIZE[1]))
    for side, flip in (("p1", 1), ("p2", -1)):
        off = [float(v) for v in opts.get(side + ".face2.offset", "0,0").split(",")]
        px = off[0] if flip > 0 else off[0] - portrait[0]
        box = (px, off[1], px + portrait[0], off[1] + portrait[1])
        for state in ("random", "loading"):
            key = "%s.face2.%s" % (side, state)
            spr = [int(v) for v in opts.get(key + ".spr", "0,0").split(",")]
            hit = have.get((spr[0], spr[1]))
            if hit is None:
                continue
            so = [float(v) for v in opts.get(key + ".offset", "0,0").split(",")]
            ss = [float(v) for v in opts.get(key + ".scale", "1,1").split(",")]
            ax, ay = hit["axis"]
            rx = so[0] - ax * ss[0] if flip > 0 else so[0] + (ax - hit["w"]) * ss[0]
            ry = so[1] - ay * ss[1]
            rect = (rx, ry, rx + hit["w"] * ss[0], ry + hit["h"] * ss[1])
            if (rect[0] < box[0] - 1 or rect[1] < box[1] - 1
                    or rect[2] > box[2] + 1 or rect[3] > box[3] + 1):
                err("select screen: %s draws %d,%d-%d,%d, outside the portrait "
                    "rect %d,%d-%d,%d, so it shows around the preview art"
                    % ((key,) + tuple(int(v) for v in rect)
                       + tuple(int(v) for v in box)))

    for group, number in ((220, 0), (222, 0), (223, 0), (223, 1), (223, 2), (223, 3)):
        if (group, number) not in have:
            err("select screen: system.sff has no sprite %d,%d" % (group, number))
    bg = have.get((220, 0))
    want_bg = (MOTIF_WIDTH, MOTIF_WIDTH * 9 // 16)
    if bg and (bg["w"], bg["h"]) != want_bg:
        err("select screen: background is %dx%d, expected %dx%d"
            % (bg["w"], bg["h"], want_bg[0], want_bg[1]))
    if "spriteno = 220, 0" not in def_text:
        err("select screen: [SelectBGdef] does not draw the painted background")

    for name, _stage in chars:
        def_path, folder = resolve_char(name)
        if not (def_path and os.path.isfile(def_path)):
            continue
        files = dict(ini_sections(read(def_path)).get("files", []))
        char_sff = os.path.join(folder, files.get("sprite", ""))
        if not os.path.isfile(char_sff):
            continue
        _cd, char_sprites, _cp = sff.read_sff(char_sff)
        # The engine draws a portrait at scale * motif.localcoord / char
        # localcoord, so the size that matters is the one on screen, not the
        # one in the sheet: a 320x240 fighter's art is blown up 4x.
        lc_match = re.search(r"^\s*localcoord\s*=\s*(\d+)", read(def_path),
                             re.M | re.I)
        localcoord = int(lc_match.group(1)) if lc_match else 320
        factor = MOTIF_WIDTH / localcoord  # motif [Info] localcoord width
        # portrait.scale is what the screen draws the cell art at: it is painted
        # at twice the cell (build_portraits.CELL_RES) and drawn at 0.5, so the
        # screen size is the cell either way. The VS and side art draw at 1.
        cell_scale = [float(v) for v in opts.get("portrait.scale", "1,1").split(",")]
        side_scale = [float(v) for v in opts.get("p1.face2.scale", "1,1").split(",")]
        scales = {(9000, 0): cell_scale, (9000, 1): (1.0, 1.0),
                  (9000, 2): side_scale}
        want = {(9000, 0): CELL_SIZE, (9000, 1): BIG_SIZE,
                (9000, 2): SIDE_SIZE}
        for key, size in want.items():
            hit = {(sp["group"], sp["number"]): sp for sp in char_sprites}.get(key)
            if hit is None:
                err("%s: no portrait sprite %d,%d" % (name, key[0], key[1]))
                continue
            sc = scales[key]
            drawn = (hit["w"] * factor * sc[0], hit["h"] * factor * sc[1])
            if abs(drawn[0] - size[0]) > 4 or abs(drawn[1] - size[1]) > 4:
                err("%s: portrait %d,%d draws %dx%d on screen at localcoord %d, "
                    "expected %dx%d"
                    % (name, key[0], key[1], round(drawn[0]), round(drawn[1]),
                       localcoord, size[0], size[1]))
    notes.append("select screen: 10x5 portrait grid, " + str(CELL) + "px cells, framed sides; "
                 "every fighter carries 9000,0 cell art, 9000,1 VS art and "
                 "9000,2 side art")


def check_menu_theme():
    """Menus wear the title logo's face and its gold/red palette.

    tools/build_fonts.py installs Display/Body and retints system.def; this fails
    loudly if a regeneration left a font pointing at a file that is not shipped,
    or if any of the old blue/pink text colours survived.
    """
    path = os.path.join(ROOT, "data", "ikemen1", "system.def")
    if not os.path.isfile(path):
        err("menu theme: data/ikemen1/system.def is missing")
        return
    def_text = read(path)

    declared = {}
    for line in def_text.splitlines():
        m = re.match(r"^\s*(font\d+)\s*=\s*(\S+)", line, re.I)
        if m and not line.strip().startswith(";"):
            declared[m.group(1).lower()] = m.group(2)
    for key, rel in declared.items():
        if not (os.path.isfile(os.path.join(ROOT, "data", rel))
                or os.path.isfile(os.path.join(ROOT, "font", rel))):
            err("menu theme: %s points at %s, which is not shipped" % (key, rel))

    for name in ("Display", "Body"):
        fdef = os.path.join(ROOT, "data", "ikemen1", "fonts", name + ".def")
        if not os.path.isfile(fdef):
            err("menu theme: %s.def is missing" % name)
            continue
        body = read(fdef)
        f = re.search(r"^File\s*=\s*(\S+)", body, re.I | re.M)
        asset = os.path.join(os.path.dirname(fdef), f.group(1)) if f else ""
        if not f or not os.path.isfile(asset):
            err("menu theme: %s.def does not point at a shipped font file" % name)
            continue
        if re.search(r"^Type\s*=\s*bitmap", body, re.I | re.M):
            # baked glyphs: the gold face must actually be in the sheet
            if not asset.lower().endswith(".sff"):
                err("menu theme: %s.def is a bitmap font but does not ship a .sff" % name)
                continue
            _h, sheet, _pl = sff.read_sff(asset)
            codes = {sp["number"] for sp in sheet if sp["group"] == 0}
            missing = [c for c in range(65, 91) if c not in codes]
            if missing:
                err("menu theme: %s.sff has no glyphs for %s"
                    % (name, ", ".join(chr(c) for c in missing[:6])))
        elif not re.search(r"^Type\s*=\s*truetype", body, re.I | re.M):
            err("menu theme: %s.def is neither a bitmap nor a truetype font" % name)

    stale = [c for c in ("123,206,255", "255,210,239", "210,210,255", "0,247,247")
             if c in def_text]
    if stale:
        err("menu theme: system.def still uses the old menu colours (%s)"
            % ", ".join(stale))
    if declared.get("font10") is None or declared.get("font11") is None:
        err("menu theme: font10/font11 are not registered in [Files]")

    # Every "[* Pause Menu]" block needs its own geometry. The engine fills a
    # derived pause menu from its default motif, not from our [Pause Menu], so a
    # section that merely exists renders with the stock layout.
    sections, cur = {}, None
    for line in def_text.splitlines():
        head = re.match(r"^\s*\[([^\]]+)\]", line)
        if head:
            cur = head.group(1).strip()
            sections[cur] = set()
        elif cur is not None:
            key = re.match(r"^\s*([A-Za-z0-9_.]+)\s*=", line)
            if key:
                sections[cur].add(key.group(1))
    for name, keys in sections.items():
        if not name.lower().endswith("pause menu"):
            continue
        for need in ("menu.pos", "menu.item.spacing", "menu.item.font"):
            if need not in keys:
                err("menu theme: [%s] has no %s, so it renders with the stock "
                    "layout" % (name, need))

    # The cursor band must cover the row it marks. The engine draws it from
    # pos.y + coords[2] with height coords[4]-coords[2]+1 while the item text is
    # drawn from pos.y, so a negative coords[2] parks it on the row above.
    cur_sec, cursor = None, {}
    for line in def_text.splitlines():
        head = re.match(r"^\s*\[([^\]]+)\]", line)
        if head:
            cur_sec = head.group(1).strip()
            cursor[cur_sec] = {}
        elif cur_sec is not None and not line.strip().startswith(";"):
            kv = re.match(r"^\s*(menu\.boxcursor\.(?:visible|coords))\s*=\s*([^;]*)",
                          line, re.I)
            if kv:
                cursor[cur_sec][kv.group(1).lower()] = kv.group(2).strip()
    for name, keys in cursor.items():
        if not keys or keys.get("menu.boxcursor.visible", "0") == "0":
            continue
        try:
            vals = [float(v) for v in keys["menu.boxcursor.coords"].split(",")]
            y1, y2 = vals[1], vals[3]
        except (KeyError, ValueError, IndexError):
            continue
        if y1 < -6 or y1 > 8 or (y2 - y1 + 1) < 40:
            err("menu theme: [%s] cursor band spans y%+.0f..%+.0f, so it does "
                "not sit on the row it marks (want 0..44)" % (name, y1, y2))

    # The pause list must be centred on the frame and fit inside it. Its rows are
    # placed from menu.pos (main.f_menuItemPos sets them; the engine's own base
    # came from the stock 320x240 [Menu Info] anchor and drew the list off the
    # bottom edge), so menu.pos and the pitch decide what a player can reach.
    lc = re.search(r"^\s*localcoord\s*=\s*(\d+)\s*,\s*(\d+)", def_text, re.I | re.M)
    frame_h = int(lc.group(2)) if lc else 1080
    values, cur = {}, None
    for line in def_text.splitlines():
        head = re.match(r"^\s*\[([^\]]+)\]", line)
        if head:
            cur = head.group(1).strip()
            values[cur] = {}
        elif cur is not None and not line.strip().startswith(";"):
            kv = re.match(r"^\s*([A-Za-z0-9_.]+)\s*=\s*([^;]*)", line)
            if kv:
                values[cur][kv.group(1).lower()] = kv.group(2).strip()
    for name, keys in values.items():
        if not name.lower().endswith("pause menu"):
            continue
        try:
            top = float(keys["menu.pos"].split(",")[1])
            pitch = float(keys["menu.item.spacing"].split(",")[1])
            rows = max(1, int(float(keys.get("menu.window.visibleitems", "10"))))
            align = int(keys["menu.item.font"].split(",")[2].strip())
            band = [float(v) for v in keys["menu.boxcursor.coords"].split(",")]
        except (KeyError, ValueError, IndexError):
            continue
        row_h = max(45.0, band[3] - band[1] + 1)
        bottom = top + (rows - 1) * pitch + row_h
        if bottom > frame_h - 20:
            err("menu theme: [%s] runs its %dth row to y=%.0f, past the "
                "%d-tall frame" % (name, rows, bottom, frame_h))
        if align != 0:
            err("menu theme: [%s] rows are not centre-aligned, so the list is "
                "not centred on the frame" % name)
        centre = (top + bottom) / 2.0
        if abs(centre - frame_h / 2.0) > 100:
            err("menu theme: [%s] rows centre on y=%.0f, not the frame's middle"
                % (name, centre))

    # The options list is the other two-column screen. Labels are right-aligned
    # (they end at menu.pos.x) and values start menu.pos.x + value.offset further
    # on, so the boundary between the columns has to sit on the frame's middle -
    # every row then straddles the centre - and the gutter has to stay wide
    # enough that a value cannot print over its label at any width.
    frame_w = int(lc.group(1)) if lc else 1920
    for name, keys in values.items():
        if name.lower() != "option info":
            continue
        try:
            pos = [float(v) for v in keys["menu.pos"].split(",")]
            offset = [float(v) for v in keys["menu.item.value.offset"].split(",")]
            pitch = float(keys["menu.item.spacing"].split(",")[1])
            rows = max(1, int(float(keys.get("menu.window.visibleitems", "13"))))
            label_align = int(keys["menu.item.font"].split(",")[2].strip())
            value_align = int(keys["menu.item.value.font"].split(",")[2].strip())
        except (KeyError, ValueError, IndexError):
            continue
        boundary = pos[0] + offset[0] / 2.0
        if abs(boundary - frame_w / 2.0) > 20:
            err("menu theme: [%s] puts the label/value boundary at x=%.0f, not "
                "the frame's middle" % (name, boundary))
        if offset[0] < 12:
            err("menu theme: [%s] leaves %.0fpx between labels and values, so a "
                "value can print over its label" % (name, offset[0]))
        if label_align != -1 or value_align != 1:
            err("menu theme: [%s] does not keep labels right of their column "
                "edge and values left of theirs" % name)
        bottom = pos[1] + (rows - 1) * pitch + 45
        if bottom > frame_h - 20:
            err("menu theme: [%s] runs its %dth row to y=%.0f, past the %d-tall "
                "frame" % (name, rows, bottom, frame_h))
        centre = (pos[1] + bottom) / 2.0
        if abs(centre - frame_h / 2.0) > 100:
            err("menu theme: [%s] rows centre on y=%.0f, not the frame's middle"
                % (name, centre))

    # The title list is the third centred column, on the wordmark's axis. It is
    # not centred vertically on purpose - the logo fills the top half - so only
    # the horizontal axis is enforced here, plus the rows fitting the frame.
    for name, keys in values.items():
        if name.lower() != "title info":
            continue
        try:
            pos = [float(v) for v in keys["menu.pos"].split(",")]
            pitch = float(keys["menu.item.spacing"].split(",")[1])
            align = int(keys["menu.item.font"].split(",")[2].strip())
            active = int(keys["menu.item.active.font"].split(",")[2].strip())
            rows = max(1, int(float(keys.get("menu.window.visibleitems", "10"))))
        except (KeyError, ValueError, IndexError):
            continue
        if abs(pos[0] - frame_w / 2.0) > 0.5:
            err("menu theme: [%s] column is at x=%.0f, not the wordmark's axis"
                % (name, pos[0]))
        if align != 0 or active != 0:
            err("menu theme: [%s] rows are not centre-aligned, so the column "
                "does not centre under the logo" % name)
        bottom = pos[1] + (rows - 1) * pitch + 45
        if bottom > frame_h - 20:
            err("menu theme: [%s] runs its %dth row to y=%.0f, past the "
                "%d-tall frame" % (name, rows, bottom, frame_h))

    # The command list's columns are measured at draw time, so this window is the
    # box they are clipped to. Keep it symmetric on the frame so a list that runs
    # to the margin is not cut short on one side, and keep the heading on the
    # frame's middle, over the block the rows settle in.
    for name, keys in values.items():
        if "movelist.pos" not in keys:
            continue
        try:
            mpos = [float(v) for v in keys["movelist.pos"].split(",")]
            width = float(keys["movelist.window.width"])
            toff = [float(v) for v in keys["movelist.title.offset"].split(",")]
        except (KeyError, ValueError, IndexError):
            continue
        if abs((mpos[0] + width) - (frame_w - mpos[0])) > 1:
            err("menu theme: [%s] command list window runs %.0f..%.0f, which is "
                "not symmetric on the %d-wide frame"
                % (name, mpos[0], mpos[0] + width, frame_w))
        if abs((mpos[0] + toff[0]) - frame_w / 2.0) > 1:
            err("menu theme: [%s] command list heading sits at x=%.0f, not the "
                "frame's middle" % (name, mpos[0] + toff[0]))

    notes.append("menu theme: logo face, gold face on maroon extrusion")


def check_commands():
    """Every ChangeState in a .cmd must carry a trigger1.

    Ikemen refuses the whole file with "Missing trigger1" when a state block has
    triggerall lines but no trigger1, and the engine shows it as a load-error
    dialog the moment the character enters a match: Lightning's Storm Step was
    written that way, which crashed Lo Pan's Throne whenever he was on screen.
    """
    base = os.path.join(ROOT, "chars")
    if not os.path.isdir(base):
        return
    for folder in sorted(os.listdir(base)):
        folder_path = os.path.join(base, folder)
        if not os.path.isdir(folder_path):
            continue
        for filename in sorted(f for f in os.listdir(folder_path)
                               if f.lower().endswith(".cmd")):
            path = os.path.join(folder_path, filename)
            label = "%s/%s" % (folder, filename)
            cur, has_t1, is_change = None, False, False
            for lineno, line in enumerate(read(path).splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("["):
                    if cur and is_change and not has_t1:
                        err("%s:%d %s is a ChangeState with no trigger1"
                            % (label, cur[0], cur[1]))
                    cur, has_t1, is_change = (lineno, stripped), False, False
                    continue
                low = stripped.lower().replace(" ", "")
                if low.startswith("trigger1"):
                    has_t1 = True
                elif low.startswith("type=changestate"):
                    is_change = True
            if cur and is_change and not has_t1:
                err("%s:%d %s is a ChangeState with no trigger1"
                    % (label, cur[0], cur[1]))
    notes.append("commands: every ChangeState carries a trigger1")


def _report_gate(label, cur, idx):
    if not cur or len(idx) < 2:
        return
    with_cmd = [n for n, has in idx.items() if has]
    without = [n for n, has in idx.items() if not has]
    if with_cmd and without:
        err("%s:%d %s gates a command on trigger%d while trigger%d is a separate "
            "OR branch, so the move fires without the input"
            % (label, cur[0], cur[1], with_cmd[0], without[0]))


def check_command_gates():
    """A command must not sit on a numbered trigger beside state conditions.

    Numbered triggers are OR'ed by the engine, so `trigger1 = command = "x"`
    next to `trigger2 = statetype != A` fires the move whenever the state
    condition holds, with no input at all. Storm Step shipped like that and
    teleported Lightning on the first frame of every round.
    """
    base = os.path.join(ROOT, "chars")
    if not os.path.isdir(base):
        return
    for folder in sorted(os.listdir(base)):
        folder_path = os.path.join(base, folder)
        if not os.path.isdir(folder_path):
            continue
        for filename in sorted(f for f in os.listdir(folder_path)
                               if f.lower().endswith(".cmd")):
            path = os.path.join(folder_path, filename)
            label = "%s/%s" % (folder, filename)
            cur, idx = None, {}
            for lineno, line in enumerate(read(path).splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("["):
                    _report_gate(label, cur, idx)
                    cur, idx = (lineno, stripped), {}
                    continue
                m = re.match(r"^trigger(\d+)\s*=\s*(.*)$", stripped, re.I)
                if m:
                    n = int(m.group(1))
                    idx[n] = idx.get(n, False) or ("command" in m.group(2).lower())
            _report_gate(label, cur, idx)
    notes.append("commands: no command is OR'ed with a state condition")


def check_ladder():
    """Every order the roster uses needs a non-zero maxmatches slot.

    start.f_unifySettings() builds the ladder from <mode>maxmatches indexed by
    order, so an order whose slot is 0 produces no fights at all: a boss with
    order=4 is unreachable while the fourth entry is 0.
    """
    sel = read(os.path.join(ROOT, "data", "select.def"))
    body = sel.split("[Characters]", 1)[-1].split("\n[", 1)[0]
    orders = set()
    for line in body.splitlines():
        line = line.split(";")[0].strip()
        if not line:
            continue
        m = re.search(r"\border\s*=\s*(\d+)", line)
        if m and int(m.group(1)) > 0:
            orders.add(int(m.group(1)))
    if not orders:
        return
    for mode in ("arcade", "team", "timeattack"):
        m = re.search(r"^%s\.maxmatches\s*=\s*([^\n;]*)" % mode, sel, re.M)
        if not m:
            err("ladder: %s.maxmatches is missing from select.def" % mode)
            continue
        try:
            slots = [int(v) for v in m.group(1).split(",")]
        except ValueError:
            err("ladder: %s.maxmatches is not a number list" % mode)
            continue
        for order in sorted(orders):
            if order > len(slots) or slots[order - 1] <= 0:
                err("ladder: %s.maxmatches = %s gives order=%d no fights, so "
                    "a character with that order never appears"
                    % (mode, m.group(1).strip(), order))
    notes.append("ladder: every roster order has fights in arcade and team")


def check_intro_states():
    """[Statedef 191] must not spawn KFM's wood pieces or their hit sounds.

    Anims 191/192 are full-body poses in these characters, so the stock
    explods threw copies of the fighter across the screen while fight-fx hit
    sounds looped over the intro.
    """
    base = os.path.join(ROOT, "chars")
    paths = [os.path.join(base, d, f)
             for d in sorted(os.listdir(base))
             if os.path.isdir(os.path.join(base, d))
             for f in sorted(os.listdir(os.path.join(base, d)))
             if f.lower().endswith(".cns")]
    for path in paths:
        label = os.path.relpath(path, ROOT)
        inside = False
        for lineno, line in enumerate(read(path).splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("["):
                inside = stripped.startswith("[Statedef 191")
                continue
            if inside and re.match(r"^type\s*=\s*(PlaySnd|Explod)\b", stripped, re.I):
                err("%s:%d intro state spawns %s" % (label, lineno, stripped))
    notes.append("intro: no leftover wood explods or hit sounds")


def check_stage_aspect():
    """Stages listed for play must be 16:9, or they letterbox."""
    sel = read(os.path.join(ROOT, "data", "select.def"))
    body = sel.split("[ExtraStages]", 1)[-1].split("\n[", 1)[0]
    for line in body.splitlines():
        path = line.split(";")[0].strip()
        if not path or "stage0" in path:
            continue          # the training room is meant to stay arcade-shaped
        full = os.path.join(ROOT, path)
        if not os.path.isfile(full):
            err("stages: %s is listed in [ExtraStages] but missing" % path)
            continue
        m = re.search(r"^\s*localcoord\s*=\s*(\d+)\s*,\s*(\d+)", read(full),
                      re.M | re.I)
        if not m:
            err("stages: %s has no localcoord, so it falls back to 4:3" % path)
            continue
        w, h = int(m.group(1)), int(m.group(2))
        if abs(w / float(h) - 16 / 9.0) > 0.02:
            err("stages: %s is %dx%d (%.2f:1), so it letterboxes in a 16:9 "
                "window" % (path, w, h, w / float(h)))
        body = read(full)
        # A 3D stage gets its depth from the model, so it has no sky and
        # lip sprite layers to find - the same reason the layer count above
        # does not apply to it.
        if re.search(r"^\s*model\s*=", body, re.M | re.I):
            continue
        for need in ("[BG sky]", "[BG lip]"):
            if need not in body:
                err("stages: %s has no %s layer, so it has no depth" % (path, need))
    notes.append("stages: 16:9 canvases, no letterbox bars")


def check_launchers():
    """The Windows launchers must parse before they can run.

    cmd has no second chance at syntax: an unescaped | in an echo line is a
    pipe into a program that does not exist, and the window dies on its first
    breath. That shipped twice, so every launcher is read by
    tools/check_launchers.py here rather than being taken on trust.
    """
    path = os.path.join(ROOT, "tools", "check_launchers.py")
    if not os.path.isfile(path):
        err("launchers: tools/check_launchers.py is missing")
        return
    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    namespace = {"__name__": "check_launchers"}
    exec(compile(source, path, "exec"), namespace)
    for problem in namespace["problems"](ROOT):
        err("launchers: " + problem)
    notes.append("launchers: no stray operators, labels and variables resolve")

def check_launcher_checks():
    """The launcher rules must still catch what they exist for.

    Reading the launchers is only as good as the rules doing the reading: a
    pattern that can never match reports nothing, which looks exactly like a
    clean build. tools/test_launchers.py feeds every cmd trap to
    tools/check_launchers.py, and the correct form of each, then brings the
    muzzle-count bug back three ways to prove its guards still fire. It needs no
    engine and no lupa, so it can run here on every build; the engine-backed
    tests cannot be asked for in CI.
    """
    path = os.path.join(ROOT, "tools", "test_launchers.py")
    if not os.path.isfile(path):
        err("launchers: tools/test_launchers.py is missing, so nothing proves "
            "the syntax rules still fire")
        return
    result = subprocess.run([sys.executable, path], capture_output=True, text=True)
    if result.returncode != 0:
        lines = [l.strip() for l in (result.stdout + result.stderr).splitlines()
                 if l.strip().startswith("FAIL")]
        if not lines:
            lines = (result.stdout + result.stderr).strip().splitlines()[-4:]
        for line in lines[-6:]:
            err("launchers: " + line)
        err("launchers: tools/test_launchers.py failed (exit %d)" % result.returncode)
        return
    notes.append("launchers: every syntax rule still catches its cmd trap")


def check_motif_ints():
    """Coordinates the engine reads as ints have to be whole numbers.

    A window written "0, 45, 808.5, 883.5" fails ParseInt, so the engine drops
    the whole key with a warning and the window falls back to its default - the
    art lands in the wrong place with nothing else to show for it.
    """
    path = os.path.join(ROOT, "data", "ikemen1", "system.def")
    if not os.path.isfile(path):
        return
    whole = {"window", "offset", "spr", "anim", "layerno", "spacing", "pos", "icon", "tile", "col"}
    with open(path, encoding="utf-8") as fh:
        for number, line in enumerate(fh.read().splitlines(), 1):
            m = re.match(r"\s*([A-Za-z0-9_.]+)\s*=\s*(.*)$", line)
            if not m or m.group(1).lower().split(".")[-1] not in whole:
                continue
            if re.search(r"\d\.\d", m.group(2)):
                err("motif: %s:%d %s is not a whole number, so the engine drops it"
                    % (os.path.basename(path), number, m.group(1)))
    notes.append("motif: every coordinate the engine reads is a whole number")

def check_powerbar_fonts():
    """Every power bar level the engine can select must carry a font.

    readPBKeys maps "counterMax" to counter key -1 and resolvePBKey returns that
    key at maximum power. PowerBar.draw only checks counter[0].fnt before it
    draws the selected one, and an entry with text but no font has a nil font,
    which Layout.DrawText dereferences before it reads the (empty) text. That
    shipped once and crashed the fight screen the moment a bar filled, so the
    levels are checked here instead.
    """
    path = os.path.join(ROOT, "data", "fight.def")
    if not os.path.isfile(path):
        return
    lines = read(path).splitlines()
    start = next((i for i, ln in enumerate(lines)
                  if ln.strip().lower() == "[powerbar]"), None)
    if start is None:
        err("powerbar: data/fight.def has no [Powerbar] section")
        return
    end = next((j for j in range(start + 1, len(lines))
                if lines[j].lstrip().startswith("[")), len(lines))
    keys = {}
    for line in lines[start + 1:end]:
        m = re.match(r"\s*([A-Za-z0-9_.]+)\s*=\s*(.*)$", line)
        if m:
            keys[m.group(1).lower()] = m.group(2)
    for side in ("p1", "p2"):
        for family in ("counter", "value"):
            if ("%s.%s.font" % (side, family)) not in keys:
                continue  # the engine skips the whole family without a base font
            elements = {k.split(".")[1] for k in keys
                        if k.startswith("%s.%s" % (side, family))
                        and len(k.split(".")) > 2}
            for element in sorted(elements):
                if ("%s.%s.font" % (side, element)) not in keys:
                    err("powerbar: %s.%s has no font, so the engine draws a nil "
                        "font at that level (crash at full power)"
                        % (side, element))
    notes.append("powerbar: every counter/value level has a font")

def check_hud_fonts():
    """Text levels on the life, guard, stun and time bars must carry fonts.

    Each of those bars picks a level by value and guards the draw with level 0's
    font only (LifeBar.draw checks value[0].fnt, then draws value[fv2]). A level
    with text but no font therefore reaches Layout.DrawText with a nil font,
    which is dereferenced before the text is read - the same shape as the
    counterMax crash the power bar already shipped. A family whose base has no
    font is never drawn at all, so it is skipped. This screenpack currently has
    no value levels and every [Time] counter has a font; the check keeps it that
    way.
    """
    path = os.path.join(ROOT, "data", "fight.def")
    if not os.path.isfile(path):
        return
    sections, name = {}, None
    for line in read(path).splitlines():
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            name = s[1:-1].lower()
            sections.setdefault(name, {})
            continue
        if name is None:
            continue
        m = re.match(r"\s*([A-Za-z0-9_.]+)\s*=\s*(.*)$", line)
        if m:
            sections[name].setdefault(m.group(1).lower(), m.group(2))

    def families(section):
        sides = ["p%d" % i for i in range(1, 9)]
        if "lifebar" in section:
            return [(side, fam) for side in sides
                    for fam in ("value", "red.value")]
        if "guardbar" in section or "stunbar" in section:
            return [(side, "value") for side in sides]
        if section == "time":
            return [("", "counter")]
        return []

    levels = 0
    for section, keys in sections.items():
        for side, fam in families(section):
            pre = (side + "." if side else "") + fam
            if pre + ".font" not in keys:
                continue  # no base font: the engine draws no level of this family
            pat = re.compile(r"^" + re.escape(pre) + r"(\d*|[Mm]ax)\.[a-z0-9]+$")
            found = {m.group(1).lower() for m in map(pat.match, keys) if m}
            for level in sorted(found):
                levels += 1
                if pre + level + ".font" not in keys:
                    err("hud: %s%s has no font, so the engine draws a nil font "
                        "at that level (crash)" % (pre, level))
    notes.append("hud: life, guard, stun and time text levels all have fonts "
                 "(%d levels)" % levels)

def check_team_screen():
    """The team-mode screen: a flat heading, and markers in the game's palette.

    "TEAM MODE" was drawn through a perspective projection (yangle 52.5), so the
    heading came out as a skewed parallelogram that read as a broken face beside
    the upright mode list, and the slot markers were stock blue art that did not
    separate a filled slot from an empty one. Both are generator-owned: the
    heading by tools/build_fonts.py, the markers by tools/build_select_icons.py.
    """
    import sff as sffmod

    text = read(os.path.join(ROOT, "data", "ikemen1", "system.def"))
    parts = text.split("[Select Info]", 1)
    if len(parts) != 2:
        err("system.def: no [Select Info] block")
        return
    body = parts[1].split("\n[", 1)[0]
    keys = {}
    for line in body.splitlines():
        line = line.split(";", 1)[0].strip()
        if "=" in line:
            name, value = line.split("=", 1)
            keys[name.strip()] = value.strip()

    for side, align in (("p1", "1"), ("p2", "-1")):
        for part in ("selftitle", "enemytitle"):
            key = "%s.teammenu.%s" % (side, part)
            yangle = keys.get(key + ".yangle", "0")
            try:
                flat = abs(float(yangle)) < 0.01
            except ValueError:
                flat = False
            if not flat:
                err("select screen: %s.yangle is %s, so the TEAM MODE heading is "
                    "drawn as a skewed parallelogram" % (key, yangle))
            fields = [f.strip() for f in keys.get(key + ".font", "").split(",")]
            if len(fields) < 3 or fields[2] != align:
                err("select screen: %s.font is %r, so the heading does not share "
                    "the mode list's edge" % (key, keys.get(key + ".font")))
            if keys.get(key + ".offset", "").replace(" ", "") != "0,23":
                err("select screen: %s.offset is %r, so the heading is not on the "
                    "list's own edge" % (key, keys.get(key + ".offset")))

    for side in ("p1", "p2"):
        for part in ("value.icon", "value.empty.icon"):
            name = "%s.teammenu.%s.offset" % (side, part)
            if keys.get(name, "").replace(" ", "") != "0,0":
                err("select screen: %s is %r, but the markers are placed from the "
                    "measured word width and any baked offset pushes them over the "
                    "portrait grid" % (name, keys.get(name)))
        spacing = keys.get("%s.teammenu.value.spacing" % side, "").replace(" ", "")
        want = "38,0" if side == "p1" else "-38,0"
        if spacing != want:
            err("select screen: %s.teammenu.value.spacing is %r, expected %s so a "
                "four-marker row fits between the mode names and the grid"
                % (side, spacing, want))

    select_lua = read(os.path.join(ROOT, "external", "script", "start.lua"))
    if "local iconX0 = iconDir * (wordW + " not in select_lua:
        err("select screen: start.f_teamMenu no longer places the team markers "
            "beside the mode names")
    if "x + (j - 1) * valueCfg.spacing[1]" in select_lua:
        err("select screen: start.f_teamMenu still places the team markers at the "
            "raw item offset, which lands on the portrait grid")

    want = {(180, 0): (22, 38), (181, 0): (30, 48), (182, 0): (30, 48),
            (191, 0): (30, 48), (192, 0): (30, 48)}
    data, sprites, palettes = sffmod.read_sff(
        os.path.join(ROOT, "data", "ikemen1", "system.sff"))
    for key, size in want.items():
        sprite = next((s for s in sprites
                       if (s["group"], s["number"]) == key), None)
        if sprite is None:
            err("select screen: team marker sprite %d,%d is missing" % key)
            continue
        if (sprite["w"], sprite["h"]) != size:
            err("select screen: team marker %d,%d is %dx%d, expected %dx%d"
                % (key[0], key[1], sprite["w"], sprite["h"], size[0], size[1]))
            continue
        img = sffmod.decode_sprite(data, sprite, palettes).convert("RGBA")
        px = [p for p in img.getdata() if p[3] > 128]
        if px:
            red = sum(p[0] for p in px) / len(px)
            blue = sum(p[2] for p in px) / len(px)
            if blue > red:
                err("select screen: team marker %d,%d is blue art again" % key)
    notes.append("select screen: team heading flat, markers in the palette")


def check_fight_hud():
    """The HUD's corner cells and the countdown's place on the yin-yang.

    Both corners used to frame the portrait in their own 100x100 and 108x108
    boxes and clip it with a 92x92 window, so the HUD matched nothing else in
    the game. tools/build_face_boxes.py redraws them as the select screen's
    128x160 gold cell, and the countdown moved off the banner onto the disc. The
    portrait is clipped to the cell's opening, because the art's size varies per
    character and the taller ones hung out of the frame.
    """
    import re as _re

    import sff as sffmod

    text = read(os.path.join(ROOT, "data", "fight.def"))
    cell_spr = "222,0"
    for name in ("Face", "Simul Face", "Tag Face", "Turns Face"):
        parts = text.split("[%s]" % name, 1)
        if len(parts) != 2:
            err("fight.def: no [%s] section" % name)
            continue
        body = parts[1].split("\n[", 1)[0]
        keys = {}
        for line in body.splitlines():
            line = line.split(";", 1)[0].strip()
            if "=" in line:
                k, v = line.split("=", 1)
                keys[k.strip()] = v.strip()
        for side in ("p1", "p2"):
            if keys.get("%s.bg1.spr" % side) != cell_spr:
                err("fight HUD: [%s] %s.bg1.spr is %r, not the select screen's gold "
                    "cell %s" % (name, side, keys.get("%s.bg1.spr" % side), cell_spr))
            if keys.get("%s.face.spr" % side) != "9000,0":
                err("fight HUD: [%s] %s.face.spr is %r, not the character cell art"
                    % (name, side, keys.get("%s.face.spr" % side)))
            import build_face_boxes as fb
            want_scale = "%.3f, %.3f" % (fb.portrait_scale(), fb.portrait_scale())
            scale = keys.get("%s.face.scale" % side, "")
            if ", ".join(p.strip() for p in scale.split(",")) != want_scale:
                err("fight HUD: [%s] %s.face.scale is %r, not the select screen's "
                    "portrait size (%s), so the fighter does not fit its cell"
                    % (name, side, scale or "missing", want_scale))
        import build_face_boxes as fb
        for side in ("p1", "p2"):
            want = ", ".join(str(v) for v in fb.cell_window(side))
            have = keys.get("%s.face.window" % side, "")
            norm = ", ".join(p.strip() for p in have.split(",")) if have else ""
            if norm != want:
                err("fight HUD: [%s] %s.face.window is %r, not the cell's opening "
                    "(%s), so the portrait is not held inside its box"
                    % (name, side, have or "missing", want))

    data, sprites, palettes = sffmod.read_sff(
        os.path.join(ROOT, "data", "fight.sff"))
    cell = next((s for s in sprites
                 if (s["group"], s["number"]) == (222, 0)), None)
    if cell is None:
        err("fight HUD: fight.sff has no 222,0 gold cell frame")
    elif (cell["w"], cell["h"]) != (128, 160):
        err("fight HUD: the cell frame in fight.sff is %dx%d, expected 128x160"
            % (cell["w"], cell["h"]))

    parts = text.split("[Time]", 1)
    if len(parts) == 2:
        body = parts[1].split("\n[", 1)[0]
        import build_banner as bb
        want = int(round(bb.TIME_NUM_CELL * bb.TIME_NUM_SCALE / 2.0))
        m = _re.search(r"(?m)^\s*counter\.offset\s*=\s*(-?\d+)\s*,\s*(-?\d+)", body)
        if not m or int(m.group(2)) != want:
            err("fight HUD: [Time] counter.offset is %s, so the countdown is not on "
                "the yin-yang's centre line between its two dots (expected y %d)"
                % ("missing" if not m else m.group(2), want))
    notes.append("fight HUD: gold cells in both corners, clock between the yin-yang dots")


def check_stage_camera():
    """Every stage must let the camera pull back when the fighters separate.

    They all shipped zoomout = 1, which pins the view at 1:1: the camera could
    pan along a level but never widen, so two players walking apart simply hit
    the edge of the screen. tools/build_camera.py sets zoomout on every stage and
    the stage generators write the same value.
    """
    import glob as _glob
    import re as _re

    for path in sorted(_glob.glob(os.path.join(ROOT, "stages", "*.def"))):
        if not os.path.isfile(path):
            continue
        name = os.path.basename(path)
        text = read(path)
        m = _re.search(r"(?im)^\[Camera\][ \t]*$", text)
        if not m:
            continue
        body = text[m.end():].split("\n[", 1)[0]
        z = _re.search(r"(?im)^\s*zoomout\s*=\s*([^;\r\n]+)", body)
        if not z:
            err("stage %s has no [Camera] zoomout, so the camera can never widen "
                "and the fighters cannot walk apart to the full width" % name)
            continue
        try:
            value = float(z.group(1).strip())
        except ValueError:
            err("stage %s: zoomout is %r, not a number" % (name, z.group(1).strip()))
            continue
        if value > 0.76:
            err("stage %s: zoomout is %.2f, which pins the view at 1:1 - the camera "
                "can pan but not pull back" % (name, value))
    notes.append("stage camera: every stage can zoom out")


VIDEO_EXTS = {".webm", ".mp4", ".avi", ".mkv", ".mov", ".m4v", ".y4m", ".ogv"}
AUDIO_EXTS = {".ogg", ".wav", ".mp3", ".flac", ".opus", ".m4a", ".mid",
              ".midi", ".mod", ".xm", ".s3m", ".it", ".669"}
MEDIA_EXTS = VIDEO_EXTS | AUDIO_EXTS
MEDIA_DIRS = ("sound/", "video/", "music/")


def _media_kind(value):
    """'video' or 'sound' for a value that names one, else None."""
    ext = os.path.splitext(value.replace("\\", "/"))[1].lower()
    if ext in VIDEO_EXTS:
        return "video"
    if ext in AUDIO_EXTS:
        return "sound"
    return None


def _media_file(value, *bases):
    """The file a def reference points at, or None.

    Screens and stages name their media from the game root - system.def sits in
    data/ikemen1/ and names sound/Title.ogg, which is sound/Title.ogg in the
    folder - but a stage may also name a track beside itself, so both are tried
    rather than guessing which one the engine picks.
    """
    rel = value.replace("\\", "/").strip()
    while rel.startswith("./"):
        rel = rel[2:]
    for base in bases:
        candidate = os.path.normpath(os.path.join(base, rel))
        if os.path.isfile(candidate):
            return candidate
    return None


def _def_media_refs(text):
    """(key, value) for every INI value that names a video or a sound file."""
    for raw in text.splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line or line.startswith("[") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip()
        if _media_kind(value):
            yield key.strip(), value


def _lua_media_refs(text):
    """Sound and video paths a screen script names in full."""
    for raw in text.splitlines():
        line = raw.split("--", 1)[0]
        for m in re.finditer(r"""["']([^"'\n]+)["']""", line):
            value = m.group(1)
            if _media_kind(value) and value.replace("\\", "/").lower().startswith(MEDIA_DIRS):
                yield value


def _json_media_refs(node, out):
    """Every media path anywhere in a JSON value, whatever its shape."""
    if isinstance(node, str):
        if _media_kind(node):
            out.append(node)
    elif isinstance(node, dict):
        for value in node.values():
            _json_media_refs(value, out)
    elif isinstance(node, list):
        for value in node:
            _json_media_refs(value, out)


def _media_problem(value, bases, tracked):
    """What is wrong with a media reference, or None when it is fine."""
    full = _media_file(value, *bases)
    if full is None:
        return "there is no such file in the folder"
    if tracked is not None:
        rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
        if rel not in tracked:
            return ("it is on this machine but not in the repo, so it never "
                    "reaches anyone who updates")
    if os.path.getsize(full) == 0:
        return "it is an empty file"
    return None


def _tracked():
    """Every path git tracks here, or None when this is not a checkout.

    A file sitting in the folder is not a file that ships: the updater copies
    what main has. The credits clip was in video/ here and in no commit at all,
    which is exactly the reference this has to catch.
    """
    try:
        out = subprocess.run(["git", "-C", ROOT, "ls-files", "-z"],
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             check=True).stdout
    except Exception:
        return None
    return {p.decode("utf-8", "replace").replace("\\", "/")
            for p in out.split(b"\0") if p}


def check_media_refs():
    """Every video and sound a stage or a screen names has to ship with the game.

    A def that names a file nobody shipped says nothing about it: the engine drops
    the layer or plays nothing, and the screen is just quietly wrong. Lo Pan's
    throne named video/fog.webm and the credits named ik_credits.webm; neither was
    ever in the repo, so the mouth was black and the credits had no clip. Only a
    stage's bgmusic was checked before; this covers video layers, sounds, the
    screens' own music and the album list the music browser shows.
    """
    import glob as _glob
    import json as _json

    tracked = _tracked()
    found = 0
    missing = 0

    for pattern in ("stages/*.def", "stages/*/*.def", "data/*.def", "data/*/*.def"):
        for path in sorted(_glob.glob(os.path.join(ROOT, pattern))):
            if not os.path.isfile(path):
                continue
            where = os.path.relpath(path, ROOT).replace(os.sep, "/")
            seen = set()
            for key, value in _def_media_refs(read(path)):
                if (key, value) in seen:
                    continue
                seen.add((key, value))
                found += 1
                problem = _media_problem(value, (ROOT, os.path.dirname(path)), tracked)
                if problem:
                    missing += 1
                    err("media: %s names %s = %s, and %s - the engine just leaves "
                        "that layer or sound out" % (where, key, value, problem))

    for path in sorted(_glob.glob(os.path.join(ROOT, "external", "**", "*.lua"),
                                 recursive=True)):
        where = os.path.relpath(path, ROOT).replace(os.sep, "/")
        seen = set()
        for value in _lua_media_refs(read(path)):
            if value in seen:
                continue
            seen.add(value)
            found += 1
            problem = _media_problem(value, (ROOT,), tracked)
            if problem:
                missing += 1
                err("media: %s plays %s, and %s" % (where, value, problem))

    music_json = os.path.join(ROOT, "data", "music.json")
    if os.path.isfile(music_json):
        try:
            refs = []
            _json_media_refs(_json.loads(read(music_json)), refs)
        except ValueError as exc:
            err("media: data/music.json does not parse: %s" % exc)
        else:
            for value in sorted(set(refs)):
                found += 1
                problem = _media_problem(value, (ROOT,), tracked)
                if problem:
                    missing += 1
                    err("media: data/music.json lists %s, and %s, so the list shows "
                        "a track that cannot play" % (value, problem))

    notes.append("media: %d video/sound reference(s) ship and resolve" % (found - missing))



def check_retired():
    """Root files main stopped shipping have to be deleted from the folder.

    The updater copies the six game folders, so a file that used to sit at the
    root - Start.html, Test Big Trouble.bat - stayed in every folder that had ever
    updated, for good, after main dropped it. data/retired.txt is the list the
    updater deletes from; this keeps that list equal to the repository's own
    history, so retiring a root file cannot be forgotten, and refuses to name a
    file the repo still ships.
    """
    path = os.path.join(ROOT, "data", "retired.txt")
    if not os.path.isfile(path):
        err("retired: data/retired.txt is missing, so dropped root files are never "
            "removed from a folder that has them")
        return

    listed = []
    for raw in read(path).splitlines():
        name = raw.split(";", 1)[0].strip()
        if name:
            listed.append(name)

    tracked = _tracked()
    for name in listed:
        if "/" in name or "\\" in name:
            err("retired: %s is listed, but only files at the root of the game "
                "folder can be retired this way - the update already removes "
                "dropped files inside the game folders" % name)
        elif tracked is not None and name in tracked:
            err("retired: %s is listed as retired, but the repo still ships it"
                % name)

    if tracked is not None:
        try:
            out = subprocess.run(["git", "-C", ROOT, "log", "--diff-filter=D",
                                  "--name-only", "--format="],
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                 check=True).stdout
        except Exception:
            out = b""
        gone = set()
        for raw in out.decode("utf-8", "replace").splitlines():
            name = raw.strip()
            if name and "/" not in name:
                gone.add(name)
        missing = sorted(gone - set(listed))
        if missing:
            err("retired: %s was deleted from the root of the repo but is not in "
                "data/retired.txt, so folders that still have it keep it"
                % ", ".join(missing))

    launcher = read(os.path.join(ROOT, "Update and Play.bat"))
    if "data\\retired.txt" not in launcher:
        err("retired: Update and Play.bat no longer reads data\\retired.txt, so the "
            "list is never acted on")
    elif 'for /f "usebackq delims=" %%R in ("%~dp0data\\retired.txt")' not in launcher:
        err("retired: Update and Play.bat does not loop over data\\retired.txt")
    elif 'del /q "%~dp0%R%"' not in launcher:
        err("retired: Update and Play.bat lists the retired files but never deletes "
            "one")
    elif not any(line.strip().lower() == "call :retired"
                 for line in launcher.splitlines()):
        # the substring also matches "call :retiredone", which is the loop body,
        # so this has to be the call itself or a launcher that never runs it passes
        err("retired: Update and Play.bat never calls :retired, so nothing is "
            "removed before the game starts")

    notes.append("retired: %d dropped root file(s) are removed on update" % len(listed))


def main():
    check_media_refs()
    check_retired()
    chars = check_select()
    check_menu_theme()
    check_commands()
    check_command_gates()
    check_ladder()
    check_intro_states()
    check_stage_aspect()
    check_launchers()
    check_launcher_checks()
    check_motif_ints()
    check_powerbar_fonts()
    check_hud_fonts()
    check_select_screen(chars)
    check_team_screen()
    check_fight_hud()
    check_stage_camera()
    check_rain_thunder()
    for name, _stage in chars:
        def_path, folder = resolve_char(name)
        if def_path and os.path.isfile(def_path):
            check_character(def_path, folder)

    stage_defs = sorted(
        os.path.join(ROOT, "stages", f) for f in os.listdir(os.path.join(ROOT, "stages"))
        if f.endswith(".def"))
    for stage in stage_defs:
        check_stage(stage)

    # roster palettes should not all be identical
    pal_sets = []
    for name, _stage in chars:
        def_path, folder = resolve_char(name)
        if not (def_path and os.path.isfile(def_path)):
            continue
        files = dict(ini_sections(read(def_path)).get("files", []))
        sff_path = os.path.join(folder, files.get("sprite", ""))
        if os.path.isfile(sff_path):
            _d, _s, pals = sff.read_sff(sff_path)
            if pals:
                pal_sets.append(bytes(pals[0]["rgba"]))
    if len(pal_sets) > 1 and len(set(pal_sets)) == 1:
        err("roster: every character uses the same palette")

    for note in notes:
        print("  ok  " + note)
    if errors:
        print()
        for e in errors:
            print("  FAIL " + e)
        print(f"\n{len(errors)} problem(s) found")
        return 1
    print(f"\nAll checks passed ({len(notes)} checks)")
    return 0


def check_rain_thunder():
    """The rainfall stage's flash, flag and rumble must stay in step.

    The stage def cannot play a sound, so the thunder is an agreement between four
    files: the def's [Constants] flag, the animated layer, the action it plays, and
    the Lua module that listens for the flag and plays the sample. Any one of them
    missing is silent, and silence looks exactly like a working build - so each is
    checked here, along with the sprites the action names.
    """
    import struct

    def_path = os.path.join(ROOT, "stages", "stage3d_rain.def")
    if not os.path.isfile(def_path):
        err("rain thunder: stages/stage3d_rain.def is missing")
        return
    body = read(def_path)
    if not re.search(r"^\s*RainThunder\s*=\s*1\s*$", body, re.M | re.I):
        err("rain thunder: the stage has no [Constants] RainThunder = 1, so the "
            "module cannot tell it is in the storm")
    layer = re.search(r"\[BG lightning\](.*?)(?=\n\[)", body, re.S)
    if not layer:
        err("rain thunder: the stage has no [BG lightning] layer, so nothing flashes")
    else:
        block = layer.group(1)
        if not re.search(r"^\s*type\s*=\s*anim", block, re.M | re.I):
            err("rain thunder: [BG lightning] is not an anim layer")
        if not re.search(r"^\s*actionno\s*=\s*9001", block, re.M | re.I):
            err("rain thunder: [BG lightning] does not play action 9001")
    start = re.search(r"^\[Begin Action 9001\]\s*$", body, re.M | re.I)
    if not start:
        err("rain thunder: action 9001 is missing, so nothing flashes")
    else:
        end = re.search(r"^\[", body[start.end():], re.M)
        block = body[start.end():start.end() + (end.start() if end else len(body))]
        frames = re.findall(r"^\s*(\d+)\s*,\s*(\d+)\s*,", block, re.M)
        if not frames:
            err("rain thunder: action 9001 has no frames")
        else:
            try:
                _d, sprites, _p = sff.read_sff(
                    os.path.join(ROOT, "stages", "stage3d_rain.sff"))
            except Exception as exc:                       # noqa: BLE001
                err("rain thunder: cannot read stage3d_rain.sff: %s" % exc)
                frames = []
            have = {(sp["group"], sp["number"]) for sp in sprites}
            for g, n in frames:
                if (int(g), int(n)) not in have:
                    err("rain thunder: action 9001 uses %s,%s, which is not in "
                        "stage3d_rain.sff" % (g, n))
                    break

    snd = os.path.join(ROOT, "data", "system.snd")
    if not os.path.isfile(snd):
        err("rain thunder: data/system.snd is missing")
    else:
        with open(snd, "rb") as fh:
            blob = fh.read()
        if blob[:12] != b"ElecbyteSnd\x00":
            err("rain thunder: data/system.snd is not a MUGEN sound file")
        else:
            _v, count, start, _b = struct.unpack("<IIII", blob[12:28])
            found = False
            for _ in range(count):
                _nxt, _len, g, n = struct.unpack("<IIII", blob[start:start + 16])
                if (g, n) == (900, 0):
                    found = True
                    break
                if _nxt == 0:
                    break
                start = _nxt
            if not found:
                err("rain thunder: data/system.snd has no 900,0 sample, so the "
                    "module has nothing to play")

    mod = os.path.join(ROOT, "external", "mods", "rainthunder.lua")
    if not os.path.isfile(mod):
        err("rain thunder: external/mods/rainthunder.lua is missing, so the "
            "rumble is never played")
    else:
        with open(mod, encoding="utf-8") as fh:
            source = fh.read()
        for need, why in (("stageConst", "it never checks the stage flag"),
                          ("hook.add('loop'", "it never runs during a match"),
                          ("900", "it does not play the thunder sample")):
            if need not in source:
                err("rain thunder: rainthunder.lua " + why)
    notes.append("rain thunder: action 9001 flashes, RainThunder is set, 900,0 rumbles")


if __name__ == "__main__":
    raise SystemExit(main())
