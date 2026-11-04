@echo off
rem ===========================================================================
rem  Update and Play - one double-click, newest files
rem
rem  Put this file in the game folder you already play from: the one with
rem  BigTroubleInLittleChinaTheGame.exe (or Ikemen_GO.exe) in it. Each run:
rem
rem    1. fetches whatever is newest on main - with git if it is installed
rem       (small, fast updates), otherwise as a single zip download
rem    2. copies data\ chars\ stages\ font\ external\ sound\ over this folder
rem    3. leaves your save\ folder and the engine files exactly as they are
rem    4. tells you which HUD is in the files it just copied
rem    5. starts the game
rem
rem  Nothing to install, nothing to copy by hand.
rem ===========================================================================
setlocal
cd /d "%~dp0"

set "EXE="
if exist "BigTroubleInLittleChinaTheGame.exe" set "EXE=BigTroubleInLittleChinaTheGame.exe"
if not defined EXE if exist "Ikemen_GO.exe" set "EXE=Ikemen_GO.exe"
if not defined EXE (
  echo.
  echo This file belongs in your game folder - the one that has
  echo BigTroubleInLittleChinaTheGame.exe in it.
  echo Copy it there and run it again.
  echo.
  pause
  exit /b 1
)

set "CACHE=%~dp0.update-cache"
if not exist "%CACHE%" mkdir "%CACHE%"
set "SRC="
set "WHICH="

where git >nul 2>nul
if not errorlevel 1 goto usegit
goto usezip

:usegit
if not exist "%CACHE%\repo\.git" (
  echo First run: fetching the game files, this takes a minute ...
  git clone --depth 1 https://github.com/jackrabbit72380/bigtroubleinlittlechinathegame.git "%CACHE%\repo" >nul 2>nul
) else (
  echo Checking for new commits ...
  git -C "%CACHE%\repo" fetch --depth 1 origin main >nul 2>nul
  git -C "%CACHE%\repo" reset --hard origin/main >nul 2>nul
)
if exist "%CACHE%\repo\data\fight.def" set "SRC=%CACHE%\repo"
if not defined SRC (
  echo Git could not fetch the files - falling back to the zip download.
  goto usezip
)
set "WHICH=git"
goto sync

:usezip
echo Downloading the newest files ^(one zip, no git needed^) ...
curl -L --fail --silent --show-error -o "%CACHE%\main.zip" "https://codeload.github.com/jackrabbit72380/bigtroubleinlittlechinathegame/zip/refs/heads/main"
if errorlevel 1 (
  echo.
  echo Could not download the files. Check the connection and run this again,
  echo or install Git for Windows to get small incremental updates instead.
  echo.
  pause
  exit /b 1
)
if exist "%CACHE%\unpack" rd /s /q "%CACHE%\unpack"
mkdir "%CACHE%\unpack"
where tar >nul 2>nul
if not errorlevel 1 goto untar
powershell -NoProfile -Command "Expand-Archive -Force -LiteralPath '%CACHE%\main.zip' -DestinationPath '%CACHE%\unpack'"
goto unpacked
:untar
tar -xf "%CACHE%\main.zip" -C "%CACHE%\unpack"
:unpacked
for /d %%D in ("%CACHE%\unpack\*") do set "SRC=%%~fD"
if not defined SRC (
  echo.
  echo The download unpacked to nothing. Delete "%CACHE%" and try again.
  echo.
  pause
  exit /b 1
)
set "WHICH=zip"
goto sync

:sync
echo Copying the game files over this folder ...
for %%F in (data chars stages font external sound) do (
  if exist "%SRC%\%%F" (
    echo   %%F
    xcopy "%SRC%\%%F" "%~dp0%%F" /E /I /Y /Q >nul
  )
)
if exist "%SRC%\config.ini" copy /Y "%SRC%\config.ini" "%~dp0config.ini" >nul 2>nul
if not exist "%~dp0save" mkdir "%~dp0save" 2>nul
if not exist "%~dp0save\config.ini" if exist "%SRC%\config.ini" copy /Y "%SRC%\config.ini" "%~dp0save\config.ini" >nul 2>nul

set "VER="
if "%WHICH%"=="git" for /f %%v in ('git -C "%CACHE%\repo" rev-parse --short HEAD 2^>nul') do set "VER=%%v"

echo.
findstr /c:"bg1.spr = 20,0" "%~dp0data\fight.def" >nul 2>nul
if errorlevel 1 (
  echo HUD   : OLD - the copy did not land, tell the dev and keep this window
) else (
  echo HUD   : dragon - back is health, belly is audacity, heads on the yin-yang
)
if defined VER echo Files : main @ %VER%
echo.
echo Starting the game ...
echo.

"%EXE%" -config "save\config.ini"

echo.
echo The game has closed.
pause
