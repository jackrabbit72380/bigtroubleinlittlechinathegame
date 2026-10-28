"""Minimal SFF v2 reader/writer for Ikemen GO / M.U.G.E.N sprite files.

Layout as implemented by Ikemen GO (src/image.go):
  header 512 bytes
    12  signature "ElecbyteSpr\\0"
    4   version bytes: 00 01 00 02  (engine reads verhi == 2)
    20  reserved
    4   first sprite header offset
    4   sprite count
    4   first palette header offset
    4   palette count
    4   lofs (base offset for palette and sprite data)
    4   reserved
    4   tofs (alternate base offset, used when sprite flags bit 0 is set)

  palette header 16 bytes: group, number, colours, reserved, offset, length
  sprite header 28 bytes:
    int16 group, int16 number, int16 w, int16 h, int16 axisx, int16 axisy,
    uint16 link, uint8 format, uint8 coldepth,
    uint32 dataoffset, uint32 length, uint16 palidx, uint16 flags

Sprite formats handled here:
  0  raw           (coldepth 8 or 32)
  4  LZ5           (coldepth 5, 32-colour palettes)
  10 PNG8, 11 PNG24, 12 PNG32 (PNG payload starts 4 bytes into the data)
"""

from __future__ import annotations

import struct
from io import BytesIO

from PIL import Image

SIG = b"ElecbyteSpr\x00"
HDR_SIZE = 512
SPR_HDR = 28
PAL_HDR = 16
FMT_RAW = 0
FMT_LZ5 = 4
FMT_PNG8 = 10
FMT_PNG24 = 11
FMT_PNG32 = 12


