# The arenas

Nine stages, all drawn procedurally — no bitmaps are committed as source — packed
into SFF v2 and named for the film's locations, plus the engine's training room.

| Stage | File | Setting |
|---|---|---|
| Lo Pan's Throne | `stages/lopans_throne.def` | skull gate, green neon, red temple glyphs |
| Lo Pan's Ceremony | `stages/lopans_ceremony.def` | six-armed statue, lotus plinth, broad steps |
| Lo Pan's Hallway | `stages/lopans_hallway.def` | long blue-lacquer corridor, gold Buddhas, lanterns, carpet runner |
| Wing Kong Exchange | `stages/wingkong_exchange.def` | loading bay, neon signage, rain |
| Chinatown Back Alley | `stages/chinatown_alley.def` | lanterns, vertical shop signs, steam |
| Pork Chop Express | `stages/porkchop_express.def` | storm highway, lightning, wet asphalt |
| The Upside Down | `stages/the_upside_down.def` | brick sewer vault, steel sump, dead tree, dragon |
| Hell of the Upside-Down Sinners | `stages/hell_sinners.def` | rusted steel works lit from the floor, furnace fires, flooded sumps |
| Airport Terminal | `stages/airport_terminal.def` | departures hall, glazed wall, parked airliners |
| Training Room | `stages/stage0.def` | the engine's training stage |

## The HD stage model

`tools/stages_hd.py` paints each arena natively at **1920×1080**
(`localcoord = 1920, 1080`), the arcade layout at 4.5×. The engine no longer
stretches a 240-line image across a 1080p window, so a 16:9 display shows all
1920 units at 1:1.

Each stage canvas is **8192×1080**, painted as two 4096-wide halves:

- the camera travels ±3136 and the art reaches ±4096, so the view always lands on
  painted artwork;
- fighters may walk to ±4028, 68 px short of the art edge, so the whole canvas is
  playable and the background never freezes under an invisible wall;
- the ground line is row 900 (`zoffset = 900`);
- every stage ships a `9000,1` select-screen preview sprite.

## Using your own art

Drop `backdrop.png` (and optionally `foreground.png`) into `art_src/<stage id>/`
and rebuild. `tools/build_hd_stage.py` replaces that stage with your image
cover-fitted to its own canvas and layer layout (`localcoord = 1920, 1080`), with
no code changes. That is the same HD stage model a high-resolution commercial fan
remake uses, applied to art you own.

```sh
python3 tools/build_hd_stage.py   # any stage that has art_src/ art
python3 tools/dump_stage_art.py   # unpack stage sprites back to PNG
```

On Windows, `Dump Stage Art.bat` does the same from a double-click.

`tools/build_stages.py` accepts `STAGE_DEBUG=1` to dump each layer as PNG into
`artifacts/`. Set `STAGES_HD_PREVIEW_DIR` when running `tools/stages_hd.py` to save
4:3 and 16:9 crops of each arena for eyeballing.
