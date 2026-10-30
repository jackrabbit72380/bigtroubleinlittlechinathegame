"""Build the Big Trouble in Little China roster from the bundled Kung Fu Man base.

Kung Fu Man's art is LZ5-compressed 32-colour indexed sprites, so each fighter
is coloured by baking a graded copy of the palette table into their own SFF.
Sprite payloads are copied verbatim, which keeps every folder small and keeps
the animations pixel-identical to the base character.

Run:  python3 tools/build_chars.py
"""

from __future__ import annotations

import os
import re
import shutil
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art
import jackburton
import lightning
import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "chars", "kfm")

# id, name, palette transform (hue shift in degrees, saturation, value), stats
ROSTER = [
    dict(
        id="jackburton", name="Jack Burton", display="Jack Burton",
        pal=(205, 0.85, 1.12), life=1050, attack=108, defence=100,
        extra=jackburton,
        xscale=1.0, yscale=1.0, order=0,
        blurb="Truck driver. Reluctant hero. Owns one very good knife.",
        moves=dict(throw="Trucker Toss", palm="Pork Chop Palm", upper="Reflex Upper",
                   blow="Six-Dollar Blow", zankou="Knife Hand",
                   knee="Big Boot", super1="It's All in the Reflexes",
                   super2="Pork Chop Express"),
        quotes=[
            "You leave Jack Burton alone! We are in his debt.",
            "It's all in the reflexes.",
            "I'm a reasonable guy. But I've just experienced some very unreasonable things.",
            "You know what ol' Jack Burton says at a time like this?",
            "Have you paid your dues, friend?",
            "Son of a bitch must pay.",
            "The check is in the mail.",
        ],
    ),
    dict(
        id="wangchi", name="Wang Chi", display="Wang Chi",
        pal=(355, 1.25, 1.05), life=950, attack=108, defence=95,
        xscale=1.0, yscale=1.0, order=2,
        blurb="Green-eyed restaurateur and the best friend you could ask for.",
        moves=dict(throw="Green Eyes Throw", palm="Restaurant Palm",
                   upper="Nephew Upper", blow="Fiancee Rescue",
                   zankou="Cleaver Strike", knee="Crane Kick",
                   super1="Two Green Eyes", super2="Wang's Fury"),
        quotes=[
            "We're going to get Miao Yin back.",
            "You are not my friend, Lo Pan.",
            "My green eyes see everything.",
            "Try again, old man.",
            "This is for Miao Yin.",
            "The Dragon of the Black Pool never closes.",
            "Not bad for a restaurant owner.",
        ],
    ),
    dict(
        id="eggshen", name="Egg Shen", display="Egg Shen",
        pal=(32, 1.35, 1.0), life=900, attack=115, defence=88,
        xscale=0.97, yscale=0.97, order=3,
        blurb="Bus driver, tour guide, and the greatest sorcerer in Chinatown.",
        moves=dict(throw="Six Demon Toss", palm="Hex Palm", upper="Bag Upper",
                   blow="Thunder Scroll", zankou="Chicken Feather",
                   knee="Bus Driver Kick", super1="Six Demon Bag",
                   super2="Egg Shen's Ritual"),
        quotes=[
            "We take what we want from the Six Demon Bag.",
            "I'm a reasonable guy, but I've seen some very unreasonable things.",
            "Black blood of the earth!",
            "You want to know what's in the bag? Look inside.",
            "The potion works. Ask the Wildman.",
            "Old magic beats new tricks.",
            "Lo Pan fears the bag.",
        ],
    ),
    dict(
        id="gracielaw", name="Gracie Law", display="Gracie Law",
        pal=(315, 1.3, 1.12), life=880, attack=94, defence=92,
        xscale=0.96, yscale=0.96, order=2,
        blurb="Lawyer, reporter, and the only adult in the room.",
        moves=dict(throw="Due Process", palm="Lawyer's Slap", upper="Scoop Upper",
                   blow="Front Page", zankou="Cross-Examine",
                   knee="Deadline Kick", super1="Interview with a Demon",
                   super2="Federal Injunction"),
        quotes=[
            "I want the truth and I want it on the record.",
            "You cannot just go around kidnapping people!",
            "This is the story of a lifetime.",
            "I have a lawyer. I am a lawyer.",
            "Somebody get me a phone!",
            "That is not a legal contract, Lo Pan.",
            "Off the record? Fine. You lose.",
        ],
    ),
    dict(
        id="thunder", name="Thunder", display="Thunder",
        pal=(14, 0.8, 0.9), life=1200, attack=115, defence=112,
        xscale=1.12, yscale=1.12, order=2,
        blurb="One of the Three Storms. Speaks in thunder, hits like a truck.",
        moves=dict(throw="Storm Slam", palm="Thunder Palm", upper="Warrior Upper",
                   blow="Storm Blow", zankou="Axe Hand", knee="Earthshaker",
                   super1="Thunder Roar", super2="Three Storms"),
        quotes=[
            "Shut up, Mr. Burton!",
            "You are not invited to the wedding.",
            "Thunder does not negotiate.",
            "The hell of boiling oil awaits you!",
            "You have no manners.",
            "I will teach you respect.",
            "The storm always comes back.",
        ],
    ),
    dict(
        id="rain", name="Rain", display="Rain",
        pal=(175, 1.1, 1.05), life=950, attack=100, defence=96,
        xscale=0.99, yscale=1.0, order=1,
        blurb="The quiet one of the Three Storms, quick as falling water.",
        moves=dict(throw="Rain Drop", palm="Storm Palm", upper="Downpour Upper",
                   blow="Flood Blow", zankou="Slick Hand",
                   knee="Rising Tide", super1="Rain of Blades", super2="Storm Front"),
        quotes=[
            "Rain falls where it wants.",
            "You were warned.",
            "The wedding will go on.",
            "You fight like a wet paper bag.",
            "One more drop is all it takes.",
            "Chinatown is ours at night.",
            "I do not need to shout.",
        ],
    ),
    dict(
        id="lightning", name="Lightning", display="Lightning",
        pal=(272, 1.35, 1.1), life=1000, attack=105, defence=100,
        extra=lightning,
        xscale=1.0, yscale=1.0, order=1,
        blurb="Fastest of the Three Storms, all narrow eyes and quicker hands.",
        moves=dict(throw="Bolt Throw", palm="Volt Palm", upper="Flash Upper",
                   blow="Static Blow", zankou="Arc Hand",
                   knee="Thunder Step", super1="Chain Lightning",
                   super2="Storm of the Three"),
        quotes=[
            "Too slow, old man.",
            "You blink. You lose.",
            "Lightning never strikes twice. It does not need to.",
            "I was behind you the whole time.",
            "The Three Storms are eternal.",
            "Lo Pan commands. We obey.",
            "Shall I light up the room?",
        ],
    ),
    dict(
        id="lopan", name="David Lo Pan", display="Lo Pan",
        pal=(105, 1.15, 0.95), life=1300, attack=125, defence=112,
        xscale=1.1, yscale=1.08, order=4,
        blurb="Ghost emperor, sorcerer, and very bad wedding planner.",
        moves=dict(throw="Thousand Year Grip", palm="Fire of Lo Pan",
                   upper="Emperor's Judgment", blow="Curse of the No-Name",
                   zankou="Skull Hand", knee="Ghost Emperor Kick",
                   super1="Hell of Boiling Oil", super2="Wedding of Blood"),
        quotes=[
            "You will bow before Lo Pan!",
            "I have been waiting two thousand years for this.",
            "Little man, you have no idea what you are fighting.",
            "Your soul is already mine.",
            "The Three Storms serve me. Even now they watch.",
            "There is no escape from the throne.",
            "You are nothing but a grain of rice.",
        ],
    ),
]

