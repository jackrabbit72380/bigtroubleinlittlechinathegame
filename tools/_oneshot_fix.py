"""One-shot source repair, run once by .github/workflows/fix-scale.yml.

Two defects:
  * the puppet-rig fighters are painted at 3x scale, but bake_char.py never wrote
    a localcoord into their .def, so Ikemen drew them in its 320x240 default and
    they came out three times too big (giant cropped boots in select and in play);
  * build_chars.py graded the whole palette, so skin went magenta and hands cyan.
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NEW_GRADE = '''def grade_colour(rgb, spec):
    """Hue-rotate and grade one colour, keeping skin, whites and blacks neutral.

    Only the clothing colours are meant to move. Grading everything turned faces
    magenta and hands cyan, so skin tones and near-neutral pixels pass through
    untouched and the fighter keeps his own face.
    """
    hue, sat, val = _rgb_to_hsv(*rgb)
    if val < 0.06:                      # keep outlines black
        return rgb
    if sat < 0.12:                      # whites and greys stay neutral
        return rgb
    if 0.010 <= hue <= 0.110 and 0.15 <= sat <= 0.75 and val >= 0.30:
        return rgb                      # skin: shifting this turns faces neon
    sat_shift = spec["pal"][1]
    val_shift = spec["pal"][2]
    hue = (hue + spec["pal"][0] / 360.0) % 1.0
    sat = min(1.0, sat * sat_shift)
    val = min(1.0, val * val_shift)
    return _hsv_to_rgb(hue, sat, val)
'''


def patch_grade_colour():
    path = os.path.join(ROOT, "tools", "build_chars.py")
    src = open(path, encoding="utf-8").read()
    if "skin tones and near-neutral pixels pass" in src:
        print("build_chars.py already patched")
        return
    start = src.index("def grade_colour(")
    end = src.index("def grade_palette(")
    src = src[:start] + NEW_GRADE + "\n\n" + src[end:]
    open(path, "w", encoding="utf-8").write(src)
    print("patched tools/build_chars.py")


def patch_def_template():
    path = os.path.join(ROOT, "tools", "bake_char.py")
    src = open(path, encoding="utf-8").read()
    if "localcoord" in src:
        print("bake_char.py already patched")
        return
    old = "pal.defaults = 1\n\n[Files]"
    new = ("pal.defaults = 1\n"
           "localcoord = {int(320 * clsn_k)}, {int(240 * clsn_k)}\n\n[Files]")
    if src.count(old) != 1:
        raise SystemExit("expected one char-def template, found %d" % src.count(old))
    open(path, "w", encoding="utf-8").write(src.replace(old, new))
    print("patched tools/bake_char.py")


if __name__ == "__main__":
    patch_grade_colour()
    patch_def_template()
    sys.exit(0)
