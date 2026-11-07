"""Prove the launcher checks catch what they exist for.

tools/check_launchers.py reads the batch files instead of running them, because
this repo cannot run cmd. A rule that is only ever pointed at good files proves
nothing: the updater's muzzle count shipped a line every existing check passed
and cmd could not parse. This feeds each construct cmd mis-parses to the checker
and asserts it is caught, feeds the correct form and asserts it is not, then
checks the launchers in the tree and the count's own guards.

Run:  python3 tools/test_launchers.py
"""

from __future__ import annotations

import base64
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UPDATER = "Update and Play.bat"

_spec = importlib.util.spec_from_file_location(
    "check_launchers", os.path.join(HERE, "check_launchers.py"))
checker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(checker)


def script(*lines):
    """A batch body, CRLF terminated like the files this repo ships."""
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")


# what cmd acts on before a command runs; every one has to be reported
TRAPS = [
    ("a sign with no partner", ('set "X=a%b"',)),
    ("a sign against the next variable",
     ('set /p "=%ESC%[u%GCOL%G| %PCT3%%%ESC%[K" <nul',)),
    ("a caret at the end of a line", ("echo one ^", 'set "X=1"')),
    ("a caret inside quotes", ('echo "a ^| b"',)),
    ("a caret before plain text", ("echo a ^b c",)),
    ("an operator in a for command",
     ("for /f \"delims=\" %%v in ('dir /b 2>nul') do echo %%v",)),
    ("a quote left open after set", ('set "ESC=\x1b',)),
    ("a label defined twice", (":done", "exit /b 0", ":done", "exit /b 0")),
    ("a trailing space", ("echo x ",)),
    ("an append inside a for body", ('for /l %%P in (1,1,3) do set "X=%X%a"',)),
    ("a literal ! with delayed expansion",
     ("setlocal EnableDelayedExpansion", "echo a!b!")),
    ("a path passed to call unquoted", ("call :log folder %~dp0  exe %EXE%",)),
]

# the same things written the way cmd reads them: none may be reported
CLEAN = [
    ("arguments and modifiers",
     ('set "X=%~dp0"', 'set "Y=%~f0"', 'set "Z=%1"', 'set "W=%*"')),
    ("substitution that holds a space",
     ('set "GW=%GW: =%"', 'set "U=%REL:\\=/%"')),
    ("quoted substitution",
     ('set "A=%ASHA:</id>=%"', 'set RSHA=%RSHA:"=%')),
    ("an escaped sign",
     ("echo 100%%", 'set "PCT=%%"', 'set "PCTX=%GNUM%%PCT%"')),
    ("an escaped operator in art", ("echo    ..._...^|..____, ,",)),
    ("an escaped redirect in a for command",
     ("for /f \"delims=\" %%v in ('dir /b 2^>nul') do echo %%v",)),
    ("a quoted path passed to call", ('call :log folder "%~dp0"  exe %EXE%',)),
    ("a quoted operator", ('echo "a | b > c"',)),
    ("a padded count", ('if %GNUM% LSS 10 set "GNUM=  %GNUM%"',)),
]


def encoded(text):
    """A -EncodedCommand line holding exactly this PowerShell."""
    return ("-NoProfile -ExecutionPolicy Bypass -EncodedCommand "
            + base64.b64encode(text.encode("utf-16-le")).decode())


# PowerShell the launcher hands over: decoded and read, never run
PS_TRAPS = [
    ("an encoded helper that is not base64", ("-EncodedCommand A",)),
    ("an encoded helper that is not UTF-16LE", ("-EncodedCommand AA==",)),
    ("an encoded helper with a bracket left open",
     (encoded("if ($x) { Write-Host 'hi'"),)),
    ("a double quote inside a -Command body",
     ('-Command "Write-Host ""hi"""',)),
    ("a bracket left open in a -Command body", ('-Command "$x = @(1, 2"',)),
    ("a quote left open in a -Command body", ("-Command \"Write-Host 'hi\"",)),
    ("a path in single quotes in a -Command body",
     ('-Command "Get-Content -LiteralPath \'%CACHE%\\git.log\'"',)),
    ("a generated helper with a block left open",
     ('>> "%VPS%" echo if ($a -gt 0) {',)),
]

