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
            after = line[m.end():m.end() + 1]
            if after == '"' or after in ("n", "N") or after.isdigit():
                continue          # deliberate redirect / pipe, or 2>nul
            out.append("%s:%d: echo text holds an unescaped %r, which cmd reads "
                       "as an operator: %s" % (name, i, m.group(1), line.strip()[:70]))
            break

    # 2. parenthesised blocks have to close
    depth = 0
    for line in lines:
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
        for m in re.finditer(r"%([A-Za-z0-9_()]+)%", line):
            var = m.group(1).lower()
            if var.isdigit() or var in defined or var in BUILTIN:
                continue
            out.append("%s:%d: %%%s%% is never set" % (name, i, m.group(1)))

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


def problems(root):
    """Every problem found in the launchers, as ready-to-print strings."""
    found = []
    for name in LAUNCHERS:
        path = os.path.join(root, name)
        if not os.path.isfile(path):
            continue
        with open(path, "rb") as fh:
            found.extend(_problems_for(name, fh.read()))
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
