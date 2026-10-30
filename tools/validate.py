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


def main():
    chars = check_select()
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
