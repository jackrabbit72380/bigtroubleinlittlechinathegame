# Jack Burton art brief

Jack is built from the shared Kung Fu Man base, so his sprites are Kung Fu Man's
body. Replacing them is the only way he can look like himself. This brief lists
every frame, in priority order.

## How to deliver

Preferred: frame PNGs named `<group>_<number>.png`, one per row below.
Transparent background, **exactly** the listed pixel size, feet on the sprite
axis given, figure facing right. Drop them in `art_src/chars/jackburton/` and run
`python3 tools/build_chars.py`. Anything not supplied keeps the current art, so
this can land in stages.

Best result: a 3D model of Jack (`glb`/`fbx`/`blend`) plus a turnaround. Every
frame below can then be rendered from it at the listed sizes, in one consistent
light, with no hand painting.

## The character

From the concept art: white ribbed tank top with the pink-sun / green demon
graphic, mid-blue denim jeans, knee-high dark brown boots with buckles, brown
shoulder-length mullet, blue eyes, stubble, an easy smirk. Pistol in his right
hand, large knife in his left, held low and relaxed. Reference build is heavy:
wide shoulders, thick forearms. He stands 106px tall in game at the base
character's scale, so silhouette, the white top, the jeans and the boots do the
reading, not the face.

## Tier 1 - visible in every match (162 frames)

