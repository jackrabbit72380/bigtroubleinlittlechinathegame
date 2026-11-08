@echo off
setlocal enableextensions
title Big Trouble in Little China - set up online play
rem Copies this game into a folder holding the online (Nakama) engine, next to
rem this one. This game folder is only ever read: nothing in it is changed.
set "SRC=%~dp0"
if "%SRC:~-1%"=="\" set "SRC=%SRC:~0,-1%"
for %%I in ("%SRC%\..\Big Trouble Online") do set "DST=%%~fI"
set "ZIP=%TEMP%\ikgo-nakama-windows.zip"
set "URL=https://github.com/RollinJay/IkemenGo-Nakama/releases/download/nightly/Ikemen_GO-dev-windows.zip"

echo.
echo   Your game : %SRC%
echo   New folder: %DST%
echo.
echo   Your game folder is not changed. The new folder gets its own copy.
echo   It needs internet once, to download the online engine (about 30 MB).
echo.
pause
if not exist "%DST%" mkdir "%DST%"

if exist "%DST%\Ikemen_GO.exe" goto haveengine
echo Downloading the online engine ...
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

echo Copying your characters, stages, sounds, screenpack and settings ...
robocopy "%SRC%\chars"  "%ENGINE%\chars"  /E /NFL /NDL /NJH /NJS /NP >nul
robocopy "%SRC%\stages" "%ENGINE%\stages" /E /NFL /NDL /NJH /NJS /NP >nul
robocopy "%SRC%\sound"  "%ENGINE%\sound"  /E /NFL /NDL /NJH /NJS /NP >nul
robocopy "%SRC%\font"   "%ENGINE%\font"   /E /NFL /NDL /NJH /NJS /NP >nul
robocopy "%SRC%\save"   "%ENGINE%\save"   /E /NFL /NDL /NJH /NJS /NP >nul
robocopy "%SRC%\external\mods" "%ENGINE%\external\mods" /E /NFL /NDL /NJH /NJS /NP >nul
rem data: everything of ours except the engine's *.zss rules, which must stay the
rem online engine's own newer copies.
robocopy "%SRC%\data" "%ENGINE%\data" /E /XF *.zss /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto copyfail

echo.
echo Done. The online build is here:
echo   %ENGINE%
echo.
echo Next: start it, then title menu - NETWORK. See ONLINE-SETUP.md for the server.
echo.
start "" "%ENGINE%\Ikemen_GO.exe"
exit /b 0

:dlfail
echo.
echo The download or unpack failed. Check the internet connection and run this again.
pause
exit /b 1
:noexe
echo.
echo The engine was unpacked, but Ikemen_GO.exe was not found under:
echo   %DST%
pause
exit /b 1
:copyfail
echo.
echo Copying the game files failed. Nothing in your game folder was changed.
pause
exit /b 1
