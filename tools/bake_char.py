"""Bake a puppet rig into engine data: an SFF plus a matching AIR.

The rig draws 17 poses; a character needs 121 actions / 666 frames. This walks
the existing AIR, keeps every action number, frame count and frame duration,
and swaps the art for rig renders - so nothing the state files expect goes
missing. Collision boxes are scaled by the same factor as the figure.

Run:  python3 tools/bake_char.py jackburton
"""

from __future__ import annotations

import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import char_rig
import sff
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_HEIGHT = 318.0     # 3x the 106px base fighter
BASE_HEIGHT = 106.0


def pose_for(action, frame):
    """Which rig pose stands in for this animation."""
    a = action
    if a <= 5:
        return "stance" if frame % 2 == 0 else "breath"
    if a in (6, 10, 11, 12):
        return "crouch"
    if 20 <= a <= 29:
        return "walk_a" if frame % 2 == 0 else "walk_b"
    if 40 <= a <= 59:
        return "jump"
    if 100 <= a <= 109:
        return "cross" if a % 2 else "jab"
    if 110 <= a <= 119:
        return "crouch"
    if 120 <= a <= 129:
        return "jump"
    if 130 <= a <= 139:
        return "boot"
    if 140 <= a <= 149:
        return "low_kick"
    if 150 <= a <= 159:
        return "block"
    if 180 <= a <= 199:
        return "win"
    if 160 <= a <= 179:
        return "hit"
    if 5000 <= a <= 5210:
        return "hit"
    if 7000 <= a <= 7009:
        return "gun_fire"
    if 7010 <= a <= 7029:
        return "knife_throw"
    return "stance"


def parse_air(text):
    actions, cur = {}, None
    for raw in text.splitlines():
        line = raw.split(";", 1)[0].strip()
        m = re.match(r"\[Begin Action\s+(\d+)\]", line)
        if m:
            cur = int(m.group(1))
            actions[cur] = {"clsn": [], "frames": []}
            continue
        if cur is None or not line:
            continue
        if line.lower().startswith("clsn"):
            actions[cur]["clsn"].append(raw.rstrip())
            continue
        fm = re.match(r"^(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)", line)
        if fm:
            actions[cur]["frames"].append(int(fm.group(5)))
    return actions


def scale_clsn(line, k):
    def mul(m):
        return str(int(round(int(m.group(0)) * k)))
    return re.sub(r"-?\d+", mul, line, count=0) if "=" in line else line


def bake(char_id, target_height=TARGET_HEIGHT):
    src = os.path.join(ROOT, "chars", char_id)
    out = os.path.join(ROOT, "chars", char_id + "_rig")
    os.makedirs(out, exist_ok=True)

    work = os.path.join(ROOT, "art_src", "chars", char_id, "work", "front.png")
    art_h = Image.open(work).height if os.path.isfile(work) else 607.0
    k = target_height / art_h
    clsn_k = target_height / BASE_HEIGHT

    rig = char_rig.load_rig(char_id)
    sprites = []

    actions = parse_air(open(os.path.join(src, char_id + ".air"), encoding="utf-8-sig").read())
    print(f"{len(actions)} actions, {sum(len(a['frames']) for a in actions.values())} frames")

    air_out = []
    for number in sorted(actions):
        act = actions[number]
        frames = act["frames"] or [4]
        air_out.append(f"; baked from the rig\n[Begin Action {number}]")
        air_out.extend(act["clsn"])
        # AIR frames are (group, number) - the sprite's number INSIDE its own
        # group, not a global index. Using a global index left 110 frame
        # references pointing at sprites that did not exist.
        local = {}
        for i, ticks in enumerate(frames):
            pose_name = pose_for(number, i)
            if pose_name not in local:
                img = char_rig.render(rig, char_rig.POSES[pose_name])
                img = img.resize((max(1, round(img.width * k)),
                                  max(1, round(img.height * k))), Image.LANCZOS)
                axis = (round(rig.axis[0] * k), round(rig.axis[1] * k))
                local[pose_name] = len(local)
                sprites.append({"group": number, "number": local[pose_name],
                                "image": img, "axis": axis})
            air_out.append(f"{number},{local[pose_name]}, 0,0, {ticks}")
        air_out.append("")

    palette = bytearray()
    for i in range(256):
        palette += bytes((i, i, i, 255))
    data = sff.write_sff(sprites, [bytes(palette)])
    open(os.path.join(out, char_id + ".sff"), "wb").write(data)
    open(os.path.join(out, char_id + ".air"), "w", encoding="utf-8").write(
        "\n".join(air_out) + "\n")

    for name in (f"{char_id}.cns", f"{char_id}.cmd", "common1.cns",
                 f"{char_id}.snd", "movelist.dat"):
        p = os.path.join(src, name)
        if os.path.isfile(p):
            shutil.copy(p, os.path.join(out, name))

    def_text = f"""[Info]
name = "Jack Burton (rig)"
displayname = "Jack Burton"
versiondate = 10,29,2026
mugenversion = 1.0
author = "Big Trouble in Little China: The Game"
pal.defaults = 1

[Files]
cmd      = {char_id}.cmd
cns      = {char_id}.cns
st       = {char_id}.cns
stcommon = common1.cns
sprite   = {char_id}.sff
anim     = {char_id}.air
sound    = {char_id}.snd
movelist = movelist.dat

[Size]
height   = {int(target_height * 0.62)}
mid.pos  = 0,{int(-target_height * 0.48)}
head.pos = 0,{int(-target_height * 0.92)}
ground.back  = {int(28 * clsn_k)}
ground.front = {int(24 * clsn_k)}
air.back     = {int(-24 * clsn_k)}
air.front    = {int(24 * clsn_k)}
attack.dist  = {int(160 * clsn_k)}
"""
    open(os.path.join(out, char_id + ".def"), "w", encoding="utf-8").write(def_text)
    print(f"wrote {len(sprites)} sprites, {len(air_out)} AIR lines -> chars/{char_id}_rig")
    return out


if __name__ == "__main__":
    bake(sys.argv[1] if len(sys.argv) > 1 else "jackburton")
