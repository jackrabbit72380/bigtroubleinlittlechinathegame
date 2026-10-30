# UI concept art

Reference art for the game's screens - title, splash, select and VS screens.
Put images here as PNG or JPG. Nothing in this folder is read by the build
except the two filenames below; everything else is reference material for
whoever is painting the screen.

## Files the build picks up

| File | Used for | Notes |
| --- | --- | --- |
| `title_logo.png` | title screen wordmark | transparent PNG, any size, cropped to the logo |
| `splash.png` | splash before the title | 1280x720, opaque, full bleed |

These are a fallback for `art_src/ui/`, which is checked first. If both exist,
`art_src/ui/` wins. Drop a file here and run:

```
python3 tools/build_title.py     # title_logo.png
python3 tools/build_splash.py    # splash.png
```

or `python3 tools/build_all.py` to rebuild everything. The console prints which
path it used, e.g. `using painted splash concept_art/ui/splash.png`.

Without these files the build paints its own title wordmark and splash card, so
nothing breaks if the folder is empty.

## Not read by the build

Screenshots, mockups and reference stills are welcome here - the select screen
layout, the VS screen, the front-end menu art - but they are documentation only.
See `art_src/ui/README.md` for the exact specs the build expects.
