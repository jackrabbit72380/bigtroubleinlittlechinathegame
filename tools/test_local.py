#!/usr/bin/env python3
"""Play this checkout in the engine, so a fix can be tried in one step.

The first run fetches the official Ikemen GO nightly for this platform into
.test/engine/ and reuses it from then on. The game always runs from this folder
with this folder's own data/, chars/ and stages/, so nothing is copied by hand
and there is no way to end up playing a stale data/fight.def.

    python tools/test_local.py                   pull, set up, launch
    python tools/test_local.py --no-pull         launch what is on disk right now
    python tools/test_local.py --no-launch       set up or refresh only
    python tools/test_local.py --engine-dir DIR  reuse an engine you already have
    python tools/test_local.py -- 2560 1440      extra arguments go to the engine

On Windows run it from a command prompt in this folder: python tools\\test_local.py
"""
from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".test"
ENGINE_DIR = CACHE / "engine"
ENGINE_ZIP = CACHE / "engine.zip"

DOWNLOAD = "https://github.com/ikemen-engine/Ikemen-GO/releases/download/nightly/{}"
ASSETS = {
    "Windows": "Ikemen_GO-dev-windows.zip",
    "Linux": "Ikemen_GO-dev-linux.zip",
    "Darwin": "Ikemen_GO-dev-macos.zip",
}

# Engine folders that must never be imported over ours:
#   save   - the player's own settings and logs
#   docs   - this project's docs, not the engine's
#   tools  - this project's generators
SKIP_DIRS = {"save", "docs", "tools", ".git", ".test", "__pycache__"}
SKIP_FILES = {"config.ini", "README.md", "LICENCE.txt", "LICENSE", "VERSION.txt"}
EXE_STEMS = ("BigTroubleInLittleChinaTheGame", "Ikemen_GO")


def say(text: str = "") -> None:
    print(text, flush=True)


def die(text: str) -> "NoReturn":  # type: ignore[name-defined]
    say(f"\n{text}")
    sys.exit(1)


# --------------------------------------------------------------------------- git

def pull_latest() -> None:
    """Fast-forward to the newest commit, quietly giving up if that is not safe."""
    if not shutil.which("git") or not (ROOT / ".git").exists():
        say("not a git checkout - using the files as they are")
        return
    try:
        run = subprocess.run(
            ["git", "pull", "--ff-only", "--quiet"],
            cwd=ROOT, capture_output=True, text=True, timeout=120,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        say(f"could not pull ({exc}) - using the files as they are")
        return
    if run.returncode == 0:
        say("pulled the latest commit")
    else:
        reason = (run.stderr or run.stdout).strip().splitlines()
        say(f"not pulling ({reason[-1] if reason else 'git said no'}) - using the files as they are")


# ------------------------------------------------------------------------ engine

def find_exe(root: Path) -> Path | None:
    for stem in EXE_STEMS:
        for suffix in ("", ".exe"):
            candidate = root / f"{stem}{suffix}"
            if candidate.is_file():
                return candidate
    for candidate in sorted(root.iterdir()):
        name = candidate.name.lower()
        if name.startswith("ikemen_go") and candidate.is_file() and not name.endswith(".zip"):
            return candidate
    for app in sorted(root.glob("*.app")):
        binaries = app / "Contents" / "MacOS"
        if binaries.is_dir():
            for candidate in sorted(binaries.iterdir()):
                if candidate.is_file():
                    return candidate
    return None


def find_engine_root(base: Path) -> Path | None:
    """The folder holding the engine binary next to its data/ folder."""
    folders = [base] + [p for p in sorted(base.rglob("*")) if p.is_dir()]
    fallback = None
    for folder in folders:
        try:
            depth = len(folder.relative_to(base).parts)
        except ValueError:
            continue
        if depth > 3 or not (folder / "data").is_dir():
            continue
        if find_exe(folder):
            return folder
        fallback = fallback or folder
    return fallback


def download_engine(asset: str) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    url = DOWNLOAD.format(asset)
    say(f"downloading the engine once: {url}")
    last: Exception | None = None
    for attempt in (1, 2, 3):
        try:
            with urllib.request.urlopen(url, timeout=120) as response, \
                    open(ENGINE_ZIP, "wb") as handle:
                shutil.copyfileobj(response, handle)
            return
        except Exception as exc:  # noqa: BLE001 - retried below
            last = exc
            say(f"  attempt {attempt} failed: {exc}")
    die(f"could not download the engine build ({last}).")


def ensure_engine(explicit: str | None) -> Path:
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if not (root / "data").is_dir():
            die(f"{root} does not look like an engine folder (no data/ inside).")
        return root

    if ENGINE_DIR.is_dir():
        cached = find_engine_root(ENGINE_DIR)
        if cached:
            return cached

    system = platform.system()
    asset = ASSETS.get(system)
    if not asset:
        die(f"no engine build is published for {system}. Pass --engine-dir with one.")
    if not ENGINE_ZIP.is_file():
        download_engine(asset)

    say("unpacking the engine ...")
    if ENGINE_DIR.exists():
        shutil.rmtree(ENGINE_DIR)
    with zipfile.ZipFile(ENGINE_ZIP) as archive:
        archive.extractall(ENGINE_DIR)
    root = find_engine_root(ENGINE_DIR)
    if not root:
        die("the engine archive has no folder with a data/ directory in it.")
    return root


# ------------------------------------------------------------------------- merge

def merge_engine(engine_root: Path) -> int:
    """Bring in engine files this folder does not have; never overwrite ours."""
    added = 0
    for source in sorted(engine_root.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(engine_root)
        if relative.parts and relative.parts[0] in SKIP_DIRS:
            continue
        if len(relative.parts) == 1 and relative.name in SKIP_FILES:
            continue
        target = ROOT / relative
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        added += 1
    return added


def write_config() -> bool:
    """The engine only reads save/config.ini; seed it from our pinned defaults."""
    seed = ROOT / "config.ini"
    target = ROOT / "save" / "config.ini"
    if target.is_file() or not seed.is_file():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(seed, target)
    return True


# ----------------------------------------------------------------------- reports

def git_line() -> str:
    if not (ROOT / ".git").exists():
        return "not a git checkout"
    try:
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True, timeout=30).stdout.strip()
        subject = subprocess.run(["git", "log", "-1", "--format=%s"], cwd=ROOT,
                                 capture_output=True, text=True, timeout=30).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                              capture_output=True, text=True, timeout=30).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown commit"
    return f"{head}  {subject}" + ("  (with uncommitted edits)" if dirty else "")