| action | name | frames | sprites: name (size @ axis) |
|---|---|---|---|
| 0 | Standing Animation | 6 | 0_0 (47x106 @ 18,105), 0_1 (48x105 @ 18,104), 0_2 (49x105 @ 18,104), 0_3 (50x105 @ 18,104), 0_4 (51x105 @ 18,104), 0_5 (51x105 @ 18,104) |
| 20 | Walking Forward | 16 | 20_0 (49x109 @ 22,108), 20_1 (43x110 @ 16,109), 20_2 (38x110 @ 11,109), 20_3 (39x109 @ 12,108), 20_4 (44x108 @ 17,107), 20_5 (47x106 @ 20,105), 20_6 (51x105 @ 22,104), 20_7 (49x107 @ 22,106), 20_8 (49x109 @ 22,108), 20_9 (43x110 @ 16,109), 20_10 (38x110 @ 11,109), 20_11 (39x109 @ 12,108), 20_12 (44x108 @ 17,107), 20_13 (47x106 @ 20,105), 20_14 (51x105 @ 22,104), 20_15 (49x107 @ 22,106) |
| 21 | Walking Back | 16 | 21_11 (51x111 @ 17,110), 21_10 (51x112 @ 17,111), 21_9 (51x112 @ 17,111), 21_8 (56x111 @ 22,110), 21_7 (56x109 @ 22,108), 21_6 (56x107 @ 22,106), 21_5 (54x108 @ 20,107), 21_4 (51x110 @ 17,109), 21_3 (51x111 @ 17,110), 21_2 (51x112 @ 17,111), 21_1 (51x112 @ 17,111), 21_0 (56x111 @ 22,110), 21_15 (56x109 @ 22,108), 21_14 (56x107 @ 22,106), 21_13 (54x108 @ 20,107), 21_12 (51x110 @ 17,109) |
| 10 | Stand to crouch | 2 | 11_0 (49x92 @ 17,91), 11_1 (49x80 @ 17,79) |
| 11 | Crouching animation | 1 | 11_2 (50x75 @ 18,73) |
| 41 | Starting Jumping up | 9 | 41_0 (48x118 @ 18,117), 41_1 (44x107 @ 17,110), 41_2 (39x94 @ 17,102), 41_3 (39x81 @ 17,95), 41_4 (39x76 @ 16,93), 41_5 (44x94 @ 17,102), 41_6 (51x107 @ 17,110), 41_7 (51x117 @ 17,116), 41_8 (51x117 @ 17,116) |
| 42 | Starting Jumping forwards | 5 | 42_0 (54x116 @ 21,116), 42_1 (53x104 @ 20,109), 42_3 (58x37 @ 27,77), 42_4 (37x58 @ 19,85), 42_5 (58x37 @ 31,79) |
| 43 | Starting Jumping backwards | 2 | 43_0 (48x115 @ 18,116), 43_1 (46x107 @ 17,110) |
| 100 | Run forwards | 6 | 100_0 (72x100 @ 38,99), 100_1 (90x102 @ 55,101), 100_2 (73x107 @ 36,106), 100_3 (71x100 @ 37,99), 100_4 (91x100 @ 55,101), 100_5 (69x107 @ 33,106) |
| 120 | GUARDSTART (stand) | 1 | 120_0 (45x105 @ 22,104) |
| 121 | GUARDSTART (crouch) | 1 | 121_0 (48x74 @ 19,72) |
| 122 | GUARDSTART (air) | 1 | 122_0 (37x74 @ 16,100) |
| 200 | Stand Light Punch | 3 | 200_0 (46x106 @ 16,105), 200_1 (61x106 @ 14,105), 200_2 (76x106 @ 14,105) |
| 210 | Stand Strong Punch | 6 | 210_0 (65x101 @ 11,100), 210_1 (70x98 @ 7,97), 210_2 (64x102 @ 6,101), 210_3 (95x104 @ 13,103), 210_4 (60x104 @ 13,103), 210_5 (52x105 @ 14,104) |
| 230 | Standing Light Kick | 3 | 230_0 (53x109 @ 18,108), 230_1 (83x107 @ 11,106), 230_2 (78x108 @ 11,107) |
| 240 | Standing Strong Kick | 6 | 240_0 (48x107 @ 21,106), 240_1 (51x107 @ 19,106), 240_2 (94x105 @ 26,104), 240_3 (93x105 @ 22,104), 240_4 (81x105 @ 14,104), 240_5 (56x105 @ 6,104) |
| 400 | Crouching light punch | 2 | 400_0 (59x75 @ 19,73), 400_1 (73x75 @ 18,73) |
| 410 | Crouching strong punch | 5 | 410_0 (51x84 @ 12,83), 410_1 (52x84 @ 12,83), 410_2 (61x85 @ 12,84), 410_3 (69x95 @ 11,94), 410_4 (62x89 @ 12,88) |
| 430 | Crouching Light Kick | 4 | 430_0 (49x74 @ 20,72), 430_1 (63x66 @ 28,64), 430_2 (103x62 @ 32,60), 430_3 (98x62 @ 31,60) |
| 440 | Crouching Strong Kick | 7 | 440_0 (51x73 @ 14,71), 440_1 (64x68 @ 19,62), 440_2 (52x73 @ 11,62), 440_3 (104x67 @ 22,65), 440_4 (96x69 @ 18,65), 440_5 (83x73 @ 14,64), 440_6 (53x69 @ 19,63) |
| 600 | Jump light punch | 2 | 600_0 (61x87 @ 19,97), 600_1 (68x87 @ 17,97) |
| 610 | Jump strong punch | 4 | 610_0 (76x96 @ 30,102), 610_1 (51x87 @ 12,98), 610_2 (75x81 @ 17,94), 610_3 (63x86 @ 13,97) |
| 630 | Jump light kick | 3 | 640_0 (60x90 @ 19,99), 630_1 (71x71 @ 27,97), 630_2 (67x68 @ 25,97) |
| 640 | Jump strong kick | 2 | 640_1 (102x73 @ 30,97), 640_2 (97x73 @ 28,97) |
| 1200 | Light Kung Fu Blow | 7 | 1210_0 (42x107 @ 20,106), 1210_1 (41x108 @ 21,107), 1210_2 (48x106 @ 18,105), 1210_3 (69x105 @ 15,104), 1210_4 (105x94 @ 13,93), 1210_5 (103x94 @ 15,93), 1210_6 (94x97 @ 18,95) |
| 1300 | Kung Fu Blocking High (attempt) | 3 | 1300_0 (67x107 @ 17,105), 1300_1 (63x107 @ 17,105), 1300_2 (55x107 @ 17,105) |
| 1320 | Kung Fu Blocking Low (attempt) | 3 | 1320_0 (55x73 @ 16,71), 1320_1 (52x73 @ 16,71), 1320_2 (51x73 @ 19,71) |
| 1400 | Light Kung Fu Zankou | 8 | 1400_0 (48x79 @ 16,78), 1400_1 (57x79 @ 15,78), 1400_2 (82x78 @ 35,76), 1400_3 (64x108 @ 26,106), 1400_4 (63x108 @ 26,106), 1400_5 (64x108 @ 26,106), 1400_6 (59x106 @ 23,104), 1400_7 (56x103 @ 29,101) |
| 1100 | Light Kung Fu Upper | 10 | 1100_0 (37x104 @ 14,103), 1100_1 (38x104 @ 14,103), 1100_2 (54x104 @ 12,102), 1100_3 (55x104 @ 11,102), 1100_4 (56x106 @ 10,104), 1100_5 (56x141 @ 7,139), 1100_6 (54x134 @ 7,132), 1100_7 (54x134 @ 7,132), 1100_8 (54x130 @ 7,128), 1100_9 (57x115 @ 8,113) |
| 1000 | Light Kung Fu Palm | 7 | 1000_0 (74x95 @ 39,94), 1000_1 (85x90 @ 49,89), 1000_2 (85x90 @ 49,89), 1000_3 (117x84 @ 54,83), 1000_4 (123x84 @ 54,83), 1000_5 (121x84 @ 54,83), 1000_7 (110x87 @ 53,86) |
| 5000 | Stand/Air Hit high (light) | 2 | 5000_0 (53x106 @ 23,105), 5000_10 (63x105 @ 31,104) |
| 5010 | Stand/Air Hit low (light) | 2 | 5010_0 (58x97 @ 31,96), 5010_10 (58x88 @ 34,87) |
| 5020 | Crouch Hit (light) | 2 | 5020_0 (52x76 @ 20,74), 5020_10 (60x74 @ 28,72) |
| 5030 | Stand/Air Hit back | 1 | 5030_0 (75x100 @ 38,107) |
| 170 | Lose | 4 | 5000_11 (70x95 @ 38,94), 5300_3 (71x80 @ 31,78), 5300_2 (70x81 @ 31,79), 5300_1 (69x83 @ 31,81) |

