# Online play for Big Trouble in Little China: The Game

Two ways exist. The one recommended here is the **Online Lobby Pack**, because it
runs on stock Ikemen GO and needs no server of your own to start.

| | Online Lobby Pack | IkemenGo-Nakama fork |
|---|---|---|
| Engine | stock Ikemen GO **v1.0.0** | a forked engine build |
| To host | a small room server, or the public rooms list | a Nakama server **and** a database |
| Gives you | rooms, lobby list, train-while-you-wait, fighter preview, per-player online controls, replays with watch tools, training input display and playback | ranked sets with Elo, levels, leaderboards, tournaments, spectating |
| Install | unzip over a v1.0.0 folder | replace the engine and wire a server profile |

This game is on an **older engine than v1.0.0**: its `main.lua` differs from
v1.0.0's by 736 lines, the engine rejects a config key it does not know
(`Netplay.Rollback.LogsEnabled`), and a mod reports `commonStatesInsert is not
available in this build`. The pack will not run on it. So the first step is the
upgrade, and that is what the script below does.

## What is in this folder

- **UPGRADE-AND-GO-ONLINE.bat** — the one-click step. It downloads Ikemen GO
  v1.0.0, unpacks it into a folder called `Big Trouble Online` next to your game,
  copies your characters, stages, sounds, fonts, screenpack, settings and mods
  into it, and — if the lobby pack zip is sitting in this folder — unpacks that
  over the top, which is exactly how the pack is meant to be installed.
  Your own game folder is only read.
- `data/ikemen1/system.def` carries an **ONLINE** submenu entry under NETWORK
  (`menu.itemname.menunetwork.onlinelobby`), written by `tools/build_fonts.py`.
  The engine this game ships today has no handler for it and prunes it, so the
  current title screen is unchanged; a build with a lobby installed reads it.
- `data/online/servers.json` is only for the Nakama fork. Ignore it unless you
  go that way.

## Doing it

1. Download `IkemenGO-OnlineLobbyPack-v0.10.0.zip` and put it in this game
   folder, next to the .bat files (do not unzip it).
2. Double-click **UPGRADE-AND-GO-ONLINE.bat**.
3. When `Big Trouble Online` opens, the title menu's NETWORK submenu should offer
   ONLINE LOBBY.
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
