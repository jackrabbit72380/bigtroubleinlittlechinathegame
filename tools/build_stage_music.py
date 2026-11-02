"""Synthesise the game's music: one loopable cue per stage, written in code.

There was no audio in the repository at all - ``sound/`` held only a README,
and every stage's ``bgmusic`` was blank - so every match ran silent. Shipping
third-party tracks is not an option (the README is explicit that nothing
redistributable is bundled by default), so the music is generated the same way
the art is: procedural, deterministic, and checked in as a build artifact.

Each cue is a short seamless loop, mono 22050 Hz 16-bit WAV - the engine picks
its decoder off the extension, so WAV needs no extra toolchain:

    sound/Throne.wav       Lo Pan's hall: low gong, slow drone, minor second
    sound/Exchange.wav     the Wing Kong warehouse: industrial pulse, metallic
    sound/Alley.wav        Chinatown at night: rain, distant percussion
    sound/Highway.wav      the Pork Chop Express: driving bass ostinato
    sound/UpsideDown.wav   the cavern: drips, a hollow fifth
    sound/Airport.wav      the terminal: fluorescent hum, tense pulse

Loops are seam-blended: the tail is cross-faded into the head so the file can
repeat without a click, which matters more than the last bar of the phrase.

Run:  python3 tools/build_stage_music.py     (also part of tools/build_all.py)
"""

from __future__ import annotations

import math
import os
import random
import struct
import sys
import wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOUND = os.path.join(ROOT, "sound")

RATE = 22050
SECONDS = 24
N = RATE * SECONDS
FADE = int(RATE * 0.75)          # loop cross-fade


def note(semi, root):
    """Semitone offset from a root frequency."""
    return root * (2.0 ** (semi / 12.0))


def env(t, attack, decay, sustain, release, dur):
    """A simple ADSR over one note of length dur."""
    if t < 0 or t > dur:
        return 0.0
    if t < attack:
        return t / attack
    t -= attack
    if t < decay:
        return 1.0 - (1.0 - sustain) * (t / decay)
    t -= decay
    if t < release:
        return sustain
    t -= release
    if t < dur - attack - decay - release:
        return sustain
    left = dur - attack - decay - release - t
    return max(0.0, sustain * left / max(0.01, dur * 0.25))


def triangle(phase):
    return 2.0 * abs(2.0 * (phase - math.floor(phase + 0.5))) - 1.0


def render(spec):
    """Render one cue to a list of floats in -1..1."""
    rnd = random.Random(spec["seed"])
    root = spec["root"]
    beat = 60.0 / spec["bpm"]
    out = [0.0] * N

    # --- drone bed: root and fifth, detuned, slowly breathing ---------------
    drone = spec.get("drone", 0.22)
    for semi, gain, det in spec.get("drone_notes", ((0, 1.0, 0.0), (7, 0.6, 0.12))):
        f = note(semi, root) * (1.0 + det / 100.0)
        w = 2.0 * math.pi * f / RATE
        lfo = 2.0 * math.pi * (1.0 / (SECONDS * 0.5)) / RATE
        for i in range(N):
            amp = 0.5 + 0.5 * math.sin(lfo * i + semi)
            out[i] += drone * gain * amp * math.sin(w * i)

    # --- bass pulse on the beat --------------------------------------------
    bass = spec.get("bass", 0.0)
    if bass:
        steps = spec.get("bass_steps", (0, 0, -5, 0, -2, -2, -5, -5))
        per_bar = len(steps)
        pos = 0.0
        k = 0
        while pos < SECONDS:
            i0 = int(pos * RATE)
            dur = beat * spec.get("bass_len", 0.9)
            f = note(steps[k % per_bar], root * 0.5)
            n = int(dur * RATE)
            w = 2.0 * math.pi * f / RATE
            for j in range(n):
                idx = i0 + j
                if idx >= N:
                    break
                t = j / float(RATE)
                a = min(1.0, t / 0.012) * math.exp(-t * spec.get("bass_decay", 3.2))
                out[idx] += bass * a * (math.sin(w * j) * 0.8 +
                                        triangle(w * j * 0.5) * 0.2)
            pos += beat * spec.get("bass_step", 1.0)
            k += 1

    # --- percussion: a noise burst with a tuned body ------------------------
    perc = spec.get("perc", 0.0)
    if perc:
        steps = spec.get("perc_steps", (0, 3, 4, 3, 0, 3, 5, 3))
        pos = spec.get("perc_offset", 0.0)
        k = 0
        while pos < SECONDS:
            i0 = int(pos * RATE)
            big = (k % len(steps)) == 0
            dur = 0.34 if big else 0.16
            n = int(dur * RATE)
            body = note(steps[k % len(steps)] - 12, root * 2.0)
            w = 2.0 * math.pi * body / RATE
            for j in range(n):
                idx = i0 + j
                if idx >= N:
                    break
                t = j / float(RATE)
                a = math.exp(-t * (16.0 if not big else 8.0))
                noise = rnd.uniform(-1.0, 1.0)
                out[idx] += perc * a * (noise * 0.55 + math.sin(w * j) * 0.45)
            pos += beat * spec.get("perc_step", 0.5)
            k += 1

    # --- bells / gongs: long decaying tones on the phrase -------------------
    bell = spec.get("bell", 0.0)
    if bell:
        steps = spec.get("bell_steps", (12, 7, 5, 0))
        pos = spec.get("bell_offset", beat * 4)
        k = 0
        while pos < SECONDS:
            i0 = int(pos * RATE)
            f = note(steps[k % len(steps)], root * 2.0)
            dur = 3.4
            n = int(dur * RATE)
            for j in range(n):
                idx = i0 + j
                if idx >= N:
                    break
                t = j / float(RATE)
                a = math.exp(-t * 1.5) * min(1.0, t / 0.008)
                out[idx] += bell * a * (math.sin(2 * math.pi * f * j / RATE) +
                                        0.5 * math.sin(2 * math.pi * f * 2.01 * j / RATE) +
                                        0.25 * math.sin(2 * math.pi * f * 3.02 * j / RATE))
            pos += spec.get("bell_gap", SECONDS / 2.0)
            k += 1

    # --- air: a moving filtered-noise bed, the sound of the room ------------
    air = spec.get("air", 0.0)
    if air:
        lp = 0.0
        for i in range(N):
            lp += 0.02 * (rnd.uniform(-1.0, 1.0) - lp)
            out[i] += air * lp

    # --- seam blend: the tail is mixed into the head, so the loop is smooth --
    for i in range(FADE):
        a = i / float(FADE)
        out[i] = out[i] * a + out[N - FADE + i] * (1.0 - a)
    out = out[:N - FADE]

    peak = max(1e-9, max(abs(v) for v in out))
    scale = spec.get("level", 0.72) / peak
    return out, scale


