"""Preview the stage screen as the game lays it out.

The cards, the picked card's frame and the PLAYER captions are the sprites the
screen itself draws - 240,<n> cards, 241,0 / 242,0 frames and 151,20 / 151,21
captions out of data/ikemen1/system.sff - placed at the coordinates
start.stageGrid produces. So this is the wall the game shows, not a second
rendering of it.

Two thin guides are drawn on top: the window the screen clips to (blue) and the
bottom edge of the 1920x1080 frame (red). A card touching or crossing either is a
card the player cannot see. The frame is drawn on the last card on purpose: that
is the bottom row.

Run: python3 tools/preview_stage_wall.py
"""

from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import build_stage_wall as wall
import sff

ROOT = wall.ROOT
SYSTEM_SFF = wall.SYSTEM_SFF
OUT = os.path.join(ROOT, "artifacts", "stage_wall_fit.png")

SCREEN = (1920, 1080)
BACKDROP = (225, 0)
CAPTIONS = ((58, (151, 20)), (1544, (151, 21)))
CAPTION_Y = 0
GUIDE = (74, 148, 196)
EDGE = (206, 86, 86)
NAME_ROW = 1005
PICKED_SIDE = 1


def main():
    refs = wall.pool()
    if not refs:
        raise SystemExit("stage wall: [ExtraStages] is empty")
    cards, cols, rows = wall.layout(len(refs))
    window = wall.screen_window()

    data, sprites, pals = sff.read_sff(SYSTEM_SFF)
    by = {(sp["group"], sp["number"]): sp for sp in sprites}

    def image(key):
        sp = by.get(key)
        if sp is None:
            return None
        return sff.decode_sprite(data, sp, pals).convert("RGBA")

    def place(screen, key, x, y):
        """Put a sprite's axis point on x, y, the way the screen positions it."""
        sp, art = by.get(key), image(key)
        if art is None:
            return False
        screen.alpha_composite(art, (int(round(x)) - sp["axis"][0],
                                     int(round(y)) - sp["axis"][1]))
        return True

    screen = Image.new("RGBA", SCREEN, (10, 11, 14, 255))
    backdrop = image(BACKDROP)
    if backdrop is not None:
        screen.alpha_composite(backdrop if backdrop.size == SCREEN
                              else backdrop.resize(SCREEN, Image.LANCZOS))
    for x, key in CAPTIONS:
        place(screen, key, x, CAPTION_Y)

    missing = [i + 1 for i in range(len(cards))
               if not place(screen, (wall.CARD_SPRITE, i),
                            cards[i]["cx"], cards[i]["cy"])]
    picked = len(cards)
    if picked:
        place(screen, (wall.FRAME_SPRITES[PICKED_SIDE], 0),
              cards[picked - 1]["cx"], cards[picked - 1]["cy"])

    draw = ImageDraw.Draw(screen)
    x1, y1, x2, y2 = window
    draw.rectangle([x1, y1, x2 - 1, y2 - 1], outline=GUIDE + (255,), width=2)
    draw.line([(0, SCREEN[1] - 1), (SCREEN[0] - 1, SCREEN[1] - 1)],
              fill=EDGE + (255,), width=2)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    screen.convert("RGB").save(OUT)

    half_w, half_h = wall.CARD[0] / 2.0, wall.CARD[1] / 2.0
    top = min(c["cy"] for c in cards) - half_h
    bottom = max(c["cy"] for c in cards) + half_h
    left = min(c["cx"] for c in cards) - half_w
    right = max(c["cx"] for c in cards) + half_w
    print("  %d stages: %d across, %d rows" % (len(refs), cols, rows))
    print("  window      x %d..%d   y %d..%d" % (x1, x2, y1, y2))
    print("  wall        x %.0f..%.0f  y %.0f..%.0f" % (left, right, top, bottom))
    print("  bottom row  %.0f..%.0f  ->  %.0f px above the frame edge, %.0f above the names"
          % (bottom - wall.CARD[1], bottom, SCREEN[1] - bottom, NAME_ROW - bottom))
    if missing:
        print("  MISSING card sprites for stage(s): %s" % ", ".join(map(str, missing)))
    print("  preview: %s (%d KB)" % (os.path.relpath(OUT, ROOT),
                                     os.path.getsize(OUT) // 1024))

if __name__ == "__main__":
    main()
