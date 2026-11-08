# Playing and running the game

Questions about any of this? The [Discord](https://discord.gg/Bn2kABJsK5) is the
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

## Try the latest changes in one step

When you want to play whatever is newest on `main` — a HUD tweak, a stage fix —
there is nothing to download by hand and nothing to copy:

| Platform | Do this |
|---|---|
| Windows | `python tools\test_local.py` |
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
game's own exe. Each run fetches whatever is newest on `main`, copies only the files that changed inside `data/`,
`chars/`, `stages/`, `font/`, `external/` and `sound/`, and leaves
your `save/` and the engine files alone, prints which HUD it copied, and starts
the game. With Git installed it compares the files already in that folder against
`main` and downloads only the ones that differ - the art you already have
is read and hashed, not fetched again; without git
it reads the public commit feed (a few tens of KB, no token, no API quota) and
only downloads the `main` zip when that feed shows `main` has moved, so a launch
with nothing new behind it costs one small request. When it does download, the
archive is opened in place and only the entries that differ are written into the
folder, so an update no longer expands and recopies the whole game. Nothing to
by hand.

Before it fetches anything it says what it found - `Update available: main @
e14800a` with `This folder has:  5d796a3` underneath, or `Up to date:       main @
e14800a is already in this folder.` - and waits for one keypress. `C` carries
on, `E` closes the window with nothing downloaded, copied or deleted. Where
the check cannot read main, it says so instead of guessing.

Asking GitHub for the latest commit runs beside the window rather than
silently: the seconds are counted on the status line, git aborts itself
after thirty seconds of less than 1 KB/s, and after three minutes without
an answer the launcher takes the verified download instead of waiting.

The launcher closes as soon as the game starts. The engine attaches to
whichever console launched it, so it used to print its log into the
updater's window and that window had to be left open while the game ran.
It is started in a console of its own now, minimised, with that output
discarded; the engine still writes `save/logs/` beside the exe, which is
where to look if it does not come up.

The launcher gets the files four ways before it gives up, and it counts the
bytes as they arrive, so a slow line looks slow rather than broken:

1. **git**, working on the game folder itself rather than on a copy of it. It
   records the folder as a repository (`git init` - no commit, no file rewritten),
   fetches `main` with `--filter=blob:none`, then compares the content of the six
   folders the game uses against it. A file that already matches is never
   transferred; only the blobs that really differ are fetched, straight into
   place. The first run pays for one hash pass over the art already on disk, with
   no download at all, and later runs transfer only what a commit touched -
   recent updates have been 3 to 8 files. `artifacts`, `concept_art`, `art_src`
   and `tools` are outside those paths and are never read. When nothing differs
   it prints `Already current` and starts the game in a couple of seconds, and
   there is no second copy of the art anywhere: `.update-cache` holds only logs,
   and a copy left by an older launcher is deleted. A certificate bundle that
   a Git Bash install left pointing at `/usr/ssl/certs/ca-bundle.crt` is swapped
   for the one that ships beside the git actually running, so a fetch is not
   refused with `error setting certificate file`; if no bundle is found,
   verification is left on and the archive download below takes over.
2. **curl**, with `CURL_CA_BUNDLE`/`SSL_CERT_FILE` cleared for that window and
   `--ssl-no-revoke`, and one status line at the bottom of the window:
   `[####----------------]  86.2/190 MB  640 KB/s  4:12 left`. Where the
   terminal understands ANSI - Windows Terminal, or conhost with
   `VirtualTerminalLevel` switched on - that line is cleared and rewritten in
   place, so there is one bar and not a column of them; older consoles get the
   same line printed once every half minute instead of escapes they cannot
   read. During a git update the line names the file being fetched, for
   example `[########------------]  12/463  chars/rain_rig/rain.def`.
3. **PowerShell**, which uses the .NET and Windows proxy settings.
4. **BITS**, the Windows download service, when a corporate proxy only allows it.

If all four are refused, it opens the zip in your browser, watches `Downloads`
for the finished file, and starts the game itself — no second script, no coming
back to the window. `main.zip` sitting next to the launcher is used first and
skips the network completely.

`Apply main.zip.bat` remains for the case where you would rather do the download
by hand: save the zip in the game folder and double-click it.

### The updater closes itself

If `Update and Play.bat` disappears in the middle of a run, it reached a line cmd
cannot parse - usually a percent sign or an operator that a second read of the
line left behind - and a batch file that cannot parse a line stops there and
closes its window, which looks like a crash. The folder is not stuck with that
copy:

1. look for `Update and Play.new` next to the launcher and rename it over
   `Update and Play.bat` if it is still there - the launcher stages a whole
   replacement before it starts work;
2. or double-click `Apply main.zip.bat`, which puts a whole launcher in place
   even when no zip was downloaded;
3. or download `Update and Play.bat` from the repository and save it over the
   old one.

The version in use is in the window title and on the first line of
`btilc-updater.log`, so it is easy to say which copy is running.

### Why the scripts name `System32` tools in full

A Git for Windows install that puts its `usr\bin` on `PATH` shadows the Windows
programs with MSYS builds of the same name, and they behave differently: the MSYS
`timeout` answers `invalid time interval '/t'`, the MSYS `tar` reads `H:\...` as a
remote host and answers `Cannot connect to H:`, and the MSYS `curl` looks for its
CA bundle at `/usr/ssl/certs/ca-bundle.crt`, which does not exist there. That is
what produced the certificate error and the instant `timeout` failures. Both
launchers now call `%SystemRoot%\System32\...` for every tool and never rely on
`PATH`; if you write your own script for this folder, do the same.

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
