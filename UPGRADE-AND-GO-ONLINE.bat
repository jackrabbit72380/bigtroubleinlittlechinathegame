@echo off
setlocal enableextensions
title Big Trouble in Little China - upgrade and add online play
rem Builds a second folder next to this game: the Ikemen GO nightly engine, the
rem one this screenpack is drawn for, holding this game's characters, stages,
rem sounds, screenpack, mods and *.zss state files. The tagged v1.0.0 cannot
rem load data/system.zss, so it is not used.
rem This game folder is only ever read.
set "SRC=%~dp0"
if "%SRC:~-1%"=="\" set "SRC=%SRC:~0,-1%"
for %%I in ("%SRC%\..\Big Trouble Online") do set "DST=%%~fI"
set "ZIP=%TEMP%\Ikemen_GO-dev-windows.zip"
set "URL=https://github.com/ikemen-engine/Ikemen-GO/releases/download/nightly/Ikemen_GO-dev-windows.zip"

echo.
echo   Your game : %SRC%
echo   New folder: %DST%
echo.
echo   Your game folder is not changed: the new folder gets its own copy.
echo   Needs internet once, for the Ikemen GO nightly engine (about 55 MB).
echo.
pause
if not exist "%DST%" mkdir "%DST%"

if exist "%DST%\Ikemen_GO.exe" goto haveengine
for /d %%D in ("%DST%\*") do if exist "%%D\Ikemen_GO.exe" goto haveengine
echo Downloading the Ikemen GO nightly engine ...
curl -L --fail --retry 2 -o "%ZIP%" "%URL%"
if errorlevel 1 goto dlfail
echo Unpacking ...
tar -xf "%ZIP%" -C "%DST%"
if errorlevel 1 goto dlfail

:haveengine
set "ENGINE="
if exist "%DST%\Ikemen_GO.exe" set "ENGINE=%DST%"
for /d %%D in ("%DST%\*") do if exist "%%D\Ikemen_GO.exe" set "ENGINE=%%D"
if not defined ENGINE goto noexe

echo Copying your game in ...
robocopy "%SRC%\chars"  "%ENGINE%\chars"  /E /NFL /NDL /NJH /NJS /NP >nul
robocopy "%SRC%\stages" "%ENGINE%\stages" /E /NFL /NDL /NJH /NJS /NP >nul
robocopy "%SRC%\sound"  "%ENGINE%\sound"  /E /NFL /NDL /NJH /NJS /NP >nul
robocopy "%SRC%\font"   "%ENGINE%\font"   /E /NFL /NDL /NJH /NJS /NP >nul
robocopy "%SRC%\save"   "%ENGINE%\save"   /E /NFL /NDL /NJH /NJS /NP >nul
robocopy "%SRC%\external\mods" "%ENGINE%\external\mods" /E /NFL /NDL /NJH /NJS /NP >nul
rem data: our screenpack, lifebars, sounds and stage data - but not the engine's
rem *.zss state files, which are written for the same engine.
robocopy "%SRC%\data" "%ENGINE%\data" /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto copyfail

:nopack
echo.
echo Done: %ENGINE%
echo   Start it, then title menu - NETWORK - HOST GAME or JOIN GAME.
echo   Everyone you play with needs the same game and the same engine build.
echo.
start "" "%ENGINE%\Ikemen_GO.exe"
exit /b 0

:dlfail
echo.
echo The engine download or unpack failed. Check the internet and run this again.
pause
exit /b 1
:noexe
echo.
echo Unpacked, but Ikemen_GO.exe was not found under:
echo   %DST%
pause
exit /b 1
:copyfail
echo.
echo Copying your game files failed. Your game folder was not changed.
pause
exit /b 1
:packfail
echo.
echo The lobby pack zip could not be unpacked. Nothing else was changed.
pause
exit /b 1
