"""Offline validation for the game data, so a typo does not wait for a playtest.

Checks, without launching the engine:
  * every select.def character and stage resolves to real files
  * character DEFs reference files that exist, and their SFF loads
  * every animation frame in each .air resolves to a sprite in the .sff
  * stage DEFs reference sprites that exist in their .sff, plus preview sprite
  * optional: roster palettes differ from the base character

Run:  python3 tools/validate.py
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sff

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
        if line in ("{", "}") or line.lower().startswith("slot"):
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

    if opts.get("rows") != "2" or opts.get("columns") != "5":
        err("select screen: grid is %s rows by %s columns, expected 2 by 5"
            % (opts.get("rows"), opts.get("columns")))
    if opts.get("cell.size") != "120,120":
        err("select screen: cell.size is %r, expected 120,120" % opts.get("cell.size"))
    if opts.get("portrait.spr") != "9000,0":
        err("select screen: portrait.spr is %r, expected 9000,0" % opts.get("portrait.spr"))
    if "p1.face.window" not in opts or "p2.face.window" not in opts:
        err("select screen: the big side portraits have no window")

    sff_path = os.path.join(ROOT, "data", "ikemen1", "system.sff")
    if not os.path.isfile(sff_path):
        err("select screen: data/ikemen1/system.sff is missing")
        return
    _d, sprites, _p = sff.read_sff(sff_path)
    have = {(sp["group"], sp["number"]): sp for sp in sprites}
    for group, number in ((220, 0), (222, 0), (223, 0), (223, 1), (223, 2), (223, 3)):
        if (group, number) not in have:
            err("select screen: system.sff has no sprite %d,%d" % (group, number))
    bg = have.get((220, 0))
    if bg and (bg["w"], bg["h"]) != (1280, 720):
        err("select screen: background is %dx%d, expected 1280x720" % (bg["w"], bg["h"]))
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
        cell = {(sp["group"], sp["number"]): sp for sp in char_sprites}.get((9000, 0))
        if cell is None:
            err("%s: no select portrait 9000,0" % name)
        elif (cell["w"], cell["h"]) != (120, 120):
            err("%s: select portrait is %dx%d, expected 120x120"
                % (name, cell["w"], cell["h"]))
        want = {(9000, 1): (120, 140), (9000, 2): (300, 520)}
        for key, size in want.items():
            hit = {(sp["group"], sp["number"]): sp for sp in char_sprites}.get(key)
            if hit is None:
                err("%s: no portrait sprite %d,%d" % (name, key[0], key[1]))
            elif (hit["w"], hit["h"]) != size:
                err("%s: portrait %d,%d is %dx%d, expected %dx%d"
                    % (name, key[0], key[1], hit["w"], hit["h"], size[0], size[1]))
    notes.append("select screen: 5x2 portrait grid, 120px cells, framed sides")


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
        if not re.search(r"^Type\s*=\s*truetype", body, re.I | re.M):
            err("menu theme: %s.def is not a truetype font, so RGB tints are ignored" % name)
        f = re.search(r"^File\s*=\s*(\S+)", body, re.I | re.M)
        if not f or not os.path.isfile(os.path.join(os.path.dirname(fdef), f.group(1))):
            err("menu theme: %s.def does not point at a shipped typeface" % name)

    stale = [c for c in ("123,206,255", "255,210,239", "210,210,255", "0,247,247")
             if c in def_text]
    if stale:
        err("menu theme: system.def still uses the old menu colours (%s)"
            % ", ".join(stale))
    if declared.get("font10") is None or declared.get("font11") is None:
        err("menu theme: font10/font11 are not registered in [Files]")
    if "footer.title.font" in def_text and "72, 10, 16" not in def_text:
        err("menu theme: the footer bar is not in the logo palette")
    notes.append("menu theme: logo face, gold/red palette, footer bar restyled")


def main():
    chars = check_select()
    check_menu_theme()
    check_select_screen(chars)
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


if __name__ == "__main__":
    raise SystemExit(main())
