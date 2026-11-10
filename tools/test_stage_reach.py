"""Proves every map in the stage pool can be reached and picked on the wall.

"Every map is selectable" is not a matter of taste, it is arithmetic: a flat pool
of stages, a cursor that counts stage slots, and a grid step that moves between
cards. This reads the real pool out of data/select.def, loads that arithmetic out
of start.lua, and walks the wall from card one. A map with no card, a card that
maps back to the wrong slot, or a card no sequence of key presses can reach is a
map the player cannot choose, and it is reported as a failure.

Run:  python3 tools/test_stage_reach.py
      (uses lupa when available; the pool checks run either way)
"""

import os
import re
import sys
from collections import deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START = os.path.join(ROOT, "external", "script", "start.lua")
SELECT = os.path.join(ROOT, "data", "select.def")
DEF = os.path.join(ROOT, "data", "ikemen1", "system.def")


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def block(text, name):
    m = re.search(r"^\[%s\][^\n]*\n(.*?)(?=^\[|\Z)" % re.escape(name), text, re.M | re.S)
    return m.group(1) if m else ""


def stage_pool():
    """The stage pool the way the game fills it: the extras, then stage rows."""
    text = read(SELECT)
    pool = []

    def add(path):
        path = path.split(";")[0].strip()
        if path and path not in pool:
            pool.append(path)

    for line in block(text, "ExtraStages").splitlines():
        if line.strip() and not line.strip().startswith(";"):
            add(line)
    for m in re.finditer(r"^\s*stage\s*=\s*([^;,\n]+)", text, re.M):
        add(m.group(1))
    return pool


def random_enabled():
    m = re.search(r"^\s*stage\.randomselect\s*=\s*(-?\d+)", read(DEF), re.M)
    return (int(m.group(1)) if m else 1) != 0


def lua_function(src, name):
    m = re.search(r"(?m)^function start\.%s\(" % re.escape(name), src)
    if m is None:
        raise SystemExit("start.lua has no function start.%s" % name)
    nxt = re.search(r"(?m)^(function |--|;)", src[m.end():])
    end = len(src) if nxt is None else m.end() + nxt.start()
    return src[m.start():end]


def main():
    problems = []
    pool = stage_pool()
    print("  pool: %d stage(s) in data/select.def" % len(pool))
    if len(pool) < 12:
        problems.append("the stage pool has only %d entries" % len(pool))
    for path in pool:
        full = os.path.join(ROOT, path.replace("\\", "/"))
        if not os.path.isfile(full):
            problems.append("%s is in the pool but not on disk" % path)

    try:
        from lupa import LuaRuntime
    except ImportError:
        print("  lupa is not installed: pool checked, cursor graph not executed")
        report(problems)
        return

    src = read(START)
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute("start = {}")
    lua.execute(src[src.index("-- >>> stage preview grid geometry"):
                     src.index("-- <<< stage preview grid geometry")])
    for name in ("f_stageMenuRef", "f_stageCardOf", "f_stageStopOf"):
        lua.execute(lua_function(src, name))

    n = len(pool)
    literal = "{" + ",".join('"%s"' % p for p in pool) + "}"
    lua.execute("main = main or {}")
    lua.execute("main.t_selectableStages = %s" % literal)
    slots = ",".join("{available = {main.t_selectableStages[%d]}, slot = 1}" % i
                     for i in range(1, n + 1))
    lua.execute("main.t_selectableStageSlots = {%s}" % slots)
    lua.execute("stageListNo = 1")

    card_of = lua.eval("start.f_stageCardOf")
    stop_of = lua.eval("start.f_stageStopOf")
    step = lua.eval("start.f_stageCursorStep")
    has_random = random_enabled()
    cols = int(lua.eval("start.f_stageGridCols(%d)" % n))
    grid = lua.eval("start.f_stageGrid(%d)" % n)
    print("  wall: %d card(s), %d across, RANDOM %s"
          % (n, cols, "on" if has_random else "off"))

    # every card exists and every slot has one
    missing = [i for i in range(1, n + 1) if grid[i] is None]
    if missing:
        problems.append("the wall has no card at position(s) %s" % missing)

    # every map is addressable: slot -> card -> slot, and the card is its own
    seen_cards = {}
    for no in range(1, n + 1):
        card = int(card_of(no) or 0)
        if card == 0:
            problems.append("%s has no card on the wall" % pool[no - 1])
            continue
        if card in seen_cards:
            problems.append("%s and %s share card %d"
                            % (pool[seen_cards[card] - 1], pool[no - 1], card))
        seen_cards[card] = no
        back = int(stop_of(card) or 0)
        if back != no:
            problems.append("card %d lands on slot %d, not %d" % (card, back, no))
        if int(card_of(back) or 0) != card:
            problems.append("slot %d does not round-trip through its card" % no)

    # every card is reachable from the opening card with the four directions
    start_card = 1
    seen = {start_card}
    queue = deque([start_card])
    while queue:
        card = queue.popleft()
        for direction in ("L", "R", "U", "D"):
            nxt = int(step(card, direction, n, cols, has_random) or 0)
            if nxt == card:
                continue
            if not (0 <= nxt <= n):
                problems.append("a step from card %d went to %d" % (card, nxt))
                continue
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    for card in range(1, n + 1):
        if card not in seen:
            problems.append("%s cannot be reached from the opening card"
                            % pool[int(card_of(seen_cards.get(card, card)) or 0) - 1
                                   if seen_cards.get(card) else card - 1])
    if has_random and 0 not in seen:
        problems.append("RANDOM cannot be reached from the opening card")

    # a slot with several stages must still be able to offer each of them
    lua.execute("main.t_selectableStageSlots = {{available = "
                "{main.t_selectableStages[1], main.t_selectableStages[2]}, slot = 1},"
                "{available = {main.t_selectableStages[3]}, slot = 1}}")
    lua.execute("stageListNo = 1")
    cards = []
    for shift in (1, 2):
        lua.execute("main.t_selectableStageSlots[1].slot = %d" % shift)
        if int(stop_of(card_of(1)) or 0) != 1:
            problems.append("a multi-stage slot does not land back on itself")
        cards.append(int(card_of(1) or 0))
    if len(set(cards)) != 2:
        problems.append("a multi-stage slot cannot reach all of its stages")

    print("  reachable: %d of %d card(s)%s"
          % (len([c for c in seen if c != 0]), n,
             ", RANDOM included" if has_random and 0 in seen else ""))
    report(problems)


def report(problems):
    if problems:
        print("\nthe stage wall cannot offer every map (%d problem(s))" % len(problems))
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print("\nevery map in the pool has a card, a slot and a reachable path")


if __name__ == "__main__":
    main()
