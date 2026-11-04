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
