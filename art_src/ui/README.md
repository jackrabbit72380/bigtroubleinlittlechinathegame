# UI art

Painted art that overrides a generated screen element. Nothing here is required:
if a file is missing, the build draws that element itself.

## Title logo

Drop the logo at either of these paths and the build packs it into the title
screen instead of painting one:

```
art_src/ui/title_logo.png        (preferred)
art_src/ui/title_logo_logo.png   (same thing, art-pack file name)
concept_art/ui/title_logo.png    (also picked up)
```

- **Any size.** The picture is fitted to the logo sprite (900×420) preserving
  aspect ratio, so a 1600×600 export lands with the same proportions.
- **Transparent background.** PNG with alpha. The sprite is composited over the
  title screen's sky, so an opaque background would cover the clouds.
- **Cropped tight.** The art is centred on its own ink, so surrounding empty
  space just shrinks the logo. Crop to the logo itself.

Then rebuild:

```
python3 tools/build_title.py
```

or let `python3 tools/build_all.py` (and CI) do it. The build prints which path
it used, so you can tell a plate from the procedural rendition:

```
using painted title plate art_src/ui/title_logo.png
```

Delete the file and the project's own rendition comes back. The layer wiring,
the additive glow behind the logo and the on-screen placement are generated
either way — a plate only has to be one picture.

## Title backdrop overlay

The same `splash.png` also becomes a full-screen layer *on the title screen*,
drawn over the animated clouds and under the wordmark and the menu:

- **1920x1080, cover-cropped.** It fills the title frame, so a wider or taller
  export loses its edges rather than being squashed. Transparency is kept, so a
  cut-out lets the clouds show through behind it.
- It is packed as sprite `205, 0` and added to `[TitleBGdef]` as
  `[TitleBG Title Overlay]`, between the cloud layers and the logo layers —
  that definition order is what puts it above the sky and below the logo
  (`layerno = 1`) and the menu text (`layerno = 2`).
- Delete the file and the layer plus its sprite are removed again on the next
  build, leaving the plain clouds.

The wordmark can be flattened onto a solid background: a flat plate colour found
in all four corners is keyed out automatically and the art is cropped to its own
ink, so an exported logo with a white or grey box does not paint a rectangle over
the backdrop.

## Splash screen

The splash that plays before the title reads the same two folders:

```
art_src/ui/splash.png            (preferred)
concept_art/ui/splash.png        (also picked up)
```

- **1920×1080 is the frame, and 16:9 art is never cropped.** The title layer
  covers a 1920×1080 box, and an image already that shape is only ever resized,
  so an 8192×4608 export arrives whole. The card that plays before the title is
  1280×720.
- **Big art keeps its detail.** A source with the pixels for 3840×2160 is packed
  at twice the frame and drawn back down with `scalestart = 0.5`, so a 4K render
  sampling the title screen uses the art's own pixels instead of an upscale.
  Anything smaller is packed at 1× and simply downsampled.
- **RGB or RGBA.** The card is drawn over the night sky, so a cut-out with
  transparency blends into it and an opaque poster covers it completely.
- **Full bleed.** Details at the frame edges may be cropped on other sizes.

What the build does with it:

- packs it into `data/ikemen1/system.sff` as sprite `205, 0` and places it in
  `system.def` as `[TitleBG Title Overlay]`, drawn over
  `[TitleBG Background Sky]`: the art keeps every pixel of its transparency and
  the night sky shows through it;
- packs the title lettering into the slots at `0,0`-`0,3` and draws it with the
  backdrop's own `start` and `scalestart`, so the engine's logo lands where the
  art puts it on the backdrop's grid instead of being centred on its own. Art on
  the same canvas as the backdrop is packed as-is: nothing is cropped or
  re-fitted.

A master larger than the frame is packed at its own resolution and drawn back
down with `scalestart`, so an 8K painting keeps its detail on a 4K render.

There is no separate splash screen any more. The title stack draws the painting,
and the title fades up from black over the first second, which is why the art
lives in `tools/build_title.py` rather than in a splash storyboard.

Without the file the title keeps its painted clouds, and the console says which
plate it used.

`system.sff` and `system.def` come from the engine download and are restored on
every build, which is why the art is generated rather than committed.
