# UI art

Painted art that overrides a generated screen element. Nothing here is required:
if a file is missing, `tools/build_title.py` draws that element itself.

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
