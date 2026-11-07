"""Static checks for the Windows launchers.

cmd gives a batch file no second chance at syntax. An unescaped | in an echo
line is a pipe into a program that does not exist, so the window dies on its
first breath; an unescaped > swallows the line into a file; a goto to a label
that was renamed stops the run at that point; and a %VAR% that nothing ever sets
silently expands to nothing. None of that is visible to python or to the eye,
and this repo cannot run cmd, so the launchers are read here instead.

A metacharacter followed by a quote is left alone: those are the deliberate
ones - ">" into a cache file, and "|" into a program named by its full path.

Run:  python3 tools/check_launchers.py
"""

from __future__ import annotations

import os
import re

LAUNCHERS = (
    "Update and Play.bat",
    "Apply main.zip.bat",
    "Play Big Trouble.bat",
    "Test Big Trouble.bat",
)

# cmd's own variables: never set by the script, always present
BUILTIN = {
    "time", "date", "errorlevel", "cd", "random", "temp", "tmp", "userprofile",
    "localappdata", "appdata", "systemroot", "windir", "programfiles",
    "programfiles(x86)", "programw6432", "path", "pathext", "computername",
    "username", "wt_session", "term_program", "cmdextversion", "cmdcmdline",
}

ECHO = re.compile(r"^\s*(?:if\s+.*?\s)?echo\s", re.I)
WRITES_HELPER = re.compile(r"^\s*>>?")


def _problems_for(name, raw):
    out = []

    if raw.count(b"\n") != raw.count(b"\r\n"):
        out.append("%s: mixed line endings, cmd misparses a bare LF" % name)
    if raw and not raw.endswith(b"\r\n"):
        out.append("%s: does not end with a newline" % name)

    text = raw.decode("utf-8", "replace").replace("\r\n", "\n")
    lines = text.split("\n")

    # 1. operators that cmd will act on inside echoed text
    for i, line in enumerate(lines, 1):
        if not ECHO.match(line) or re.match(r"^\s*echo\.?>", line):
            continue
        for m in re.finditer(r"(?<!\^)([|&<>])", line):
            before = line[m.start() - 1:m.start()]
            after = line[m.end():m.end() + 3]
            if after[:1] == '"':
                continue          # a redirect to a quoted path, or a pipe into
                #                   a program named by its full path
            if m.group(1) in "<>" and (before.isdigit() or after.lower().startswith(("nul", "&"))):
                continue          # a stream redirect: 2>nul, 2>&1, >nul
            if m.group(1) == "&" and before in "<>":
                continue          # the stream copy inside 2>&1
            out.append("%s:%d: echo text holds an unescaped %r, which cmd reads "
                       "as an operator: %s" % (name, i, m.group(1), line.strip()[:70]))
            break

    # 2. parenthesised blocks have to close
    depth = 0
    for line in lines:
        if depth == 0 and re.match(r"^\s*echo", line, re.I):
            continue          # at this depth a parenthesis is only printed
        bare = re.sub(r'"[^"]*"', '""', line)
        depth += bare.count("(") - bare.count(")")
    if depth:
        out.append("%s: parentheses do not balance (%+d), so a block is left "
                   "open" % (name, depth))

    # 3. every jump lands somewhere
    labels = set(m.group(1).lower()
                 for m in re.finditer(r"(?m)^:([A-Za-z0-9_]+)", text))
    for i, line in enumerate(lines, 1):
        if WRITES_HELPER.match(line):
            continue              # the line writes a helper .bat, not this file
        for m in re.finditer(r"(?i)\bgoto\s+:?([A-Za-z0-9_]+)", line):
            if m.group(1).lower() not in labels and m.group(1).lower() != "eof":
                out.append("%s:%d: goto %s has no label" % (name, i, m.group(1)))
        for m in re.finditer(r"(?i)\bcall\s+:([A-Za-z0-9_]+)", line):
            if m.group(1).lower() not in labels:
                out.append("%s:%d: call :%s has no label" % (name, i, m.group(1)))

    # 4. every %VAR% is set somewhere, or it expands to nothing at run time
    defined = set()
    for m in re.finditer(r'(?i)\bset\s+(?:/a\s+|/p\s+)?"?([A-Za-z0-9_()]+)=', text):
        defined.add(m.group(1).lower())
    for i, line in enumerate(lines, 1):
        for var in _variable_refs(line):
            if var.isdigit() or var.lower() in defined or var.lower() in BUILTIN:
                continue
            out.append("%s:%d: %%%s%% is never set" % (name, i, var))

    # 5. the PowerShell helpers written at run time: a parameter and a local that
    #    differ only in case are the same variable, and the parameter loses
    helpers = {}
    for m in re.finditer(r'^(?:>>?)\s+"%(\w+)%"\s+echo\s+(.*)$', text, re.M):
        helpers.setdefault(m.group(1), []).append(m.group(2))
    for helper, chunk in sorted(helpers.items()):
        code = "\n".join(chunk)
        params = set()
        for p in re.finditer(r"param\((.*?)\)", code):
            params |= set(x.lower() for x in re.findall(r"\$(\w+)", p.group(1)))
        assigned = set(x.lower()
                       for x in re.findall(r"(?m)^\s*\$(\w+)\s*=", code))
        for clash in sorted(params & assigned):
            out.append("%s: helper %s assigns $%s, shadowing its parameter of the "
                       "same name, so the parameter arrives empty"
                       % (name, helper, clash))

    return out


