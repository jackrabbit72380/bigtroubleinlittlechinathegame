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
    "Dump Stage Art.bat",
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


def _percent_tokens(line):
    """The percent tokens on one line, read left to right as cmd reads them.

    "%%" is an escaped sign, "%~dp0" / "%1" / "%*" is an argument, and
    "%VAR%" or "%VAR:old=new%" is a variable or a substitution. A sign with no
    partner is not a token at all: cmd cannot pair it, so everything after it on
    the line stops being read as text, and the window answers with
    "... is not recognized as an internal or external command".
    """
    i, n, out = 0, len(line), []
    while i < n:
        if line[i] != "%":
            i += 1
            continue
        nxt = line[i + 1:i + 2]
        if nxt == "%":
            out.append(("escaped", "%%"))
            i += 2
            continue
        if nxt == "~":
            j = i + 2
            while j < n and line[j].lower() in "dpnxfztas":
                j += 1
            if j < n and line[j] in "0123456789*":
                out.append(("argument", line[i:j + 1]))
                i = j + 1
                continue
        if nxt == "*":
            out.append(("argument", "%*"))
            i += 2
            continue
        if nxt.isdigit():
            out.append(("argument", line[i:i + 2]))
            i += 2
            continue
        j = line.find("%", i + 1)
        body = line[i + 1:j] if j > i else ""
        if j > i and re.fullmatch(r"[A-Za-z0-9_()]+(?::.*)?", body, re.S):
            out.append(("variable", line[i:j + 1]))
            i = j + 1
            continue
        out.append(("stray", "%"))
        i += 1
    return out


ESCAPED_BY_CARET = "|&<>()!^\"%"


