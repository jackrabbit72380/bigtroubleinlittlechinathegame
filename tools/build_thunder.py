#!/usr/bin/env python3
"""Put a thunder rumble in data/system.snd for the rainfall stage.

A stage DEF cannot play a sound: the only audio a stage owns is its bgmusic. The
rumble therefore lives in the motif's sound bank, data/system.snd, as group 900
number 0 - a high group no menu key points at, so nothing else can pick it up by
accident - and external/mods/rainthunder.lua plays it in time with the lightning
that [Begin Action 9001] in stages/stage3d_rain.def draws.

The sample is synthesised here rather than sampled, so it is ours and the file
stays reproducible: a crack of broadband noise, brown noise through a one-pole
lowpass for the body, a falling sub for the weight, and a second, later rumble
rolling in behind it.

system.snd is the standard MUGEN container, laid out exactly as
tools/build_ui_sounds.py writes it, and that module's reader and writer are used
here so the two can never disagree about the format. Every other sample is read
straight back and compared byte for byte, because system.snd is what every menu
beep comes out of.

Run: python3 tools/build_thunder.py
"""
from __future__ import annotations

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build_ui_sounds import RATE, read_snd, wav_bytes, write_snd   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SND = os.path.join(ROOT, "data", "system.snd")
GROUP, NUMBER = 900, 0
SECONDS = 5.0
SEED = 90210


def thunder(seconds=SECONDS, seed=SEED):
    """A thunderclap: crack, body, sub, and a distant second rumble."""
    n = int(RATE * seconds)
    rng = random.Random(seed)
    out = [0.0] * n

    # the crack: broadband noise, high-passed by differencing neighbours, gone
    # inside a fifth of a second so it reads as a tear rather than as hiss
    previous = 0.0
    crack = int(0.18 * RATE)
    for i in range(crack):
        value = rng.uniform(-1.0, 1.0)
        out[i] += (value - previous) * 0.55 * math.exp(-i / (0.035 * RATE))
        previous = value

    # the body: brown noise (a random walk) through a 130Hz one-pole lowpass, so
    # it is a deep roll and not static, swelling over the first 45ms then dying
    coeff = 2.0 * math.pi * 130.0 / RATE
    coeff = coeff / (1.0 + coeff)
    brown = 0.0
    low = 0.0
    for i in range(n):
        brown = brown * 0.998 + rng.uniform(-1.0, 1.0) * 0.02
        low += coeff * (brown - low)
        t = i / float(RATE)
        attack = min(1.0, t / 0.045)
        body = math.exp(-t / 1.35) * attack
        roll = 0.72 + 0.28 * math.sin(2.0 * math.pi * 0.55 * t + 0.7)
        out[i] += low * 5.2 * body * roll
        # the sub: it drops in pitch as it decays, which is what the chest reads
        hz = 58.0 - 18.0 * min(1.0, t / 3.0)
        out[i] += 0.30 * math.exp(-t / 2.1) * math.sin(2.0 * math.pi * hz * t)

    # a second, distant rumble rolling in behind the first: thunder arrives late
    delay = int(0.32 * RATE)
    for i in range(delay, n):
        t = (i - delay) / float(RATE)
        hz = 42.0 - 6.0 * min(1.0, t / 2.0)
        out[i] += 0.22 * math.exp(-t / 1.6) * math.sin(2.0 * math.pi * hz * t)

    # normalise, then fade the tail so the sample cannot click
    peak = max(abs(v) for v in out) or 1.0
    scale = 0.86 / peak
    fade = max(1, int(0.08 * RATE))
    for i in range(n):
        value = out[i] * scale
        if i > n - fade:
            value *= (n - i) / float(fade)
        out[i] = value
    return out


def main():
    entries = read_snd(open(SND, "rb").read())
    before = [(e["group"], e["number"], e["wav"]) for e in entries]
    wav = wav_bytes(thunder())

    if (GROUP, NUMBER) in {(g, n) for g, n, _w in before}:
        for e in entries:
            if (e["group"], e["number"]) == (GROUP, NUMBER):
                e["wav"] = wav
    else:
        entries.append({"group": GROUP, "number": NUMBER, "next": 0, "wav": wav})

    with open(SND + ".tmp", "wb") as fh:
        fh.write(write_snd(entries))
    os.replace(SND + ".tmp", SND)

    # read it straight back: the count, every other sample untouched, and the
    # thunder itself still a valid RIFF wav
    check = read_snd(open(SND, "rb").read())
    if len(check) != len(before):
        raise SystemExit("sound count changed: %d -> %d" % (len(before), len(check)))
    for (g, n, old), e in zip(before, check):
        if (g, n) == (GROUP, NUMBER):
            continue
        if (e["group"], e["number"]) != (g, n) or e["wav"] != old:
            raise SystemExit("sample %d,%d was damaged" % (g, n))
    thunder_entry = [(e["group"], e["number"], e["wav"]) for e in check
                     if (e["group"], e["number"]) == (GROUP, NUMBER)]
    if not thunder_entry:
        raise SystemExit("the thunder sample did not survive the write")
    if thunder_entry[0][2] != wav or thunder_entry[0][2][:4] != b"RIFF":
        raise SystemExit("the thunder sample came back different")
    print("system.snd: %d samples, %d,0 thunder is %.2fs (%.0f KB)"
          % (len(check), NUMBER, len(thunder()) / float(RATE),
             len(wav) / 1024.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
