#!/usr/bin/env python3
"""Pin the Ikemen GO nightly this project is built and released against.

The engine the game ships is the `nightly` pre-release, and that tag is rolling:
its assets are replaced every time `develop` is built, so the same commit of this
repository could ship two different engines, and a change to the engine's own
`data/`, `font/` or `external/` reaches players with nothing in this repository
changing. That is why the build pipeline imports engine data too.

`engine.lock.json` records the exact bytes this project has been tested against.
Every place that downloads an engine checks the file it got against that record:
if the nightly has moved, the build stops and says so rather than quietly
shipping an engine nobody has run.

    python3 tools/pin_engine.py                       # re-pin to the current nightly
    python3 tools/pin_engine.py --check               # has the nightly moved?
    python3 tools/pin_engine.py --verify dl.zip NAME  # is this download the pinned build?
    python3 tools/pin_engine.py --local               # is the lock itself in order?
    python3 tools/pin_engine.py --show                # what is pinned, and where it came from

Re-pinning is a deliberate act: run this, then play the game and run the engine
harness (tools/engine_linux.sh) against it, and commit the result with the change
that needed it. Nothing re-pins itself.
"""

import argparse
import datetime
import hashlib
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCK = os.path.join(ROOT, "engine.lock.json")
TAG = "nightly"
SOURCE = "https://github.com/ikemen-engine/Ikemen-GO/releases/download/%s/" % TAG
ASSETS = (
    "Ikemen_GO-dev-windows.zip",
    "Ikemen_GO-dev-linux.zip",
    "Ikemen_GO-dev-macos.zip",
)
USER_AGENT = "bigtroubleinlittlechina-engine-pin/1"


def say(text=""):
    print(text, flush=True)