def _syntax_problems(name, raw):
    """The characters cmd acts on before a single command runs.

    Everything here is a way for a line to mean something other than what it
    says, which is invisible to python and to the eye:
      * an unpaired percent swallows the rest of the line;
      * a caret on the end of a line continues it onto the next one;
      * a caret inside quotes does not escape, it is printed;
      * an operator inside a for /f command string splits that command;
      * a quote left open in "set "NAME=value" runs the value past the quote;
      * a value appended to itself inside a for body is expanded once, before
        the loop, so the append silently does nothing;
      * a label defined twice sends a goto to the first one;
      * a path passed to call unquoted is read a second time, so a folder named
        with & or | turns into a command;
      * a trailing space is swallowed by a caret continuation;
      * a literal ! is eaten when delayed expansion is on.
    """
    text = raw.decode("utf-8", "replace").replace("\r\n", "\n")
    lines = text.split("\n")
    out = []
    labels = {}
    delayed = "EnableDelayedExpansion" in text
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("::"):
            continue
        if re.match(r"(?i)^rem\b", stripped):
            continue          # nothing follows the text, so a lone sign is safe
        if line != line.rstrip():
            out.append("%s:%d: the line ends in a space, which a caret "
                       "continuation swallows: %s" % (name, i, stripped[:60]))
        for kind, token in _percent_tokens(line):
            if kind == "stray":
                out.append("%s:%d: a per cent sign has no partner, so cmd reads "
                           "the rest of the line as text: %s"
                           % (name, i, stripped[:70]))
                break
        if stripped.endswith("^"):
            out.append("%s:%d: the line ends in a caret, so it continues onto "
                       "the next one: %s" % (name, i, stripped[:60]))
        quoted = False
        for ch in line:
            if ch == '"':
                quoted = not quoted
            elif ch == "^" and quoted:
                out.append("%s:%d: a caret inside quotes does not escape "
                           "anything, cmd prints it: %s" % (name, i, stripped[:60]))
                break
        for m in re.finditer(r"\^(.)", line):
            if m.group(1) not in ESCAPED_BY_CARET:
                out.append("%s:%d: a caret before %r escapes nothing, so it is "
                           "printed: %s" % (name, i, m.group(1), stripped[:60]))
                break
        for m in re.finditer(r"(?i)\bfor\s+/[a-z]*\s.*?\bin\s+\((['`])(.*?)\1\)",
                             line):
            inner = m.group(2)
            bad = re.search(r"(?<!\^)[|&<>]", inner)
            if bad:
                out.append("%s:%d: a for /f command string holds an unescaped %r, "
                           "which splits the command: %s"
                           % (name, i, bad.group(0), stripped[:60]))
        if (re.match(r'(?i)^\s*(?:if\s+.*?\s)?set\s+"', stripped)
                and line.count('"') % 2):
            out.append("%s:%d: the quote after set is never closed, so the value "
                       "runs to the end of the line: %s" % (name, i, stripped[:60]))
        if (delayed and "!" in line):
            out.append("%s:%d: a literal ! is eaten while delayed expansion is "
                       "on: %s" % (name, i, stripped[:60]))
        grown = re.search(r'(?i)\bfor\b.*\bdo\b.*\bset\s+(?:/a\s+)?"?([A-Za-z0-9_]+)=',
                          stripped)
        if grown and "call set" not in stripped.lower():
            seen = grown.group(1)
            if re.search(r"%%%s%%" % re.escape(seen), stripped, re.I):
                out.append("%s:%d: appends %%%s%% inside a for body without "
                           "call set, so the value is expanded once, before the "
                           "loop: %s" % (name, i, seen, stripped[:60]))
        if re.match(r"(?i)^\s*call\s+:", stripped):
            for m in re.finditer(r"%~[df][a-z]?[0-9]", line):
                if line[m.start() - 1:m.start()] != '"':
                    out.append("%s:%d: %s is passed to call unquoted, and call "
                               "reads its line twice, so a path holding & or | "
                               "runs as a command: %s"
                               % (name, i, m.group(0), stripped[:60]))
        m = re.fullmatch(r":([A-Za-z0-9_]+)", stripped)
        if m:
            labels.setdefault(m.group(1).lower(), []).append(i)
    for lab, at in sorted(labels.items()):
        if len(at) > 1:
            out.append("%s: label :%s is defined %d times (%s), so a goto lands "
                       "on the first" % (name, lab, len(at),
                                         ", ".join(str(a) for a in at)))
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
        elif int(measured.group(1)) != column + 3:
            out.append("%s: MUZZLE is %s but the drawn barrel ends at column %d, so "
                       "the bar would not start one breath past its end"
                       % (name, measured.group(1), column))
        up = f"%ESC%[u%ESC%[{below + 1}A"
        if (up not in text or 'set /p "=%GWRITE%" <nul' not in text
                or 'set "GWRITE=%GWRITE%%PCTX%"' not in text
                or 'set "GWRITE=%GWRITE%%ESC%[K%ESC%[u"' not in text):
            out.append("%s: the barrel is not filled with a pipe per percent "
                       "with the count after the bar, or the write is not built "
                       "in one piece, so the cursor comes back mid-sequence and "
                       "the rest prints as letters" % name)
    if "if not defined VTOK goto gaugeone_plain" not in text:
        out.append("%s: the muzzle write is not guarded, so a console without "
                   "cursor control would print the escape sequence as text" % name)
    if not re.search(r"(?m)^:gaugeone_plain\s*$", text):
        out.append("%s: a console without cursor control is left with no progress "
                   "line at all" % name)
    elif "call :gunredraw" not in text or not re.search(r"(?m)^:gunredraw\s*$", text):
        out.append("%s: a console without cursor control only gets the title bar, "
                   "so the window shows a picture with no number on it" % name)
    elif "^|]=  %RBAR%" not in text:
        out.append("%s: the redrawn barrel does not start its pipes where the "
                   "drawn barrel ends, so the count does not sit at the muzzle" % name)
    if "for /l %%P in (%GFROM%,1,%GTO%)" not in text:
        out.append("%s: the percentage no longer counts every point, so the run "
                   "skips from one milestone to the next instead of 1 to 100" % name)
    pct_lines = [(number, line.strip())
                 for number, line in enumerate(text.splitlines(), 1)
                 if re.search(r"(?<![A-Za-z])PCT=", line)]
    if not pct_lines:
        out.append("%s: the per cent sign is not made once on its own, so the "
                   "count pairs signs in the source and cmd reads the pair as "
                   "text" % name)
    # The sign has to be made on every line that sets it, not merely somewhere:
    # :gun sets it, and :gunredraw sets it again only when it is undefined, so
    # breaking one line still left the other holding the correct form.
    for number, line in pct_lines:
        if not re.search(r'(?i)set "PCT=%%"$', line):
            out.append("%s:%d: the per cent sign is not made once on its own - "
                       "the count has to end with set \"PCT=%%%%\", and this line "
                       "does not: %s" % (name, number, line[:70]))
    if ('set "PCTX=%GNUM%%PCT%"' not in text
            or 'set "RPCT=%RNUM%%PCT%"' not in text):
        out.append("%s: the count is not padded as digits and then given its "
                   "sign, so a per cent sign sits inside a value call re-reads "
                   "and is dropped - the window shows 25 instead of 25%%" % name)
    if ('if %GNUM% LSS 10 set "GNUM=  %GNUM%"' not in text
            or 'if %RNUM% LSS 10 set "RNUM=  %RNUM%"' not in text):
        out.append("%s: the count is not padded by comparison, so it is padded "
                   "through call and the per cent sign goes with it" % name)
    for held in ("PCTX", "RPCT", "GNUM", "RNUM"):
        if re.search(r"(?m)^\s*call\s.*%s" % held, text):
            out.append("%s: %s is expanded on a call line, and call reads its "
                       "line twice, so the count or the sign inside it is lost"
                       % (name, held))
    if "BARLEFT" in text:
        out.append("%s: a loading bar is back; the progress is the number alone"
                   % name)
    # one pipe for every percent, on a bar sized to the window it draws in
    if 'set "BARMAX=' not in text or "set /a BARMAX=%%w-%MUZZLE%-6" not in text:
        out.append("%s: the pipe bar has no width of its own, so it either "
                   "wraps over the drawing or cannot fill to 100%%" % name)
    if "set /a GPOS=%~1*%BARMAX%/100" not in text:
        out.append("%s: the barrel no longer fills one pipe per percent" % name)
    if not re.search(r"(?m)^echo\s+BIG TROUBLE IN LITTLE CHINA.*$", text):
        out.append("%s: the game's title is not drawn above the pistol" % name)
    if "GMAXPCT" not in text:
        out.append("%s: the gauge can report a lower percentage than it just showed, "
                   "so one run reads as a rewind" % name)
    if "$whole" not in text:
        out.append("%s: the download no longer reports the run's percentage" % name)
    if ("-Vt %VTFLAG% -Col %MUZZLE% -Bar %BARMAX%" not in text
            or "'[7A'" not in text or "[char]124" not in text
            or "$pipe + ' ' + $pct" not in text):
        out.append("%s: the download writes its percentage somewhere other than "
                   "the muzzle" % name)
    if "-EncodedCommand" not in text or "VTDONE" not in text:
        out.append("%s: the console helper is gone, so the mode the muzzle "
                   "write needs is never asked for" % name)
    if "\x1b" not in text:
        out.append("%s: the escape character is no longer in the file, so the "
                   "number cannot be written at the muzzle" % name)
    if "-bor 4" not in text:
        out.append("%s: nothing turns on the console mode the escape "
                   "sequences need" % name)
    return out


