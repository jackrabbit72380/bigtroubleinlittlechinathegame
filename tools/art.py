"""Shared drawing helpers for the Big Trouble in Little China stage art."""

from __future__ import annotations

import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

FONT_CANDIDATES = (
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir,
                 "data", "ikemen1", "fonts", "Display.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
)


def font(size):
    """Bold display font at the requested pixel size."""
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    # Pillow >= 10.1 ships a scalable default face we can size on demand.
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # very old Pillow
        return ImageFont.load_default()


def vgrad(size, stops):
    """Vertical gradient. stops = [(y, (r,g,b)), ...] sorted by y."""
    w, h = size
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    stops = sorted(stops, key=lambda s: s[0])
    for y in range(h):
        prev = stops[0]
        nxt = stops[-1]
        for i in range(len(stops) - 1):
            if stops[i][0] <= y <= stops[i + 1][0]:
                prev, nxt = stops[i], stops[i + 1]
                break
        span = max(1, nxt[0] - prev[0])
        t = min(1.0, max(0.0, (y - prev[0]) / span))
        col = tuple(int(prev[1][i] + (nxt[1][i] - prev[1][i]) * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=col + (255,))
    return img


def hgrad(size, stops):
    w, h = size
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    stops = sorted(stops, key=lambda s: s[0])
    for x in range(w):
        prev, nxt = stops[0], stops[-1]
        for i in range(len(stops) - 1):
            if stops[i][0] <= x <= stops[i + 1][0]:
                prev, nxt = stops[i], stops[i + 1]
                break
        span = max(1, nxt[0] - prev[0])
        t = min(1.0, max(0.0, (x - prev[0]) / span))
        col = tuple(int(prev[1][i] + (nxt[1][i] - prev[1][i]) * t) for i in range(3))
        d.line([(x, 0), (x, h)], fill=col + (255,))
    return img


def glow(layer, radius=6, gain=1.0):
    """Blurred copy of a layer keeping its own alpha (safe for alpha_composite)."""
    g = layer.filter(ImageFilter.GaussianBlur(radius))
    if gain != 1.0:
        r, gr, b, a = g.split()
        a = a.point(lambda v: min(255, int(v * gain)))
        g = Image.merge("RGBA", (r, gr, b, a))
    return g


def premultiplied(layer):
    """Colour scaled by its own alpha, for additive ImageChops.screen.

    ImageChops.screen ignores alpha, so without this a blurred halo would
    lift the whole frame towards grey instead of glowing locally.
    """
    r, g, b, a = layer.split()
    return Image.merge("RGBA", (ImageChops.multiply(r, a),
                                ImageChops.multiply(g, a),
                                ImageChops.multiply(b, a),
                                Image.new("L", layer.size, 255)))


def screen(base, layer, glow_radius=None, gain=1.0, passes=1):
    """Additive 'light' composite of layer onto base, with an optional halo.

    Every layer is premultiplied first: layers built from masks (outline(),
    text, lines) keep their colour in fully transparent pixels, and
    ImageChops.screen ignores alpha, which would otherwise flood the frame.
    """
    lit = premultiplied(layer)
    if glow_radius:
        lit = ImageChops.screen(lit, premultiplied(glow(layer, glow_radius, gain)))
    out = base
    for _ in range(max(1, passes)):
        out = ImageChops.screen(out, lit)
    return out


def outline(mask, color, thickness=2, expand=0):
    """Return a colored rim (outline) image from a mask image."""
    m = mask
    if expand:
        for _ in range(expand):
            m = m.filter(ImageFilter.MaxFilter(3))
    edge = ImageChops.subtract(m, m.filter(ImageFilter.MinFilter(thickness * 2 + 1)))
    rim = Image.new("RGBA", mask.size, color + (0,))
    rim.putalpha(edge)
    solid = Image.new("RGBA", mask.size, color + (255,))
    solid.putalpha(edge)
    return solid


def vignette(img, strength=0.75, color=(0, 0, 0)):
    """Darken towards the frame edges.

    Image.radial_gradient is 0 at the centre and 255 at the edges, so the mask
    must scale it directly: inverting it darkened the middle of every stage and
    left the corners untouched.
    """
    w, h = img.size
    mask = Image.radial_gradient("L").resize((w, h), Image.BICUBIC)
    mask = mask.point(lambda v: int(v * strength))
    dark = Image.new("RGBA", (w, h), color + (255,))
    dark.putalpha(mask)
    return Image.alpha_composite(img, dark)


def grain(img, amount=8, seed=7):
    rnd = random.Random(seed)
    w, h = img.size
    noise = Image.effect_noise((w, h), amount).convert("L")
    shift = Image.new("L", (w, h), rnd.randint(100, 155))
    noise = ImageChops.subtract(noise, shift, scale=1)
    layer = Image.merge("RGBA", (noise, noise, noise, Image.new("L", (w, h), 60)))
    return Image.alpha_composite(img, layer)


def radial_light(size, center, radius, color, peak=200):
    """Soft round light blob, returned as an RGBA layer."""
    w, h = size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    steps = 14
    for i in range(steps, 0, -1):
        t = i / steps
        r = radius * t
        a = int(peak * (1 - t) ** 2)
        d.ellipse([center[0] - r, center[1] - r * 0.85,
                   center[0] + r, center[1] + r * 0.85],
                  fill=color + (a,))
    return img.filter(ImageFilter.GaussianBlur(radius * 0.12))


def rain(img, count=140, length=(8, 26), color=(170, 200, 225), alpha=46, seed=3,
         angle=-0.24, area=None):
    rnd = random.Random(seed)
    w, h = img.size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0, y0, x1, y1 = area if area else (0, 0, w, h)
    for _ in range(count):
        x = rnd.uniform(x0, x1)
        y = rnd.uniform(y0, y1)
        ln = rnd.uniform(*length)
        dx = math.sin(angle) * ln
        dy = math.cos(angle) * ln
        a = rnd.randint(max(8, alpha // 3), alpha)
        d.line([(x, y), (x + dx, y + dy)], fill=color + (a,), width=1)
    return Image.alpha_composite(img, layer)


def wet_floor(img, y_top, color=(120, 150, 170), alpha=38, seed=5, bands=26):
    """Fake vertical smears below y_top so the ground reads as wet stone."""
    rnd = random.Random(seed)
    w, h = img.size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(bands):
        x = rnd.randint(0, w)
        bw = rnd.randint(2, 18)
        y0 = y_top + rnd.randint(0, 8)
        y1 = h - rnd.randint(0, 12)
        a = rnd.randint(6, alpha)
        d.rectangle([x, y0, x + bw, y1], fill=color + (a,))
    return Image.alpha_composite(img, layer.filter(ImageFilter.GaussianBlur(2)))


def fake_glyph(draw, x, y, size, color, seed=0, width=None):
    """Blocky pseudo-ideogram strokes (kept abstract on purpose)."""
    rnd = random.Random(seed)
    s = size
    w = width or max(2, s // 6)
    cells = 3
    cs = s / cells
    for row in range(cells):
        for col in range(cells):
            if rnd.random() < 0.45:
                continue
            cx = x + col * cs
            cy = y + row * cs
            if rnd.random() < 0.5:
                draw.rectangle([cx, cy + cs * 0.35, cx + cs, cy + cs * 0.35 + w], fill=color)
            else:
                draw.rectangle([cx + cs * 0.35, cy, cx + cs * 0.35 + w, cy + cs], fill=color)


def lantern(draw, cx, cy, r, body=(196, 32, 34), cap=(224, 184, 96)):
    draw.ellipse([cx - r, cy - r * 0.78, cx + r, cy + r * 0.78], fill=body)
    draw.rectangle([cx - r * 0.34, cy - r * 0.95, cx + r * 0.34, cy - r * 0.66], fill=cap)
    draw.rectangle([cx - r * 0.34, cy + r * 0.66, cx + r * 0.34, cy + r * 0.95], fill=cap)
    draw.line([(cx, cy - r * 0.78), (cx, cy + r * 0.78)], fill=(120, 16, 18), width=1)
    draw.line([(cx - r * 0.6, cy), (cx + r * 0.6, cy)], fill=(120, 16, 18), width=1)


def taper_column(draw, x, y_top, y_bot, w_top, w_bot, color):
    draw.polygon([(x - w_top / 2, y_top), (x + w_top / 2, y_top),
                  (x + w_bot / 2, y_bot), (x - w_bot / 2, y_bot)], fill=color)


def arch_shape(draw, cx, y_base, w, h, color, spring=0.55):
    """Roman/Chinese arch: straight sides + semicircular top."""
    r = w / 2
    y_spring = y_base - h + r
    draw.rectangle([cx - r, y_spring, cx + r, y_base], fill=color)
    draw.pieslice([cx - r, y_base - h, cx + r, y_base - h + 2 * r], 180, 360, fill=color)
    _ = spring
