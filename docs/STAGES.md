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

## The rig on the Pork Chop Express is solid

The truck's own surfaces are the stage walls. `tools/stages_hd.py` computes them
from the painting constants, so they move with the artwork:

| | world x | what it is |
|---|---|---|
| `leftbound` | **-2422** | the head of the bed at the cab's back, so a fighter cannot walk through the cab |
| `rightbound` | **3790** | the trailer's tail board, so a fighter cannot walk off the bed |

The cab is painted behind the play plane and cannot stop anyone by itself, and a
MUGEN/Ikemen stage definition carries no collision geometry — these bounds are the
only stage-level solidity the format offers.

That is the whole mechanic, by design: no standing on the cab roof and no run-over
death. The deck is a single flat floor plane, and a stage definition has no ledges,
hazards or per-stage match script, so a wall at each end of the bed is what the
format can honestly give. A fighter stops at the cab's back, 72 px of coupling
before it, and at the trailer's tail board with the end of the stage behind it.

## The floating terrace

The three Storms stages (`stage3d.def`, `stage3d_outline.def`, `stage3d_rain.def`)
carry the Third Heights pack's island. Its `.glb` models are still in the tree, but
the stages no longer draw them: on a renderer without model support the island
never appeared, and the stage was a black field with only its weather over it.
`tools/build_stage3d_rain.py` paints the terrace, the sea and the sky at the
stages' own 1280x720 localcoord instead - day, night and storm - so each one shows
its arena on every machine. The ground line is painted at `zoffset` 660, which is
where these stages put the play plane.

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

## The map wall is baked

The stage screen's wall of maps is not assembled at runtime. `tools/build_stage_wall.py`
reads the pool from `data/select.def`, decodes each stage's `9000,1` preview, frames
it, prints its name under it and composites all twelve at the boxes
`start.f_stageGrid` lays out, then writes the finished 1920x1080 wall into
`data/ikemen1/system.sff` as `240,0` - with `241,<n>` and `242,<n>` as the picked
card's frame for player 1 and player 2. The screen draws those at `0,0`, 1:1.

Before that it scaled each preview anim through the motif's `stage.portrait.scale`,
the stage's own `portraitscale`, the stage/motif localcoord ratio and the grid fit,
inside a clip window. Those factors did not agree: cards landed at half the box the
grid reserved for them, and the picked card's frame was drawn out in the gap beside
it. Painting the wall settles the layout once, in Python, where it can be looked at.
