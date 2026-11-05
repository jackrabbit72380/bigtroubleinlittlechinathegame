"""Replace the menu confirm beep with a soft oriental bell.

The engine plays sample group 100, number 1 for a confirmed selection and for
opening the pause menu (the motif points cursor.done.snd and enter.snd at it),
and number 0 for cursor movement, 2 for cancel. Number 1 was the stock
Elecbyte beep: a bright square-ish click that is louder than anything else on
the screen. It is replaced in place with a struck bell - inharmonic partials
over a long exponential decay, struck softly - so every screen that confirms
something gets the new voice without touching a single `snd` key.

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
DEF = os.path.join(ROOT, "data", "ikemen1", "system.def")

SIG = b"ElecbyteSnd\x00"
RATE = 32000
KEY = (100, 1)                 # the "confirm" sample the motif points at

# A struck bell: the fundamental, then the inharmonic partials that make a bell
# read as metal rather than as a tone. (ratio, amplitude, decay in seconds)
PARTIALS = (
    (1.00, 1.00, 0.95),
    (2.00, 0.30, 0.70),
    (2.76, 0.45, 0.55),
    (4.07, 0.18, 0.40),
    (5.40, 0.22, 0.30),
    (8.93, 0.10, 0.18),
)
F0 = 523.25                    # C5: low enough to sit under the music
SECONDS = 1.25
AMP = 0.26                     # deliberately quiet - it was too loud before


def bell(seconds=SECONDS, f0=F0, amp=AMP):
    n = int(RATE * seconds)
    attack = max(1, int(0.003 * RATE))
    out = []
    norm = sum(p[1] for p in PARTIALS)
    for i in range(n):
        t = i / float(RATE)
        v = 0.0
        for ratio, a, decay in PARTIALS:
            v += a * math.exp(-t / decay) * math.sin(2.0 * math.pi * f0 * ratio * t)
        v /= norm
        if i < attack:
            v *= i / float(attack)
        out.append(v * amp)
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


def main():
    blob = open(SND, "rb").read()
    before = read_snd(blob)
    target = next((e for e in before
                   if (e["group"], e["number"]) == KEY), None)
    if target is None:
        raise SystemExit("system.snd has no sample %d,%d to replace" % KEY)

    new_wav = wav_bytes(bell())
    after = [dict(e) for e in before]
    for e in after:
        if (e["group"], e["number"]) == KEY:
            e["wav"] = new_wav

    out = write_snd(after)
    with open(SND + ".tmp", "wb") as f:
        f.write(out)
    os.replace(SND + ".tmp", SND)

    # read it straight back: the count, every other sample byte for byte, and
    # the new one, so a malformed header can never ship silently
    check = read_snd(open(SND, "rb").read())
    if len(check) != len(before):
        raise SystemExit("sound count changed: %d -> %d" % (len(before), len(check)))
    changed = 0
    for a, b in zip(before, check):
        if (a["group"], a["number"]) == KEY:
            if b["wav"] != new_wav or b["wav"][:4] != b"RIFF":
                raise SystemExit("the new bell did not survive the write")
            changed += 1
        elif a["wav"] != b["wav"]:
            raise SystemExit("sample %d,%d was damaged"
                             % (a["group"], a["number"]))
    print("system.snd: %d samples, %d replaced with the bell (%.2fs, %dHz mono)"
          % (len(check), changed, SECONDS, RATE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
