@echo off
setlocal enableextensions
title Big Trouble in Little China - upgrade to v1.0.0 and add online play
rem Builds a second folder next to this game: Ikemen GO v1.0.0 (the version the
rem Online Lobby Pack needs) with this game's characters, stages, sounds,
rem screenpack and mods copied in. Then, if the lobby pack zip is in this folder,
rem unpacks it over that build, which is how the pack is installed.
rem This game folder is only ever read.
set "SRC=%~dp0"
if "%SRC:~-1%"=="\" set "SRC=%SRC:~0,-1%"
for %%I in ("%SRC%\..\Big Trouble Online") do set "DST=%%~fI"
set "ZIP=%TEMP%\Ikemen_GO-v1.0.0-windows.zip"
set "URL=https://github.com/ikemen-engine/Ikemen-GO/releases/download/v1.0.0/Ikemen_GO-v1.0.0-windows.zip"

echo.
echo   Your game : %SRC%
echo   New folder: %DST%
echo.
echo   Your game folder is not changed: the new folder gets its own copy.
echo   Needs internet once, for Ikemen GO v1.0.0 (about 40 MB).
echo.
pause
if not exist "%DST%" mkdir "%DST%"

if exist "%DST%\Ikemen_GO.exe" goto haveengine
for /d %%D in ("%DST%\*") do if exist "%%D\Ikemen_GO.exe" goto haveengine
echo Downloading Ikemen GO v1.0.0 ...
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
rem *.zss state files, which have to stay v1.0.0's own newer copies.
robocopy "%SRC%\data" "%ENGINE%\data" /E /XF *.zss /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto copyfail

set "PACK="
for %%F in ("%SRC%\IkemenGO-OnlineLobbyPack*.zip") do if exist "%%~fF" set "PACK=%%~fF"
if not defined PACK goto nopack
echo Installing the Online Lobby Pack ...
tar -xf "%PACK%" -C "%ENGINE%"
if errorlevel 1 goto packfail
echo Lobby pack installed.

:nopack
echo.
echo Done: %ENGINE%
echo   Start it, then title menu - NETWORK - ONLINE LOBBY.
echo   Everyone you play with needs the same game and the same lobby pack version.
echo.
start "" "%ENGINE%\Ikemen_GO.exe"
exit /b 0

:dlfail
echo.
echo The v1.0.0 download or unpack failed. Check the internet and run this again.
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
