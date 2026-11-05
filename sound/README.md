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

# Track lists

If an album folder contains a `.metadata.pegasus.txt` file (the list most album
packs ship for the Pegasus frontend, with one `game:` line per track and a `file:`
line under it), the build reads it instead of guessing:

- the album keeps the metadata's order, so track 10 stays after track 2;
- the song's `game:` line is what the browser prints, so numbers and punctuation
  come out exactly as the pack wrote them;
- `assets.boxFront:` is used for the cover when that file exists, otherwise the
  `boxFront.png` sitting in the album folder is used;
- `file:` paths may be written as `sound/<name>.ogg` or just `<name>.ogg`; the
  build finds the file in the album folder, in `sound/` itself, or one folder
  down, and says so if it truly is not there. A name that matches except for
  spacing or punctuation ("12- Lopan's" for "12 - Lopan's") still finds its file
  and is reported, rather than being treated as a missing track.

Audio in the folder that the metadata does not mention is added at the end of the
album rather than dropped, so a pack with a bonus track and an out-of-date list
still plays everything. The metadata is optional: without it the album lists its
audio files by name.
