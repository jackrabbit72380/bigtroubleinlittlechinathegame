# Design notes

## Why the fighters are recoloured Kung Fu Man

Kung Fu Man ships with Ikemen GO as the sample character. Reproducing eight
distinct movie characters as original sprite art is weeks of pixel work, so the
repo starts from a working, animatable fighter and changes everything that is
data: identity, stats, scale, colour, move names, victory quotes.

Two approaches were tried; only one works with this asset:

1. **`.act` palette files (`pal1 = jack.act`).** Rejected. This SFF stores its
   palettes as 32-colour tables (the art is LZ5-compressed, 5-bit indexed), and
   the sprite palette slots are shared stubs. A separate `.act` does not map
   reliably onto them.
2. **Graded palette table baked into each fighter's own `.sff`.** Shipped. Every
   fighter folder contains a copy of the base sprite file with the same sprite
   payloads (byte-identical, so animations are unchanged) and a palette table
   where each colour is hue-rotated and saturation/value graded for that
   character. This is deterministic, needs no runtime support, and each fighter
   set costs ~200 KB instead of a re-encoded multi-megabyte PNG set.

Grading avoids recolouring outlines (very dark colours are left alone) and fades
the hue shift out for low-saturation pixels, which keeps skin highlights and
whites from turning neon.

## Jack Burton: a real costume instead of a hue shift

Hue-rotating the whole table gives Jack a teal body, not Jack. His palette is
therefore written out by hand in `tools/jackburton.py` (`COSTUME`), using the fact
that Kung Fu Man's 32-colour table is laid out in ramps that map onto body
regions consistently in every frame:

| Indices | Base art region | Jack |
|---|---|---|
| 16-20 | trousers | denim jeans |
| 21-24 | vest and headband | white tank top |
| 25-29 | skin | tanned skin |
| 30 | hair | brown |
| 31 | outline / shadow | warm dark |

Rebuilding those ramps (rather than rotating them) is what produces white,
denim and brown instead of a single shifted hue. Palette 1 is the costume; the
other fifteen slots are grades of it, so alternate colours stay available.

## Jack Burton: the pistol and the knife

Jack is the only fighter with weapon moves, so his `.air`, `.cmd` and `.cns`
carry extra sections that the other seven do not. `tools/build_chars.py` appends
them from `tools/jackburton.py` during a build, which keeps them out of the
shared base files:

* **Sprites** 7000 (pistol round), 7001 (three-frame muzzle flash), 7002
  (three-frame impact spark), 7010 (four-frame spinning knife), written as PNG32
  into `jackburton.sff` alongside the indexed base art.
* **Animations** 7000-7010 in the AIR, each with the Clsn1 box the projectile
  needs.
* **States** 1500 (Six Shooter: three `Projectile` controllers on successive
  animation elements, with an `Explod` flash and a sound at each shot) and 1600
  (Knife Toss: one heavier projectile).
* **Commands** `QCB + K` and `QDBF + K`, wired in the CMD ahead of the shared
  specials.

Because the projectiles are engine objects rather than helpers, they inherit the
own damage, pausetime and spark settings from their own state, and they disappear
on hit or at the end of the round without cleanup code.

## Lightning: the second fighter cut from parts

Jack's parts come from a photographic turnaround. Lightning has none, so
`tools/lightning_art.py` paints his parts from the concept sheet instead: the
huge fringed straw hat, the slate robe with its beaded demon-face chest and grey
waist chevron, the crimson cloak, the black boots, and the blue current that
crawls over his hands and his hat brim. It writes the same
`art_src/chars/lightning/parts/` a hand-drawn turnaround would, so the rig,
the baker and the validator do not care where the pixels came from.

The rig grew one part for him: `cape`. It is drawn first, behind everything
else, hangs from the shoulder joint and rides only 35% of the torso's lean, so
it drapes instead of swinging with the arms. Its pose angle is `cape` in
`POSES`, which is why the two storm poses (`cast`, `cast_release`) also set it.