def hud_line() -> str:
    definition = ROOT / "data" / "fight.def"
    if not definition.is_file():
        return "data/fight.def is MISSING - the game will not load this HUD"
    text = definition.read_text(errors="replace")
    if "p1.pos = 595,2" in text and "bg1.spr = 20,0" in text:
        return "dragon HUD - back is health, belly is audacity, heads on the yin-yang"
    return "STOCK bars - data/fight.def in this folder is not the dragon HUD"


# -------------------------------------------------------------------------- main

def main() -> int:
    parser = argparse.ArgumentParser(description="Set this checkout up in the engine and play it.")
    parser.add_argument("--no-pull", action="store_true", help="do not git pull first")
    parser.add_argument("--no-launch", action="store_true", help="set up only, do not start the game")
    parser.add_argument("--engine-dir", help="an engine folder you already have (contains data/)")
    parser.add_argument("engine_args", nargs="*", help="extra arguments passed to the engine")
    args = parser.parse_args()

    say("Big Trouble in Little China: The Game - local test")
    if not args.no_pull:
        pull_latest()

    engine_root = ensure_engine(args.engine_dir)
    exe = find_exe(engine_root)
    if not exe:
        die(f"no engine binary found in {engine_root}.")

    added = merge_engine(engine_root)
    if platform.system() == "Linux" and exe.is_file():
        exe.chmod(exe.stat().st_mode | 0o111)
    seeded = write_config()

    say()
    say(f"  folder : {ROOT}")
    say(f"  commit : {git_line()}")
    say(f"  engine : {exe}" + (f"  ({added} engine file(s) added)" if added else ""))
    say(f"  settings: {'save/config.ini seeded' if seeded else 'save/config.ini already there'}")
    say(f"  hud    : {hud_line()}")
    say()

    if args.no_launch:
        say("set up only - run this again without --no-launch to play")
        return 0

    command = [str(exe), "-config", "save/config.ini", *args.engine_args]
    say("starting: " + " ".join(command))
    if platform.system() == "Windows":
        # The engine is a console program. Started normally it takes this
        # window for its log, and the window then has to stay open for the whole
        # session - that is the black box that sat over the game. CREATE_NO_WINDOW
        # gives it a console of its own that is never shown, so this window can
        # close and the game's own window is the only thing on screen.
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        try:
            subprocess.Popen(
                command, cwd=ROOT, creationflags=flags,
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError as exc:
            die(f"could not start the engine ({exc}).")
        say("the game is starting hidden - this window closes now")
        return 0
    try:
        return subprocess.call(command, cwd=ROOT)
    except OSError as exc:
        die(f"could not start the engine ({exc}).")


if __name__ == "__main__":
    sys.exit(main())
