@echo off
rem ===========================================================================
rem  BIG TROUBLE IN LITTLE CHINA - apply main.zip  (no internet needed)
rem
rem  1. in your browser, download
rem     https://codeload.github.com/jackrabbit72380/bigtroubleinlittlechinathegame/zip/refs/heads/main
rem  2. save the zip in this folder
rem  3. double-click this file
rem
rem  Windows tools are called by full path: a Git for Windows install that puts
rem  its usr\bin on PATH shadows System32, and its tar reads H:\... as a remote
rem  host ("Cannot connect to H:").
rem ===========================================================================
setlocal EnableExtensions DisableDelayedExpansion
color 0E
cd /d "%~dp0"
title Big Trouble in Little China - apply update

set "SYS=%SystemRoot%\System32"
set "TAR=%SYS%\tar.exe"
set "FINDSTR=%SYS%\findstr.exe"
set "TASKLIST=%SYS%\tasklist.exe"
set "ROBOCOPY=%SYS%\robocopy.exe"
set "POWERSHELL=%SYS%\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%TAR%" set "TAR="
if not exist "%POWERSHELL%" set "POWERSHELL="

echo.
echo   ==============================================================
echo.
echo        B I G   T R O U B L E   I N   L I T T L E   C H I N A
echo.
echo                    a p p l y   u p d a t e
echo.
echo   ==============================================================
echo.
echo   folder : %~dp0
echo.

set "EXE="
if exist "BigTroubleInLittleChinaTheGame.exe" set "EXE=BigTroubleInLittleChinaTheGame.exe"
if not defined EXE if exist "Ikemen_GO.exe" set "EXE=Ikemen_GO.exe"

set "ZIP="
if exist "%~dp0main.zip" set "ZIP=%~dp0main.zip"
if not defined ZIP if exist "%~dp0bigtroubleinlittlechinathegame-main.zip" set "ZIP=%~dp0bigtroubleinlittlechinathegame-main.zip"
rem a zip the browser dropped in Downloads is used too, newest first
if not defined ZIP call :fromdownloads
if defined ZIP goto unzip
echo   [ ! ]  no zip found
echo.
echo   download it in your browser from:
echo     https://codeload.github.com/jackrabbit72380/bigtroubleinlittlechinathegame/zip/refs/heads/main
echo   save it here, then run this file again
echo.
pause
exit /b 1

:unzip
echo   [ 1/3 ]  unpacking
echo            %ZIP%
set "SRC="
set "TMP=%~dp0.update-cache"
if not exist "%TMP%" mkdir "%TMP%" 2>nul
if exist "%TMP%\unpack" rd /s /q "%TMP%\unpack" >nul 2>&1
mkdir "%TMP%\unpack" 2>nul
if not defined TAR goto unzip_ps
"%TAR%" -xf "%ZIP%" -C "%TMP%\unpack"
if errorlevel 1 goto unzip_ps
goto unpacked

:unzip_ps
if not defined POWERSHELL goto badzip
if exist "%TMP%\unpack" rd /s /q "%TMP%\unpack" >nul 2>&1
mkdir "%TMP%\unpack" 2>nul
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force -LiteralPath '%ZIP%' -DestinationPath '%TMP%\unpack'"

:unpacked
for /d %%D in ("%TMP%\unpack\*") do set "SRC=%%~fD"
if not defined SRC goto badzip
echo.
echo   [ 2/3 ]  copying the game files over this folder
for %%F in (data chars stages font external sound) do (
  if exist "%SRC%\%%F" echo            %%F
  if exist "%SRC%\%%F" "%ROBOCOPY%" "%SRC%\%%F" "%~dp0%%F" /E /NFL /NDL /NJH /NJS /NP >nul
)
if not exist "%SRC%\config.ini" goto copied
copy /Y "%SRC%\config.ini" "%~dp0config.ini" >nul
if not exist "%~dp0save" mkdir "%~dp0save" 2>nul
if not exist "%~dp0save\config.ini" copy /Y "%SRC%\config.ini" "%~dp0save\config.ini" >nul

:copied
echo.
"%FINDSTR%" /c:"bg1.spr = 20,0" "%~dp0data\fight.def" >nul 2>nul
if errorlevel 1 echo   HUD    : OLD - the copy did not land
if not errorlevel 1 echo   HUD    : dragon - back is health, belly is audacity
"%FINDSTR%" /c:"'Ctrl+Alt+1..9'" "%~dp0external\mods\devhelp.lua" >nul 2>nul
if errorlevel 1 echo   keys   : OLD developer keys screen
if not errorlevel 1 echo   keys   : two columns, no scrolling
echo.
if not defined EXE goto noexe
echo   [ 3/3 ]  starting the game
echo.
start "" "%EXE%" -config "save\config.ini"
echo   started. have fun.
call :sleep 3
exit /b 0

:noexe
echo   no game exe here, so the files were copied but the game was not started
echo.
pause
exit /b 0

:badzip
echo.
echo   could not unpack that zip - it is probably an incomplete download.
echo   delete it, download it again, and run this file.
echo.
pause
exit /b 1

:sleep
set /a "P=%~1+1"
"%SYS%\ping.exe" -n %P% 127.0.0.1 >nul 2>&1
exit /b 0

:fromdownloads
for /f "delims=" %%Z in ('dir /b /a-d /o-d "%USERPROFILE%\Downloads\*bigtrouble*.zip" 2^>nul') do (
  if not defined ZIP set "ZIP=%USERPROFILE%\Downloads\%%Z"
)
if defined ZIP echo            using %ZIP%
exit /b 0
