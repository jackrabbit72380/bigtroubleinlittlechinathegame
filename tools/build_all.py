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
    for script in ("build_stages.py", "stages_hd.py", "stage_throne.py",
                   "stage_upside_down.py", "build_hd_stage.py",
                   "build_chars.py", "build_music.py", "validate.py"):
        code = run(script)
        if code != 0:
            print(f"\n{script} failed (exit {code})")
            return code
    print("\nAll assets rebuilt and validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
