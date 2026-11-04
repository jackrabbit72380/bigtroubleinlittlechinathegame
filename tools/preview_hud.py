"""Composite a full in-game HUD frame from the shipped art.

Every position comes from data/fight.def - health bars from [Lifebar], power
meters from [Powerbar], the yin-yang and digits from [Time] - so this shows the
real layout rather than a hand-placed bar. Nothing is annotated: if it is not
part of the HUD, it is not in the picture.

Output: artifacts/hud_ingame.png  (1920x1080)

Run:  python3 tools/preview_hud.py
"""

import glob
import os
import re
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import sff as mugen  # noqa: E402

STAGE = os.path.join(ROOT, "artifacts", "lopans_throne_preview.png")
FIGHT_SFF = os.path.join(ROOT, "data", "fight.sff")
FIGHT_DEF = os.path.join(ROOT, "data", "fight.def")
FONT_DIR = os.path.join(ROOT, "data", "ikemen1", "fonts")
OUT = os.path.join(ROOT, "artifacts")

W, H = 1920, 1080
S = W / 1280.0                     # one fight unit -> screen pixels
CHAR = S * (1280.0 / 960.0)        # fighters are authored at localcoord 960x720
GROUND = 640 * S


def load(path):
    d, sprites, pals = mugen.read_sff(path)
    return d, {(s["group"], s["number"]): s for s in sprites}, pals


def pic(d, by_key, pals, key):
    sp = by_key[key]
    return mugen.decode_sprite(d, sp, pals, sp["pal"]), sp["w"], sp["h"]


def blit(canvas, img, x, y, scale, mirror=False):
    """Paste the image's top-left corner at (x, y), optionally mirrored."""
    w = max(1, round(img.width * scale))
    h = max(1, round(img.height * scale))
    out = img.convert("RGBA").resize((w, h), Image.LANCZOS)
    if mirror:
        out = out.transpose(Image.FLIP_LEFT_RIGHT)
    canvas.alpha_composite(out, (int(round(x)), int(round(y))))


def draw_sprite(canvas, d, by_key, pals, key, x, y, scale, mirror=False):
    img, _w, _h = pic(d, by_key, pals, key)
    blit(canvas, img, x, y, scale, mirror)


# ------------------------------------------------------------------- meters
def draw_banner(canvas, d, by_key, pals):
    """[Lifebar] bg1: the VS banner halves, anchored on the screen centre."""
    text = open(FIGHT_DEF, encoding="utf-8", errors="surrogateescape").read()
    body = text.split("[Lifebar]", 1)[1].split("\n[", 1)[0]
    for side in ("p1", "p2"):
        m = re.search(r"(?m)^\s*%s\.bg1\.spr\s*=\s*(\d+)\s*,\s*(\d+)" % side,
                      body)
        o = re.search(r"(?m)^\s*%s\.bg1\.offset\s*=\s*(-?\d+)\s*,\s*(-?\d+)"
                      % side, body)
        p = re.search(r"(?m)^\s*%s\.pos\s*=\s*(-?\d+)\s*,\s*(-?\d+)" % side,
                      body)
        if not (m and o and p):
            continue
        key = (int(m.group(1)), int(m.group(2)))
        if key not in by_key:
            continue
        sp = by_key[key]
        img, _w, _h = pic(d, by_key, pals, key)
        x = (int(p.group(1)) + int(o.group(1)) - sp["axis"][0]) * S
        y = (int(p.group(2)) + int(o.group(2)) - sp["axis"][1]) * S
        blit(canvas, img, x, y, S)


def _tint(img, add):
    """Approximate palfx.add so player two's bar shows its green dragon skin."""
    r, g, b, a = img.convert("RGBA").split()
    shift = lambda ch, d: ch.point(lambda v: max(0, min(255, v + d)))
    return Image.merge("RGBA", (shift(r, add[0]), shift(g, add[1]),
                                shift(b, add[2]), a))


P2_ADD = (-150, 90, -10)


