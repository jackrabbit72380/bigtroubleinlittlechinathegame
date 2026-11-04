@echo off
rem ===========================================================================
rem  BIG TROUBLE IN LITTLE CHINA - apply main.zip  (no internet needed)
rem
rem  1. in your browser, download
rem     https://codeload.github.com/jackrabbit72380/bigtroubleinlittlechinathegame/zip/refs/heads/main
rem  2. save the zip in this folder
rem  3. double-click this file
rem
rem  It unpacks that zip, copies data\ chars\ stages\ font\ external\ sound\
rem  over this folder, leaves save\ and the engine alone, and starts the game.
rem  There is no download code here, so nothing can hang on a proxy.
rem ===========================================================================
setlocal
color 0E
cd /d "%~dp0"
title Big Trouble in Little China - apply update

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
if defined ZIP goto unzip
echo   [ ! ]  no main.zip in this folder
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
set "TMP=%~dp0.update-cache"
if not exist "%TMP%" mkdir "%TMP%"
if exist "%TMP%\unpack" rd /s /q "%TMP%\unpack"
mkdir "%TMP%\unpack" 2>nul
where tar >nul 2>nul
if errorlevel 1 goto unzip_ps
tar -xf "%ZIP%" -C "%TMP%\unpack"
goto unpacked

:unzip_ps
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force -LiteralPath '%ZIP%' -DestinationPath '%TMP%\unpack'"

:unpacked
set "SRC="
for /d %%D in ("%TMP%\unpack\*") do set "SRC=%%~fD"
if not defined SRC goto badzip
echo.
echo   [ 2/3 ]  copying the game files over this folder
for %%F in (data chars stages font external sound) do (
  if exist "%SRC%\%%F" echo            %%F
  if exist "%SRC%\%%F" robocopy "%SRC%\%%F" "%~dp0%%F" /E /NFL /NDL /NJH /NJS /NP >nul
)
if not exist "%SRC%\config.ini" goto copied
copy /Y "%SRC%\config.ini" "%~dp0config.ini" >nul
if not exist "%~dp0save" mkdir "%~dp0save" 2>nul
if not exist "%~dp0save\config.ini" copy /Y "%SRC%\config.ini" "%~dp0save\config.ini" >nul

:copied
echo.
findstr /c:"bg1.spr = 20,0" "%~dp0data\fight.def" >nul 2>nul
if errorlevel 1 echo   HUD    : OLD - the copy did not land
if not errorlevel 1 echo   HUD    : dragon - back is health, belly is audacity
echo.
if not defined EXE goto noexe
echo   [ 3/3 ]  starting the game
echo.
"%EXE%" -config "save\config.ini"
echo.
echo   the game has closed.
echo.
pause
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
