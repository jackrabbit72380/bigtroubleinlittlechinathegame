# Online play for Big Trouble in Little China: The Game

Two players, one rule: **the same build on both machines**. Everything here is
about meeting that rule with as little work as possible.

## What the updater does for you

`Update and Play.bat` adds one step before it starts the game. It keeps a second
folder beside your game - `Big Trouble Online` - holding:

- the **Ikemen GO nightly engine**, unpacked from one archive so the engine and
  its own scripts always agree with each other;
- this game's characters, stages, sounds, screenpack, mods and `*.zss` state
  files, copied in fresh on every run.

Then the game starts **from that folder**. One double-click, every time; game
updates reach the online folder too. Your own game folder is only ever read.

The engine archive is cached next to the updater and re-fetched once it is more
than a day old, so a stale engine cannot sit next to fresh state files. Two
players should both start the game on the same day before a match.

## Why the nightly, and not the tagged v1.0.0

The tagged release cannot run this screenpack. That is measured, not assumed:
the Linux build of v1.0.0, pointed at this game's data, dies before it draws a
frame.

    Panic: external/script/main.lua:3781: data/system.zss:30:
    Invalid data: inrunstate

`data/system.zss` uses `inRunState`, a state function only the newer engine has.
The same data on the nightly engine boots normally. Beyond that one file the
screenpack uses nightly-only screen keys (`p1.face2`, `stage.portrait.slot`,
`menu.item.scale` and many more), so even a v1.0.0 that loaded the data would
draw the wrong thing.

That also rules out the **Online Lobby Pack**: it asks for stock v1.0.0, which
cannot run this game, so it is not installed by the updater and an
`IkemenGO-OnlineLobbyPack*.zip` in the folder is ignored. There is no room list
for now - host and join by address.

## Playing

The engine's own NETWORK menu does the work:

- **HOST GAME** opens a TCP port (7500 unless `save\config.ini` says otherwise)
  and waits.
- **JOIN GAME** opens a list of remembered addresses; **NEW ADDRESS** asks for a
  name and then the address. The port comes from the host, not from a field here.

Both sides then pick **VERSUS 2P**. Two machines, addresses, firewalls and what
each failure means are in [TEST-ONLINE-WITH-A-FRIEND.md](TEST-ONLINE-WITH-A-FRIEND.md)
- which also shows how to be both players on one PC, with no second person.

## "Waiting for player 2... (7500)"

That screen is the engine's HOST GAME waiting on the port, not a lobby. Nobody
can join unless they know the address, can reach that port, and run exactly the
same build. Leave it with the menu's cancel key - it waits forever otherwise.

## Windows Defender and the engine

Defender reports the engine as `Trojan:Win32/Tecabans.A!cl` on a fresh download.
It is a false alarm on an unsigned binary, and the engine's own maintainers say
so (ikemen-engine/Ikemen-GO issue 2811). Run **ALLOW-IN-DEFENDER.bat** once per
PC: it adds this game folder and `Big Trouble Online` to Defender's exclusions
and prints whether each path really was added. If the engine was already
removed, restore it from Windows Security, Protection history, or run the
updater again so it is fetched once more.

## Checking which build you are in

Double-click **CHECK-ONLINE.bat**. It opens `online-check.txt` and changes
nothing. For this folder and for `Big Trouble Online` it reports:

- which engine executables are there,
- the newest engine log's `Version:` and `Build Time:` - the quickest proof of
  which nightly that folder is running,
- the engine's SHA-256, so two machines can be compared exactly,
- any lobby pack files and the server profile,
- the NETWORK submenu rows the screenpack defines,
- the netplay port and rollback settings in `save\config.ini`.

Compare the SHA-256 lines from both PCs: identical means the same engine. If they
differ, both run `Update and Play.bat` again on the same day.
