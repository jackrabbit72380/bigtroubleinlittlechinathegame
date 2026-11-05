# sound/ — menu music

Drop tracks here and `tools/build_music.py` points the screenpack at them
automatically; the `Build game assets` workflow runs it on every push, so you do
not edit `data/ikemen1/system.def` by hand (the engine data is re-copied on each
build and would overwrite it).

| Filename | Screen |
|---|---|
| `Title.ogg` | title screen |
| `Select.ogg` | character select |
| `Versus.ogg` | versus screen |
| `Winner.ogg` | victory screen |
| `Continue.ogg` | continue screen |
| `Options.ogg`, `Replay.ogg`, `Results.ogg`, `Hiscore.ogg` | those screens |

Names are matched case-insensitively. Only extensions the engine can decode work:
`.ogg` (Vorbis), `.mp3`, `.wav`, `.flac`, `.mid`/`.midi`. Anything else (`.opus`,
`.m4a`, `.aac`) is ignored — the decoder is chosen from the extension, so renaming
does not help. Prefer `.ogg` for loops.

A slot with no matching file is left blank, which the engine treats as silence.
Give several slots the same filename if you want one track to run across screens.

Release bundles copy this folder, so whatever is here also ships in the
downloadable builds. Only add audio you have the right to redistribute; nothing
is bundled in the repository by default.

## Music select albums

Each directory in this folder is an album, and the title menu's **MUSIC** screen
lists them with the album's `boxFront.png` beside its track list:

```
sound/Big Trouble in Little China OST Movie Version/
    01 - Pork Chop Express.ogg
    boxFront.png
sound/Big Trouble in Little China OST Game Version/
    ...
    boxFront.png
```

`tools/build_music.py` scans the folders on every build and writes
`data/music.json` and `data/albums.sff` from what it finds, so adding a track or
replacing a cover only means dropping the file in and rebuilding. Albums sort
alphabetically and tracks sort by title; the `boxFront.png` is resized to at most
640px on its long edge. Picking a track sets `bgmusic` for the next match only —
"Default (stage music)" in the browser hands the match back to whatever music the
mode or stage asked for.
