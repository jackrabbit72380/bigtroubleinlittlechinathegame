# Testing online play with a friend

Two machines, two players. Nothing here needs a server.

## The one rule

Both machines must be running **the same build**: the same Ikemen GO version,
the same game files (characters, stages, screenpack), and - if you use it - the
same Online Lobby Pack version. A v1.0.0 on one side and an old nightly on the
other will not connect, and if it does connect the match will fall apart.

**The easy way to guarantee that:** zip your finished `Big Trouble Online`
folder and give your friend that exact zip. He unzips it anywhere and runs
`Ikemen_GO.exe` in it. Nothing to install, nothing to match up.

If he downloads a release himself, it must be **Ikemen GO v1.0.0** plus your
game's data over it - not the latest nightly, and not a different game's build.

## Checking you match

Run `CHECK-ONLINE.bat` on both machines and compare the two text files: the
`Version:` and `Build Time:` lines must be identical, and both must list the same
engine executable.

## Same house / same network

1. **Host:** open NETWORK > HOST GAME. It shows "Waiting for player 2... (7500)"
   and stays there. Leave it alone.
2. **Host:** find his local address: press Win+R, run `cmd`, type `ipconfig`,
   read **IPv4 Address** (looks like 192.168.1.24).
3. **Guest:** open NETWORK > JOIN GAME, type that address, port 7500.
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
| Connects, then the game freezes or panics | A fight is starting on an old binary; both must be on v1.0.0 |
| Host's screen never changes | Guest joined a different port, or the host's window lost focus and stopped listening |

## Later: the room list

HOST GAME and JOIN GAME are manual - someone has to know someone's address. The
Online Lobby Pack adds **ONLINE LOBBY**, a list of rooms, so nobody types an
address. It has to be on both machines, same version, and it goes in the same
folder as the game (`IkemenGO-OnlineLobbyPack-<version>.zip` unzipped over it, or
dropped in the folder your updater reads).
