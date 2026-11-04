"""Regenerate every generated asset and validate the result.

Run:  python3 tools/build_all.py
"""

from __future__ import annotations

import os
import subprocess
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)

import gangs


def run(script, *args):
    print("$ python3 tools/" + " ".join((script,) + args))
    result = subprocess.run([sys.executable, os.path.join(TOOLS, script), *args])
    return result.returncode


def main():
    # stages_hd paints the same arenas at 1920x1080; stage_throne then repaints
    # Lo Pan's Throne from the concept art, stage_upside_down adds the cavern,
    # and build_hd_stage overlays any stage that has real art in art_src/, so
    # the order matters.
    # The menu face is installed first, so every later step that draws text
    # through art.font() uses the same vendored typeface.
    scripts = ["build_fonts.py"]
    scripts += ["build_stages.py", "stages_hd.py", "stage_throne.py",
               "stage_ceremony.py", "stage_hallway.py",
               "stage_upside_down.py", "stage_airport.py", "stage_sinners.py",
               "build_hd_stage.py",
               "readme_cards.py",
               "build_chars.py", "build_music.py"]
    # The puppet rig: cut Jack's concept turnaround into parts, then bake those
    # parts into a complete character. Only the concept art is needed, which is
    # already in the repo, so a clean checkout builds Jack itself instead of
    # anyone having to commit megabytes of generated sprites.
    concept = os.path.join(TOOLS, os.pardir, "concept_art", "fighters",
                           "jack_burton",
                           "bernardo-mercurio-jack-turnable.jpg")
    if os.path.isfile(concept):
        # side_parts cuts the profile set the fight poses are drawn from. It was
        # never in this chain, so a clean build baked whatever parts_side copy
        # happened to be on disk - including the one with the arm pivoted at a
        # placeholder corner and a torso bone longer than the torso art.
        scripts += ["jack_parts.py",
                    ("bake_char.py", "jackburton")]
    # Lightning has no turnaround to cut: his parts are painted in code, so the
    # only inputs are the tools themselves and a clean checkout can build him.
    scripts += ["lightning_art.py", ("bake_char.py", "lightning")]
    # Rain is the third Storm and wears the same hat and cloak, so he is painted
    # from the same pieces in pale grey cloth, with a claw rake in each fist.
    scripts += ["rain_art.py", ("bake_char.py", "rain")]
    # Thunder is the last of the Three Storms: the same hat and cloak, but he
    # is the heavyweight - quilted ochre robe, iron pauldrons and a crescent
    # blade in each fist, throwing air pressure rather than lightning.
    scripts += ["thunder_art.py", ("bake_char.py", "thunder")]
    # Lo Pan, from the concept sheet and the film: the towering headdress, the
    # navy imperial robe with the phoenix on it, the beard and the claws. His
    # sorcery is conjured sigils and green fire, in tools/lopan.py.
    scripts += ["lopan_art.py", ("bake_char.py", "lopan")]
    # Gracie Law and Maio Yin are painted in code too: vermilion wedding silk,
    # a gold sunburst on Maio Yin and a silver filigree on Gracie. Their base skeleton
    # comes from build_chars.py above, so both bake after it.
    scripts += ["women_art.py", ("bake_char.py", "gracielaw"),
                ("bake_char.py", "jade")]
    # Egg Shen, from the statue and the concept drawing: baggy jacket, rope
    # belt, satchel slung across him, long grey hair and a small beard.
    scripts += ["eggshen_art.py", ("bake_char.py", "eggshen")]
    # Wang Chi, from the warehouse drawing and the film still: brown fedora,
    # blue-and-tan striped scarf, light shirt, charcoal trousers.
    scripts += ["wangchi_art.py", ("bake_char.py", "wangchi")]
    # Eddie Lee, the roster's counter-fighter: an open jacket over rolled
    # sleeves, fingerless gloves and the Chang Sing colours, painted in code.
    scripts += ["eddilee_art.py", ("bake_char.py", "eddilee")]
    # The sewer monster: the half-mummified wild man from the drains, authored
    # taller than the roster so his crouch still stands over the fighters.
    scripts += ["sewermonster_art.py", ("bake_char.py", "sewermonster")]
    # Margo, the reporter: denim jacket, press badge, satchel and wrist
    # recorder, painted in code like the rest of the roster.
    scripts += ["margo_art.py", ("bake_char.py", "margo")]
    # The two gangs are puppet rigs like everyone else: gangs.py paints each
    # member's parts under art_src/chars/<id>/, and that member is then baked on
    # his own. One bake per fighter, so editing Bo's gi or Bai's bandana and
    # rebuilding touches that fighter's parts and nobody else's.
    #
    # gang_kfm.py is NOT in this chain. It rebuilds every member from Kung Fu
    # Man's recoloured sheet, which drops the rig art and the portraits, so a
    # full rebuild used to silently undo hand-tuned fighters. It is a prototype
    # now, writes to chars/<id>_kfm, and needs --force to touch a shipped rig.
    scripts.append("gangs.py")
    gang_ids = [f"{gang}_{member[0]}"
                for gang, members in gangs.MEMBERS for member in members]
    scripts += [("bake_char.py", cid) for cid in gang_ids]
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
    # The in-fight captions (ROUND 1, FIGHT, HITS!, the names) take the same
    # gold as the menus; fight.def is one of the files reset above.
    fight_def = os.path.join(TOOLS, os.pardir, "data", "fight.def")
    if os.path.isfile(fight_def):
        scripts.append("build_fight_text.py")
    # The power meters are painted into the engine's fight.sff.
    # The VS HUD: one dragon per side whose back is the health bar, whose belly
    # is the audacity bar, and whose heads frame the yin-yang timer. It repaints
    # [Lifebar], [Powerbar] and [Time] in data/fight.def and the sprites in
    # data/fight.sff, both of which the engine copy above starts from stock, so
    # it has to run here or a rebuild would put the old bars back.
    scripts += ["build_banner.py", "build_powerbar.py"]
    # The pause menu's Developer Keys entry is declared in the motif, which the
    # engine copy above resets, so it is re-applied here rather than edited by
    # hand. external/mods/devhelp.lua supplies the screen it opens.
    devhelp_motif = os.path.join(TOOLS, os.pardir, "data", "ikemen1", "system.def")
    if os.path.isfile(devhelp_motif):
        scripts.append("build_devhelp.py")
    # The in-game HUD render shown on the project page. Compositing it here
    # means the picture cannot drift from the HUD that ships in data/, and a
    # push refreshes it without anyone opening the engine.
    preview_stage = os.path.join(TOOLS, os.pardir, "artifacts",
                                 "lopans_throne_preview.png")
    if os.path.isfile(preview_stage):
        scripts.append("preview_hud.py")
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
