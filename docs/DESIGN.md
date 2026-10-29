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

## Replacing the art

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

The four arenas are painted twice: `tools/build_stages.py` keeps the arcade
version (1000×240 art, `localcoord = 320, 240`), and `tools/stages_hd.py` paints
the shipped one at arcade resolution ×4. Same layout, real pixels at 1080p.

| | arcade (`build_stages.py`) | HD (`stages_hd.py`) |
|---|---|---|
| localcoord | 320, 240 | **1280, 960** |
| canvas | 1000 × 240 | **4000 × 960** |
| camera travel | ±260 | ±1040 |
| player bounds | ±405 | ±1620 |
| ground (`zoffset`) | 200 | 800 |
| screen at 4:3 | 320 × 240 units | 1280 × 960 units |
| screen at 16:9 | ~427 × 240 units | **1707 × 960 units** |

**Why `localcoord` height is 960 and not 720.** Ikemen derives the vertical
framing from it. `src/camera.go` does:

```go
cutlow = (localcoord[1] - zoffset) - localcoord[1] * 0.05
```

With a 960-row canvas, `zoffset = 800` and `localcoord[1] = 960`, that resolves to
`100` — consistent, and the same relationship as the arcade stages
(`(240-200) - 12 = 28`). With `localcoord = 1280, 720` it resolves *negative*: the
floor sits past the bottom of the coordinate space and the backdrop is framed
wrong no matter how the art is drawn. Any future stage must keep
`localcoord[1] == canvas height`.

The 16:9 row is the useful one: the engine scales a stage by height, so a
16:9 window shows `960 × 16/9 ≈ 1707` units of width. That is why the canvas is
4000 wide — it covers the full camera travel and both ends of a wide window.

Precedence, in `tools/build_all.py` order:

1. `build_stages.py` — arcade stages
2. `stages_hd.py` — overwrites the same four ids at 1280×960
3. `stage_throne.py` — repaints Lo Pan's Throne from the concept art
4. `build_hd_stage.py` — overwrites any id that has `art_src/<id>/backdrop.png`

The HD painters use one `SCALE = 4` and read coordinates through `px(n)`, so
`px(150)` means "150 arcade pixels", which keeps the HD compositions honest
against the arcade ones. Post-processing is what stops the art reading as flat
vector shapes: `texture()` multiplies a soft noise so masonry has surface,
`bloom()` screens the brightest pixels back over the frame for lantern and neon
glow, `seam()` adds contact shading where walls meet the floor, then vignette and
grain.

### Lo Pan's Throne: the arena from the concept art

`tools/stage_throne.py` paints the arena to follow the throne-room art rather
than a generic hall: a ring-shaped mezzanine whose arched niches each hold a red
neon ideogram, with `ring_y()` giving the balcony its outward dip and
`ring_line()` tracing a cyan and red neon strip along that curve; a colossal
skull over the gate; a stone staircase in perspective with guardian lions and
fire bowls at its foot; and a plaza laid out in one-point perspective with an
engraved inlay ring.

The props are painted as a colour layer plus a height map, then shaded by
`hillshade()`, so sockets, nasal cavity, fangs and mane read as carved rather
than drawn. Two details in that pipeline are easy to get wrong:

* `ImageChops.subtract` clamps at zero, so each axis needs both a "falling
  towards the light" and a "falling away" term to keep the gradient signed. The
  multiplier itself has to sit near white (208) because it scales the albedo —
  a mid-grey bias turns every sculpted prop into a silhouette.
* `art.vignette()` must scale PIL's radial gradient directly. It used to invert
  the mask, which darkened the *centre* of every stage and left the corners
  clear; that is why all four arenas read flat and grey.

The skull is composited after `finish()`. It is lit by its own neon, and the
frame's edge darkening turned it into a glass outline when it went through the
same pass as the wall behind it.

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