def write_wav(path, samples, scale):
    with wave.open(path, "wb") as fh:
        fh.setnchannels(1)
        fh.setsampwidth(2)
        fh.setframerate(RATE)
        frames = bytearray()
        for v in samples:
            s = int(max(-1.0, min(1.0, v * scale)) * 32000)
            frames += struct.pack("<h", s)
        fh.writeframes(bytes(frames))


TRACKS = {
    "Throne": dict(seed=11, root=73.0, bpm=52, drone=0.26,
                   drone_notes=((0, 1.0, 0.0), (7, 0.55, 0.10), (1, 0.18, 0.0)),
                   bass=0.30, bass_steps=(0, 0, -1, 0, -5, -5, -1, -1),
                   bass_step=2.0, bass_decay=1.6,
                   perc=0.22, perc_steps=(0, 0, 5, 0), perc_step=2.0,
                   bell=0.20, bell_steps=(12, 7, 5, 0, 7, 12), bell_gap=4.0,
                   air=0.05, level=0.70),
    "Exchange": dict(seed=23, root=87.0, bpm=96, drone=0.18,
                     drone_notes=((0, 1.0, 0.0), (3, 0.5, 0.15)),
                     bass=0.32, bass_steps=(0, 0, 3, 0, -2, -2, 3, 3),
                     bass_step=0.5, bass_len=0.42, bass_decay=6.0,
                     perc=0.26, perc_steps=(0, 4, 2, 4, 0, 4, 5, 4),
                     perc_step=0.25, air=0.04, level=0.72),
    "Alley": dict(seed=37, root=98.0, bpm=72, drone=0.24,
                  drone_notes=((0, 1.0, 0.0), (7, 0.45, 0.08), (10, 0.3, 0.0)),
                  bass=0.24, bass_steps=(0, 0, -5, -5), bass_step=2.0,
                  bass_decay=2.4,
                  perc=0.16, perc_steps=(0, 7, 3, 7), perc_step=0.75,
                  bell=0.14, bell_steps=(7, 5, 3, 7), bell_gap=6.0,
                  air=0.10, level=0.70),
    "Highway": dict(seed=41, root=82.0, bpm=112, drone=0.16,
                    drone_notes=((0, 1.0, 0.0), (5, 0.4, 0.12)),
                    bass=0.34, bass_steps=(0, 0, 0, 5, 3, 3, 5, 5),
                    bass_step=0.5, bass_len=0.40, bass_decay=6.5,
                    perc=0.24, perc_steps=(0, 4, 4, 2), perc_step=0.5,
                    air=0.07, level=0.74),
    "UpsideDown": dict(seed=53, root=65.0, bpm=58, drone=0.28,
                       drone_notes=((0, 1.0, 0.0), (6, 0.5, 0.05), (11, 0.22, 0.0)),
                       bass=0.20, bass_steps=(0, -2, -5, -2), bass_step=2.0,
                       bass_decay=1.4,
                       perc=0.12, perc_steps=(0, 9, 6, 9), perc_step=1.5,
                       bell=0.16, bell_steps=(11, 6, 2, 6), bell_gap=5.0,
                       air=0.12, level=0.68),
    "Airport": dict(seed=67, root=110.0, bpm=84, drone=0.20,
                    drone_notes=((0, 1.0, 0.0), (-5, 0.5, 0.10), (7, 0.3, 0.0)),
                    bass=0.26, bass_steps=(0, -5, 0, -2), bass_step=1.0,
                    bass_decay=3.0,
                    perc=0.18, perc_steps=(0, 3, 6, 3), perc_step=0.75,
                    bell=0.12, bell_steps=(12, 12, 7), bell_gap=8.0,
                    air=0.09, level=0.70),
}

# Which stage points at which cue. The menu slots reuse the same files so the
# screens are not silent either; tools/build_music.py picks up sound/Title.wav
# and friends for the screenpack.
STAGE_TRACK = {
    "lopans_throne": "Throne",
    "wingkong_exchange": "Exchange",
    "chinatown_alley": "Alley",
    "porkchop_express": "Highway",
    "the_upside_down": "UpsideDown",
    "airport_terminal": "Airport",
}


def main():
    os.makedirs(SOUND, exist_ok=True)
    only = sys.argv[1:] or sorted(TRACKS)
    for name in only:
        spec = TRACKS[name]
        samples, scale = render(spec)
        path = os.path.join(SOUND, name + ".wav")
        write_wav(path, samples, scale)
        secs = len(samples) / float(RATE)
        print(f"  sound/{name}.wav  {secs:.1f}s loop  "
              f"{os.path.getsize(path) / 1024:.0f} KiB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
