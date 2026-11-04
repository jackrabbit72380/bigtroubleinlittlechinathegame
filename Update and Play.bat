@echo off
rem ===========================================================================
rem  Update and Play - one double-click, newest files
rem
rem  Put this file in the game folder you already play from: the one with
rem  BigTroubleInLittleChinaTheGame.exe (or Ikemen_GO.exe) in it. Each run:
rem
rem    1. fetches whatever is newest on main - git if it works, otherwise one
rem       zip, tried three ways until a download succeeds
rem    2. copies data\ chars\ stages\ font\ external\ sound\ over this folder
rem    3. leaves your save\ folder and the engine files exactly as they are
rem    4. says which HUD is in the files it copied, then starts the game
rem
rem  If every download fails, save the zip yourself next to this file as
rem  main.zip and run this again - it uses that file and skips the network.
rem ===========================================================================
setlocal
cd /d "%~dp0"

echo Update and Play v3 - newest files, one double-click
echo launcher : %~f0
echo folder   : %~dp0
echo.

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

rem Something on this machine points git and curl at /usr/ssl/certs/ca-bundle.crt,
rem an MSYS path that only exists inside Git Bash, so both fail before they
rem connect. Clearing the variables and ignoring the system gitconfig for this
rem window gives git its own correct bundle path.
set "GIT_SSL_CAINFO="
set "CURL_CA_BUNDLE="
set "SSL_CERT_FILE="
set "GIT_CONFIG_NOSYSTEM=1"

set "CACHE=%~dp0.update-cache"
if not exist "%CACHE%" mkdir "%CACHE%"
set "ZIPURL=https://codeload.github.com/jackrabbit72380/bigtroubleinlittlechinathegame/zip/refs/heads/main"
set "GITURL=https://github.com/jackrabbit72380/bigtroubleinlittlechinathegame.git"
set "SRC="
set "WHICH="
set "ZIPSIZE="
set "ZIPOK=0"

if exist "%~dp0main.zip" goto manualzip
if exist "%~dp0bigtroubleinlittlechinathegame-main.zip" goto manualzip2
where git >nul 2>nul
if errorlevel 1 goto download
goto trygit

:manualzip
echo Using main.zip from this folder, no download needed.
copy /Y "%~dp0main.zip" "%CACHE%\main.zip" >nul
goto havezip

:manualzip2
echo Using bigtroubleinlittlechinathegame-main.zip from this folder.
copy /Y "%~dp0bigtroubleinlittlechinathegame-main.zip" "%CACHE%\main.zip" >nul
goto havezip

:trygit
echo Checking for new files with git ...
if exist "%CACHE%\repo\.git" goto gitpull
if exist "%CACHE%\repo" rd /s /q "%CACHE%\repo"
git clone --depth 1 "%GITURL%" "%CACHE%\repo" >"%CACHE%\git.log" 2>&1
goto gitdone

:gitpull
git -C "%CACHE%\repo" fetch --depth 1 origin main >"%CACHE%\git.log" 2>&1
git -C "%CACHE%\repo" reset --hard origin/main >>"%CACHE%\git.log" 2>&1

:gitdone
if not exist "%CACHE%\repo\data\fight.def" goto gitfail
set "SRC=%CACHE%\repo"
set "WHICH=git"
goto sync

:gitfail
echo.
echo Git is installed but could not fetch the files. It said:
if exist "%CACHE%\git.log" type "%CACHE%\git.log"
echo.
echo Trying the zip download instead.
goto download

:download
echo Downloading the newest files ...
if exist "%CACHE%\main.zip" del /q "%CACHE%\main.zip"
echo This is a one-off download of about 190 MB and can take a few minutes
echo on a slow connection. A progress bar appears in a moment.
echo.
if not exist "%SystemRoot%\System32\curl.exe" goto dl_powershell
echo   trying Windows curl ...
echo   "%SystemRoot%\System32\curl.exe" -L --fail --progress-bar -o main.zip "%ZIPURL%"
"%SystemRoot%\System32\curl.exe" -L --fail --progress-bar --connect-timeout 30 -o "%CACHE%\main.zip" "%ZIPURL%"
call :zipok
if "%ZIPOK%"=="1" goto havezip

:dl_powershell
where powershell >nul 2>nul
if errorlevel 1 goto dl_certutil
echo   trying Windows PowerShell ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -UseBasicParsing -TimeoutSec 900 -Uri '%ZIPURL%' -OutFile '%CACHE%\main.zip'; exit 0 } catch { Write-Host ('     ' + $_.Exception.Message); exit 1 }"
call :zipok
if "%ZIPOK%"=="1" goto havezip

:dl_certutil
if exist "%CACHE%\main.zip" del /q "%CACHE%\main.zip"
where certutil >nul 2>nul
if errorlevel 1 goto dl_curl
echo   trying certutil ...
certutil -urlcache -split -f "%ZIPURL%" "%CACHE%\main.zip" >nul 2>&1
call :zipok
if "%ZIPOK%"=="1" goto havezip

:dl_curl
if exist "%CACHE%\main.zip" del /q "%CACHE%\main.zip"
where curl >nul 2>nul
if errorlevel 1 goto downloadfailed
echo   trying curl ...
curl -L --fail --silent --show-error --output "%CACHE%\main.zip" "%ZIPURL%"
call :zipok
if "%ZIPOK%"=="1" goto havezip
goto downloadfailed

:havezip
echo Unpacking ...
if exist "%CACHE%\unpack" rd /s /q "%CACHE%\unpack"
mkdir "%CACHE%\unpack" 2>nul
where powershell >nul 2>nul
if errorlevel 1 goto unzip_tar
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force -LiteralPath '%CACHE%\main.zip' -DestinationPath '%CACHE%\unpack'"
goto unpacked

:unzip_tar
where tar >nul 2>nul
if errorlevel 1 goto downloadfailed
tar -xf "%CACHE%\main.zip" -C "%CACHE%\unpack"

:unpacked
for /d %%D in ("%CACHE%\unpack\*") do set "SRC=%%~fD"
if not defined SRC goto downloadfailed
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
if not "%WHICH%"=="git" goto skipver
for /f %%v in ('git -C "%CACHE%\repo" rev-parse --short HEAD 2^>nul') do set "VER=%%v"

:skipver
echo.
findstr /c:"bg1.spr = 20,0" "%~dp0data\fight.def" >nul 2>nul
if errorlevel 1 echo HUD   : OLD - the copy did not land, tell the dev and keep this window
if not errorlevel 1 echo HUD   : dragon - back is health, belly is audacity, heads on the yin-yang
if defined VER echo Files : main @ %VER%
if not defined VER echo Files : main from zip
echo.
echo Starting the game ...
echo.
"%EXE%" -config "save\config.ini"
echo.
echo The game has closed.
pause
exit /b 0

:downloadfailed
echo.
echo Could not get the files automatically.
echo.
echo The reliable fix: open this link in your browser and save the file
echo as main.zip next to this file, then run this again:
echo.
echo    %ZIPURL%
echo.
echo It will use that zip and never touch the network.
echo.
pause
exit /b 1

:zipok
set "ZIPOK=0"
if not exist "%CACHE%\main.zip" exit /b 0
for %%A in ("%CACHE%\main.zip") do set "ZIPSIZE=%%~zA"
if not defined ZIPSIZE exit /b 0
if %ZIPSIZE% LSS 1000000 exit /b 0
set "ZIPOK=1"
exit /b 0
