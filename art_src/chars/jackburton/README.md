# jackburton - part art for the puppet rig

Drop these PNGs in `art_src/chars/jackburton/parts/`, then run
`python3 tools/char_rig.py --sheet jackburton`. Each part is drawn ONCE, at rest,
and the rig rotates it about its pivot for every animation frame.

Draw at 2x the sizes below and add `{"scale": 0.5}` to `rig.json`; the rig
downsamples with LANCZOS.

| file | size (px) | drawn as | pivot |
|---|---|---|---|
| torso.png | 104 x 110 | upright, head end at the top | bottom centre (the hip) |
| pelvis.png | 62 x 38 | upright | 25% down, centre |
| head.png | 62 x 48 | upright, crown at the top | bottom centre (the neck) |
| uarm_n.png / uarm_f.png | 34 x 62 | hanging straight DOWN | top centre (the shoulder) |
| farm_n.png / farm_f.png | 28 x 52 | hanging straight DOWN | top centre (the elbow) |
| hand_n.png / hand_f.png | 30 x 30 | fingers down | top centre (the wrist) |
| thigh_n.png / thigh_f.png | 42 x 74 | hanging straight DOWN | top centre (the hip) |
| shin_n.png / shin_f.png | 34 x 77 | hanging straight DOWN | top centre (the knee) |
| foot_n.png / foot_f.png | 44 x 36 | TOE POINTING RIGHT, sole flat | 34% across, 62% down (the heel) |
| prop.png | 52 x 30 | pointing +x | the grip |

`_n` is the near (screen-left of the enemy) limb, `_f` the far one.

Pivots can be overridden in `rig.json`:

```json
{
  "scale": 1.0,
  "pivots": {"foot_n": [10, 20], "head": [33, 60]},
  "metrics": {"hip_y": -165},
  "angles": {"uarm_n": 45, "uarm_f": 45, "farm_n": 20, "farm_f": 20}
}
```

`angles` says how far each part is rotated in the source art, so an A-pose
figure (arms out at 45 deg) still bends correctly: cut the arm as drawn and
declare the angle it sits at instead of redrawing it straight down.

Keep the joint ends of each part full-bleed to the edge of its canvas - the rig
overlaps them at the joint, so a soft or empty edge shows as a gap when a limb
bends hard.

Animation frames the rig drives (poses in `POSES`, `tools/char_rig.py`):
stance, breath, walk_a, walk_b, crouch, jump, jab, cross, upper, boot, low_kick, block, gun_aim, gun_fire, knife, hit, win
