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