def _gun_block(text):
    """The pistol as the window shows it: (muzzle column, lines below it).

    The percentage is written on the barrel line itself, so the column it goes
    to and the row it comes back from are measurements of the drawing. They are
    taken from the art rather than trusted, so a changed picture fails here
    instead of leaving the number floating beside the barrel.
    """
    lines = text.split("\n")
    start = next((i for i, line in enumerate(lines) if line.strip() == ":gun"), None)
    if start is None:
        return None, None
    art = []
    for line in lines[start + 1:]:
        stripped = line.strip()
        if stripped.startswith(":") or stripped.lower().startswith("exit"):
            break                         # the label is over, the art is done
        if not stripped.lower().startswith("echo"):
            continue                      # rem, set, and the save after it
        shown = stripped[4:]
        if not shown.strip():
            continue                      # the blank line above the drawing
        art.append(shown.replace("^", ""))
    for i, shown in enumerate(art):
        if "|]=" in shown:
            return len(shown), len(art) - i - 1
    return None, None


def _progress_problems(name, raw):
    """The updater's pistol and the number at its muzzle are product, not
    decoration.

    A rewrite that only looked at the console plumbing dropped them twice: the
    gun was left behind as an unreachable label, and the count became a bare
    percentage at ten-point steps. The number also has to come off the barrel
    rather than sit under the drawing, which is a column and a row measured from
    the art. All of it is checked here so a later edit cannot lose it silently.
    """
    if name != "Update and Play.bat":
        return []
    text = raw.decode("utf-8", "replace")
    out = []
    if not re.search(r"(?m)^call :gun\s*$", text):
        out.append("%s: :gun is never called, so the updater shows no pistol" % name)
    if not re.search(r"(?m)^call :vt\s*$", text):
        out.append("%s: :vt is never called, so the console never gets the cursor "
                   "control the number at the muzzle needs" % name)
    column, below = _gun_block(text)
    if column is None:
        out.append("%s: the barrel line cannot be found in :gun, so where the "
                   "number is written is unknown" % name)
    else:
        measured = re.search(r'set "MUZZLE=(\d+)"', text)
        if not measured:
            out.append("%s: MUZZLE is never set, so the percentage is written "
                       "somewhere other than the end of the barrel" % name)
        elif int(measured.group(1)) != column + 2:
            out.append("%s: MUZZLE is %s but the drawn barrel ends at column %d, so "
                       "the number would not sit at its end"
                       % (name, measured.group(1), column))
        write = f"%ESC%[u%ESC%[{below + 1}A%ESC%[%MUZZLE%G%PCT3%%%ESC%[u"
        if write not in text:
            out.append("%s: the percentage is not written at the end of the barrel "
                       "with the cursor brought back under the pistol" % name)
    if "if not defined VTOK goto gaugeone_plain" not in text:
        out.append("%s: the muzzle write is not guarded, so a console without "
                   "cursor control would print the escape sequence as text" % name)
    if not re.search(r"(?m)^:gaugeone_plain\s*$", text):
        out.append("%s: a console without cursor control is left with no progress "
                   "line at all" % name)
    if "for /l %%P in (%GFROM%,1,%GTO%)" not in text:
        out.append("%s: the percentage no longer counts every point, so the run "
                   "skips from one milestone to the next instead of 1 to 100" % name)
    if text.count("%PCT3%%%") != 2:
        out.append("%s: the percentage is printed more or less than once per step"
                   % name)
    if "BARLEFT" in text or "$bar" in text:
        out.append("%s: a loading bar is back; the progress is the number alone"
                   % name)
    if "GMAXPCT" not in text:
        out.append("%s: the gauge can report a lower percentage than it just showed, "
                   "so one run reads as a rewind" % name)
    if "$whole" not in text:
        out.append("%s: the download no longer reports the run's percentage" % name)
    if "-Vt %VTFLAG% -Col %MUZZLE%" not in text or "'[7A'" not in text:
        out.append("%s: the download writes its percentage somewhere other than "
                   "the muzzle" % name)
    if "-bor 4" not in text or "[char]27" not in text:
        out.append("%s: the console is never put into the mode the muzzle write "
                   "needs, so the number can only go out as text" % name)
    return out


def _report_problems(name, raw):
    """The end-of-update data report is the only place a player can see that a
    fix actually arrived, so it is checked rather than trusted."""
    if name != "Update and Play.bat":
        return []
    text = raw.decode("utf-8", "replace")
    out = []
    if "call :datareport" not in text:
        out.append("%s: the update no longer reports the data files it wrote" % name)
    for need in ('call :note "data\\fight.def"', 'call :note "data\\music.json"'):
        if need not in text:
            out.append("%s: the data report no longer names %s" % (name, need))
    return out


def _variable_refs(line):
    """The %NAME% references on one line, read the way cmd reads them.

    "%%" is an escaped percent (a for variable, or part of a URL), so the scan
    steps over it instead of pairing it with the percent that follows. A lone
    "%" with no partner is text, which is how "100%" survives in an echo.
    """
    found = []
    i = 0
    while i < len(line):
        if line[i] != "%":
            i += 1
            continue
        if line[i + 1:i + 2] == "%":
            i += 2
            continue
        j = line.find("%", i + 1)
        if j < 0:
            break
        name = line[i + 1:j]
        if re.fullmatch(r"[A-Za-z0-9_()]+", name):
            found.append(name)
        i = j + 1
    return found


def problems(root):
    """Every problem found in the launchers, as ready-to-print strings."""
    found = []
    for name in LAUNCHERS:
        path = os.path.join(root, name)
        if not os.path.isfile(path):
            continue
        with open(path, "rb") as fh:
            raw = fh.read()
            found.extend(_problems_for(name, raw))
            found.extend(_progress_problems(name, raw))
            found.extend(_report_problems(name, raw))
    return found


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    found = problems(root)
    for problem in found:
        print("FAIL " + problem)
    if not found:
        print("launchers: clean")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
