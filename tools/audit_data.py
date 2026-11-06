"""Audit the data the engine loads at launch for the things it complains about.

tools/validate.py covers the roster: character and stage DEFs, every AIR frame in
a char SFF, stage sprites. It does not look at the screenpack itself, which is
where the launch console warnings come from. This checks, without an engine:

  * sprite references in the motif DEFs, fight.def and the stages resolve to real
    sprites in the SFF that DEF draws from ("missing sprite 220,0" on stderr)
  * sound and music paths name files that exist ("Failed to open BGM: ...")
  * an `anim = N` in a DEF that carries its own AIR blocks has a matching
    "[Begin Action N]" there
  * no key is declared twice inside one section (the second silently wins)
  * integer fields (offset, pos, coords, window, spriteno, anim, layerno) hold
    whole numbers - "parsing 808.5: invalid syntax" otherwise

Run:  python3 tools/audit_data.py
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INT_KEYS = ("offset", "pos", "coords", "window", "spriteno", "anim", "layerno",
            "font", "spacing", "localcoord")
SOUND_EXTS = (".ogg", ".mp3", ".wav", ".flac", ".mid", ".midi")
# A DEF whose sprites live in another file names it here.
SPR_KEYS = ("spr", "sprite", "sff")

findings = []
_sff_cache = {}


def fail(where, msg):
    findings.append(f"{where}: {msg}")


def read(path):
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        return fh.read()


def sections(text):
    """[(section, [(key, value, lineno)])] in file order, comments stripped."""
    out, cur = [], None
    for no, raw in enumerate(text.splitlines(), start=1):
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            cur = (line[1:-1].strip(), [])
            out.append(cur)
        elif "=" in line and cur is not None:
            key, value = line.split("=", 1)
            cur[1].append((key.strip(), value.strip(), no))
    return out


def sprite_ids(path):
    """{(group, number)} for an SFF, decoded once and cached."""
    if path not in _sff_cache:
        if not os.path.isfile(path):
            _sff_cache[path] = None
        else:
            try:
                _d, sprites, _p = sff.read_sff(path)
                _sff_cache[path] = {(sp["group"], sp["number"]) for sp in sprites}
            except Exception as err:  # an unreadable SFF is its own finding
                _sff_cache[path] = f"unreadable ({err})"
    return _sff_cache[path]


def companion_sff(def_path, secs):
    """The SFF a DEF draws its sprites from."""
    for _name, entries in secs:
        for key, value, _no in entries:
            if key.lower() in SPR_KEYS and value.lower().endswith(".sff"):
                cand = os.path.join(os.path.dirname(def_path), value.replace("\\", "/"))
                if os.path.isfile(cand):
                    return cand
    stem = os.path.splitext(def_path)[0]
    for ext in (".sff",):
        if os.path.isfile(stem + ext):
            return stem + ext
    # the screenpack motif and its storyboards all share system.sff
    shared = os.path.join(os.path.dirname(def_path), "system.sff")
    return shared if os.path.isfile(shared) else None


def audit_def(path, has_own_air=None):
    rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
    text = read(path)
    secs = sections(text)

    sff_path = companion_sff(path, secs)
    ids = sprite_ids(sff_path) if sff_path else None
    if isinstance(ids, str):
        fail(rel, f"{os.path.basename(sff_path)} {ids}")
        ids = None

    actions = {int(m.group(1)) for m in re.finditer(r"(?mi)^\[begin action\s+(\d+)\]", text)}
    if has_own_air is None:
        has_own_air = bool(actions)

    for name, entries in secs:
        low = name.lower()
        if low.startswith(("begin action", "clsn", "palette")):
            continue
        local = set()
        for key, value, no in entries:
            k = key.lower()
            where = f"{rel}:{no} [{name}] {key}"

            if k in local:
                fail(where, "declared twice in this section (the second one wins)")
            local.add(k)

            # whole numbers only in fields the engine parses as ints
            if any(k == want or k.endswith("." + want) for want in INT_KEYS):
                for field in re.findall(r"-?\d+\.\d+", value):
                    fail(where, f"fractional value {field} in an integer field")

            if k in ("spriteno", "spr"):
                m = re.match(r"\s*(-?\d+)\s*,\s*(-?\d+)", value)
                if m and ids:
                    pair = (int(m.group(1)), int(m.group(2)))
                    if pair not in ids:
                        fail(where, f"sprite {pair[0]},{pair[1]} missing from "
                                    f"{os.path.basename(sff_path)}")

            if k == "anim" and has_own_air:
                m = re.match(r"\s*(-?\d+)\s*$", value)
                if m and -1 not in (int(m.group(1)),) and int(m.group(1)) not in actions:
                    fail(where, f"anim {value} has no [Begin Action {value}] in this file")

            # any path with a known audio extension has to exist on disk
            low_value = value.lower()
            if low_value.endswith(SOUND_EXTS) and not value.startswith(";"):
                cand = value.replace("\\", "/").strip()
                if not (os.path.isfile(os.path.join(ROOT, cand))
                        or os.path.isfile(os.path.join(ROOT, "sound", os.path.basename(cand)))):
                    fail(where, f"audio file {value} does not exist")


def main():
    targets = [os.path.join(ROOT, "data", "ikemen1", n)
               for n in ("system.def", "logo.def", "credits.def")]
    targets.append(os.path.join(ROOT, "data", "fight.def"))
    stage_dir = os.path.join(ROOT, "stages")
    if os.path.isdir(stage_dir):
        targets += [os.path.join(stage_dir, n) for n in sorted(os.listdir(stage_dir))
                    if n.lower().endswith(".def")]
    targets = [t for t in targets if os.path.isfile(t)]

    for path in targets:
        audit_def(path)
        print(f"  audited {os.path.relpath(path, ROOT).replace(os.sep, '/')}")

    if not findings:
        print(f"\nAll clean: {len(targets)} DEF(s), no sprite/sound/anim/int problems.")
        return 0

    print(f"\n{len(findings)} problem(s):\n")
    for line in findings:
        print("  " + line)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
