fog.webm lives in this folder.

Lo Pan's throne draws its fog with:

    [BG fog]
    type = video
    path = video/fog.webm

Background paths in a stage def resolve from the stage file's own folder, so
`video/fog.webm` means stages/video/fog.webm.

The clip is 15 seconds of VP9 at 3840x2160, 25 fps. The stage's coordinate space
is 1920x1080 and the layer sits at start = 0,0 with delta = 0,0, so it is pinned
to the screen and covers it about twice over - the mouth sees the middle of the
plate rather than its top-left corner. Fog does not need to be 1:1, so it reads
as intended; re-time or rescale the plate if you ever swap it for another clip.

The video is the last background in the stack, so it sits behind every painted
layer of the hall. The only opening in the backdrop is the skull's mouth, which
tools/stage_throne.py punches out of the artwork, so that is the one place the
fog can be seen. Without the file the mouth reads as a dark aperture instead of
a lit one.
