# Playing and running the game

Questions about any of this? The [Discord](https://discord.gg/bY6NJ35c6P) is the
fastest place to get an answer.

## Playing a release

Nothing to install. Every zip from the
[latest release](https://github.com/jackrabbit72380/bigtroubleinlittlechinathegame/releases/latest)
already contains the Ikemen GO engine with this game's fighters, stages and
screenpack in place.

| Platform | File | Launch |
|---|---|---|
| Windows | `BigTroubleInLittleChina-Windows.zip` | unzip, double-click `BigTroubleInLittleChinaTheGame.exe` |
| Linux | `BigTroubleInLittleChina-Linux.zip` | unzip, `chmod +x BigTroubleInLittleChinaTheGame && ./BigTroubleInLittleChinaTheGame` |
| macOS | `BigTroubleInLittleChina-macOS.zip` | unzip, right-click the app → **Open** the first time |

Releases are produced by the `Build release bundles` workflow: it downloads the
official engine build for each platform, copies this game's files over it, checks
that the executable, roster, stages and engine licence are all present, then
publishes the zips.

### Unsigned downloads

If a bundle trips SmartScreen (Windows) or Gatekeeper (macOS), that is because the
downloads are unsigned: choose *More info → Run anyway*, or right-click → *Open*.

### It closes on boot with an Engine error

The renderer is the usual cause. *Video Settings → Renderer* offers Vulkan as well
as OpenGL, and `vk.QueueSubmit failed with vulkan error: device lost` is what a
driver that cannot run it reports. Choose **OpenGL 3.3**.

If the box appears before you can reach that menu, delete `save/config.ini`: the
engine recreates it on the default renderer, and your other settings are the only
thing in there.

## The easy route: open `Start.html`

Double-click `Start.html` in the repository (or in your game folder) and a themed
page opens in your browser with the two downloads that matter: the game zip and
`Apply main.zip.bat`. Both are ordinary browser downloads, so they still work on a
machine where the command window cannot reach GitHub.

## Try the latest changes in one step

When you want to play whatever is newest on `main` — a HUD tweak, a stage fix —
there is nothing to download by hand and nothing to copy:

| Platform | Do this |
|---|---|
| Windows | double-click `Test Big Trouble.bat` |
| Linux / macOS | `python3 tools/test_local.py` |

The first run fetches the official engine nightly for your platform into
`.test/engine/` and keeps it. Every run after that pulls the latest commit, drops
the engine binary in beside this folder's own `data/`, `chars/` and `stages/`, and
starts the game from here — so what you play is exactly the files in this checkout,
never an old copy. It prints the commit it is running and whether `data/fight.def`
is the dragon HUD, which is the quickest way to tell a stale folder from a broken
change.

```sh
python3 tools/test_local.py --no-pull      # play what is on disk, no pull
python3 tools/test_local.py --no-launch    # set up or refresh only
python3 tools/test_local.py -- 2560 1440   # render size for this run
```

It needs Python 3.9+ and leaves engine files, `save/` and `.test/` untracked.

### Already playing a downloaded folder?

Drop `Update and Play.bat` into that folder and double-click it instead of the
game's own exe. Each run fetches whatever is newest on `main`, copies `data/`,
`chars/`, `stages/`, `font/`, `external/` and `sound/` over the folder, leaves
your `save/` and the engine files alone, prints which HUD it copied, and starts
the game. With Git installed the update is a few megabytes; otherwise it downloads
the `main` zip once per run. Nothing to install or copy by hand.

The launcher gets the files four ways before it gives up, and it counts the
bytes as they arrive, so a slow line looks slow rather than broken:

1. **git**, forced onto the Windows certificate store (`http.sslBackend=schannel`)
   so a broken CA path from a Git Bash install cannot stop it. This one only
   fetches what changed.
2. **curl**, with `CURL_CA_BUNDLE`/`SSL_CERT_FILE` cleared for that window and
   `--ssl-no-revoke`, printing `112 of about 190 MB` as it goes.
3. **PowerShell**, which uses the .NET and Windows proxy settings.
4. **BITS**, the Windows download service, when a corporate proxy only allows it.

If all four are refused, it opens the zip in your browser, watches `Downloads`
for the finished file, and starts the game itself — no second script, no coming
back to the window. `main.zip` sitting next to the launcher is used first and
skips the network completely.

`Apply main.zip.bat` remains for the case where you would rather do the download
by hand: save the zip in the game folder and double-click it.

## Run from source

Everything below is for editing the game. If you only want to play, use a release.

1. Download an Ikemen GO build (Windows/Linux/macOS) from the
   [engine releases page](https://github.com/ikemen-engine/Ikemen-GO/releases) —
   the nightly is what the bundled screenpack targets.
2. Copy the engine executable into this folder, next to `data/`.

   ```
   bigtroubleinlittlechinathegame/
     Ikemen_GO.exe          <- drop the engine here
     data/                  <- screenpack + system config (this repo)
     chars/                 <- fighters (this repo)
     stages/                <- arenas (this repo)
     font/ external/        <- engine support files (this repo)
     tools/                 <- asset generators + validator (this repo)
   ```

3. Run the engine. The default motif reads `data/ikemen1/system.def`, which points
   at `data/select.def` — the roster in this repo.

On Linux, `chmod +x Ikemen_GO_Linux` first. If the engine reports a missing
`.dll`/`.so`, you copied the binary out of its release archive without the sibling
libraries — keep the release folder intact and only replace its `data/`, `chars/`
and `stages/` with these.

## Editing assets

The tooling needs Python 3.9+ and Pillow; the game itself does not.

```sh
python3 tools/build_all.py        # every generator, then the validator
python3 tools/validate.py         # offline checks only, no engine needed
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the per-generator commands.
