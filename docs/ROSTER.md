# The roster

Nine fighters, each in their own folder with a `.def`, `.cmd`, `.cns`, `.air`,
`.sff`, `.snd` and a themed `movelist.dat`, plus movie-flavoured victory quotes in
the CNS `[Quotes]` section.

| Fighter | Role | Life | ATK | DEF | Notes |
|---|---|---|---|---|---|
| Jack Burton | hero | 1050 | 108 | 100 | balanced, pistol and knife specials |
| Wang Chi | hero | 950 | 108 | 95 | faster, lower defence; painted rig |
| Gracie Law | hero | 880 | 94 | 92 | fastest, lowest damage; painted rig |
| Maio Yin | hero | 900 | 101 | 94 | Lo Pan's bride-to-be; painted rig |
| Egg Shen | hero | 900 | 115 | 88 | glass cannon sorcerer; painted rig |
| Rain | storm | 950 | 100 | 96 | water specials, twin claw rakes; painted rig |
| Lightning | storm | 1000 | 105 | 100 | first-tier ladder opponent |
| Thunder | storm | 1200 | 115 | 112 | heavy, scaled up 12% |
| Lo Pan | boss | 1300 | 125 | 112 | final boss |

Stats, scale and colours are listed once in `tools/build_chars.py` (`ROSTER`) and
regenerated from there, so a change to a fighter's numbers belongs in that table,
not in the generated files.

Gracie Law and Maio Yin are not recolours at all: `tools/women_art.py` paints
their parts in code — vermilion wedding silk, a gold sunburst crown on Maio Yin, a
silver filigree one on Gracie — and `tools/bake_char.py` bakes them into full
fighters in `chars/gracielaw_rig` and `chars/jade_rig`, which is what `select.def`
points at.

Jack is the one fighter whose palette is hand-built rather than hue-shifted.
`tools/jackburton.py` maps Kung Fu Man's colour ramps onto his costume — white tank
top, denim jeans, brown hair, tanned skin, leather boots — and adds his weapon art,
animations and states, so a rebuild cannot drift back to a recoloured base.

## Shared command set

The command set is deliberately shared while every fighter still uses one
animation set.

| Input | Move |
|---|---|
| `F + X` / `DF + X` | high / low guard |
| `B or F + Y` | throw |
| `QCF + P` | palm special (light/strong/fast on x/y/xy) |
| `D-S-F + P` | rising upper |
| `QCB + P` | blow |
| `QDF + K` | kick special |
| `F, F + K` | dash kick |
| `QCB + K` | Jack only: Six Shooter, a three-round pistol burst |
| `QDBF + K` | Jack only: Knife Toss, a spinning thrown blade |
| `QCF, QCF + P` | super (1000 power) |
| `QCB, QCB + P` | super (1000 power) |

## +Chi

Every hit that deals damage awards Chi to the attacker. Normal, special and hyper
attacks and projectiles award 1; hyper attacks and hyper projectiles award 3;
throws award nothing, because they carry no attack attributes. The totals live per
player and are handled in `data/score.zss`.

## Placeholder art

All nine fighters currently use Kung Fu Man's sprites, recoloured per fighter
through graded palette tables, so the silhouettes and animations are all Kung Fu
Man. Replacing them is the project's biggest open job — see
[DESIGN.md](DESIGN.md) for the folder layout and animation list, and
[CONTRIBUTING.md](CONTRIBUTING.md) for how to get a set into the build.