def draw_lifebar(canvas, d, by_key, pals, pos, frac, mirror):
    """[Lifebar]: bg0 trough, top frame, mid fill, front on top of the fill."""
    px, py = pos[0] * S, pos[1] * S
    bg, bw, bh = pic(d, by_key, pals, (10, 0))
    top, _tw, _th = pic(d, by_key, pals, (11, 0))
    mid, _mw, _mh = pic(d, by_key, pals, (12, 0))
    key = (13, 0 if frac > 0.5 else (1 if frac > 0.25 else 2))
    front, fw, fh = pic(d, by_key, pals, key)
    if mirror:
        bg, top, mid, front = (_tint(x, P2_ADD) for x in (bg, top, mid, front))

    if not mirror:
        blit(canvas, bg, px - bw * S, py, S)
        blit(canvas, mid, px - bw * S, py, S)
        blit(canvas, top, px - bw * S, py, S)
        span = max(1, round(fw * frac))
        piece = front.crop((fw - span, 0, fw, fh))
        blit(canvas, piece, px - 4 * S - piece.width * S, py, S)
    else:
        blit(canvas, bg, px, py, S, mirror=True)
        blit(canvas, mid, px, py, S, mirror=True)
        blit(canvas, top, px, py, S, mirror=True)
        span = max(1, round(fw * frac))
        piece = front.crop((0, 0, span, fh)).transpose(Image.FLIP_LEFT_RIGHT)
        blit(canvas, piece, px + 4 * S, py, S)


def draw_powerbar(canvas, d, by_key, pals, pos, frac, mirror,
                  glyphs=None, text=None):
    """[Powerbar]: trough, frame, the dragon front, then the level readout."""
    px, py = pos[0] * S, pos[1] * S
    bg, bw, bh = pic(d, by_key, pals, (40, 0))
    frame, _fw2, _fh2 = pic(d, by_key, pals, (41, 0))
    key = (44, 0) if frac >= 1.0 else (43, 0)
    front, fw, fh = pic(d, by_key, pals, key)
    if mirror:
        bg, frame, front = (_tint(x, P2_ADD) for x in (bg, frame, front))

    if not mirror:
        blit(canvas, bg, px - bw * S, py, S)
        blit(canvas, frame, px - bw * S, py, S)
        span = max(1, round(fw * min(1.0, frac)))
        piece = front.crop((fw - span, 0, fw, fh))
        blit(canvas, piece, px - 4 * S - piece.width * S, py, S)
    else:
        blit(canvas, bg, px, py, S, mirror=True)
        blit(canvas, frame, px, py, S, mirror=True)
        span = max(1, round(fw * min(1.0, frac)))
        piece = front.crop((0, 0, span, fh)).transpose(Image.FLIP_LEFT_RIGHT)
        blit(canvas, piece, px + 4 * S, py, S)

    # the level readout sits under the meter: number, or MAXIMUM / AUDACITY
    if glyphs and text:
        draw_text(canvas, glyphs, text, px - 241 * S, py + 80 * S, S,
                  centre=True)


def draw_text(canvas, glyphs, text, x, y, scale, centre=True):
    widths = [round(glyphs[ord(c)][1] * scale) for c in text if ord(c) in glyphs]
    if centre:
        x -= sum(widths) // 2
    for ch in text:
        if ord(ch) not in glyphs:
            continue
        img, gw, _gh = glyphs[ord(ch)]
        blit(canvas, img, x, y, scale)
        x += round(gw * scale)