PS_CLEAN = [
    ("a balanced encoded helper", (encoded("if ($x) { Write-Host 'hi' }"),)),
    ("a balanced -Command body",
     ('-Command "Get-Content -LiteralPath \'%CQ%\\git.log\' -Tail 8"',)),
    ("a script path built from a character",
     ('-Command "Start-Process -FilePath \'cmd.exe\' -ArgumentList \'/c\',([char]34 + \'%RUNQ%\' + [char]34)"',)),
    ("a generated helper with balanced blocks",
     ('>> "%VPS%" echo foreach ($x in @(1, 2)) { Write-Host $x }',)),
]

# edits that would bring the muzzle-count bug back: each has to be reported
MUTATIONS = [
    ("the sign is not made on its own",
     b'set "PCT=%%"\r\n', b'', "per cent sign is not made once"),
    ("the count is padded through call",
     b'if %GNUM% LSS 10 set "GNUM=  %GNUM%"\r\n',
     b'call set "GNUM=%%GNUM:~-3%%"\r\n', "not padded by comparison"),
    ("the count pairs signs in the source",
     b'set "PCTX=%GNUM%%PCT%"',
     b'call set "PCTX=%%GNUM%%PCT%"', "padded as digits"),
    # breaking only the line that sets the sign left gunredraw's fallback
    # intact, and the guard used to accept the file on that alone
    ("the sign is broken where it is set",
     b'\r\nset "PCT=%%"\r\n', b'\r\ncall set "PCT=%%PCT%%"\r\n', "not made once"),
]


# ways the launcher could lose itself: each has to be reported
SELFUPDATE = [
    ("the launcher is written over in place",
     b'move /Y "%STAGE%" "%~f0"', b'copy /Y "%NEWB%" "%~f0"',
     "writes over the file this window"),
    ("the last line the file ships with is gone",
     b'\r\nrem btilc-launcher-end\r\n', b'\r\n',
     "does not end with"),
    ("the refresh needs curl alone",
     b'if not defined CURL if not defined POWERSHELL exit /b 0',
     b'if not defined CURL exit /b 0', "curl.exe"),
    ("a download is not checked for its last line",
     b'"%FINDSTR%" /c:"btilc-launcher-end" "%NEWB%" >nul 2>&1\r\n', b'',
     "stopped half way"),
    ("a refresh closes the window and restarts",
     b'exit /b 0\r\n:selfupdate_ps', b'start "" "%~f0" --updated\r\nexit /b 0\r\n:selfupdate_ps',
     "costs the run it interrupted"),
]

# a run that ends without a word: the file has to outlive its own last line
SILENT = [
    ("a branch that reaches the last line closes the window",
     b'call "%~f0" --body %*', b'call "%~f0"',
     "closes the window with nothing said"),
    ("the early-end report does not wait",
     b':stopped_tail\r\necho.\r\necho   saved as  %LOG%\r\necho.\r\npause',
     b':stopped_tail\r\necho.\r\necho   saved as  %LOG%\r\necho.',
     "does not wait for a key"),
]

# the log has to be open before the run can fail: it is opened ahead of the
# pistol now, and the step it writes is the proof the window got that far
FIRSTLOG = [
    ("nothing is logged before the pistol",
     b'call :log step 1 folder "%~dp0"\r\n', b'',
     "cannot say where it stopped"),
    ("the log is opened again after the pistol",
     b'call :gun\r\n',
     b'call :gun\r\n>"%LOG%" echo [%DATE% %TIME%] launcher start  arg=%1 2>nul\r\n',
     "is thrown away"),
]

# the progress paint must not redraw the pistol
PAINT = [
    ("the progress keeps redrawing the pistol",
     b':gaugeone_plain_title\r\n',
     b'call :gunredraw %~1 1\r\n:gaugeone_plain_title\r\n',
     "stops the batch dead"),
    ("the no-cursor path prints no number",
     b'echo   ... %~1 percent\r\n', b'',
     "shows nothing"),
]

REPAIR = [
    ("the launcher repair is gone",
     b"call :fixlauncher\r\n", b"", "never called"),
    ("the repair installs an unchecked download",
     b'"%FINDSTR%" /c:"btilc-launcher-end" "%NEWL%" >nul 2>&1\r\n', b'',
     "not checked for its last"),
]


