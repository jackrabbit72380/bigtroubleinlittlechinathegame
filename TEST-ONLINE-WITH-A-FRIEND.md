# Testing online play with a friend

Two machines, two players. Nothing here needs a server.

## The one rule

Both machines must be running **the same build**: the same Ikemen GO nightly,
and the same game files (characters, stages, screenpack). Two nightlies from
different days will not connect, and if they do connect the match will fall
apart - the engine changes between builds.

**The easy way to guarantee that:** zip your finished `Big Trouble Online`
folder and give your friend that exact zip. He unzips it anywhere and runs
`Ikemen_GO.exe` in it. Nothing to install, nothing to match up.

If he downloads a release himself, make sure he then runs **Update and Play.bat**
in it and starts the game from `Big Trouble Online`, on the same day you do. The
tagged v1.0.0 cannot run this screenpack at all - `ONLINE-SETUP.md` has the
panic it produces.

## Checking you match

Run `CHECK-ONLINE.bat` on both machines and compare the two text files: the
`Version:` and `Build Time:` lines must be identical, and both must list the same
engine executable.

## Testing on your own, no second person

One PC can be both players, because a host and a guest are just two copies of the
same game talking over the network - and a PC can talk to itself.

1. Start the game the way you normally do (`Update and Play.bat`), so it launches
   from `Big Trouble Online`, the nightly build.
2. Title menu: **NETWORK > HOST GAME**. It sits on "Waiting for player 2... (7500)".
   Leave it there.
3. Start the same game a **second** time: go into `Big Trouble Online` and
   double-click `Ikemen_GO.exe`. A second window opens.
4. In the second window: **NETWORK > JOIN GAME > NEW ADDRESS**. It asks for two
   things, in this order:
   - a **name** for the address - type anything, e.g. `me` (this is just a label
     that gets remembered for next time),
   - the **address** - type `127.0.0.1`, which always means "this PC".
   There is no port box: the guest uses the host's listen port, 7500 by default.
5. The first window leaves the waiting screen and both windows show a small
   netplay menu - **VERSUS 2P**, **ARCADE CO-OP**, **SURVIVAL CO-OP**, **EXIT**.
   Pick **VERSUS 2P**, then characters and a stage as usual.

If a match starts, hosting, joining, the port and the build all work, and a friend
only adds distance. The keyboard is shared by both windows, so this is a
connection test rather than a real fight: click into one window to move that
player, click into the other to move theirs.

What the outcomes mean:

| What happens | What it means |
|---|---|
| Second window connects, match starts | Everything works: port, build, content |
| Second window cannot connect at all | Firewall blocking 7500 - allow it for private networks |
| Connects, then drops or desyncs instantly | The two copies are not identical; `CHECK-ONLINE.bat` shows it |
| First window never leaves "Waiting for player 2..." | The guest typed the address wrong, or hit a different port in `save\config.ini` |

## Same house / same network

1. **Host:** open NETWORK > HOST GAME. It shows "Waiting for player 2... (7500)"
   and stays there. Leave it alone.
2. **Host:** find his local address: press Win+R, run `cmd`, type `ipconfig`,
   read **IPv4 Address** (looks like 192.168.1.24).
3. **Guest:** open NETWORK > JOIN GAME > NEW ADDRESS, give it a name (anything,
   e.g. `host`), then type that address. There is no port prompt: the guest calls
   the host's listen port, 7500 unless it was changed in `save\config.ini`.
4. The host's screen changes, a match starts.

## Different houses / over the internet

Port 7500 has to reach the host's PC. Two ways:

- **Forward the port** on the host's router: TCP 7500 to the host's local
  address, then the guest joins the host's *public* IP (whatismyipaddress.com).
- **Use a VPN - much less hassle:** both install ZeroTier or Tailscale, both join
  the same network, and the guest joins the host's VPN address instead. No router
  changes.

Either way, the first time the game opens a port Windows asks about the firewall
- allow it for private networks. If it was dismissed, add an inbound rule for
TCP 7500.

## What the results mean

| What happens | What it means |
|---|---|
| Host waits forever, guest says it cannot reach | Wrong address or port, or the firewall/router is blocking 7500 |
| Connects, then instantly drops | Builds do not match - compare the `Version:` lines |
| Connects, then the game freezes or panics | The two engine builds differ; compare the SHA-256 lines and update both the same day |
| Host's screen never changes | Guest joined a different port, or the host's window lost focus and stopped listening |
| The game will not start, or the exe has vanished | Antivirus took it: `Trojan:Win32/Tecabans.A!cl` is a known false alarm on Ikemen GO's unsigned engine. Run **ALLOW-IN-DEFENDER.bat** on that PC, then **Update and Play.bat** to fetch the engine again |

## The room list

There is none yet. The Online Lobby Pack that provides it targets the tagged
v1.0.0 engine, which cannot run this screenpack, so the updater does not install
it. HOST GAME and JOIN GAME are what works today; each pair of players only has
to exchange an address once, because JOIN GAME remembers the ones it is given.
