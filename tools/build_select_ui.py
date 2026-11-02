"""Bake the stage-select hint into the character-select screen.

The screenpack can already show and change the stage before a match: [Select
Info] in system.def has the stage name block (``stage.pos``, ``stage.font``,
``stage.active.font``, ``stage.done.font``) and the portrait window
(``stage.portrait.spr = 9000,1``, ``stage.portrait.window = 521,567,759,665``),
and select.def's [ExtraStages] is the list it walks. What nothing on screen says
is that the stage can be changed - so this paints a hint strip into system.sff
(group 221, unused by the engine's own art) and adds it to [SelectBGdef] just
above the stage name.

The strip names no keys: which input moves the stage cursor is the engine's
select-screen input, not a motif parameter, so the hint shows the affordance
(arrows around the word) rather than a binding that could be wrong.

Run:  python3 tools/build_select_ui.py
"""

from __future__ import annotations

import os
import re
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageStat

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art
import sff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYSTEM_SFF = os.path.join(ROOT, "data", "ikemen1", "system.sff")
SYSTEM_DEF = os.path.join(ROOT, "data", "ikemen1", "system.def")

# The hint sits just above the stage name, which the motif draws at 640,707 in
# its 1280x720 select-screen space.
SPRITE = (221, 0)
STRIP = (300, 30)
POS = (0, 700)

GOLD = (255, 214, 96)
GOLD_DEEP = (120, 78, 16)
INK = (12, 10, 24)


def chevron(d, x, y, size, facing, fill):
    """A solid triangular arrow pointing left (-1) or right (+1)."""
    d.polygon([(x - facing * size, y - size), (x - facing * size, y + size),
               (x + facing * size, y)], fill=fill)


