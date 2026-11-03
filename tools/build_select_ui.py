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



# The stage card. Every stage bakes a 1215x398 establishing shot as sprite
# 9000,1 and both the select screen and the VS screen draw it. The card had
# grown to 760x249 and its window no longer matched its scale (the art was
# drawn at .4 = 486x159 inside a 760-wide clip), so the picture sat in a box of
# empty plate and overlapped the fourth row of the portrait grid, which ends at
# y=460. The card is 400x159 now - it clears the grid - and it carries its own
# name: the plate behind it has a dark band across the top, the art is clipped
# to the frame below that band, and the engine's stage text is moved up into
# the band, so the stage name sits on the card instead of under it.
STAGE_ART = (1215, 398)
CARD_W = 460
BAND_H = 30                              # the name band, under the art
ART_H = int(round(CARD_W * STAGE_ART[1] / float(STAGE_ART[0])))   # 151
CARD_H = ART_H + BAND_H                  # 181
CARD_CX = 640
# A stage's 9000,1 is drawn at (motif localcoord / stage localcoord) of the
# scale in the .def, which is 1280/1920 = 2/3 for these 1920-wide stages. At
# the card's own scale the picture landed 307px wide inside a 460px window - a
# postage stamp in a frame, which is what "the preview does not fill the box"
# looked like. Overscaling by that ratio makes the art cover the window and the
# window clip it, so the box is full whatever a stage's localcoord turns out
# to be.
MOTIF_LOCALCOORD = 1280
STAGE_LOCALCOORD = 1920
CARD_FILL = STAGE_LOCALCOORD / float(MOTIF_LOCALCOORD)
# 20px of cap height. The name used to be font 11 (the 13px Body face) at
# scale .5, i.e. six pixels tall: legible nowhere, least of all on a television.
# It is the Display face now at 20/34, which is what the rest of the screenpack
# draws its headings with, so the stage name reads at the same weight. The card
# is 60px wider for it, and its bottom edge moved down to 660 to keep the top
# clear of the portrait grid, which ends at y=460.
NAME_PX = 13
NAME_FONT = 11                           # Body, a 13px cell: the face the
                                         # engine sets VERSUS in


def _card(bottom_y):
    """The stage card and its name band, hung from a given bottom edge.

    The card is anchored by its bottom edge because that is where both screens
    had it before, so nothing else on either screen moves. Offsets are
    measured from ``stage.pos``, which now points at the name band rather than
    at a caption under the card, so every offset is computed from that point.
    """
    left = CARD_CX - CARD_W // 2
    top = bottom_y - CARD_H
    band_top = top + ART_H
    text_y = band_top + (BAND_H - NAME_PX) // 2
    scale = CARD_W / float(STAGE_ART[0]) * CARD_FILL
    # 9000,1's axis is the centre of the art, so place the art's centre
    art_centre = top + ART_H / 2.0
    return (
        ("stage.portrait.spr", "9000,1"),
        ("stage.portrait.offset", "0, %d" % int(round(art_centre - text_y))),
        ("stage.portrait.scale", "%.4f, %.4f" % (scale, scale)),
        # inset inside the plate's own 2px gold rule, or the art paints over
        # the frame and the card loses its outline
        ("stage.portrait.window",
         "%d, %d, %d, %d" % (left + 3, top + 3,
                             left + CARD_W - 3, band_top - 3)),
        ("stage.portrait.bg.offset", "%d, %d" % (left - CARD_CX, top - text_y)),
        ("stage.portrait.bg.scale", "1.0, 1.0"),
        ("stage.pos", "%d, %d" % (CARD_CX, text_y)),
    )


# The stage name is in the card's band now, so the text is the bare name -
# "Stage 7: Lo Pan's Hallway" does not fit across a 400px card - set in the
# same gold as the rest of the screen and sized to the band.
# font 11 is a 13px cell, so the name is set at 1:1 and reads at the size the
# engine draws VERSUS in - the stage name used to be the only text on the row
# that was set in another face and at another size.
NAME_SCALE = "1, 1"
SELECT_TEXT = (
    ("stage.font", f"{NAME_FONT}, 0, 0, 236, 200, 120"),
    ("stage.active.font", f"{NAME_FONT}, 0, 0, 255, 228, 140"),
    ("stage.active2.font", f"{NAME_FONT}, 0, 0, 200, 168, 104"),
    ("stage.done.font", f"{NAME_FONT}, 0, 0, 200, 168, 104"),
    ("stage.text", "%s"),
    ("stage.active.text", "%s"),
    ("stage.scale", NAME_SCALE),
)