## Tier 2 - situations and supers (77 frames)

| action | name | frames | sprites: name (size @ axis) |
|---|---|---|---|
| 5 | Turning | 1 | 5_0 (42x106 @ 16,105) |
| 6 | Crouch Turning | 1 | 6_0 (44x74 @ 19,73) |
| 150 | Hit back while guarding (stand) | 2 | 120_1 (49x105 @ 26,104), 120_2 (53x105 @ 30,104) |
| 800 | Kung Fu Throw Attempt | 4 | 800_0 (47x104 @ 14,103), 800_1 (82x98 @ 14,97), 800_2 (87x93 @ 13,92), 800_4 (75x91 @ 15,90) |
| 810 | Kung Fu Throw | 9 | 800_3 (88x89 @ 13,88), 800_5 (67x105 @ 12,104), 800_6 (68x101 @ 12,100), 800_7 (72x101 @ 15,100), 800_8 (81x96 @ 24,95), 800_9 (86x112 @ 29,111), 800_10 (106x89 @ 49,88), 800_11 (96x87 @ 39,86), 800_12 (94x87 @ 37,86) |
| 820 | throw animation (action 810). | 8 | 5061_0 (55x107 @ 25,40), 5071_0 (73x108 @ 42,47), 5071_10 (97x81 @ 56,39), 5071_20 (111x45 @ 60,18), 5031_0 (75x100 @ 38,44), 5011_0 (58x97 @ 15,43), 5030_40 (97x81 @ 47,103), 5030_30 (111x53 @ 58,90) |
| 191 | INTRO -- WOOD (projectile) | 4 | 191_3 (15x35 @ 8,18), 191_2 (27x26 @ 14,12), 191_1 (35x17 @ 18,8), 191_0 (30x28 @ 14,13) |
| 192 | Note: Putting -1,0 for the sprite  | 2 | 192_0 (32x30 @ 17,14), 192_1 (35x31 @ 15,16) |
| 195 | Taunt | 6 | 181_0 (35x110 @ 16,108), 181_2 (25x115 @ 13,113), 181_3 (38x114 @ 12,112), 181_4 (51x106 @ 13,104), 181_5 (63x91 @ 13,89), 181_6 (64x87 @ 13,85) |
| 1010 | Strong Kung Fu Palm | 1 | 1000_6 (121x84 @ 54,83) |
| 1025 | Hit by Fast Kung Fu Palm | 2 | 5010_20 (53x81 @ 35,80), 5030_10 (99x86 @ 49,98) |
| 1050 | Light Kung Fu Knee - move forwards | 3 | 1050_0 (48x100 @ 19,99), 1050_1 (43x103 @ 18,102), 1050_2 (53x115 @ 24,114) |
| 1051 | Light Kung Fu Knee - jump | 5 | 1050_3 (60x114 @ 27,115), 1050_4 (60x114 @ 27,115), 1050_5 (59x113 @ 23,113), 1050_6 (52x113 @ 18,113), 1050_7 (49x114 @ 16,115) |
| 1052 | Light Kung Fu Knee - land | 4 | 1052_0 (53x100 @ 19,99), 1052_1 (48x86 @ 15,85), 1052_2 (39x92 @ 15,91), 1052_3 (36x107 @ 18,106) |
| 1055 | Light Kung Fu Knee - kick | 8 | 1055_0 (79x87 @ 36,107), 1055_1 (69x94 @ 29,108), 1055_2 (56x110 @ 26,109), 1055_3 (69x124 @ 20,118), 1055_4 (60x116 @ 18,110), 1055_5 (64x118 @ 18,113), 1055_6 (77x115 @ 19,113), 1055_7 (64x109 @ 19,112) |
| 1340 | Kung Fu Blocking Air (attempt) | 2 | 1340_0 (45x84 @ 16,101), 1340_1 (42x84 @ 16,101) |
| 5002 | Stand/Air Hit high (hard) | 1 | 5000_20 (83x89 @ 53,88) |
| 5007 | Stand Recover high (hard) | 1 | 5000_21 (83x90 @ 53,89) |
| 5011 | Stand/Air Hit low (medium) | 1 | 5010_21 (53x82 @ 35,81) |
| 5021 | Crouch Hit (medium) | 1 | 5020_20 (72x62 @ 39,60) |
| 5050 | Air Fall (going up) | 1 | 5030_31 (111x53 @ 58,90) |
| 5051 | Air Fall (up-type, going up) | 2 | 5060_0 (55x107 @ 23,107), 5060_1 (55x107 @ 23,107) |
| 5061 | Air Fall (up-type, coming down) | 2 | 5030_50 (73x108 @ 35,120), 5060_10 (34x115 @ 19,113) |
| 5080 | LieDown Hit (stay down) | 3 | 5040_20 (104x62 @ 49,55), 5040_0 (99x52 @ 49,45), 5040_10 (108x42 @ 50,33) |
| 5101 | Hit ground from fall (up-type) | 1 | 5040_1 (83x69 @ 49,63) |
| 5120 | Get up from LieDown | 1 | 5040_11 (74x74 @ 18,67) |
| 5300 | Dizzy | 1 | 5300_0 (68x84 @ 31,82) |

