# Online play for Big Trouble in Little China: The Game

Online play is not something this game can gain from a mod. It needs a different
**engine build** — [IkemenGo-Nakama](https://github.com/RollinJay/IkemenGo-Nakama),
a fork of Ikemen GO that adds accounts, quick and ranked matchmaking, lobbies,
spectating, replays and leaderboards on top of a Nakama game server.

Your game — characters, stages, sounds, screenpack, menus — is content, not
engine, so it moves across unchanged. The menus keep their look: the online items
were added to your existing **NETWORK** submenu, so nothing on the title screen
moved.

## What is already prepared here

- `data/ikemen1/system.def` now has three extra rows in the NETWORK submenu:
  QUICK MATCH, RANKED MATCH and ONLINE LOBBIES. They are written by
  `tools/build_fonts.py`, so regenerating the screenpack keeps them.
  The engine this game ships today has no handler for those items and prunes
  them, so **your current build shows the same NETWORK submenu as before**.
- `data/online/servers.json` is the server profile the online build reads. Two
  servers are listed: `local` (this PC, for testing) and `community` (a
  placeholder you edit).

## Setting it up (Windows)

1. Double-click **MIGRATE-TO-ONLINE.bat** in the game folder.
   It downloads the online engine once, unpacks it into a folder called
   `Big Trouble Online` next to your game, and copies your game's content in.
   Your own game folder is only read — nothing in it changes.
2. The online build starts. In the title menu open **NETWORK** and you should see
   QUICK MATCH, RANKED MATCH and ONLINE LOBBIES above HOST GAME and JOIN GAME.
3. Both players need the **same game content and the same `game`/`build` values**
   in `data/online/servers.json` — the server only pairs players whose `game` and
   `build` match. Send a friend the same folder (or the zip the game is shared as).

## Getting a server

Online play needs a Nakama server running this fork's modules; players connect
directly to each other and the server only matches them up.

- **Run your own:** `Ikemen_GO.exe -server-wizard` walks through creating a server
  and a matching client profile. A server needs its own database (the fork's
  `nakama/hosting.md` covers it).
- **Join a community server:** put its host, port and key in
  `data/online/servers.json`, set `"status": true` and make it `"default"`.

Never share a server's secret key in a public chat or repository. The default
`defaultkey` is Nakama's stock key for local testing only.

## If something misbehaves

- **No NETWORK items** — the game is not running the online build's engine.
  Check that the folder it started from contains the fork's `Ikemen_GO.exe`.
- **"Lobby is full" / cannot connect** — the server profile points at a server
  that is not running, or at the placeholder `CHANGE-ME.example.com`.
- **Menus look wrong** — the `external/mods` files from this game were copied in;
  remove any single file from the online build's `external/mods` to see whether it
  is the one objecting to the newer engine.
