# Contributing

Thanks for wanting to help. The short version: the game is generated from code in
`tools/`, so most contributions are small Python changes with a clear before and
after — and `python3 tools/validate.py` tells you if you broke something, with no
engine needed.

Say hello first in the [Discord](https://discord.gg/Bn2kABJsK5) and say what you
fancy working on; it stops two people building the same thing.

## What needs doing

| Job | Notes |
|---|---|
| **Original fighter sprites** | The biggest and most valuable job. All nine fighters still use Kung Fu Man's silhouettes, recoloured. See [DESIGN.md](DESIGN.md) for the folder layout and animation list. |
| **Character-specific specials** | The command set is shared only because everyone shares one animation set; it should stop being shared. |
| **Intro and ending storyboards** | Arcade mode per fighter. |
| **Music and voice stings** | Slots in `sound/` are wired already — see [MUSIC.md](MUSIC.md). |
| **Playtesting** | Which move feels wrong, which stage reads badly at 1080p, where the HUD fights the action. Bug reports are contributions. |

## Getting set up

Python 3.9+ and Pillow are all the tooling needs.

```sh
git clone https://github.com/jackrabbit72380/bigtroubleinlittlechinathegame.git
cd bigtroubleinlittlechinathegame
python3 tools/build_all.py     # every generator, then the validator
```

To play your changes, follow [INSTALL.md](INSTALL.md) and drop an engine build next
to `data/`.

## The pipeline

`tools/` is the source of truth. Generators write the engine formats; the binary
files they produce are outputs, not places to hand-edit.

| Generator | Writes |
|---|---|
| `tools/build_chars.py` | the roster folders in `chars/` from the `ROSTER` table |
| `tools/build_stages.py` | arcade-resolution stages |
| `tools/stages_hd.py` | the nine arenas at 1920×1080 (what ships) |
| `tools/build_hd_stage.py` | replaces any stage that has `art_src/` art |
| `tools/women_art.py`, `tools/bake_char.py`, `tools/jackburton.py` | painted fighters |
| `tools/build_banner.py`, `tools/build_timer.py` | the dragon HUD in `data/fight.sff` |
| `tools/build_music.py` | `[Music]` paths in `data/ikemen1/system.def` |
| `tools/dump_stage_art.py` | unpacks stage sprites to PNG for inspection |
| `tools/validate.py` | 44 offline checks: roster, `.air` frames, stage layers, previews, palettes |

If you change a stat, a colour, a stage layer or a HUD sprite, change the generator
and rerun it — that way the change survives the next rebuild. Pull requests that
hand-edit a `.sff` or a generated `.def` will be asked to move into the generator.

On GitHub, the `Build game assets` workflow runs `tools/build_all.py` on every push
that touches the sources and commits the regenerated `chars/`, `stages/`, `data/`
and `artifacts/` back to `main`, so generated files are expected to change with your
source change.

## Before you open a pull request

```sh
python3 tools/build_all.py     # regenerate, then validate
python3 tools/validate.py      # must report: All checks passed (44 checks)
```

Keep pull requests small and focused; a change to one stage or one fighter is much
easier to review than a sweep. Write the commit message about *why* the change was
made, not just what moved.

## Art rules

- **Nothing from the film.** No stills, posters, music, or actor likenesses.
  Character and move names are used as fan fiction; the art has to be original.
- **Stage art is procedural** or supplied by you as `art_src/<stage id>/backdrop.png`.
- **Don't commit assets you don't have the right to distribute.** This project is
  non-commercial, and the release bundles ship whatever is in the repository.
- Keep the Kung Fu Man placeholder rule intact until a replacement set is finished:
  a half-replaced fighter looks worse than a coherent placeholder.

## Code layout

```
data/      screenpack, HUD (fight.def), system and select definitions, ZSS states
chars/     fighters: .def .cmd .cns .air .sff .snd + movelist.dat
stages/    arena definitions and their SFF art
tools/     generators, validators and previews
art_src/   source art and drop-in folders
sound/     menu and stage music
docs/      these documents
artifacts/ generated previews used by the README
```

Screenpack logic is Ikemen's ZSS (`.zss` under `data/`), not raw M.U.G.E.N CNS:
`mapAdd{...}`, `let`, `call Name()`, `[Function Name(args) ret]`, `if ... { }`,
`ignoreHitPause if ...`, `text{...}`. `data/score.zss` is a compact example — it is
where the +Chi reward on damaging hits lives.

## Roadmap

1. Replace the Kung Fu Man silhouettes with original per-character sprite sets.
2. Character-specific specials.
3. Intro and ending storyboards for arcade mode.
4. Original music and voice stings.

## Debug keys

`Ctrl`+`D` shows the debug readout in-game and `Shift`+`F4` reloads the engine
after a code change. The full list, including speed control, frame stepping and
per-player AI toggles, is in [DEV_KEYS.md](DEV_KEYS.md) — or press `Ctrl`+`F1`
in-game to print it into the console.

## Proving the Developer Keys screen in the real engine

`tools/engine_linux.sh` builds the whole stack on a headless Linux box with no
root: the X/GL library closure is unpacked into a private sysroot (resolved with
`apt-get --print-uris`, nothing installed), Xvfb runs on Mesa llvmpipe, and the
official Ikemen GO **nightly** is pointed at this checkout by symlink. Use the
nightly, not a tagged release: a tagged build starts the attract demo and dies
with `Invalid data: inrunstate`, which has nothing to do with this game.

```sh
bash tools/engine_linux.sh --script tools/engine_drive/devkeys-pause.txt --out artifacts/engine
```

Drive commands are `wait N`, `key <xdotool key>`, `shot <name>` and `log`; captures
are written as PNG. `save/config.ini` keeps `AllowDebugKeys = 1`, which the screen's
Ctrl+F1 list hotkey needs.

`tools/test_devhelp.py` is the fast regression net for the same screen: it runs the
mod against a stub engine behaving like each build we might meet (font as a table
or an index, no `textImgNew`, no `textImgSetScale`) and asserts the screen opens and
draws in all four. Install `lupa` first; it exits 77 when lupa is missing.

`tools/test_musicselect.py` is the same net for the MUSIC browser: the stub engine
gives it the motif shapes we might ship, including an `[OptionBGdef]` with no
`bgclearcolor` line and one whose backdrop refuses to draw, and asserts the browser
opens, draws its albums and hands the menu back in each. That missing key once made
the pause item do nothing at all, so this is the shape the test exists for.

Two things are easy to get wrong when driving the engine headless: `[Demo Mode]
enabled = 1` in the motif starts the attract demo, which swallows menu keystrokes,
and Escape at the title quits the game instead of opening the pause menu.
