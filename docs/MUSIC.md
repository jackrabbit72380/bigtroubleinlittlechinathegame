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
`bgmusic = sound/LoPansDemise.ogg` on Lo Pan's Throne and Lo Pan's Hallway, and
`12 - Lopan's Wedding Arrival` from the game-version OST on Lo Pan's Ceremony, which
is the one ceremony cue in the score. Every arena has a track of its own there now;
the training room is deliberately silent, and Lo Pan's Office keeps `1 - Prologue`
for the quiet before the fight.

## Music select

The Music screen — reached from the title menu's options and from the pause menu —
has three pages. **Page one is the game's music**: the track the stage you are
fighting on names in its `[Music] bgmusic`. **Pages two and three are the two
albums** in `sound/`, with their covers.

Moving the cursor onto an album stops the game's music and starts the track under
the cursor, so an album can be heard as it is browsed. Picking a track on page one
clears any override and hands playback back to the stage's own music; picking one
on an album plays it immediately — which is what makes a change from the pause menu
take effect in the fight that is running — and carries it into the next match.

The page you were on and the track you picked are written to `save/music_now.cfg`
and read back when the game starts and when the screen is opened again, so the
screen reopens where you left it with the playing track on its `NOW:` line, and the
next session starts on that track. Deleting that file returns the game to the
stage's own music.

## Shipping

The tracks in `sound/` are part of this repository, and every release bundle copies
that folder along with the rest of the game, so a track you add there also ships in
the downloads. Only add music you have the right to distribute.
