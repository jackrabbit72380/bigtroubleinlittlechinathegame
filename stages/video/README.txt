fog.webm is the fog that plays inside the skull's mouth on Lo Pan's Throne.
It is a real clip, drawn by a video background layer - not baked frames.

    [BG fog]
    type = video
    path = video/fog.webm
    loop = 1
    layerno = 0
    start = -1920,0
    delta = 0,0

Two details from Ikemen GO's src/stage.go decide how it has to be written:

1. A stage video is drawn with a render origin of gameWidth/2 to the RIGHT of
   start ("Choose render origin: top-left for motif/storyboard videos, center
   for everything else"). So at start = 0,0 the clip's left edge lands on the
   middle of the screen and only the right half of the view has any fog in it -
   which is exactly the "fog in half of the mouth" bug. The clip is 3840x2160
   for a 1920x1080 stage, so start = -1920,0 centres it on the view and covers
   the screen twice over.

2. Video plays ONCE unless loop = 1 is set (`is.ReadBool("loop", &loop)` in the
   video branch of BG parsing). Without it the clip runs for 15 seconds and the
   mouth goes dark permanently - "the fog just stops".

delta = 0,0 keeps the layer screen-pinned: the plate covers the whole view, and
the wall is opaque except for the mouth aperture, so the fog is only ever seen
in the mouth. The aperture itself is punched in tools/stage_throne.py.