def online(url, path=None):
    """Fetch a URL, hashing as it arrives. Returns (sha256, bytes) or a path."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    digest = hashlib.sha256()
    size = 0
    out = open(path, "wb") if path else None
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            while True:
                chunk = response.read(1 << 20)
                if not chunk:
                    break
                digest.update(chunk)
                size += len(chunk)
                if out:
                    out.write(chunk)
    finally:
        if out:
            out.close()
    return (digest.hexdigest(), size) if path is None else path


def file_hash(path):
    digest = hashlib.sha256()
    size = 0
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def load_lock():
    if not os.path.isfile(LOCK):
        raise SystemExit("engine.lock.json is missing - run tools/pin_engine.py")
    with open(LOCK, encoding="utf-8") as handle:
        return json.load(handle)


def short(digest):
    return digest[:12] if digest else "(none)"


def local_problems(lock):
    """What is wrong with the lock itself, from the file alone."""
    problems = []
    if lock.get("tag") != TAG:
        problems.append("tag is %r, not %r" % (lock.get("tag"), TAG))
    assets = lock.get("assets") or {}
    for name in ASSETS:
        entry = assets.get(name)
        if not isinstance(entry, dict):
            problems.append("%s is not pinned" % name)
            continue
        digest = entry.get("sha256") or ""
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            problems.append("%s has no usable sha256" % name)
        if not isinstance(entry.get("bytes"), int) or entry["bytes"] <= 0:
            problems.append("%s has no byte count" % name)
    for name in sorted(set(assets) - set(ASSETS)):
        problems.append("%s is pinned but is not an asset this project ships" % name)
    try:
        datetime.date.fromisoformat(lock.get("pinned", ""))
    except ValueError:
        problems.append("pinned date %r is not a date" % lock.get("pinned"))
    return problems


def cmd_show(_args):
    lock = load_lock()
    assets = lock.get("assets") or {}
    say("engine pin: %s %s, pinned %s" % (lock.get("engine", "Ikemen GO"),
                                          lock.get("tag", "?"), lock.get("pinned", "?")))
    for name in ASSETS:
        entry = assets.get(name) or {}
        size = entry.get("bytes") or 0
        say("  %-26s %s  %.1f MB" % (name, entry.get("sha256", "(unpinned)"),
                                     size / 1e6 if size else 0.0))
    say("  source: %s" % SOURCE)
    problems = local_problems(lock)
    if problems:
        for line in problems:
            say("  FAIL " + line)
        return 1
    say("  ok  every platform asset is pinned to a SHA-256")
    return 0


def cmd_local(_args):
    lock = load_lock()
    problems = local_problems(lock)
    if problems:
        for line in problems:
            say("FAIL " + line)
        return 1
    say("engine pin: ok - %d asset(s) pinned as of %s"
        % (len(ASSETS), lock.get("pinned")))
    return 0


def cmd_verify(args):
    lock = load_lock()
    entry = (lock.get("assets") or {}).get(args.asset)
    if not entry:
        say("FAIL %s is not pinned in engine.lock.json" % args.asset)
        return 1
    if not os.path.isfile(args.file):
        say("FAIL %s does not exist" % args.file)
        return 1
    digest, size = file_hash(args.file)
    if digest != entry.get("sha256"):
        say("FAIL %s is not the pinned engine build." % os.path.basename(args.file))
        say("     pinned  %s  (%d bytes)" % (entry.get("sha256"), entry.get("bytes", 0)))
        say("     got     %s  (%d bytes)" % (digest, size))
        say("     The nightly tag has been rebuilt since this project was tested")
        say("     against it (%s). Run the game with that engine, then re-pin:" % lock.get("pinned"))
        say("         python3 tools/pin_engine.py")
        return 1
    say("engine build: %s matches the pin (%s, %s)"
        % (args.asset, short(digest), lock.get("pinned")))
    return 0


def cmd_check(_args):
    lock = load_lock()
    problems = local_problems(lock)
    if problems:
        for line in problems:
            say("FAIL " + line)
        return 1
    drifted = []
    for name in ASSETS:
        want = lock["assets"][name]
        try:
            digest, size = online(SOURCE + name)
        except Exception as exc:  # network, 404 - the check cannot answer
            say("FAIL could not download %s (%s)" % (name, exc))
            return 1
        state = "same" if digest == want.get("sha256") else "MOVED"
        say("  %-26s %s  pinned %s / live %s" % (name, state,
                                                 short(want.get("sha256")), short(digest)))
        if state == "MOVED":
            drifted.append(name)
    if drifted:
        say("")
        say("The nightly has been rebuilt since %s: %d asset(s) are no longer the"
            % (lock.get("pinned"), len(drifted)))
        say("build this project ships. Play it, run the engine harness, then re-pin:")
        say("    python3 tools/pin_engine.py")
        return 1
    say("engine pin: ok - the live nightly is still the pinned build (%s)" % lock.get("pinned"))
    return 0


def cmd_pin(args):
    assets = {}
    for name in ASSETS:
        target = os.path.join(args.keep, name) if args.keep else None
        say("  fetching %s ..." % name)
        if target:
            os.makedirs(args.keep, exist_ok=True)
            online(SOURCE + name, target)
            digest, size = file_hash(target)
        else:
            digest, size = online(SOURCE + name)
        assets[name] = {"sha256": digest, "bytes": size}
        say("    %s  %d bytes" % (digest, size))
    lock = {
        "engine": "Ikemen GO",
        "tag": TAG,
        "pinned": datetime.date.today().isoformat(),
        "source": SOURCE,
        "note": ("The build pipeline refuses to use any other engine: every download "
                 "is checked against these hashes. Re-pin with tools/pin_engine.py "
                 "after the new build has been played and tested."),
        "assets": assets,
    }
    with open(LOCK + ".new", "w", encoding="utf-8") as handle:
        json.dump(lock, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(LOCK + ".new", LOCK)
    say("")
    say("pinned %s as of %s" % (TAG, lock["pinned"]))
    say("now play it and run tools/engine_linux.sh before committing the pin")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true",
                       help="compare the live nightly with the pin")
    group.add_argument("--local", action="store_true",
                       help="check the lock file itself, with no network")
    group.add_argument("--show", action="store_true", help="print the pin")
    group.add_argument("--verify", nargs=2, metavar=("FILE", "ASSET"),
                       help="check a downloaded zip against the pin")
    parser.add_argument("--keep", metavar="DIR",
                        help="with no mode, also keep the downloaded zips here")
    args = parser.parse_args(argv)
    if args.verify:
        args.file, args.asset = args.verify
        return cmd_verify(args)
    if args.check:
        return cmd_check(args)
    if args.local:
        return cmd_local(args)
    if args.show:
        return cmd_show(args)
    return cmd_pin(args)


if __name__ == "__main__":
    sys.exit(main())
