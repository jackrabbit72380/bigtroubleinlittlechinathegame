"""Render what pressing the taunt button looks like in a match.

The engine cannot run headless here, so this composites the same art the game
draws: the Lo Pan's Throne backdrop, Jack in his taunt sprite (195,0), an
opponent in idle, and the p1 power bar at full with the AUDACITY text under it.

Outputs:
    artifacts/taunt_ingame.png    one 1920x1080 frame, taunt in progress
    artifacts/taunt_compare.png   idle stance vs taunt pose, side by side

Run:  python3 tools/preview_taunt.py
"""

import glob
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import sff as mugen  # noqa: E402

STAGE = os.path.join(ROOT, "artifacts", "lopans_throne_preview.png")
FIGHT = os.path.join(ROOT, "data", "fight.sff")
FONT = os.path.join(ROOT, "data", "ikemen1", "fonts", "PowerbarNum.sff")
OUT = os.path.join(ROOT, "artifacts")

W, H = 1920, 1080
# fight.def localcoord is 1280x720, so one fight unit is 1.5 screen pixels.
S = W / 1280.0
# Jack's own localcoord is 960x720, so his sprites are drawn 1280/960 larger
# than fight units.
CHAR = S * (1280.0 / 960.0)

GOLD = (255, 214, 120)


# ------------------------------------------------------------------ sprites
def load(path):
    d, sprites, pals = mugen.read_sff(path)
    by_key = {(s["group"], s["number"]): s for s in sprites}
    return d, by_key, pals


def sprite(d, by_key, pals, key):
    sp = by_key[key]
    return mugen.decode_sprite(d, sp, pals, sp["pal"]), sp["axis"]


def place(canvas, img, axis, x, y, scale, flip=False):
    """Paste a sprite so its axis lands on (x, y), MUGEN style."""
    w = max(1, round(img.width * scale))
    h = max(1, round(img.height * scale))
    pic = img.convert("RGBA").resize((w, h), Image.LANCZOS)
    if flip:
        pic = pic.transpose(Image.FLIP_LEFT_RIGHT)
        ax = img.width - axis[0]
    else:
        ax = axis[0]
    px = round(x - ax * scale)
    py = round(y - axis[1] * scale)
    canvas.alpha_composite(pic, (int(round(px)), int(round(py))))


def tint(img, mul):
    r, g, b, a = img.split()
    lut = []
    for band, m in zip((r, g, b), mul):
        lut.append(band.point(lambda v, m=m: min(255, round(v * m / 255.0))))
    return Image.merge("RGBA", (*lut, a))


# ------------------------------------------------------------------- text
def load_font():
    d, by_key, pals = load(FONT)
    glyphs = {}
    for (g, n), sp in by_key.items():
        if g != 0:
            continue
        glyphs[n] = (mugen.decode_sprite(d, sp, pals, sp["pal"]), sp["w"], sp["h"])
    return glyphs


def draw_text(canvas, glyphs, text, x, y, scale, colour, centre=True):
    parts = []
    total = 0
    for ch in text:
        g = glyphs.get(ord(ch))
        if g is None:
            continue
        img = g[0]
        if colour:
            img = tint(img, colour)
        parts.append((img, total))
        total += max(1, round(g[1] * scale)) + max(1, round(1 * scale))
    if centre:
        x -= total // 2
    for img, off in parts:
        w = max(1, round(img.width * scale))
        h = max(1, round(img.height * scale))
        pic = img.convert("RGBA").resize((w, h), Image.LANCZOS)
        canvas.alpha_composite(pic, (int(round(x)) + off, int(round(y))))
    return total


# ------------------------------------------------------------------ frames
def backdrop():
    img = Image.open(STAGE).convert("RGBA")
    if img.size != (W, H):
        img = img.resize((W, H), Image.LANCZOS)
    return img.copy()


def fighter(folder):
    defs = glob.glob(os.path.join(ROOT, "chars", folder, "*.sff"))
    return load(defs[0])


