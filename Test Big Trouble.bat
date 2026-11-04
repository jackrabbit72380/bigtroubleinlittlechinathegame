@echo off
rem Double-click this to play the newest fixes in this folder.
rem
rem It pulls the latest commits, then runs tools\test_local.py, which downloads
rem the engine once into .test\engine, keeps this folder's own data\ and chars\
rem in front of it and starts the game. Nothing is copied by hand, and the game
rem always loads this folder's files, so a fix can be tried in one step.
rem
rem   "Test Big Trouble.bat" --no-pull      just play what is on disk
rem   "Test Big Trouble.bat" --no-launch    set up only
rem   "Test Big Trouble.bat" -- 2560 1440   render size for this run
setlocal
cd /d "%~dp0"

set "PY=py -3"
%PY% --version >nul 2>nul || set "PY=python"
%PY% --version >nul 2>nul || set "PY=python3"
%PY% --version >nul 2>nul || (
  echo.
  echo Python 3 is needed for this launcher: https://www.python.org/downloads/windows/
  echo In the installer, tick "Add python.exe to PATH", then run this file again.
  echo.
  pause
  exit /b 1
)

%PY% "tools\test_local.py" %*

echo.
pause
