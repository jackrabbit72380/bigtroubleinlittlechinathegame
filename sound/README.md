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