DEF_TEMPLATE = """; Character definition for {name}
; Big Trouble in Little China: The Game (Ikemen GO)
; Generated by tools/build_chars.py from the Kung Fu Man base.

[Info]
name = "{name}"
displayname = "{display}"
versiondate = 10,28,2026
mugenversion = 1.0
author = "Big Trouble in Little China: The Game"
pal.defaults = 1   ; palette 1 is baked into {cid}.sff

[Files]
cmd      = {cid}.cmd
cns      = {cid}.cns
st       = {cid}.cns
stcommon = common1.cns
sprite   = {cid}.sff
anim     = {cid}.air
sound    = {cid}.snd
movelist = movelist.dat
"""

MOVELIST = """<#f0f000>:Movement:</>
Walk, jump, crouch\t\t\t\t\t\t_DPAD_
Dash forward / back\t\t\t\t\t\t_F_F_ / _B_B_

<#f0f000>:Guard:</>
High guard\t\t\t\t\t\t\t_F_+^X
Low guard\t\t\t\t\t\t\t_DF_+^X
Air guard\t\t\t\t\t\t\t_AIR_F_+^X

<#f0f000>:Throws:</>
{throw}\t\t\t\t\t\t\t[_B/_F]_+^Y

<#f0f000>:Special Moves:</>
{palm}\t\t\t\t\t\t\t_QDF^P
{upper}\t\t\t\t\t\t\t_DSF^P
{blow}\t\t\t\t\t\t\t\t_QDB^P
{zankou}\t\t\t\t\t\t\t\t_QDF^K
{knee}\t\t\t\t\t\t\t\t_F_F^K
{extra_specials}
<#f0f000>:Super Moves:</>
{super1} <#bebebe>(1000)</>\t\t\t\t_QDF_QDF^P
{super2} <#bebebe>(1000)</>\t\t\t\t_QDB_QDB^P
"""


