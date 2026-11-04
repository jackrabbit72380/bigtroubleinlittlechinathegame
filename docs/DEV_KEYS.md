# Developer keys

In-game shortcuts for testing. They are registered by
[`external/script/debug.lua`](../external/script/debug.lua) and need debug keys
enabled: **Options → Engine → Debug Keys**, stored as `Debug.AllowDebugKeys` in
`save/config.ini`.

If a key does nothing, check that line first: with debug keys off every shortcut
below is inert.

## In the game

Pause the match and choose **Developer Keys**. The whole list is on that one
screen: two columns, colour-grouped (display, time, match, players), with the
title moved up so the text can be twice the size it was, and nothing to scroll.
The size is computed from the font's real glyph metrics, so it stays inside the
frame on any screenpack revision. Cancel closes it and returns to the pause menu.
It sits in both the normal and the training pause menu.

`Ctrl`+`F1` prints the same list into the debug console if you would rather not
leave the fight. `F8` clears the console.

The entry is re-applied by `tools/build_devhelp.py` on every asset build, because
the build replaces `data/` with the engine's stock motif; the screen itself lives
in [`external/mods/devhelp.lua`](../external/mods/devhelp.lua).

## On screen

| Keys | What it shows |
|---|---|
| `Ctrl`+`D` | The debug display: character and helper info, action ID, animation state and element, state number, control/physics/move type, frame count and speed. Press it again to cycle the readout to the next player or helper. |
| `Ctrl`+`Shift`+`D` | The same readout with the extended detail on. |
| `Shift`+`D` | The readout pinned to the player you are on. |
| `Ctrl`+`C` | Collision boxes (clsn1 attack, clsn2 hurt). |
| `Ctrl`+`W` | Wireframe rendering, to see the quads the sprites are drawn from. |
| `Ctrl`+`L` | The stock life bars, which is how you check the game's own HUD is what you are looking at. |
| `Ctrl`+`V` | V-Sync on/off. |

## Time and speed

| Keys | What it does |
|---|---|
| `Ctrl`+`S` | Cycles game speed, doubling up to 4× then dropping to 0.25× and climbing back. |
| `Ctrl`+`KP +` / `Ctrl`+`KP -` | Speed up / slow down in 0.01 steps, for frame-by-frame review. |
| `Pause` | Pauses the match. |
| `ScrollLock` | Single frame step while paused. |
| `Space` | Refills life and power for everyone and resets the round timer. |
| `F5` | Sets the round timer to 0. |

## Round and match

| Keys | What it does |
|---|---|
| `F1` | KOs the second player's side (`Ctrl`+`F1` does the first player's side). |
| `F2` | KOs everyone (`Ctrl`+`F2` / `Shift`+`F2` for one side). |
| `F3` | Fills power bars to max (`Ctrl`+`Shift`+`F3` toggles max power mode). |
| `F4` | Resets the round. |
| `Shift`+`F4` | **Reloads the engine** — the way to pick up Lua and def changes without quitting. |
| `Ctrl`+`I` | Puts every fighter back in their standing state. |
| `F9` / `F10` | Load / save state. |

## Players and AI

| Keys | What it does |
|---|---|
| `Ctrl`+`1` … `Ctrl`+`8` | Toggles AI for that player number. |
| `Ctrl`+`Alt`+`1` … `Ctrl`+`Alt`+`9` | Hands you control of that player (or helper), so you can drive the opponent. |

## Console

| Keys | What it does |
|---|---|
| `F8` | Clears the debug console. |
| `Ctrl`+`F1` | Prints this list into the console (`external/mods/devhelp.lua`). |

## Where these come from

`external/script/debug.lua` is engine code and is replaced whenever the asset
build stages a fresh engine copy, so add your own keys in
`external/mods/devhelp.lua` instead — the engine requires every file in that
folder at startup.

## Compared with MUGEN's debug mode

Ikemen GO inherits M.U.G.E.N's debug keys and then adds its own. The left column
is from the [MUGEN Database *Debug Mode* page](https://mugen.fandom.com/wiki/Debug_Mode)
(the wiki blocks the article page but serves it through its API); the right
column is what this build actually binds, read from `external/script/debug.lua`.

| MUGEN key | What MUGEN does | What this build does |
|---|---|---|
| `F1` / `Ctrl`+`F1` | KOs player 2 / player 1 | Same. |
| `F2` / `Ctrl`+`F2` / `Shift`+`F2` | Lowers life to 1 | KOs instead: `F2` everyone, `Ctrl`+`F2` the first player's side, `Shift`+`F2` the second player's. |
| `F3` / `Ctrl`+`Shift`+`F3` | Max power / auto-refill power bars | Same two meanings. |
| `F4` / `Shift`+`F4` | Restart round / restart the whole match | Same, and the reload also re-reads Lua and defs, which is the point of it here. |
| `F5` | Time over | Same. |
| `F8` | Clears debug messages | Clears the console. |
| `Space` | Maxes time, life and power | Same. |
| `Ctrl`+`C` / `Ctrl`+`L` / `Ctrl`+`V` | Collision boxes / life and power bars / vsync | Same. |
| `Ctrl`+`D` | Debug mode, cycling characters and helpers | Same readout, cycling the same way. |
| `Ctrl`+`I` | Forces the standing state | Same, applied to all eight players. |
| `Ctrl`+`S` | Toggles the fastest speed | Cycles 1× → 2× → 4× → 0.25× → 0.5× instead of a single toggle. |
| `Ctrl`+`<n>` / `Ctrl`+`Alt`+`<n>` | Toggles AI / toggles a player, 1–4 | Same, extended to 1–8 AI and 1–9 players/helpers. |
| `Pause` | Pauses | Same. |

**Keys MUGEN documents that this engine's debug module does not bind:** `F12`
(screenshot), `Ctrl`+`~` (M.U.G.E.N console), `Ctrl`+`F` (frame skipping) and
`Ctrl`+`T` (auto-refill life and power). They are absent from `debug.lua`, so
unless the engine handles one natively they do nothing here — worth knowing
before you report a missing screenshot key as a bug.

**Ikemen-only keys**, all listed on the screen above: `Ctrl`+`W` wireframe,
`Ctrl`+`Shift`+`D` and `Shift`+`D` readout variants, `Ctrl`+`KP +`/`-` for 0.01
speed steps, `F9`/`F10` state save/load, and `ScrollLock` single frame step.

