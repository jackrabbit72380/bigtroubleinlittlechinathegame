/* The web version of the game.

   The engine is mugen-js - a browser rebuild of M.U.G.E.N 1.1, vendored in
   vendor/ and pinned by sha256 in vendor/mugen-js.lock.json. This file is only
   the host page: it gives the engine a canvas and a way to read the game, and
   the engine does everything else.

   The game it reads is this same checkout. chars/, stages/, data/, font/ and
   sound/ are the folders the desktop build ships, so a fix to a stage, a sprite,
   a font or a roster entry lands in both versions at once - there is no copy to
   keep in step. web/files.json lists those paths, and tools/build_web_files.py
   regenerates it. */

import { createEngine, httpSource } from './vendor/mugen.min.js';

const status = document.getElementById('status');

const PHASES = { motif: 'motif', characters: 'characters', hud: 'HUD', loading: 'match' };

function showProgress(p) {
  if (!p) {
    status.textContent = '';
    return;
  }
  const count = p.phase === 'characters' && p.done !== undefined ? ` ${p.done}/${p.total}` : '';
  status.textContent = `Loading ${PHASES[p.phase] ?? p.phase}…${count}`;
}

status.textContent = 'Reading the game files…';

try {
  const engine = await createEngine({
    canvas: document.getElementById('screen'),
    // '' is the checkout served as the game's root: the page is at /web/, the
    // game's folders at /chars, /data, /stages. httpSource joins the base and the
    // path with a '/', so '' gives '/chars/...' - while '/' would give '//chars',
    // which a browser reads as another host.
    source: await httpSource('', '/web/files.json'),
    // The Ikemen screenpack this game is built on. Passing it by path means the
    // engine never looks for a mugen.cfg, which a browser build should not need.
    motif: 'data/ikemen1/system.def',
    // The stock debug keys let Space and F1 change a fight. A public page is
    // not a debugging session.
    debug: false,
    onProgress: showProgress,
    onExit: () => location.reload(),
  });
  engine.start();
} catch (err) {
  status.textContent = `Could not start: ${err && err.message ? err.message : err}`;
  throw err;
}
