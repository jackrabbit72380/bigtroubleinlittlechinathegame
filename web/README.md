# Web version

The game, in a browser. The engine is [mugen-js](https://github.com/yojona/mugen-js) -
M.U.G.E.N 1.1 rebuilt in TypeScript and WebGL2, MIT, vendored in `vendor/` and pinned
by sha256 in `vendor/mugen-js.lock.json`.

## What is shared

Everything that can be. The browser build reads the same folders the desktop build
ships - `chars/`, `stages/`, `data/`, `font/`, `sound/` - straight out of this
checkout. There is no second copy of the art:

| | desktop (Ikemen GO) | web (mugen-js) |
|---|---|---|
| fighters, stages, sprites | `chars/`, `stages/` | the same files |
| screenpack, fonts, defs | `data/`, `font/` | the same files |
| music | `sound/` | the same files |
| generated art | `tools/build_*.py` | nothing to do: it reads what those wrote |

So a fix belongs in the shared file, once. `web/files.json` is the only generated
thing here: it is the list of paths the engine reads through, written by

```sh
python3 tools/build_web_files.py
```

Run it after adding a fighter, a stage or a sound, and it will be picked up by both
versions.

## Look at it

```sh
python3 tools/serve_web.py            # then open http://127.0.0.1:8123/web/
```

The server's root is this checkout rather than `web/`, because the page needs the
game's folders beside it. It answers Range requests (the engine reads sprite
archives in pieces) and asks the browser not to cache anything, so an edit is a
reload.

## What is not shared

The engines differ, so some content is read by only one of them:

- Ikemen GO's Lua (`external/script/*.lua`, `external/mods/*.lua`) and its `.zss`
  state scripts do not run in mugen-js. Screens and modes those scripts draw or
  drive have to exist in the motif itself to appear in the browser.
- mugen-js targets M.U.G.E.N 1.1. Ikemen-only parameters and triggers are read as
  unknown keys; a character that leans on them will not behave identically.
- The common states - standing, walking, jumping, being hit, guarding, lying down -
  are `data/common1.cns.zss` on the desktop, in Ikemen's ZSS dialect (if-blocks,
  let-bindings, `[Function]` calls), which no M.U.G.E.N engine can read. Fighters ask
  for them as `common1.cns`, so `game/common1.cns` carries the same states in plain
  CNS and `app.js` answers every `common1.cns` request with it. The two files
  describe one set of movements and hits: a change in one belongs in the other.

All three are engine differences, not asset copies, so fixing one never means
fixing the other twice.

## Updating the engine

Download the release bundle and replace `vendor/mugen.min.js`, then update
`vendor/mugen-js.lock.json`. `python3 tools/validate.py` hashes the bundle against
those numbers, so a stale pin fails the build instead of shipping a different
engine.

```sh
curl -fsSL -o web/vendor/mugen.min.js \
  https://github.com/yojona/mugen-js/releases/download/<tag>/mugen.min.js
sha256sum web/vendor/mugen.min.js
```
