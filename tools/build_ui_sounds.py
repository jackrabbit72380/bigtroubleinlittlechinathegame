"""Replace the menu beeps with a soft bell and a wooden tick.

The engine plays sample group 100, number 1 for a confirmed selection and for
opening the pause menu (the motif points cursor.done.snd and enter.snd at it),
and number 0 for cursor movement, 2 for cancel. Number 1 was the stock
Elecbyte beep: a bright square-ish click that is louder than anything else on
the screen. Number 0 is the one heard on every cursor step, which is why it
grates after a minute of navigating.

Both are replaced in place, so every screen that confirms or moves gets the new
voice without touching a single `snd` key:

    100,1  a struck bell - inharmonic partials over a long exponential decay
    100,0  a wooden tick - two short partials and a low thump, ending in 60ms

The file itself is the standard MUGEN sound container:

    12 bytes  "ElecbyteSnd\\0"
    4 x u32   version, sample count, offset of the first sample, len of block
    samples   16-byte header (next offset, wav length, group, number) + wav

Run: python3 tools/build_ui_sounds.py
"""

from __future__ import annotations

import math
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SND = os.path.join(ROOT, "data", "system.snd")

SIG = b"ElecbyteSnd\x00"
RATE = 32000

# A struck bell: the fundamental, then the inharmonic partials that make a bell
# read as metal rather than as a tone. (ratio, amplitude, decay in seconds)
BELL_PARTIALS = (
    (1.00, 1.00, 0.95),
    (2.00, 0.30, 0.70),
    (2.76, 0.45, 0.55),
    (4.07, 0.18, 0.40),
    (5.40, 0.22, 0.30),
    (8.93, 0.10, 0.18),
)
BELL_F0 = 523.25               # C5: low enough to sit under the music
BELL_SECONDS = 1.25
BELL_AMP = 0.26                # deliberately quiet - it was too loud before

# A cursor tick: a woodblock, not a tone. Two partials a fifth apart, both dead
# inside 60ms, over a low knock that gives it weight at low volume. The stock
# sample was a 440Hz square blip held for a tenth of a second - a note, and an
# annoying one; this is a piece of wood being tapped, which is what the ear
# expects a menu to sound like.
TICK_PARTIALS = (
    (1.00, 1.00, 0.022),
    (1.87, 0.55, 0.016),
    (3.41, 0.22, 0.009),
)
TICK_F0 = 660.0
TICK_THUMP_HZ = 196.0
TICK_THUMP_DECAY = 0.030
TICK_THUMP_AMP = 0.55
TICK_SECONDS = 0.075
TICK_AMP = 0.13                # under the bell, and well under the music


def struck(partials, f0, seconds, amp, attack=0.0015, thump=None):
    n = int(RATE * seconds)
    edge = max(1, int(attack * RATE))
    out = []
    norm = sum(p[1] for p in partials)
    for i in range(n):
        t = i / float(RATE)
        v = 0.0
        for ratio, a, decay in partials:
            v += a * math.exp(-t / decay) * math.sin(2.0 * math.pi * f0 * ratio * t)
        v /= norm
        if thump is not None:
            hz, decay, level = thump
            v += level * math.exp(-t / decay) * math.sin(2.0 * math.pi * hz * t)
        if i < edge:
            v *= i / float(edge)
        # the tail is cut, so fades out to nothing rather than clicking
        out.append(v * amp * min(1.0, (n - i) / float(max(1, edge * 40))))
    return out


def wav_bytes(samples):
    data = b"".join(struct.pack("<h", max(-32768, min(32767, int(v * 32767))))
                    for v in samples)
    header = b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVEfmt "
    header += struct.pack("<IHHIIHH", 16, 1, 1, RATE, RATE * 2, 2, 16)
    header += b"data" + struct.pack("<I", len(data))
    return header + data


def read_snd(blob):
    if blob[:12] != SIG:
        raise SystemExit("data/system.snd is not a MUGEN sound file")
    _version, count, start, _block = struct.unpack("<IIII", blob[12:28])
    entries = []
    for _ in range(count):
        nxt, length, group, number = struct.unpack("<IIII", blob[start:start + 16])
        entries.append({"next": nxt, "group": group, "number": number,
                        "wav": blob[start + 16:start + 16 + length]})
        if nxt == 0:
            break
        start = nxt
    return entries


def write_snd(entries):
    out = bytearray(SIG + struct.pack("<IIII", 0, len(entries), 28, 0))
    block = 0
    for i, e in enumerate(entries):
        length = len(e["wav"])
        nxt = 0 if i == len(entries) - 1 else 28 + block + 16 + length
        out += struct.pack("<IIII", nxt, length, e["group"], e["number"])
        out += e["wav"]
        block += 16 + length
    struct.pack_into("<I", out, 24, block)
    return bytes(out)


def replacement(name, wav):
    return name, wav


def main():
    blob = open(SND, "rb").read()
    before = read_snd(blob)

    wanted = {}
    wanted[(100, 1)] = ("bell", wav_bytes(
        struck(BELL_PARTIALS, BELL_F0, BELL_SECONDS, BELL_AMP, attack=0.003)))
    wanted[(100, 0)] = ("tick", wav_bytes(
        struck(TICK_PARTIALS, TICK_F0, TICK_SECONDS, TICK_AMP,
               thump=(TICK_THUMP_HZ, TICK_THUMP_DECAY, TICK_THUMP_AMP))))

    present = {(e["group"], e["number"]) for e in before}
    missing = [k for k in wanted if k not in present]
    if missing:
        raise SystemExit("system.snd has no sample %d,%d to replace" % missing[0])

    after = [dict(e) for e in before]
    for e in after:
        key = (e["group"], e["number"])
        if key in wanted:
            e["wav"] = wanted[key][1]

    with open(SND + ".tmp", "wb") as f:
        f.write(write_snd(after))
    os.replace(SND + ".tmp", SND)

    # read it straight back: the count, every other sample byte for byte, and
    # the new ones, so a malformed header can never ship silently
    check = read_snd(open(SND, "rb").read())
    if len(check) != len(before):
        raise SystemExit("sound count changed: %d -> %d" % (len(before), len(check)))
    changed = []
    for a, b in zip(before, check):
        key = (a["group"], a["number"])
        if key in wanted:
            if b["wav"] != wanted[key][1] or b["wav"][:4] != b"RIFF":
                raise SystemExit("sample %d,%d did not survive the write" % key)
            changed.append("%d,%d %s" % (key[0], key[1], wanted[key][0]))
        elif a["wav"] != b["wav"]:
            raise SystemExit("sample %d,%d was damaged" % key)
    print("system.snd: %d samples, replaced: %s" % (len(check), ", ".join(changed)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