# ------------------------------------------------------------------ colour work
def _rgb_to_hsv(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d == 0:
        h = 0.0
    elif mx == r:
        h = ((g - b) / d) % 6
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    h /= 6.0
    s = 0.0 if mx == 0 else d / mx
    return h, s, mx


def _hsv_to_rgb(h, s, v):
    i = int(h * 6) % 6
    f = h * 6 - int(h * 6)
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    r, g, b = [(v, t, p), (q, v, p), (p, v, t),
               (p, q, v), (t, p, v), (v, p, q)][i]
    return int(r * 255), int(g * 255), int(b * 255)


def grade_colour(rgb, spec):
    """Hue-rotate and grade one colour, keeping skin, whites and blacks neutral.

    Only the clothing colours are meant to move. Grading everything turned faces
    magenta and hands cyan, so skin tones and near-neutral pixels pass through
    untouched and the fighter keeps his own face.
    """
    hue, sat, val = _rgb_to_hsv(*rgb)
    if val < 0.06:                      # keep outlines black
        return rgb
    if sat < 0.12:                      # whites and greys stay neutral
        return rgb
    if 0.010 <= hue <= 0.110 and 0.15 <= sat <= 0.75 and val >= 0.30:
        return rgb                      # skin: shifting this turns faces neon
    sat_shift = spec["pal"][1]
    val_shift = spec["pal"][2]
    hue = (hue + spec["pal"][0] / 360.0) % 1.0
    sat = min(1.0, sat * sat_shift)
    val = min(1.0, val * val_shift)
    return _hsv_to_rgb(hue, sat, val)


def grade_palette(rgba, spec):
    out = bytearray()
    for i in range(0, len(rgba) - 3, 4):
        r, g, b, a = rgba[i], rgba[i + 1], rgba[i + 2], rgba[i + 3]
        if a == 0:
            out += bytes((r, g, b, 0))
            continue
        nr, ng, nb = grade_colour((r, g, b), spec)
        out += bytes((nr, ng, nb, a))
    return bytes(out)


# ------------------------------------------------------------------- text files
def split_sections(text):
    return re.split(r"(?m)(?=^\[[^\]]+\])", text)


def edit_cns(text, spec):
    out = []
    for chunk in split_sections(text):
        head = chunk.lstrip().split("\n", 1)[0].strip().lower()
        if head == "[data]":
            chunk = re.sub(r"(?mi)^life\s*=.*$", f"life = {spec['life']}", chunk)
            chunk = re.sub(r"(?mi)^attack\s*=.*$", f"attack = {spec['attack']}", chunk)
            chunk = re.sub(r"(?mi)^defence\s*=.*$", f"defence = {spec['defence']}", chunk)
        elif head == "[size]":
            chunk = re.sub(r"(?mi)^xscale\s*=.*$", f"xscale = {spec['xscale']}", chunk)
            chunk = re.sub(r"(?mi)^yscale\s*=.*$", f"yscale = {spec['yscale']}", chunk)
        elif head == "[quotes]":
            quotes = "\n".join(
                f'victory{i + 1} = "{q}"' for i, q in enumerate(spec["quotes"]))
            chunk = "[Quotes]\n; Victory quotes (English)\n" + quotes + "\n\n"
        elif head.startswith("[ja."):
            continue
        out.append(chunk)
    return "".join(out)


def override_sprites(cid, sprites):
    """Replace individual sprite slots from art_src/chars/<id>/<group>_<number>.png.

    A dropped-in frame keeps the base sprite's axis, so a painted pose lands in
    the same place on screen as the frame it replaces. Anything not supplied
    keeps the generated/base art.
    """
    folder = os.path.join(ROOT, "art_src", "chars", cid)
    if not os.path.isdir(folder):
        return 0
    index = {(sp["group"], sp["number"]): i for i, sp in enumerate(sprites)}
    swapped = 0
    for name in sorted(os.listdir(folder)):
        m = re.match(r"^(-?\d+)_(\d+)\.png$", name)
        if not m:
            continue
        key = (int(m.group(1)), int(m.group(2)))
        if key not in index:
            continue
        img = Image.open(os.path.join(folder, name)).convert("RGBA")
        base = sprites[index[key]]
        sprites[index[key]] = {"group": key[0], "number": key[1],
                               "image": img, "axis": base["axis"]}
        swapped += 1
    if swapped:
        print(f"  {cid}: {swapped} painted sprite(s) from art_src/chars/{cid}/")
    return swapped


def build(spec, base_sprites, base_palettes):
    cid = spec["id"]
    dest = os.path.join(ROOT, "chars", cid)
    os.makedirs(dest, exist_ok=True)

    extra = spec.get("extra")
    shutil.copyfile(os.path.join(BASE, "kfm.snd"), os.path.join(dest, f"{cid}.snd"))

    air = open(os.path.join(BASE, "kfm.air"), encoding="utf-8-sig").read()
    if extra:
        air += extra.AIR
    with open(os.path.join(dest, f"{cid}.air"), "w", encoding="utf-8") as f:
        f.write(air)

    cmd = open(os.path.join(BASE, "kfm.cmd"), encoding="utf-8-sig").read()
    cmd = cmd.replace("; The CMD file.", f"; {spec['name']} - command file")
    if extra:
        cmd = cmd.replace("[Statedef -1]", extra.CMD_COMMANDS + "[Statedef -1]", 1)
        cmd = cmd.rstrip("\n") + "\n" + extra.CMD_STATES
    with open(os.path.join(dest, f"{cid}.cmd"), "w", encoding="utf-8") as f:
        f.write(cmd)

    cns = open(os.path.join(BASE, "kfm.cns"), encoding="utf-8-sig").read()
    for old, new in (("Kung Fu Palm", spec["moves"]["palm"]),
                     ("Kung Fu Throw", spec["moves"]["throw"]),
                     ("Kung Fu Knee", spec["moves"]["knee"]),
                     ("Kung Fu Upper", spec["moves"]["upper"]),
                     ("Kung Fu Blow", spec["moves"]["blow"]),
                     ("Kung Fu Zankou", spec["moves"]["zankou"])):
        cns = cns.replace(old, new)
    cns = edit_cns(cns, spec)
    if extra:
        cns = cns.rstrip("\n") + "\n" + extra.CNS
    with open(os.path.join(dest, f"{cid}.cns"), "w", encoding="utf-8") as f:
        f.write(cns)

    with open(os.path.join(dest, f"{cid}.def"), "w", encoding="utf-8") as f:
        f.write(DEF_TEMPLATE.format(name=spec["name"], display=spec["display"], cid=cid))

    moves = dict(spec["moves"])
    moves["extra_specials"] = extra.EXTRA_SPECIALS if extra else ""
    if not extra:
        moves["extra_specials"] = ""
    with open(os.path.join(dest, "movelist.dat"), "w", encoding="utf-8") as f:
        f.write(MOVELIST.format(**moves))

    # sprite set: identical art, palette table graded to this fighter
    sprites = [{"group": sp["group"], "number": sp["number"], "raw": sp["raw"],
                "format": sp["format"], "depth": sp["depth"], "w": sp["w"],
                "h": sp["h"], "axis": sp["axis"], "pal": sp["pal"],
                "link": sp["link"]}
               for sp in base_sprites]
    if extra:
        sprites += extra.sprites()
        palettes = extra.palettes(base_palettes, grade_palette, spec)
    else:
        palettes = [grade_palette(p["rgba"], spec) for p in base_palettes]
    override_sprites(cid, sprites)
    with open(os.path.join(dest, f"{cid}.sff"), "wb") as f:
        f.write(sff.write_sff(sprites, palettes))

    cns_out = open(os.path.join(dest, f"{cid}.cns"), encoding="utf-8").read()
    if f"life = {spec['life']}" not in cns_out:
        raise SystemExit(f"{cid}: life constant was not rewritten")
    if f"xscale = {spec['xscale']}" not in cns_out:
        raise SystemExit(f"{cid}: xscale constant was not rewritten")
    print(f"  {cid}: {spec['name']} (life {spec['life']}, atk {spec['attack']}, "
          f"def {spec['defence']}, {len(sprites)} sprites)")


def roster_sheet():
    """Contact sheet: the same pose from every generated fighter SFF."""
    cell_w, cell_h = 110, 190
    sheet = Image.new("RGBA", (cell_w * len(ROSTER), cell_h), (18, 18, 22, 255))
    label = art.font(11)
    draw = ImageDraw.Draw(sheet)
    for i, spec in enumerate(ROSTER):
        path = os.path.join(ROOT, "chars", spec["id"], f"{spec['id']}.sff")
        d, sprites, palettes = sff.read_sff(path)
        sp = next((s for s in sprites if s["group"] == 0 and s["number"] == 0),
                  sprites[0])
        img = sff.decode_sprite(d, sp, palettes)
        sheet.alpha_composite(img, (i * cell_w + (cell_w - img.width) // 2, 16))
        draw.text((i * cell_w + 6, cell_h - 24), spec["display"].split()[0],
                  font=label, fill=(226, 226, 232, 255))
    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    sheet.save(os.path.join(ROOT, "artifacts", "roster_palettes.png"))
    print("  wrote artifacts/roster_palettes.png")


def dump_frames(cid):
    """Export a painting template for every sprite slot the fighter references.

    One transparent PNG per (group, number), at the exact size the slot needs,
    with a magenta crosshair at the sprite axis. Drop finished frames into
    art_src/chars/<id>/ to replace just those slots. Templates land in a
    `templates/` subfolder so they never get picked up as finished art.
    """
    _d, sprites, _p = sff.read_sff(os.path.join(ROOT, "chars", cid, f"{cid}.sff"))
    by_key = {(sp["group"], sp["number"]): sp for sp in sprites}

    with open(os.path.join(ROOT, "chars", cid, f"{cid}.air"),
              encoding="utf-8-sig") as fh:
        air = fh.read()
    slots, action = {}, None
    for raw in air.splitlines():
        line = raw.split(";", 1)[0].strip()
        m = re.match(r"\[Begin Action (\d+)\]", line)
        if m:
            action = int(m.group(1))
            continue
        m = re.match(r"^(-?\d+)\s*,\s*(-?\d+)", line)
        if m and action is not None and int(m.group(1)) >= 0:
            slots.setdefault((int(m.group(1)), int(m.group(2))), set()).add(action)

    folder = os.path.join(ROOT, "art_src", "chars", cid, "templates")
    os.makedirs(folder, exist_ok=True)
    rows = []
    for (group, number), actions in sorted(slots.items()):
        sp = by_key.get((group, number))
        if not sp:
            continue
        img = Image.new("RGBA", (sp["w"], sp["h"]), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        ax, ay = sp["axis"]
        d.line([(ax - 4, ay), (ax + 4, ay)], fill=(255, 0, 255, 255))
        d.line([(ax, ay - 4), (ax, ay + 4)], fill=(255, 0, 255, 255))
        name = f"{group}_{number}.png"
        img.save(os.path.join(folder, name))
        rows.append(f"{name}\t{sp['w']} x {sp['h']}\taxis {ax}, {ay}\t"
                    f"actions {', '.join(str(a) for a in sorted(actions))}")

    with open(os.path.join(folder, "README.md"), "w", encoding="utf-8") as f:
        f.write(
            f"# {cid} sprite frames\n\n"
            "Each PNG is one frame, already at the size and axis the character\n"
            "needs. Paint the figure with its feet on the crosshair, keep the\n"
            "canvas size, delete the crosshair, then move the file up into\n"
            f"`art_src/chars/{cid}/` and rebuild. Frames left in `templates/`\n"
            "are ignored.\n\n"
            "| file | size | axis | used by action(s) |\n|---|---|---|---|\n")
        for row in rows:
            cells = row.split("\t")
            f.write("| " + " | ".join(cells) + " |\n")
    print(f"  {cid}: {len(rows)} frame templates in "
          f"art_src/chars/{cid}/templates/")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--dump":
        dump_frames(sys.argv[2] if len(sys.argv) > 2 else "jackburton")
        return
    if not os.path.isdir(BASE):
        raise SystemExit("chars/kfm base is missing")
    print("Building roster")
    d, sprites, palettes = sff.read_sff(os.path.join(BASE, "kfm.sff"))
    if not palettes:
        raise SystemExit("chars/kfm/kfm.sff has no palettes")
    for spec in ROSTER:
        build(spec, sprites, palettes)
    roster_sheet()


if __name__ == "__main__":
    main()
