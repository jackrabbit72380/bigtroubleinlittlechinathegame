# art_src/ — high-resolution stage art

Anything you put here replaces the arcade-resolution procedural backdrop for that
stage. `tools/build_hd_stage.py` turns it into a stage authored at **1280×720**,
so a 1080p window shows real pixels instead of a stretched 240-line image.

```
art_src/
  lopans_throne/          <- folder name must match the stage id in stages/
    backdrop.png          required, 1280×720 or larger (2560×1440 is ideal)
    foreground.png        optional, same size, drawn in front of the fighters
    stage.txt             optional, one line: name = Lo Pan's Throne
```

The five stage ids are `lopans_throne`, `wingkong_exchange`, `chinatown_alley`,
`porkchop_express` and `stage0` (the training room).

## How the art is placed

The picture is **cover-fitted**: scaled to fill the 4000×960 stage canvas without
distorting, then centre-cropped. Because the canvas is wider than 16:9, a
2560×1440 (16:9) picture is scaled by height and the sides are cropped — keep the
important elements in the middle 55% of the frame and they always survive the pan.

Where the floor line goes matters for the fighters' feet: the art's row 800 of
960 is treated as the ground, so put the ground plane at 83% of the image height
and the fighters will stand on it. If a backdrop has its ground higher or lower,
paint it to match rather than moving the stage numbers.

## What this does not do

It does not make the fighters HD. Character sprites are still Kung Fu Man's
320×240 art, recoloured. Native HD fighters need redrawn sprite sets (or sets
rendered from 3D), one folder per fighter, with the animation numbers listed in
`docs/DESIGN.md`.
