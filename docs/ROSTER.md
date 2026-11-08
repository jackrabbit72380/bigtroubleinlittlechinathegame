# The roster

Twelve fighters, each in their own folder with a `.def`, `.cmd`, `.cns`, `.air`,
`.sff`, `.snd` and a themed `movelist.dat`, plus movie-flavoured victory quotes in
the CNS `[Quotes]` section.

| Fighter | Life | ATK | DEF | Scale | Notes |
|---|---|---|---|---|---|
| Jack Burton | 1050 | 108 | 100 | 1.0 | truck driver, reluctant hero, one very good knife |
| Eddie Lee | 900 | 104 | 90 | 1.0 | street-smart Chinatown scrapper, fast hands and faster feet |
| Mao Yin | 900 | 101 | 94 | 1.0 | Lo Pan's bride-to-be, and nobody's sacrifice |
| Rain Storm | 950 | 100 | 96 | 0.99 × 1.0 | the quiet Storm, quick as falling water; water specials |
| Lightning Storm | 1000 | 105 | 100 | 1.0 | fastest of the Three Storms |
| Wang Chi | 950 | 108 | 95 | 1.0 | green-eyed restaurateur, faster but softer on defence |
| Gracie Law | 880 | 94 | 92 | 0.96 | fastest and lightest hitter; lawyer and reporter |
| Margo | 880 | 100 | 90 | 0.98 | investigative reporter, and nobody's fool |
| Thunder Storm | 1200 | 115 | 112 | 1.12 | the big one of the Three Storms, scaled up 12% |
| Egg Shen | 900 | 115 | 88 | 0.97 | glass-cannon sorcerer, bus driver and tour guide |
| Sewer Monster | 1250 | 118 | 112 | 1.1 | half-mummified wild man who holds Lo Pan's drains |
| Daved Lo Pan | 1300 | 125 | 112 | 1.1 × 1.08 | ghost emperor, sorcerer, and very bad wedding planner |

Stats, scale and colours are listed once in `tools/build_chars.py` (`ROSTER`) and
regenerated from there, so a change to a fighter's numbers belongs in that table,
not in the generated files. The rows above are sorted by the table's `order`
value.

Gracie Law and Mao Yin are not recolours at all: `tools/women_art.py` paints
their parts in code — vermilion wedding silk, a gold sunburst crown on Mao Yin, a
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

Every fighter currently uses Kung Fu Man's sprites, recoloured per fighter through
graded palette tables, so the silhouettes and animations are all Kung Fu Man.
Replacing them is the project's biggest open job — see
[DESIGN.md](DESIGN.md) for the folder layout and animation list, and
[CONTRIBUTING.md](CONTRIBUTING.md) for how to get a set into the build.