His specials are electricity, not weapons, but they occupy the same slots Jack's
pistol and knife do - states 1500 and 1600, animations 7000/7001/7002/7010,
commands on kicks - with the same three-thrust-then-single-heavy shape. That is
the contract `bake_char.py` already had: it swaps the art for rig poses, scales
collision boxes with the figure and keeps the projectile art. It now carries a
small table instead of a hardcoded pair, `WEAPON_POSE`, so each fighter gets its
own pose for those two states.

## Replacing the art

For a partial or full repaint there is a drop-in path that needs no code
changes: put `art_src/chars/<id>/<group>_<number>.png` files next to the fighter
and rebuild. Each file replaces exactly that sprite slot, keeps the base
sprite's axis (so the pose lands where it should on screen), and is written as
true-colour PNG32 — no palette, no 32-colour limit. Slots you do not supply keep
the generated art, so a fighter can be repainted one animation at a time.

`python3 tools/build_chars.py --dump <id>` writes a template for every slot the
fighter references into `art_src/chars/<id>/templates/`: one transparent PNG at
the exact size the slot needs, a crosshair at the sprite axis, and a manifest
listing the size, axis and the actions that use it. For Jack that is 251 frames.
Templates stay in that subfolder and are ignored by the build.

Each fighter folder is a normal MUGEN/Ikemen character folder. To swap in real
art for one fighter and leave the rest alone:

1. Draw/replace `chars/<id>/<id>.sff` and `<id>.air` (keep the existing
   animation numbers so `chars/<id>/<id>.cns` keeps working).
2. Keep these animation numbers, which the shared CNS and command file use:

   | Action | Frames (group,index) | Purpose |
   |---|---|---|
   | 0 | 0,0 … | stance |
   | 20 | 20,x | walk |
   | 40 / 41 | 40,x / 41,x | jump up / jump forward |
   | 100–105 | 100,x | light attacks |
   | 200–205 | 200,x | heavy attacks |
   | 800–820 | 800,x | throw |
   | 9000,0 / 9000,1 | portraits | small / large select portraits |

3. Delete `chars/<id>/<id>.sff` only after regenerating, and do **not** re-run
   `tools/build_chars.py` for that fighter — it would overwrite the folder from
   the base character. Instead, remove the fighter from `ROSTER` in
   `tools/build_chars.py` once its art is hand-made, or keep a backup.

## HD stage pipeline (shipped)

The arenas are painted twice: `tools/build_stages.py` keeps the arcade version
(1000×240 art, `localcoord = 320, 240`) for the four film locations, and
`tools/stages_hd.py` paints the shipped one at arcade resolution ×4.5 (1920×1080).
Same layout, real pixels at 1080p. The Upside Down ships from the HD pass only — it has no
arcade-resolution counterpart.

| | arcade (`build_stages.py`) | HD (`stages_hd.py`) |
|---|---|---|
| localcoord | 320, 240 | **1920, 1080** |
| canvas | 1000 × 240 | **8192 × 1080** (two 4096-wide halves) |
| camera travel | ±260 | ±3136 |
| player bounds | ±405 | ±4028 |
| ground (`zoffset`) | 200 | 900 |
| screen at 4:3 | 320 × 240 units | 1440 × 1080 units |
| screen at 16:9 | ~427 × 240 units | **1920 × 1080 units** |

**Why `localcoord` height is 1080 and not 720.** Ikemen derives the vertical
framing from it. `src/camera.go` does:

```go
cutlow = (localcoord[1] - zoffset) - localcoord[1] * 0.05
```

With a 1080-row canvas, `zoffset = 900` and `localcoord[1] = 1080`, that resolves
to `126` — consistent, and the same relationship as the arcade stages
(`(240-200) - 12 = 28`). With `localcoord = 1920, 720` it resolves *negative*: the
floor sits past the bottom of the coordinate space and the backdrop is framed
wrong no matter how the art is drawn. Any future stage must keep
`localcoord[1] == canvas height`.

The 16:9 row is the useful one: the engine scales a stage by height, so a
16:9 window shows `1080 × 16/9 = 1920` units of width — exactly the localcoord
width, which is what makes 1080p a 1:1 pixel match. That is why the canvas is
8192 wide: the camera travels ±3136, half a screen adds 960, and each 4096-wide
half ends where the screen edge does.

Precedence, in `tools/build_all.py` order:

