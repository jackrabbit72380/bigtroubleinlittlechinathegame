@echo off
rem ===========================================================================
rem  BIG TROUBLE IN LITTLE CHINA - updater
rem
rem  Put this file in the game folder you already play from: the one with
rem  BigTroubleInLittleChinaTheGame.exe (or Ikemen_GO.exe) in it.
rem
rem  Each run: finds the newest files on main, copies data\ chars\ stages\
rem  font\ external\ sound\ over this folder, leaves save\ and the engine
rem  alone, says which HUD it copied, and starts the game.
rem
rem  No internet tricks needed: save the repo zip here as main.zip and this
rem  uses it without touching the network.
rem ===========================================================================
setlocal
color 0E
cd /d "%~dp0"
title Big Trouble in Little China - updater

echo.
echo   ==============================================================
echo.
echo        B I G   T R O U B L E   I N   L I T T L E   C H I N A
echo.
echo                        t h e   g a m e
echo                        updater  v5
echo.
echo   ==============================================================
echo.
echo   folder : %~dp0
echo.

set "EXE="
if exist "BigTroubleInLittleChinaTheGame.exe" set "EXE=BigTroubleInLittleChinaTheGame.exe"
if not defined EXE if exist "Ikemen_GO.exe" set "EXE=Ikemen_GO.exe"
if not defined EXE goto wrongfolder

rem Git and curl on this machine may point at /usr/ssl/certs/ca-bundle.crt, an
rem MSYS path that does not exist on Windows. Clear it for this window only.
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

echo   [ 1/4 ]  looking for the newest files
if exist "%~dp0main.zip" goto manualzip
if exist "%~dp0bigtroubleinlittlechinathegame-main.zip" goto manualzip2
where git >nul 2>nul
if errorlevel 1 goto checkdone
goto trygit

:manualzip
echo            using main.zip from this folder - no download needed
copy /Y "%~dp0main.zip" "%CACHE%\main.zip" >nul
goto havezip

:manualzip2
echo            using bigtroubleinlittlechinathegame-main.zip from this folder
copy /Y "%~dp0bigtroubleinlittlechinathegame-main.zip" "%CACHE%\main.zip" >nul
goto havezip

:trygit
echo            checking with git, which only fetches what changed
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
echo            git could not fetch. It said:
if exist "%CACHE%\git.log" type "%CACHE%\git.log"
echo            falling back to the zip download
goto download

:download
echo.
echo   [ 2/4 ]  downloading the files
echo            one-off download of about 190 MB
echo.
echo            checking this window can reach GitHub ...
"%SystemRoot%\System32\curl.exe" -sS -o nul --max-time 20 "https://raw.githubusercontent.com/jackrabbit72380/bigtroubleinlittlechinathegame/main/README.md"
if errorlevel 1 goto dl_blocked
echo            reachable
goto dl_start

:dl_blocked
echo            NOT reachable - a proxy or antivirus is blocking this window.
echo.
echo            Use the browser instead:
echo              1. download  https://codeload.github.com/jackrabbit72380/bigtroubleinlittlechinathegame/zip/refs/heads/main
echo              2. save the zip in this folder
echo              3. run "Apply main.zip.bat"
echo.
pause
exit /b 1

:dl_start
if not exist "%SystemRoot%\System32\curl.exe" goto dl_powershell
if exist "%CACHE%\main.zip" del /q "%CACHE%\main.zip"
if exist "%CACHE%\curl.done" del /q "%CACHE%\curl.done"
>"%CACHE%\run.bat" echo @echo off
>>"%CACHE%\run.bat" echo "%SystemRoot%\System32\curl.exe" -sS -L --fail --connect-timeout 30 --speed-time 60 --speed-limit 1024 -o "%CACHE%\main.zip" "%ZIPURL%" 2^>"%CACHE%\curl.err"
>>"%CACHE%\run.bat" echo echo %%ERRORLEVEL%%^>"%CACHE%\curl.done"
echo            working - this counter updates every 2 seconds
start /b "" "%CACHE%\run.bat"
set "SECS=0"
set "MB=0"

