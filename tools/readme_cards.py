"""Build the stage cards the README shows.

The README embedded the full 1920x1080 previews, five of them stacked, so the
page opened with more than five thousand pixels of stage art before any text -
each picture was also unlabelled unless you read its alt text. A card is the
same preview at README size with the stage name across the top: 480x300, the
art in a gold frame under a name band, styled like the in-game select card.

Names come from each stage's own ``.def``, so a card cannot say one thing while
the game says another.

Run:  python3 tools/readme_cards.py
"""

from __future__ import annotations

import os
import re
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import art

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTS = os.path.join(ROOT, "artifacts")

CARD_W = 480
BAND_H = 30
ART_H = 270                              # 16:9, the shape every preview is
CARD_H = ART_H + BAND_H

GOLD = (232, 196, 116)
GOLD_DEEP = (120, 78, 16)
INK = (10, 8, 12)


def stage_name(sid):
    """The display name out of stages/<sid>.def, or None if it has no [Info]."""
    path = os.path.join(ROOT, "stages", f"{sid}.def")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = re.match(r'\s*name\s*=\s*"?(.*?)"?\s*$', line, re.IGNORECASE)
            if m:
                return m.group(1)
    return None


def fit_font(draw, text, width, size=BAND_H - 8, floor=12):
    """Largest face that fits the band, so a long stage name is not clipped.

    Card names were drawn at one fixed size, which was fine until a stage was
    called something longer than the card is wide: the name then ran off both
    edges. Shrinking to fit keeps every name whole.
    """
    while size > floor:
        f = art.font(size)
        if draw.textlength(text, font=f) <= width:
            return f
        size -= 1
    return art.font(floor)


def card(preview, name):
    """One README card: the preview framed under its name."""
    art_img = preview.convert("RGBA")
    # cover-fit rather than letterbox: a preview is already 16:9, so this is a
    # straight resize, but an odd-sized one still fills the frame
    k = max(CARD_W / float(art_img.width), ART_H / float(art_img.height))
    art_img = art_img.resize((max(CARD_W, int(round(art_img.width * k))),
                              max(ART_H, int(round(art_img.height * k)))),
                             Image.LANCZOS)
    left = (art_img.width - CARD_W) // 2
    top = (art_img.height - ART_H) // 2
    art_img = art_img.crop((left, top, left + CARD_W, top + ART_H))

    img = Image.new("RGBA", (CARD_W, CARD_H), INK + (255,))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, CARD_W - 1, BAND_H - 1], fill=(14, 11, 16, 255))
    font = fit_font(d, name, CARD_W - 24)
    box = font.getbbox(name)
    tx = (CARD_W - (box[2] - box[0])) // 2 - box[0]
    ty = (BAND_H - (box[3] - box[1])) // 2 - box[1]
    d.text((tx + 1, ty + 1), name, font=font, fill=(0, 0, 0, 220))
    d.text((tx, ty), name, font=font, fill=GOLD + (255,))
    d.line([(0, BAND_H - 1), (CARD_W - 1, BAND_H - 1)],
           fill=GOLD_DEEP + (255,), width=2)

    img.alpha_composite(art_img, (0, BAND_H))
    d.rectangle([0, 0, CARD_W - 1, CARD_H - 1], outline=GOLD_DEEP + (255,),
                width=2)
    d.rectangle([2, 2, CARD_W - 3, CARD_H - 3], outline=GOLD + (150,), width=1)
    return img


def build():
    made = []
    for entry in sorted(os.listdir(os.path.join(ROOT, "stages"))):
        if not entry.endswith(".def"):
            continue
        sid = entry[:-4]
        preview = os.path.join(ARTS, f"{sid}_preview.png")
        if not os.path.isfile(preview):
            continue
        name = stage_name(sid)
        if not name:
            continue
        with Image.open(preview) as src:
            img = card(src, name)
        out = os.path.join(ARTS, f"{sid}_card.png")
        img.save(out)
        made.append((sid, name, os.path.getsize(out)))

    if not made:
        raise SystemExit("no stage previews found to card - build the stages first")
    for sid, name, size in made:
        print(f"  {sid}_card.png  {CARD_W}x{CARD_H}  {size / 1024:.0f} KiB  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
