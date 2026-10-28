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
   | 40 / 41 | 40,x / 41,x | jump up / forward |
   | 100–105 | 100,x | light attacks |
   | 200–205 | 200,x | heavy attacks |
   | 800–820 | 800,x | throw |
   | 9000,0 / 9000,1 | portraits | small / large select portraits |

3. Delete `chars/<id>/<id>.sff` only after regenerating, and do **not** re-run
   `tools/build_chars.py` for that fighter — it would overwrite the folder from
   the base character. Instead, remove the fighter from `ROSTER` in
   `tools/build_chars.py` once its art is hand-made, or keep a backup.

## Stage art pipeline

`tools/build_stages.py` draws each stage with Pillow on a 620×240 canvas. The
camera can travel ±150 px, and only the central 320×240 window is guaranteed to
be on screen at match start, so every focal element is placed inside that
window; the outer 150 px on each side is scenery that only appears when the
camera pans.

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