# The select card hangs lower than it used to: the taller name band needs the
# room, and the grid above it ends at y=460, so the card's top is at 477.
STAGE_PORTRAIT = _card(660)           # [Select Info]
SELECT_PLATE = STAGE_PORTRAIT + (
    # the select screen draws the plate as [Begin Action 110]; pin it to its
    # first sprite so the anim's own offsets cannot shift the plate
    ("stage.portrait.bg.anim", "-1"),
    ("stage.portrait.bg.spr", "110,0"),
) + SELECT_TEXT
VS_PLATE = _card(665) + (
    ("stage.portrait.bg.spr", "112,0"),
)

# Text on the VS screen. The two names were within a few units of each other,
# so both sides looked like the same orange: P1 is the motif's bright cream and
# P2 a warmer amber. The "Next Stage" caption used to sit under the card; it is
# the stage name in the card's band now, like the select screen.
VS_TEXT = (
    ("p1.name.font", "10, 0, 1, 255, 228, 140"),
    ("p2.name.font", "10, 0, -1, 255, 170, 96"),
    ("stage.font", f"{NAME_FONT}, 0, 0, 255, 228, 140"),
    ("stage.text", "%s"),
    ("stage.scale", NAME_SCALE),
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
            # every occurrence, not just the first: a duplicate line further
            # down the same section would win at load time, which is how the
            # card ended up drawn at one scale inside another's window
            new = pat.sub(f"{key} = {value}", body)
            # ...and collapse the duplicates the old appending left behind, so
            # the section carries one line per key
            seen = [m.start() for m in pat.finditer(new)]
            for at in reversed(seen[:-1]):
                line_end = new.find("\n", at)
                new = new[:at] + new[line_end + 1:]
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


# The stock plates behind the stage preview are grey panels with a large
# question mark printed on them: group 110 (select), 112 (VS) and 111/113 (the
# random and loading slots). The picture is drawn over the plate, so every
# pixel of the preview art that is transparent shows the question mark through
# it - which is why the VS card looked framed by one. Only group 110 was
# repainted, so the VS screen still had the "?" around its preview. All four
# groups are repainted now: each slot reads as an empty gold picture frame
# until a preview is drawn in it.
FRAME_GROUPS = (110, 111, 112, 113)


def frame_plate(w, h, band=0):
    """A dark plate with the same gold rule as the rest of the screenpack.

    ``band`` paints the name band across the top of the plate: a darker strip
    with a gold rule under it. The stage art is clipped below that band, and
    the engine's stage text is drawn in it, so the name always has a dark
    backing no matter how bright the stage behind the card is.
    """
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], fill=(16, 13, 20, 205),
                outline=GOLD_DEEP + (255,), width=2)
    d.rectangle([2, 2, w - 3, h - 3], outline=GOLD + (140,), width=1)
    if band:
        # the band is under the art: a darker strip at the bottom of the plate
        # with a gold rule above it, so the name never sits over the picture
        band_top = h - 3 - band
        d.rectangle([2, band_top, w - 3, h - 3], fill=(9, 7, 12, 240))
        d.line([(3, band_top - 2), (w - 4, band_top - 2)],
               fill=GOLD_DEEP + (255,), width=2)
        d.line([(3, band_top - 1), (w - 4, band_top - 1)],
               fill=GOLD + (150,), width=1)
    return img


# The two plates the card itself is drawn on. They are repainted at the card's
# own size, so the card's .def scale is 1 and its offsets are screen pixels;
# the other frame sprites keep whatever size the engine shipped them at.
CARD_PLATES = ((110, 0), (112, 0))


def clean_frames():
    """Repaint the stage-preview frame without its question mark."""
    _d, sprites, palettes = sff.read_sff(SYSTEM_SFF)
    out, replaced = [], 0
    for sp in sprites:
        if sp["group"] in FRAME_GROUPS:
            if (sp["group"], sp["number"]) in CARD_PLATES:
                img = frame_plate(CARD_W, CARD_H, band=BAND_H)
                axis = (0, 0)
            else:
                img = frame_plate(sp["w"], sp["h"])
                axis = sp["axis"]
            out.append({"group": sp["group"], "number": sp["number"],
                        "image": img, "axis": axis})
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