def hint_strip():
    """The painted affordance: dark plate, gold rule, arrows either side."""
    scale = 3
    w, h = STRIP[0] * scale, STRIP[1] * scale
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    plate = [scale * 2, scale * 2, w - scale * 2, h - scale * 2]
    d.rounded_rectangle(plate, radius=scale * 6, fill=INK + (190,),
                        outline=GOLD_DEEP + (255,), width=scale)
    d.rounded_rectangle([plate[0] + scale, plate[1] + scale,
                         plate[2] - scale, plate[3] - scale],
                        radius=scale * 5, outline=GOLD + (150,), width=max(1, scale // 2))

    text = "CHANGE STAGE"
    size = 0.9 * h
    font = art.font(int(round(size)))
    while font.getlength(text) > (w * 0.62) and size > 8:
        size -= 1
        font = art.font(int(round(size)))
    box = font.getbbox(text)
    tw, th = box[2] - box[0], box[3] - box[1]
    tx = (w - tw) // 2 - box[0]
    ty = (h - th) // 2 - box[1]
    # a dark pass under the type keeps it legible over the plate's own gradient
    d.text((tx, ty), text, font=font, fill=(0, 0, 0, 210),
           stroke_width=max(1, scale // 2), stroke_fill=(0, 0, 0, 210))
    d.text((tx, ty - scale // 2), text, font=font, fill=GOLD + (255,))

    mid = h // 2
    for facing in (-1, 1):
        base_x = scale * 12 if facing < 0 else w - scale * 12
        chevron(d, base_x, mid, scale * 5, facing, GOLD + (255,))
        chevron(d, base_x + facing * scale * 3, mid, scale * 3, facing,
                GOLD + (170,))

    img = img.filter(ImageFilter.GaussianBlur(0.5 * scale))
    return img.resize(STRIP, Image.LANCZOS)


def write_sprite(image, axis=(STRIP[0] // 2, STRIP[1] // 2)):
    _d, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    out, replaced = [], False
    for sp in sprites:
        if (sp["group"], sp["number"]) == SPRITE:
            out.append({"group": SPRITE[0], "number": SPRITE[1],
                        "image": image, "axis": axis})
            replaced = True
        else:
            out.append({"group": sp["group"], "number": sp["number"],
                        "raw": sp["raw"], "format": sp["format"],
                        "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                        "axis": sp["axis"], "pal": sp["pal"],
                        "link": sp["link"]})
    if not replaced:
        out.append({"group": SPRITE[0], "number": SPRITE[1], "image": image,
                    "axis": axis})

    blob = sff.write_sff(out, [p["rgba"] for p in palettes])
    if blob[:12] != sff.SIG:
        raise SystemExit("refusing to write: built file has no SFF signature")
    with open(SYSTEM_SFF + ".tmp", "wb") as f:
        f.write(blob)
    os.replace(SYSTEM_SFF + ".tmp", SYSTEM_SFF)
    return len(out)



# The stage preview art (group 9000,1 on every stage) is 1215x398 with its axis
# at its centre. The card used to be 580x190 at scale .4774 - a third of the
# screen - so a picture of the whole stage read as a thumbnail. It is 760x249
# now, and it is anchored per screen: [Select Info] puts stage.pos at 640,660
# and [VS Screen] at 640,707, and both used the offsets computed for the first
# one, so the VS card sat 47px low with its bottom cut off by its own window -
# a small picture perched on a gold band.
STAGE_ART = (1215, 398)
CARD_W = 760
PLATE_SPR = (324, 106)


def _card(centre_y, stage_y):
    """Stage preview + its plate, anchored to a screen whose stage.pos is known."""
    w = CARD_W
    h = int(round(w * STAGE_ART[1] / float(STAGE_ART[0])))
    left, top = 640 - w // 2, centre_y - h // 2
    scale = w / float(STAGE_ART[0])
    plate = w / float(PLATE_SPR[0])
    return (
        ("stage.portrait.spr", "9000,1"),
        ("stage.portrait.offset", "0, %d" % (centre_y - stage_y)),
        ("stage.portrait.scale", "%.4f, %.4f" % (scale, scale)),
        ("stage.portrait.window",
         "%d, %d, %d, %d" % (left, top, left + w, top + h)),
        ("stage.portrait.bg.offset", "%d, %d" % (left - 640, top - stage_y)),
        ("stage.portrait.bg.scale", "%.4f, %.4f" % (plate, plate)),
    )


STAGE_PORTRAIT = _card(500, 660)      # [Select Info]: clear of the stage name
SELECT_PLATE = STAGE_PORTRAIT + (
    # the select screen draws the plate as [Begin Action 110]; pin it to its
    # first sprite so the anim's own offsets cannot shift the scaled plate
    ("stage.portrait.bg.anim", "-1"),
    ("stage.portrait.bg.spr", "110,0"),
)
VS_PLATE = _card(540, 707) + (
    ("stage.portrait.bg.spr", "112,0"),
)

# Text on the VS screen. The caption under the card was DEEP (176,126,44) on a
# near-black backdrop, which is what made it read as the wrong colour - it was
# nearly invisible - and the two names were within a few units of each other, so
# both sides looked like the same orange. P1 is the motif's bright cream, P2 a
# warmer amber, and the caption is legible.
VS_TEXT = (
    ("p1.name.font", "10, 0, 1, 255, 228, 140"),
    ("p2.name.font", "10, 0, -1, 255, 170, 96"),
    ("stage.font", "11, 0, 0, 255, 228, 140"),
)


def _apply_section(text, section, pairs):
    """Set keys inside one [section] block only."""
    start = text.find(section)
    if start < 0:
        return text, []
    nxt = re.compile(r"^\[", re.M).search(text, start + len(section))
    end = nxt.start() if nxt else len(text)
    head, body, tail = text[:start], text[start:end], text[end:]
    changed = []
    for key, value in pairs:
        pat = re.compile(rf"^;?[ \t]*{re.escape(key)}[ \t]*=[^\r\n]*$", re.M)
        if pat.search(body):
            new = pat.sub(f"{key} = {value}", body, count=1)
        else:
            new = body.rstrip("\r\n") + f"\n{key} = {value}\n"
        if new != body:
            changed.append(f"{section} {key}")
        body = new
    return head + body + tail, changed


def layout(text):
    """Switch the stage preview on in both screens that draw it."""
    changed = []
    for section, extra in (("[Select Info]", SELECT_PLATE),
                           ("[VS Screen]", VS_PLATE + VS_TEXT)):
        text, done = _apply_section(text, section, extra)
        changed += done
    return text, changed

def layer_block():
    return (
        "\n;------------------------------------\n"
        "; Stage-select hint, painted by tools/build_select_ui.py\n"
        "[SelectBG Stage Hint]\n"
        "type = normal\n"
        f"spriteno = {SPRITE[0]}, {SPRITE[1]}\n"
        f"start = {POS[0]}, {POS[1]}\n"
        "layerno = 2\n"
        "mask = 1\n"
    )


# The stock plate behind the stage preview ([Begin Action 110], group 110) is a
# grey panel with a large question mark printed on it. The engine draws the
# preview over it, so any uncovered pixel of that art reads as an error - and
# the motif shipped with the preview switched off, which made the "?" the whole
# box. Repainting the plate removes the question mark entirely: the slot then
# reads as an empty picture frame until a preview is drawn in it.
FRAME_GROUP = 110
FRAME_NUMBERS = (0, 1, 2)


def frame_plate(w, h):
    """A dark plate with the same gold rule as the rest of the screenpack."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], fill=(16, 13, 20, 205),
                outline=GOLD_DEEP + (255,), width=2)
    d.rectangle([2, 2, w - 3, h - 3], outline=GOLD + (140,), width=1)
    return img


def clean_frames():
    """Repaint the stage-preview frame without its question mark."""
    _d, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    out, replaced = [], 0
    for sp in sprites:
        if sp["group"] == FRAME_GROUP and sp["number"] in FRAME_NUMBERS:
            out.append({"group": sp["group"], "number": sp["number"],
                        "image": frame_plate(sp["w"], sp["h"]),
                        "axis": sp["axis"]})
            replaced += 1
        else:
            out.append({"group": sp["group"], "number": sp["number"],
                        "raw": sp["raw"], "format": sp["format"],
                        "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                        "axis": sp["axis"], "pal": sp["pal"],
                        "link": sp["link"]})
    blob = sff.write_sff(out, [p["rgba"] for p in palettes])
    if blob[:12] != sff.SIG:
        raise SystemExit("refusing to write: built file has no SFF signature")
    with open(SYSTEM_SFF + ".tmp", "wb") as f:
        f.write(blob)
    os.replace(SYSTEM_SFF + ".tmp", SYSTEM_SFF)
    return replaced


# The VS screen's logo and "NEXT MATCH" banner are the engine's own silver
# chrome art (groups 200 and 202), which reads as a different game beside the
# gold-and-red wordmark used everywhere else. A .def cannot tint a sprite, so
# the colour is baked instead: each sprite's luminance is pushed through the
# logo's own ramp, which keeps its shading and hard outline, and the alpha is
# left alone. Pixels that are already coloured are kept as they are, so a
# second build does not shift the art again.
RAMP = ((0.00, (255, 246, 206)), (0.30, (255, 204, 96)),
        (0.62, (238, 122, 44)), (1.00, (146, 24, 30)))
VS_ART_GROUPS = (200, 202)


def _ramp_colour(t):
    for i in range(len(RAMP) - 1):
        t0, c0 = RAMP[i]
        t1, c1 = RAMP[i + 1]
        if t0 <= t <= t1:
            k = (t - t0) / max(1e-6, t1 - t0)
            return tuple(int(c0[j] + (c1[j] - c0[j]) * k) for j in range(3))
    return RAMP[-1][1]


def _is_warm(img):
    """True when the art already carries this ramp, so a rebuild is a no-op.

    Without it every build would multiply the shading in again and the logo
    would creep darker each time data/ was rebuilt.
    """
    stat = ImageStat.Stat(img.convert("RGB"), img.getchannel("A"))
    r, _g, b = stat.mean
    return (r - b) > 45 and r > 90


def goldify(img):
    """Repaint a silver sprite as the wordmark's gold, shaded down to red.

    The colour comes from a vertical gradient over the sprite rather than from
    its own luminance. The engine's VS art is chrome with a hard light/dark
    split down the middle; ramping *that* printed a band straight across the
    logo. Here the gradient runs cream -> gold -> red from top to bottom, the
    source's shading only multiplies it, and the near-black outline is kept
    exactly as it was so the silhouette still reads against the sky.
    """
    img = img.convert("RGBA")
    w, h = img.size
    if _is_warm(img):
        return img
    strip = Image.new("RGB", (1, max(1, h)))
    put = strip.load()
    for y in range(max(1, h)):
        put[0, y] = _ramp_colour(y / float(max(1, h - 1)))
    body = strip.resize((w, h)).convert("RGB")
    lum = img.convert("L")
    # Blur the source shading before it multiplies the gradient. The chrome art
    # has one hard light/dark split down its middle, and multiplying that
    # unblurred printed a seam across the logo; softened, it only models the
    # face, and the gradient carries the colour.
    smooth = lum.filter(ImageFilter.GaussianBlur(max(2, h // 22)))
    shade = smooth.point(lambda v: 96 + int(v * 0.66))
    body = ImageChops.multiply(body, Image.merge("RGB", (shade, shade, shade)))
    outline = lum.point(lambda v: 255 if v < 44 else 0)
    out = Image.composite(img.convert("RGB"), body, outline).convert("RGBA")
    out.putalpha(img.getchannel("A"))
    return out


def retint_vs_art():
    """Bake the game's colours into the engine's silver VS-screen art."""
    raw, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    out, done = [], 0
    for sp in sprites:
        if sp["group"] in VS_ART_GROUPS:
            img = sff.decode_sprite(raw, sp, palettes)
            out.append({"group": sp["group"], "number": sp["number"],
                        "image": goldify(img), "axis": sp["axis"]})
            done += 1
        else:
            out.append({"group": sp["group"], "number": sp["number"],
                        "raw": sp["raw"], "format": sp["format"],
                        "depth": sp["depth"], "w": sp["w"], "h": sp["h"],
                        "axis": sp["axis"], "pal": sp["pal"],
                        "link": sp["link"]})
    blob = sff.write_sff(out, [p["rgba"] for p in palettes])
    if blob[:12] != sff.SIG:
        raise SystemExit("refusing to write: retinted system.sff has no signature")
    with open(SYSTEM_SFF + ".tmp", "wb") as f:
        f.write(blob)
    os.replace(SYSTEM_SFF + ".tmp", SYSTEM_SFF)
    return done


def patch_def():
    """Fix the stage preview, then add the hint layer to [SelectBGdef] once.

    The layout pass runs on every build: it used to sit behind the "hint not
    added yet" check below, so after the first run the stage preview was never
    switched back on when data/ was reset from the engine copy.
    """
    with open(SYSTEM_DEF, encoding="utf-8", errors="replace") as f:
        text = f.read()
    text, changed = layout(text)
    print("  system.def layout: " + (", ".join(changed) or "already set"))
    added = False
    if f"spriteno = {SPRITE[0]}, {SPRITE[1]}" not in text:
        marker = "\n[VS Screen]"
        if marker not in text:
            raise SystemExit("system.def has no [VS Screen]; cannot place the hint")
        text = text.replace(marker, layer_block() + marker, 1)
        added = True
    with open(SYSTEM_DEF + ".tmp", "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(SYSTEM_DEF + ".tmp", SYSTEM_DEF)
    return added


def build():
    if not os.path.isfile(SYSTEM_SFF) or not os.path.isfile(SYSTEM_DEF):
        raise SystemExit("data/ikemen1 is missing - fetch the engine data first")

    strip = hint_strip()
    total = write_sprite(strip)
    frames = clean_frames()
    tinted = retint_vs_art()
    added = patch_def()

    # Read back: the hint is worth nothing if the layer points at nothing.
    _d, sprites, _p = sff.read_sff(SYSTEM_SFF)
    have = {(sp["group"], sp["number"]) for sp in sprites}
    if SPRITE not in have:
        raise SystemExit(f"hint sprite {SPRITE} did not make it into system.sff")
    with open(SYSTEM_DEF, encoding="utf-8", errors="replace") as f:
        text = f.read()
    if f"spriteno = {SPRITE[0]}, {SPRITE[1]}" not in text:
        raise SystemExit("system.def does not reference the hint sprite")

    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    strip.save(os.path.join(ROOT, "artifacts", "select_hint.png"))
    print(f"stage-select hint: sprite {SPRITE[0]},{SPRITE[1]} "
          f"({'added' if total else 'kept'}), frame repaints {frames}, "
          f"VS art retinted {tinted}, "
          f"SelectBG layer {'added' if added else 'already present'}")


if __name__ == "__main__":
    build()
