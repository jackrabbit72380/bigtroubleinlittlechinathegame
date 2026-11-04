# Music

Menu music is read from `sound/` at the game root. `tools/build_music.py` writes
the paths into the `[Music]` block of `data/ikemen1/system.def` from the files it
finds there, so you drop a track in and the wiring is done for you.

| File | Screen |
|---|---|
| `sound/Title.ogg` | title screen |
| `sound/Select.ogg` | character select |
| `sound/Versus.ogg` | versus screen |
| `sound/Winner.ogg` | victory screen |
| `sound/Continue.ogg` | continue screen |
| `sound/Options.ogg`, `Replay.ogg`, `Results.ogg`, `Hiscore.ogg` | those screens |

Names are matched case-insensitively, but the file has to sit in `sound/` and use an
extension the engine can decode: **`.ogg` (Vorbis), `.mp3`, `.wav`, `.flac`, or
`.mid`/`.midi`** (MIDI needs a soundfont). The engine picks its decoder from the
extension, so `.opus`, `.m4a` and `.aac` files are ignored — renaming one to `.ogg`
will not help either. OGG is the best pick for menu loops: smallest and gapless, and
it wins when several encodings of the same track are present.

Each key keeps its `.volume`, `.loop`, `.loopstart` and `.loopend` siblings, which
the generator never touches; menus loop by default. Give several slots the same
filename if you want one track to run across them — the engine only restarts the
music when the filename changes.

## Stage music

Stage fight music is separate, per stage: the `[Music] bgmusic =` line of each
`stages/*.def`, filled from the `MUSIC` table in `tools/stages_hd.py` — for example
`bgmusic = sound/LoPansDemise.ogg` on Lo Pan's Throne and Lo Pan's Hallway. Lo Pan's
Ceremony is the one arena still blank there, so it falls back to whatever the menu
is playing; the training room is deliberately silent.

## Shipping

The tracks in `sound/` are part of this repository, and every release bundle copies
that folder along with the rest of the game, so a track you add there also ships in
the downloads. Only add music you have the right to distribute.