:dl_poll
timeout /t 2 /nobreak >nul
set /a SECS+=2
set "SZ=0"
for %%A in ("%CACHE%\main.zip") do set "SZ=%%~zA"
set /a MB=SZ/1048576
set /a MINS=SECS/60
set /a REST=SECS%%60
set "CLOCK=%MINS%:%REST%"
if %REST% LSS 10 set "CLOCK=%MINS%:0%REST%"
echo            %MB% MB received   -   %CLOCK% elapsed
if exist "%CACHE%\curl.done" goto dl_done
if %SECS% GEQ 1800 goto dl_giveup
goto dl_poll

:dl_done
set "CODE=?"
if exist "%CACHE%\curl.done" set /p CODE=<"%CACHE%\curl.done"
echo.
echo            download finished, exit code %CODE%
call :zipok
if "%ZIPOK%"=="1" goto havezip
if exist "%CACHE%\curl.err" type "%CACHE%\curl.err"
goto dl_powershell

:dl_giveup
echo.
echo            gave up after 30 minutes.
goto dl_powershell

:dl_powershell
where powershell >nul 2>nul
if errorlevel 1 goto dl_certutil
if exist "%CACHE%\main.zip" del /q "%CACHE%\main.zip"
echo            trying Windows PowerShell instead ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -UseBasicParsing -TimeoutSec 900 -Uri '%ZIPURL%' -OutFile '%CACHE%\main.zip'; exit 0 } catch { Write-Host ('           ' + $_.Exception.Message); exit 1 }"
call :zipok
if "%ZIPOK%"=="1" goto havezip

:dl_certutil
where certutil >nul 2>nul
if errorlevel 1 goto downloadfailed
if exist "%CACHE%\main.zip" del /q "%CACHE%\main.zip"
echo            trying certutil ...
certutil -urlcache -split -f "%ZIPURL%" "%CACHE%\main.zip" >nul 2>&1
call :zipok
if "%ZIPOK%"=="1" goto havezip
goto downloadfailed

:havezip
echo.
echo   [ 3/4 ]  copying the game files over this folder
if exist "%CACHE%\unpack" rd /s /q "%CACHE%\unpack"
mkdir "%CACHE%\unpack" 2>nul
where tar >nul 2>nul
if errorlevel 1 goto unzip_ps
tar -xf "%CACHE%\main.zip" -C "%CACHE%\unpack"
goto unpacked

:unzip_ps
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force -LiteralPath '%CACHE%\main.zip' -DestinationPath '%CACHE%\unpack'"

:unpacked
for /d %%D in ("%CACHE%\unpack\*") do set "SRC=%%~fD"
if not defined SRC goto downloadfailed
set "WHICH=zip"
goto sync

:sync
for %%F in (data chars stages font external sound) do (
  if exist "%SRC%\%%F" echo            %%F
  if exist "%SRC%\%%F" robocopy "%SRC%\%%F" "%~dp0%%F" /E /NFL /NDL /NJH /NJS /NP >nul
)
if not exist "%SRC%\config.ini" goto copied
copy /Y "%SRC%\config.ini" "%~dp0config.ini" >nul
if not exist "%~dp0save" mkdir "%~dp0save" 2>nul
if not exist "%~dp0save\config.ini" copy /Y "%SRC%\config.ini" "%~dp0save\config.ini" >nul

:copied
set "VER="
if not "%WHICH%"=="git" goto skipver
for /f %%v in ('git -C "%CACHE%\repo" rev-parse --short HEAD 2^>nul') do set "VER=%%v"

:skipver
echo.
findstr /c:"bg1.spr = 20,0" "%~dp0data\fight.def" >nul 2>nul
if errorlevel 1 echo   HUD    : OLD - the copy did not land
if not errorlevel 1 echo   HUD    : dragon - back is health, belly is audacity
if defined VER echo   files  : main @ %VER%
if not defined VER echo   files  : main, from the zip
echo.
echo   [ 4/4 ]  starting the game
echo.
"%EXE%" -config "save\config.ini"
echo.
echo   the game has closed.
echo.
pause
exit /b 0

:downloadfailed
echo.
echo   could not get the files automatically.
echo.
echo   the reliable route:
echo     1. download this in your browser
echo        https://codeload.github.com/jackrabbit72380/bigtroubleinlittlechinathegame/zip/refs/heads/main
echo     2. save the zip in this folder
echo     3. run "Apply main.zip.bat"
echo.
pause
exit /b 1

:wrongfolder
echo   this file belongs in your game folder - the one that has
echo   BigTroubleInLittleChinaTheGame.exe in it.
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