CONSOLE_LABELS = {
    "githere", "confirm", "gitdrop_many", "gamelock", "gamelock_wait",
    "gitlocked", "gitfail_final", "dl_browser", "bwait_check", "launch_died",
    "selfupdate_got", "selfupdate_stuck", "launchfail", "folder_denied",
    "folder_denied_noexe", "wrongfolder", "downloadfailed", "close_soon",
    "quit", "gun", "gaugeone_plain", "gunredraw",
    # one failure line each; the rest of their lines go to the log
    "download", "skipver", "verify_again",
}

ECHO_LINE = re.compile(r"(?i)^(?:if .*?\s)?echo(?:\s|\.|$)")


def _quiet_window_problems(name, raw):
    """The window is the pistol and one number, so routine lines stay out.

    Every message that is only news goes to the run log through :say; what may
    still print is a failure the player has to act on. Walking the file label by
    label means a new echo in a routine step fails here instead of scrolling
    over the drawing.
    """
    if name != "Update and Play.bat":
        return []
    text = raw.decode("utf-8", "replace").replace("\r\n", "\n")
    out = []
    label = ""
    for i, line in enumerate(text.split("\n"), 1):
        stripped = line.strip()
        m = re.fullmatch(r":([A-Za-z0-9_]+)", stripped)
        if m:
            label = m.group(1).lower()
            continue
        if not ECHO_LINE.match(stripped):
            continue
        if ">" in stripped or "|" in stripped:
            continue                  # writes a file or pipes into a tool
        if label in CONSOLE_LABELS:
            continue
        out.append("%s:%d: %s prints to the window; routine lines belong in the run "
                   "log (:say), because the window is the pistol and its number"
                   % (name, i, stripped[:60]))
    if "call :say" not in text:
        out.append("%s: routine messages have nowhere to go; the log-only printer "
                   "is gone" % name)
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
            found.extend(_syntax_problems(name, raw))
            found.extend(_progress_problems(name, raw))
            found.extend(_quiet_window_problems(name, raw))
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