## Tier 3 - hit reactions and knockdowns (12 frames)

| action | name | frames | sprites: name (size @ axis) |
|---|---|---|---|
| 181 | Win | 1 | 181_1 (27x115 @ 12,113) |
| 7000 | Pistol round (projectile) | 1 | 7000_0 (26x8 @ 4,4) |
| 7001 | Muzzle flash | 3 | 7001_0 (38x26 @ 8,13), 7001_1 (38x26 @ 8,13), 7001_2 (38x26 @ 8,13) |
| 7002 | Impact spark | 3 | 7002_0 (30x30 @ 15,15), 7002_1 (30x30 @ 15,15), 7002_2 (30x30 @ 15,15) |
| 7010 | Thrown knife, spinning | 4 | 7010_0 (46x46 @ 23,23), 7010_1 (46x46 @ 23,23), 7010_2 (46x46 @ 23,23), 7010_3 (46x46 @ 23,23) |

## Notes

* Frames are shared: many actions reuse the same sprite, so each frame is
  counted once. Painting `200_0` (stance) covers a large share of everything.
* The listed axis is the foot contact point. Keep it; the engine aligns every
  pose on it.
* `art_src/chars/jackburton/templates/` already holds an empty canvas for each
  frame, correctly sized and marked.
* One consistent 3/4 front view. Do not flip frames for the other direction:
  the engine mirrors the whole set.