def draw_timer(canvas, d, by_key, pals, pos, glyphs, seconds):
    """[Time]: the yin-yang at pos, with the digits counting down inside it."""
    px, py = pos[0] * S, pos[1] * S
    text = open(FIGHT_DEF, encoding="utf-8", errors="surrogateescape").read()
    body = text.split("[Time]", 1)[1].split("\n[", 1)[0]
    m = re.search(r"(?m)^\s*bg\.offset\s*=\s*(-?\d+)\s*,\s*(-?\d+)", body)
    bg_off = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    m = re.search(r"(?m)^\s*counter\.offset\s*=\s*(-?\d+)\s*,\s*(-?\d+)", body)
    c_off = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    m = re.search(r"(?m)^\s*counter\.scale\s*=\s*([\d.]+)\s*,\s*([\d.]+)", body)
    c_scale = float(m.group(1)) if m else 1.0
    img, _w, _h = pic(d, by_key, pals, (30, 0))
    blit(canvas, img, px + bg_off[0] * S - img.width * S / 2,
         py + bg_off[1] * S - img.height * S / 2, S)
    draw_text(canvas, glyphs, str(seconds), px + c_off[0] * S,
              py + c_off[1] * S, c_scale * S)


def load_glyphs(name):
    path = os.path.join(FONT_DIR, name)
    d, by_key, pals = load(path)
    out = {}
    for (g, n), sp in by_key.items():
        if g != 0:
            continue
        out[n] = (mugen.decode_sprite(d, sp, pals, sp["pal"]), sp["w"], sp["h"])
    return out


def def_xy(section):
    text = open(FIGHT_DEF, encoding="utf-8", errors="surrogateescape").read()
    body = text.split("[" + section + "]", 1)[1].split("\n[", 1)[0]
    out = {}
    for side in ("p1", "p2"):
        m = re.search(r"(?m)^\s*%s\.pos\s*=\s*(-?\d+)\s*,\s*(-?\d+)" % side, body)
        out[side] = (int(m.group(1)), int(m.group(2)))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    shot = Image.open(STAGE).convert("RGBA")
    if shot.size != (W, H):
        shot = shot.resize((W, H), Image.LANCZOS)

    d, by_key, pals = load(FIGHT_SFF)
    life = def_xy("Lifebar")
    power = def_xy("Powerbar")
    text = open(FIGHT_DEF, encoding="utf-8", errors="surrogateescape").read()
    m = re.search(r"(?s)\[Time\].*?\n\s*pos\s*=\s*(-?\d+)\s*,\s*(-?\d+)", text)
    time_pos = (int(m.group(1)), int(m.group(2))) if m else (640, 105)
    mo = re.search(r"(?m)^\s*bg\.offset\s*=\s*(-?\d+)\s*,\s*(-?\d+)", text)
    bg_offset = (int(mo.group(1)), int(mo.group(2))) if mo else (0, 0)

    # fighters: Jack on the left, Lo Pan on the right, both idle and facing in
    for folder, x, mirror in (("jackburton_rig", 300, False),
                              ("lopan_rig", 980, True)):
        path = glob.glob(os.path.join(ROOT, "chars", folder, "*.sff"))[0]
        cd, ck, cp = load(path)
        img, _w, _h = pic(cd, ck, cp, (0, 0))
        sp = ck[(0, 0)]
        w = round(img.width * CHAR)
        h = round(img.height * CHAR)
        ax = (img.width - sp["axis"][0]) if mirror else sp["axis"][0]
        if mirror:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        blit(shot, img, x * S - ax * CHAR,
             GROUND - sp["axis"][1] * CHAR, CHAR)

    level_glyphs = load_glyphs("PowerbarNum.sff")
    timer_glyphs = load_glyphs("Timer.sff")

    draw_banner(shot, d, by_key, pals)
    draw_powerbar(shot, d, by_key, pals, power["p2"], 0.35, True)
    # AUDACITY is painted into the full-power sprite itself, so nothing is
    # drawn under the meter here
    draw_powerbar(shot, d, by_key, pals, power["p1"], 1.0, False)
    draw_lifebar(shot, d, by_key, pals, life["p1"], 0.82, False)
    draw_lifebar(shot, d, by_key, pals, life["p2"], 0.55, True)
    draw_timer(shot, d, by_key, pals, time_pos, timer_glyphs, 60)

    shot.convert("RGB").save(os.path.join(OUT, "hud_ingame.png"))
    print("wrote artifacts/hud_ingame.png")
    print("lifebar", life, "powerbar", power, "timer", time_pos)


if __name__ == "__main__":
    main()
