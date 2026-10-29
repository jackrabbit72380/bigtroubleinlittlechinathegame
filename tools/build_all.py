"""Regenerate every generated asset and validate the result.

Run:  python3 tools/build_all.py
"""

from __future__ import annotations

import os
import subprocess
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))


def run(script):
    print(f"$ python3 tools/{script}")
    result = subprocess.run([sys.executable, os.path.join(TOOLS, script)])
    return result.returncode


def main():
    # stages_hd paints the same arenas at 1280x960; stage_throne then repaints
    # Lo Pan's Throne from the concept art, stage_upside_down adds the cavern,
    # and build_hd_stage overlays any stage that has real art in art_src/, so
    # the order matters.
    scripts = ["build_stages.py", "stages_hd.py", "stage_throne.py",
               "stage_upside_down.py", "build_hd_stage.py",
               "build_chars.py", "build_music.py"]
    # The puppet rig: cut Jack's concept turnaround into parts, then bake those
    # parts into a complete character. Only the concept art is needed, which is
    # already in the repo, so a clean checkout builds Jack itself instead of
    # anyone having to commit megabytes of generated sprites.
    concept = os.path.join(TOOLS, os.pardir, "concept_art", "fighters",
                           "jack_burton",
                           "bernardo-mercurio-jack-turnable.jpg")
    if os.path.isfile(concept):
        scripts += ["jack_cut.py", "bake_char.py"]
    scripts.append("validate.py")
    for script in scripts:
        code = run(script)
        if code != 0:
            print(f"\n{script} failed (exit {code})")
            return code
    print("\nAll assets rebuilt and validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
