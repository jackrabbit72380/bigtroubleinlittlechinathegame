# Developer keys

In-game shortcuts for testing. They are registered by
[`external/script/debug.lua`](../external/script/debug.lua) and need debug keys
enabled: **Options → Engine → Debug Keys**, stored as `Debug.AllowDebugKeys` in
`save/config.ini`.

If a key does nothing, check that line first: with debug keys off every shortcut
below is inert.

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
