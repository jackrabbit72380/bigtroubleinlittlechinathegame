fog.webm belongs in this folder.

Lo Pan's throne draws its fog with:

    [BG fog]
    type = video
    path = video/fog.webm

Background paths in a stage def resolve from the stage file's own folder, so
`video/fog.webm` means stages/video/fog.webm. Drop the clip here under exactly
that name and the mouth of the skull gate starts breathing fog.

The video is the last background in the stack, so it sits behind every painted
layer of the hall. The only opening in the backdrop is the skull's mouth, which
tools/stage_throne.py punches out of the artwork, so that is the one place the
fog can be seen. If the file is missing the mouth simply reads as a dark
aperture instead of a lit one.