def png_bytes(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.convert("RGBA").save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# --------------------------------------------------------------------- writing
def write_sff(sprites, palettes=None) -> bytes:
    """Serialise sprites (and optional palettes) to SFF v2 bytes.

    sprites: dicts with group, number, axis and either
             image=<PIL image> (written as PNG32) or
             raw=<payload>, format=, depth=, w=, h= (written verbatim)
    palettes: list of RGBA palette byte strings (any multiple of 4 bytes)
    """
    sprites = list(sprites)
    palettes = list(palettes or [])
    n, npal = len(sprites), len(palettes)

    pal_hdr_start = HDR_SIZE
    spr_hdr_start = HDR_SIZE + npal * PAL_HDR
    data_start = spr_hdr_start + n * SPR_HDR

    pal_offsets = []
    pal_blob = bytearray()
    for p in palettes:
        pal_offsets.append(len(pal_blob))
        pal_blob += p

    headers = bytearray()
    blobs = bytearray()
    for sp in sprites:
        if "image" in sp:
            img = sp["image"]
            png = png_bytes(img)
            payload = struct.pack("<I", len(png)) + png
            fmt, depth, w, h = FMT_PNG32, 32, img.width, img.height
        else:  # verbatim pass-through of an existing sprite payload
            payload = sp["raw"]
            fmt, depth, w, h = sp["format"], sp["depth"], sp["w"], sp["h"]
        ax, ay = sp.get("axis", (0, 0))
        headers += struct.pack(
            "<hhhhhhHBBIIHH",
            sp["group"], sp["number"], w, h, ax, ay, sp.get("link", 0),
            fmt, depth,
            len(pal_blob) + len(blobs), len(payload), sp.get("pal", 0), 0,
        )
        blobs += payload

    pal_headers = bytearray()
    for i, p in enumerate(palettes):
        pal_headers += struct.pack("<HHHHII", 1, i + 1, len(p) // 4, 0,
                                   pal_offsets[i], len(p))

    head = bytearray()
    head += SIG
    head += bytes((0, 1, 0, 2))
    head += struct.pack("<I", 0)
    head += struct.pack("<4I", 0, 0, 0, 0)
    head += struct.pack("<I", spr_hdr_start)
    head += struct.pack("<I", n)
    head += struct.pack("<I", pal_hdr_start)
    head += struct.pack("<I", npal)
    head += struct.pack("<I", data_start)   # lofs
    head += struct.pack("<I", 0)
    head += struct.pack("<I", data_start)   # tofs
    head += bytes(HDR_SIZE - len(head))
    return bytes(head) + bytes(pal_headers) + bytes(headers) + bytes(pal_blob) + bytes(blobs)


# --------------------------------------------------------------------- reading
def read_sff(path):
    """Return (raw_bytes, sprite_records, palette_records)."""
    d = open(path, "rb").read()
    if d[:12] != SIG:
        raise ValueError(f"{path}: not an SFF file")
    o = 16 + 4 + 16
    firstspr, numspr, firstpal, numpal = struct.unpack_from("<4I", d, o)
    o += 16
    lofs, _dummy, tofs = struct.unpack_from("<3I", d, o)

    sprites = []
    for i in range(numspr):
        off = firstspr + i * SPR_HDR
        (g, num, w, h, ax, ay, link, fmt, cd, dofs, ln,
         pidx, flags) = struct.unpack_from("<hhhhhhHBBIIHH", d, off)
        base = lofs if flags & 1 == 0 else tofs
        sprites.append({
            "group": g, "number": num, "w": w, "h": h, "axis": (ax, ay),
            "link": link, "format": fmt, "depth": cd, "length": ln,
            "pal": pidx, "flags": flags, "offset": base + dofs,
            "raw": d[base + dofs: base + dofs + ln],
        })

    palettes = []
    for i in range(numpal):
        off = firstpal + i * PAL_HDR
        _g, _n, _count = struct.unpack_from("<HHH", d, off)
        pofs, plen = struct.unpack_from("<II", d, off + 8)
        palettes.append({"rgba": d[lofs + pofs: lofs + pofs + plen]})
    return d, sprites, palettes


# -------------------------------------------------------------------- decoding
def lz5_decode(data, width, height):
    """Port of Ikemen GO's Lz5Decode: 32-colour run-length/LZ packed pixels."""
    size = width * height
    out = bytearray(size)
    if not data:
        return bytes(out)

    i, j, n = 0, 0, 0
    ct = data[i]
    cts = 0
    rb = 0
    rbc = 0
    last = len(data) - 1
    if i < last:
        i += 1

    while j < size:
        if i > last:
            break
        d = data[i]
        if i < last:
            i += 1

        if ct & (1 << cts):
            if d & 0x3F == 0:
                nd = data[i]
                if i < last:
                    i += 1
                d = ((d << 2) | nd) + 1
                n = data[i] + 2
                if i < last:
                    i += 1
            else:
                rb |= (d & 0xC0) >> rbc
                rbc += 2
                n = d & 0x3F
                if rbc < 8:
                    d = data[i] + 1
                    if i < last:
                        i += 1
                else:
                    d = rb + 1
                    rb, rbc = 0, 0
            while True:
                if j < size and 0 <= j - d:
                    out[j] = out[j - d]
                    j += 1
                n -= 1
                if n < 0:
                    break
        else:
            if d & 0xE0 == 0:
                n = data[i] + 8
                if i < last:
                    i += 1
            else:
                n = d >> 5
                d &= 0x1F
            while n > 0:
                if j < size:
                    out[j] = d
                    j += 1
                n -= 1

        cts += 1
        if cts >= 8:
            ct = data[i] if i <= last else 0
            if i < last:
                i += 1
            cts = 0
    return bytes(out)


def palette_rgb(palette_records, index):
    """Return a 256-entry RGB LUT from the palette at ``index``."""
    rec = palette_records[index % len(palette_records)]
    rgba = rec["rgba"]
    lut = []
    for i in range(256):
        c = rgba[(i * 4) % max(4, len(rgba)):(i * 4) % max(4, len(rgba)) + 3]
        lut.append(tuple(c) + (0,) * (3 - len(c)))
    return lut


def decode_sprite(d, sp, palettes=None, palidx=None):
    """Decode one sprite record to an RGBA PIL image."""
    fmt = sp["format"]
    w, h = max(1, sp["w"]), max(1, sp["h"])
    data = d[sp["offset"]: sp["offset"] + sp["length"]]

    if fmt in (FMT_PNG8, FMT_PNG24, FMT_PNG32):
        img = Image.open(BytesIO(data[4:]))
        img.load()
        return img.convert("RGBA")
    if fmt == FMT_RAW and sp["depth"] == 32:
        return Image.frombytes("RGBA", (w, h), data)
    if fmt == FMT_RAW or fmt == FMT_LZ5:
        idx = data if fmt == FMT_RAW else lz5_decode(data, w, h)
        img = Image.frombytes("P", (w, h), idx[:w * h])
        if palettes:
            which = sp["pal"] if palidx is None else palidx
            flat = []
            for c in palette_rgb(palettes, which):
                flat.extend(c)
            img.putpalette(flat)
            transparency = 0
            img.info["transparency"] = transparency
        return img.convert("RGBA")
    raise ValueError(f"unsupported sprite format {fmt}")
