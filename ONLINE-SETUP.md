# Online play for Big Trouble in Little China: The Game

Two ways exist. The one recommended here is the **Online Lobby Pack**, because it
runs on stock Ikemen GO and needs no server of your own to start.

| | Online Lobby Pack | IkemenGo-Nakama fork |
|---|---|---|
| Engine | stock Ikemen GO **v1.0.0** | a forked engine build |
| To host | a small room server, or the public rooms list | a Nakama server **and** a database |
| Gives you | rooms, lobby list, train-while-you-wait, fighter preview, per-player online controls, replays with watch tools, training input display and playback | ranked sets with Elo, levels, leaderboards, tournaments, spectating |
| Install | unzip over a v1.0.0 folder | replace the engine and wire a server profile |

This game's scripts are not v1.0.0's — they are close to it and, in places,
ahead of it (they handle `-tcpport` / `-udpport`, which v1.0.0 does not) — while
the engine binary is behind them: it rejects the config key
`Netplay.Rollback.LogsEnabled` and a mod reports `commonStatesInsert is not
available in this build`. The pack asks for v1.0.0, so the safe move is the
upgrade rather than guessing which half is which. That is what the script does;
it takes the engine and the scripts from the same release, so they match.

## What is in this folder

- **Update and Play.bat** — unchanged in what it does for the game, with one step
  added at the end: it prepares `Big Trouble Online` (Ikemen GO v1.0.0 plus your
  content plus the lobby pack) and launches that. Your own game folder is only
  read.
- **UPGRADE-AND-GO-ONLINE.bat** — the same online step as a standalone script.
- `data/ikemen1/system.def` carries an **ONLINE** submenu entry under NETWORK
  (`menu.itemname.menunetwork.onlinelobby`), written by `tools/build_fonts.py`.
  The engine this game ships today has no handler for it and prunes it, so the
  current title screen is unchanged; a build with a lobby installed reads it.
- `data/online/servers.json` is only for the Nakama fork. Ignore it unless you
  go that way.

## Doing it

1. Download `IkemenGO-OnlineLobbyPack-v0.10.0.zip` and put it in this game
   folder, next to the .bat files (do not unzip it).
2. Double-click **Update and Play.bat**, the one you already use. It updates the
   game as before, then keeps a folder called `Big Trouble Online` beside your
   game holding Ikemen GO v1.0.0 with your characters, stages, sounds, fonts,
   screenpack, settings and mods copied into it, unpacks the lobby pack over that,
   and starts the game **from there**. One double-click, every time; the online
   folder is refreshed on each run, so an update reaches it too.
3. In the title menu's NETWORK submenu you should now find ONLINE LOBBY.

If v1.0.0 cannot be fetched, or tar/curl are missing, the updater says so in its
own words and starts the game from your normal folder instead - the run never
ends with no game. `UPGRADE-AND-GO-ONLINE.bat` is still here and does the same
online step on its own, for a folder that does not use the updater.
4. Everyone you play with needs the same lobby pack version — the pack's own
   notes say 0.10.0 sees only 0.10.0.

If the ONLINE LOBBY line does not appear, the screenpack needs its row for it:
the pack ships a PDF describing the `system.def` keys, and the label this game
already writes is `menu.itemname.menunetwork.onlinelobby`.

## About the room server

- The pack lists public rooms; you can also run your own with
  `IkemenOnlineServer-0.9.1-selfhost.zip` so your group is not on a shared list.
- The Nakama fork instead needs a Nakama server plus its database before two
  players can be matched; its own `nakama/hosting.md` covers that.
