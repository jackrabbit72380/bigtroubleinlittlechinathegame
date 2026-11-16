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

/* Every fighter asks for its common states with "stcommon = common1.cns", which
   MUGEN looks for in the fighter's folder and then in data/. Ikemen GO ships
   that as ZSS (data/common1.cns.zss) and compiles it itself; a plain-MUGEN
   engine cannot read ZSS, so the states are supplied in CNS in
   web/game/common1.cns for this build. That file is listed under the names the
   game asks for, and reads of those names are served from it. */
const COMMON_STATES = 'web/game/common1.cns';

function sharedCommonStates(source) {
  const files = source.list();
  const names = [
    'data/common1.cns',
    ...new Set(
      files
        .filter((p) => /^chars\/[^/]+\//i.test(p))
        .map((p) => `${p.split('/').slice(0, 2).join('/')}/common1.cns`),
    ),
  ];
  const ours = new Set(names.map((n) => n.toLowerCase()));
  const target = (p) => (ours.has(p.toLowerCase()) ? COMMON_STATES : p);
  return {
    list: () => [...files, COMMON_STATES, ...names],
    read: (p) => source.read(target(p)),
    readRange: (p, start, end) => source.readRange(target(p), start, end),
  };
}

function showProgress(p) {
  if (!p) {
    status.textContent = '';
    return;
  }
  const count = p.phase === 'characters' && p.done !== undefined ? ` ${p.done}/${p.total}` : '';
  status.textContent = `Loading ${PHASES[p.phase] ?? p.phase}…${count}`;
}

// A page that fails silently is indistinguishable from a game that draws black,
// so anything thrown after boot also lands on the status line.
window.addEventListener('error', (e) => {
  status.textContent = `Error: ${e.message}`;
});
window.addEventListener('unhandledrejection', (e) => {
  status.textContent = `Error: ${e.reason && e.reason.message ? e.reason.message : e.reason}`;
});

status.textContent = 'Reading the game files…';

try {
  const engine = await createEngine({
    canvas: document.getElementById('screen'),
    // '' is the checkout served as the game's root: the page is at /web/, the
    // game's folders at /chars, /data, /stages. httpSource joins the base and the
    // path with a '/', so '' gives '/chars/...' - while '/' would give '//chars',
    // which a browser reads as another host.
    source: sharedCommonStates(await httpSource('', '/web/files.json')),
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
  // Reachable from the console: what the engine is doing is otherwise invisible
  // while it draws.
  window.engine = engine;
} catch (err) {
  status.textContent = `Could not start: ${err && err.message ? err.message : err}`;
  throw err;
}