def main():
    failures = 0
    for label, body in TRAPS:
        found = checker._syntax_problems("probe.bat", script(*body))
        ok = bool(found)
        print("  %s %-34s %s" % ("ok " if ok else "FAIL", label,
                                 "" if ok else "not caught"))
        failures += 0 if ok else 1
    for label, body in CLEAN:
        found = checker._syntax_problems("probe.bat", script(*body))
        ok = not found
        print("  %s %-34s %s" % ("ok " if ok else "FAIL", label,
                                 "" if ok else found[0][:60]))
        failures += 0 if ok else 1

    for label, body in PS_TRAPS:
        found = checker._powershell_problems("probe.bat", script(*body))
        ok = bool(found)
        print("  %s %-34s %s" % ("ok " if ok else "FAIL", label,
                                 "" if ok else "not caught"))
        failures += 0 if ok else 1
    for label, body in PS_CLEAN:
        found = checker._powershell_problems("probe.bat", script(*body))
        ok = not found
        print("  %s %-34s %s" % ("ok " if ok else "FAIL", label,
                                 "" if ok else found[0][:60]))
        failures += 0 if ok else 1

    path = os.path.join(ROOT, UPDATER)
    with open(path, "rb") as handle:
        real = handle.read()
    for label, old, new, want in MUTATIONS:
        if old not in real:
            print("  FAIL %-34s the shipped line is gone" % label)
            failures += 1
            continue
        found = checker._progress_problems(UPDATER, real.replace(old, new))
        ok = any(want in problem for problem in found)
        print("  %s %-34s %s" % ("ok " if ok else "FAIL", label,
                                 "" if ok else "no guard fired"))
        failures += 0 if ok else 1

    for label, old, new, want in SELFUPDATE:
        if old not in real:
            print("  FAIL %-34s the shipped line is gone" % label)
            failures += 1
            continue
        found = checker._selfupdate_problems(UPDATER, real.replace(old, new))
        ok = any(want in problem for problem in found)
        print("  %s %-34s %s" % ("ok " if ok else "FAIL", label,
                                 "" if ok else "no guard fired"))
        failures += 0 if ok else 1

    for label, old, new, want in SILENT:
        if old not in real:
            print("  FAIL %-34s the shipped line is gone" % label)
            failures += 1
            continue
        found = checker._silent_end_problems(UPDATER, real.replace(old, new))
        ok = any(want in problem for problem in found)
        print("  %s %-34s %s" % ("ok " if ok else "FAIL", label,
                                 "" if ok else "no guard fired"))
        failures += 0 if ok else 1

    for label, old, new, want in PAINT:
        if old not in real:
            print("  FAIL %-34s the shipped line is gone" % label)
            failures += 1
            continue
        found = checker._paint_problems(UPDATER, real.replace(old, new))
        ok = any(want in problem for problem in found)
        print("  %s %-34s %s" % ("ok " if ok else "FAIL", label,
                                 "" if ok else "no guard fired"))
        failures += 0 if ok else 1

    for label, old, new, want in FIRSTLOG:
        if old not in real:
            print("  FAIL %-34s the shipped line is gone" % label)
            failures += 1
            continue
        found = checker._firstlog_problems(UPDATER, real.replace(old, new))
        ok = any(want in problem for problem in found)
        print("  %s %-34s %s" % ("ok " if ok else "FAIL", label,
                                 "" if ok else "no guard fired"))
        failures += 0 if ok else 1

    with open(os.path.join(ROOT, "Apply main.zip.bat"), "rb") as handle:
        applier = handle.read()
    for label, old, new, want in REPAIR:
        if old not in applier:
            print("  FAIL %-34s the shipped line is gone" % label)
            failures += 1
            continue
        found = checker._launcherrepair_problems("Apply main.zip.bat",
                                                 applier.replace(old, new))
        ok = any(want in problem for problem in found)
        print("  %s %-34s %s" % ("ok " if ok else "FAIL", label,
                                 "" if ok else "no guard fired"))
        failures += 0 if ok else 1

    found = checker.problems(ROOT)
    print("  %s %-34s %s" % ("ok " if not found else "FAIL",
                             "the launchers in the tree",
                             "" if not found else found[0][:60]))
    failures += 0 if not found else 1

    if failures:
        print("\nthe launcher checks regressed in %d place(s)" % failures)
        return 1
    print("\nevery cmd trap is caught, the correct forms are left alone, and the "
          "launchers in the tree are clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
