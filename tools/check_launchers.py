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


def _progress_problems(name, raw):
    """The updater's pistol and its bar are product, not decoration.

    A rewrite that only looked at the console plumbing dropped them twice: the
    gun was left behind as an unreachable label, and the bar became a bare
    percentage at ten-point steps. They are checked here so a later edit cannot
    take them away silently again.
    """
    if name != "Update and Play.bat":
        return []
    text = raw.decode("utf-8", "replace")
    out = []
    if not re.search(r"(?m)^call :gun\s*$", text):
        out.append("%s: :gun is never called, so the updater shows no pistol" % name)
    if "[%BARLEFT%o%BARRIGHT%]" not in text or "%PCT3%%%" not in text:
        out.append("%s: the gauge no longer prints a bar with its percentage" % name)
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
