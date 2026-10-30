"""Regenerate every generated asset and validate the result.

Run:  python3 tools/build_all.py
"""

from __future__ import annotations

import os
import subprocess
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))


def run(script, *args):
    print("$ python3 tools/" + " ".join((script,) + args))
    result = subprocess.run([sys.executable, os.path.join(TOOLS, script), *args])
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
        scripts += ["jack_cut.py", ("bake_char.py", "jackburton")]
    # Lightning has no turnaround to cut: his parts are painted in code, so the
    # only inputs are the tools themselves and a clean checkout can build him.
    scripts += ["lightning_art.py", ("bake_char.py", "lightning")]
    # Select-screen portraits: the pre-match screens read each fighter's 9000,0
    # and 9000,1 out of its own SFF, and a character baked from the rig has
    # neither, so they are rendered from its own art after the bake.
    scripts.append("build_portraits.py")
    # The title logo is painted into the screenpack SFF, which a fresh engine
    # data copy resets on every build, so it is regenerated rather than
    # committed by hand.
    title_sff = os.path.join(TOOLS, os.pardir, "data", "ikemen1", "system.sff")
    if os.path.isfile(title_sff):
        scripts.append("build_title.py")
    # The splash lives in the engine data too - logo.def points at system.sff -
    # so it is rebuilt from the same reset, after the title has written its
    # layers, to keep both edits to that file in one pass.
    logo_def = os.path.join(TOOLS, os.pardir, "data", "ikemen1", "logo.def")
    if os.path.isfile(logo_def):
        scripts.append("build_splash.py")
    # The select screen itself: the portrait grid, its frames and cursors,
    # painted into the same system.sff.
    if os.path.isfile(title_sff):
        scripts.append("build_select_grid.py")
    # The stage-select hint is another layer in the same screenpack.
    if os.path.isfile(title_sff):
        scripts.append("build_select_ui.py")
    scripts.append("validate.py")
    for entry in scripts:
        script, *args = (entry,) if isinstance(entry, str) else entry
        code = run(script, *args)
        if code != 0:
            print(f"\n{script} failed (exit {code})")
            return code
    print("\nAll assets rebuilt and validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