def main():
    os.makedirs(OUT, exist_ok=True)
    glyphs = load_font()
    bar_d, bar, bar_pals = load(FIGHT)
    trough, trough_ax = sprite(bar_d, bar, bar_pals, (40, 0))
    frame_img, frame_ax = sprite(bar_d, bar, bar_pals, (41, 0))
    front, front_ax = sprite(bar_d, bar, bar_pals, (43, 0))
    front_max, front_max_ax = sprite(bar_d, bar, bar_pals, (44, 0))

    ground = 640 * S          # floor line, in fight units -> screen
    jack_d, jack, jack_pals = fighter("jackburton_rig")
    idle, idle_ax = sprite(jack_d, jack, jack_pals, (0, 0))
    taunt, taunt_ax = sprite(jack_d, jack, jack_pals, (195, 0))

    foes = sorted(glob.glob(os.path.join(ROOT, "chars", "*")))
    foe = "lopan_rig" if os.path.isdir(os.path.join(ROOT, "chars", "lopan_rig")) else None
    if foe is None:
        foe = next(os.path.basename(p) for p in foes
                   if os.path.basename(p).endswith("_rig") and "jack" not in p)
    foe_d, foe_sp, foe_pals = fighter(foe)
    foe_idle, foe_ax = sprite(foe_d, foe_sp, foe_pals, (0, 0))

    # p1 power bar position from fight.def: p1.pos = 568,83, axis 460,0.
    bar_x, bar_y = 568 * S, 83 * S

    def draw_bar(canvas, fill=0.75):
        base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        place(base, trough, trough_ax, bar_x, bar_y, S)
        place(base, frame_img, frame_ax, bar_x, bar_y, S)
        # the front element is anchored to the right end of the bar
        lit = front if fill < 1.0 else front_max
        ax = front_ax if fill < 1.0 else front_max_ax
        cut = lit.crop((0, 0, max(1, round(lit.width * fill)), lit.height))
        place(base, cut, (round(ax[0] * fill), ax[1]), bar_x, bar_y, S)
        draw_text(base, glyphs, "AUDACITY", bar_x - 241 * S, bar_y + 80 * S,
                  S, GOLD)
        canvas.alpha_composite(base)

    def label(canvas, text, x, y, size=30, colour=(255, 236, 190)):
        f = None
        for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                     "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                     os.path.join(ROOT, "data", "ikemen1", "fonts", "Display.ttf")):
            try:
                f = ImageFont.truetype(path, size)
                break
            except OSError:
                continue
        if f is None:
            f = ImageFont.load_default()
        d = ImageDraw.Draw(canvas)
        d.text((x + 2, y + 2), text, font=f, fill=(0, 0, 0, 220))
        d.text((x, y), text, font=f, fill=colour + (255,))

    # --- frame: the taunt in a match
    shot = backdrop()
    place(shot, foe_idle, foe_ax, 940 * S, ground, CHAR, flip=True)
    place(shot, taunt, taunt_ax, 330 * S, ground, CHAR)
    draw_bar(shot, fill=1.0)
    label(shot, "SPACE  =  taunt   (state 195, one pose held ~0.55 s)",
          60, 60, 34)
    label(shot, "no damage, no power, no invulnerability", 60, 104, 26,
          (255, 210, 160))
    shot.convert("RGB").save(os.path.join(OUT, "taunt_ingame.png"))

    # --- comparison: idle vs taunt, same crop box and scale for both
    CS = 1.6                        # sprite pixels -> screen pixels
    cx = 330 * S
    box_w, box_h = 620, 760
    x0 = int(round(cx - box_w / 2))
    y0 = int(round(ground - (box_h - 80)))

    def panel(pose_img, pose_ax):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        place(layer, pose_img, pose_ax, cx, ground, CS)
        base = backdrop()
        base.alpha_composite(layer)
        return base.crop((x0, y0, x0 + box_w, y0 + box_h))

    left = panel(idle, idle_ax)
    right = panel(taunt, taunt_ax)

    bg = Image.open(STAGE).convert("RGBA").resize((W, H), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(10))
    bg = Image.blend(bg, Image.new("RGBA", (W, H), (0, 0, 0, 255)), 0.55)
    gap = 60
    total = box_w * 2 + gap
    ox = (W - total) // 2
    oy = (H - box_h) // 2 + 45
    for i, tile in enumerate((left, right)):
        draw_i = ImageDraw.Draw(tile)
        draw_i.rectangle([0, 0, box_w - 1, box_h - 1], outline=(210, 170, 90, 255), width=3)
        bg.alpha_composite(tile, (ox + i * (box_w + gap), oy))
    label(bg, "idle", ox + box_w // 2 - 44, oy - 56, 44)
    label(bg, "taunt", ox + box_w + gap + box_w // 2 - 62, oy - 56, 44,
          (255, 200, 120))
    label(bg, "SPACE pressed  \u2192  sprite 195,0 for ~0.55 s, then back to idle",
          ox, oy + box_h + 16, 32)
    bg.convert("RGB").save(os.path.join(OUT, "taunt_compare.png"))

    print("wrote artifacts/taunt_ingame.png, artifacts/taunt_compare.png")
    print("foe:", foe)


if __name__ == "__main__":
    main()
