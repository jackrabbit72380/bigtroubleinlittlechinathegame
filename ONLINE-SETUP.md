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

## The "Waiting for player 2... (7500)" screen

That is the engine's own **HOST GAME** screen, not the lobby: it opens a TCP port
(7500 by default) and waits for someone to connect to this PC's address on it.
Nobody can join it unless they know your IP, can reach that port, and run exactly
the same game. Leave it with the menu's cancel key - it waits forever otherwise.

The lobby pack replaces that dance: rooms are listed, and the two players are put
together without either of them typing an address.

## Why the old folder crashes when a match starts

The engine binaries that shipped in this folder are older than the game's Lua
scripts. Its own logs show the panic:

    Version: nightly   Build Time: 2026.11.03
    external/script/main.lua:3781  in function 'game'
    .\external\script\start.lua:5238  in function 'refresh'  (f_selectVersus, launchFight)

A script calls into the engine, the engine has no such function on that build and
answers with a nil, and the game panics. The same mismatch is visible without a
crash: the engine rejects `Netplay.Rollback.LogsEnabled` as a key it does not
know, and `external/mods/auraopts.lua` reports `commonStatesInsert is not
available in this build`. That is why a match in this folder cannot be relied on,
and why the online build is a whole v1.0.0 - engine and scripts from the same
release - rather than a patched binary.

## "Trojan:Win32/Tecabans.A!cl" when the game starts

Windows Defender flags the engine like that on a freshly downloaded copy. It is a
false alarm, and the engine's own authors have answered it as one - Ikemen GO
issue 2811, "IKEMEN nightly is trojan?", tagged *not an issue*: the binary is
unsigned and rebuilt for every release, which is what Defender's cloud detector
reacts to. Expect it to come back now and then after a new engine build.

What a genuine copy is, by SHA-256:

| File | SHA-256 |
|---|---|
| `Ikemen_GO.exe` from Ikemen GO v1.0.0 (what `Big Trouble Online` uses) | `c869a7fb0112257a6a581fa2d66ca76a9860b5b6ec500be38f8e480f6bf79cf7` |
| `Ikemen_GO-v1.0.0-windows.zip` itself | `9338eaeb68599ceb13b0867819a091ea3f92eba58077e800b4540b7a1f9c3731` |

The exe has no digital signature - right-click it, Properties, Digital
signatures, and you will see none. Ikemen GO ships unsigned, and that is the whole
reason for the warning.

To stop it happening: double-click **ALLOW-IN-DEFENDER.bat**. It asks Windows for
administrator rights, puts this game folder and `Big Trouble Online` on
Defender's exclusion list, and tells you whether each path really was added. Then
put a removed engine back - Windows Security, Virus and threat protection,
Protection history, the Trojan entry, Actions, Restore - or just run **Update and
Play.bat** again, which fetches it once more.

**CHECK-ONLINE.bat** now prints each engine's SHA-256, so the two machines can be
compared exactly, and so a file Defender names can be checked against the table.

## Checking which build you are in

Double-click **CHECK-ONLINE.bat**. It opens `online-check.txt` and changes
nothing. It reports, for this folder and for `Big Trouble Online`:

- which engine executables are there,
- the newest engine log's `Version:` and `Build Time:` - the quickest proof of
  whether that folder is v1.0.0 or one of the old nightlies,
- any lobby pack files and the server profile,
- the NETWORK submenu rows its screenpack defines,
- the netplay port and rollback settings in `save\config.ini`.

On a stock v1.0.0 build with no pack, NETWORK offers **HOST GAME**, **JOIN GAME**
and **BACK** only: host opens the port and waits, join needs the other machine's
address, and there is no room list until the Online Lobby Pack is installed.