1. `build_stages.py` — arcade stages
2. `stages_hd.py` — overwrites the same four ids at 1920×1080, and paints
The Upside Down
3. `build_hd_stage.py` — overwrites any id that has `art_src/<id>/backdrop.png`

The HD painters use one `SCALE = 4.5` and read coordinates through `px(n)`, so
`px(150)` means "150 arcade pixels", which keeps the HD compositions honest
against the arcade ones. Post-processing is what stops the art reading as flat
vector shapes: `texture()` multiplies a soft noise so masonry has surface,
`bloom()` screens the brightest pixels back over the frame for lantern and neon
glow, `seam()` adds contact shading where walls meet the floor, then vignette and
grain.

## Stage art pipeline (arcade fallback)

`tools/build_stages.py` draws each stage with Pillow on a 1000×240 canvas. The
camera travels ±260 px and one screen is 320 px wide, so the canvas is the
camera's travel (520 px) plus 240 px of overpaint past each end — 1.5 screens of
margin per side. Ikemen normalises the visible width to one screen whatever the
window aspect (it scales stage art by `gameWidth / localcoord`), and these stages
also set `zoomout = 1`, but the extra paint means the art cannot run out if that
ever changes. Players are clamped to ±405 px via `leftbound`/`rightbound`, i.e.
15 px inside the *camera's* painted edge and matching `[Bound]
screenleft/screenright`, so a fighter can be pushed against the screen border but
can never walk off the art. Focal elements are centred on the canvas midpoint,
which is what the match-start camera shows; the rest is pan scenery.

The geometry lives in one place — the `SCROLL` constant at the top of the
script. Changing it re-derives the canvas width, every layer's `start =` offset,
`boundleft`/`boundright` and the player bounds, so widening the arena is a
one-line change.

Layers are written as SFF v2 PNG32 sprites:

* `0,0` — the backdrop, `delta = 1,1`
* `3,0` — a foreground rail/prop layer, `layerno = 1`
* `9000,1` — the 320×240 select-screen preview

Compositing gotcha worth remembering: `ImageChops.screen` ignores alpha. Every
layer is premultiplied by its own alpha before screening (`tools/art.py`,
`premultiplied()`), otherwise mask-built layers flood the whole frame with their
colour.

## Arcade ladder

`data/select.def` assigns `order=` to each fighter; `[Options]` maps ladder tiers
to counts (`arcade.maxmatches = 3,2,1,1`):

* order 1 — Gracie Law, Rain, Lightning
* order 2 — Wang Chi, Thunder
* order 3 — Egg Shen
* order 4 — Lo Pan (final)
* order 0 — Jack Burton (player-side, not drawn as a ladder opponent)

## Simulation gaps

The shared command set exists because all fighters share one animation set —
character-specific specials only make sense once art differs. Stats, throw
range, walk/jump scaling and health already differ, so the roster plays
differently even before the art is replaced.

## The puppet rig (`tools/char_rig.py`)

Drawing 250 hand-painted frames per fighter does not scale, and the roster's
current art is Kung Fu Man recoloured. The rig draws nothing: it poses art.

Each fighter is authored **once** as parts in `art_src/chars/<id>/parts/` —
torso, head, upper and lower arm, hand, thigh, shin, foot, prop — and every
animation frame is those parts rotated about their joints, at 3x the base
character's height (318px instead of 106px).

* Pivots sit on the joints. `rig.json` can override any pivot, the whole metric
  set, or apply a `scale` (draw at 2x and let the build downsample).
* Rotated parts leave a seam, so each limb also paints a socket disc sampled
  from its own average colour, which closes the joint.
* `POSES` holds stance, breath, walk, crouch, jump, all four strikes, the boot
  and low kick, guard, hit, victory and the gun/knife poses as joint angles, so
  a new frame is a few numbers rather than a drawing.
* `--template <id>` writes the part list and sizes, `--sheet <id>` renders real
  parts into a contact sheet, `--demo` renders the same sheet from flat stand-in
  parts to check the machinery alone.

The quality of a fighter is the quality of its parts; the rig only articulates
them. It is deliberately **not** in `build_all.py` — nothing in the game reads
it until a fighter has real part art, and the roster keeps shipping on the
existing sprites until then.
