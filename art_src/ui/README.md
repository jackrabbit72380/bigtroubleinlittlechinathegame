# UI art

Painted art that overrides a generated screen element. Nothing here is required:
if a file is missing, the build draws that element itself.

## Title logo

Drop the logo at either of these paths and the build packs it into the title
screen instead of painting one:

```
art_src/ui/title_logo.png        (preferred)
concept_art/ui/title_logo.png    (also picked up)
```

- **Any size.** The picture is fitted to the logo sprite (900x420) preserving
  aspect ratio, so a 1600x600 export lands with the same proportions.
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
either way - a plate only has to be one picture.

## Splash screen

The splash that plays before the title reads the same two folders:

```
art_src/ui/splash.png            (preferred)
concept_art/ui/splash.png        (also picked up)
```

- **1280x720.** The frame is full-screen and opaque. Other sizes are scaled to
  fill and centre-cropped, with a warning if the aspect is more than 6% off 16:9.
- **RGB or RGBA.** It sits on black, so a flat poster image works as well as a
  transparent PNG.
- **Full bleed.** Details at the frame edges may be cropped on other sizes.

What the build does with it:

- packs it into `data/ikemen1/system.sff` as sprite `220, 0` (a group the
  engine does not use), axis at the frame centre;
- rewrites `data/ikemen1/logo.def` as one scene: fade up from black, hold, fade
  out into the title. The timing lives in `tools/build_splash.py`
  (`SECONDS`, `FADE_IN`, `FADE_OUT`).

With no file present, the build paints a fallback card - the game's wordmark on
a starfield - so the splash always exists. The console says which it used:

```
using painted splash art_src/ui/splash.png
```

Both `logo.def` and `system.sff` come from the engine download and are restored
on every build, which is why the splash is generated rather than committed.
