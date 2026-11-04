@echo off
rem ===========================================================================
rem  BIG TROUBLE IN LITTLE CHINA - updater  v6
rem
rem  Put this file in the game folder you already play from: the one with
rem  BigTroubleInLittleChinaTheGame.exe (or Ikemen_GO.exe) in it.
rem
rem  Double-click it. It gets the newest files on main, copies data\ chars\
rem  stages\ font\ external\ sound\ over this folder, leaves save\ and the
rem  engine alone, then starts the game and closes.
rem
rem  It tries, in order: git (smallest download), curl, PowerShell, BITS. If
rem  every one is blocked, it opens the download in your browser and finishes
rem  by itself the moment the zip lands in Downloads.
rem
rem  A copy of main.zip in this folder is used first and needs no network.
rem ===========================================================================
setlocal EnableExtensions DisableDelayedExpansion
color 0E
cd /d "%~dp0"
title Big Trouble in Little China - updater

echo.
echo   ==============================================================
echo.
echo        B I G   T R O U B L E   I N   L I T T L E   C H I N A
echo.
echo                        t h e   g a m e
echo                        updater  v6
echo.
echo   ==============================================================
echo.
echo   folder : %~dp0
echo.

set "EXE="
if exist "BigTroubleInLittleChinaTheGame.exe" set "EXE=BigTroubleInLittleChinaTheGame.exe"
if not defined EXE if exist "Ikemen_GO.exe" set "EXE=Ikemen_GO.exe"
if not defined EXE goto wrongfolder

rem ---- certificate hygiene ----------------------------------------------
rem A machine that has run Git Bash or a dev tool can carry CURL_CA_BUNDLE
rem or SSL_CERT_FILE pointing at /usr/ssl/certs/ca-bundle.crt. Windows curl
rem then refuses every https request with "(77) error setting certificate
rem file" and never downloads a byte. Clearing them for this window only
rem makes curl fall back to the Windows certificate store.
set "CURL_CA_BUNDLE="
set "CURL_CA_PATH="
set "SSL_CERT_FILE="
set "SSL_CERT_DIR="
set "GIT_SSL_CAINFO="
set "GIT_SSL_CAPATH="
set "GIT_CONFIG_NOSYSTEM=1"
set "GIT_TERMINAL_PROMPT=0"
set "GIT_CONFIG_PARAMETERS="

set "REPO=jackrabbit72380/bigtroubleinlittlechinathegame"
set "ZIPURL=https://codeload.github.com/%REPO%/zip/refs/heads/main"
set "ZIPURL2=https://github.com/%REPO%/archive/refs/heads/main.zip"
set "GITURL=https://github.com/%REPO%.git"
set "CACHE=%~dp0.update-cache"
if not exist "%CACHE%" mkdir "%CACHE%" 2>nul
set "ZIP=%CACHE%\main.zip"
set "SRC="
set "WHICH="
set "ZIPOK=0"
set "PREVCAND="
set "PREVSZ="
set "FOUNDZIP="

echo   [ 1/4 ]  looking for the newest files
if exist "%~dp0main.zip" goto manualzip
if exist "%~dp0bigtroubleinlittlechinathegame-main.zip" goto manualzip2
where git >nul 2>nul
if errorlevel 1 goto download
goto trygit

:manualzip
echo            using main.zip from this folder - no download needed
copy /Y "%~dp0main.zip" "%ZIP%" >nul
goto havezip

:manualzip2
echo            using bigtroubleinlittlechinathegame-main.zip here
copy /Y "%~dp0bigtroubleinlittlechinathegame-main.zip" "%ZIP%" >nul
goto havezip

rem ---- transport 1: git, with the Windows certificate store --------------
:trygit
echo            git found - fetching only what has changed
if exist "%CACHE%\repo\.git" goto gitpull
if exist "%CACHE%\repo" rd /s /q "%CACHE%\repo" >nul 2>&1
git -c core.longpaths=true -c http.sslBackend=schannel -c http.schannelCheckRevoke=false -c http.version=HTTP/1.1 clone --depth 1 --quiet "%GITURL%" "%CACHE%\repo" >"%CACHE%\git.log" 2>&1
goto gitdone

:gitpull
git -c core.longpaths=true -c http.sslBackend=schannel -c http.schannelCheckRevoke=false -C "%CACHE%\repo" fetch --depth 1 --quiet origin main >"%CACHE%\git.log" 2>&1
git -C "%CACHE%\repo" reset --hard --quiet origin/main >>"%CACHE%\git.log" 2>&1

:gitdone
if not exist "%CACHE%\repo\data\fight.def" goto gitfail
set "SRC=%CACHE%\repo"
set "WHICH=git"
goto sync

:gitfail
echo            git could not fetch. it said:
if not exist "%CACHE%\git.log" goto download
findstr /i /c:"fatal" /c:"error" /c:"unable" "%CACHE%\git.log"
echo            trying a direct download instead
goto download

rem ---- transports 2 to 4 -------------------------------------------------
:download
echo.
echo   [ 2/4 ]  downloading the game files
echo            about 190 MB. the count below is what has arrived.
echo.
if exist "%SystemRoot%\System32\curl.exe" goto dl_curl
goto dl_ps

:dl_curl
call :cfetch "%ZIPURL%"
if "%ZIPOK%"=="1" goto havezip
call :cfetch "%ZIPURL2%"
if "%ZIPOK%"=="1" goto havezip

:dl_ps
where powershell >nul 2>nul
if errorlevel 1 goto dl_bits
echo            trying PowerShell. this step is silent, so it may sit a while:
if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $c = New-Object Net.WebClient; $c.Headers.Add('User-Agent','btilc-updater'); $c.DownloadFile('%ZIPURL%','%ZIP%'); exit 0 } catch { Write-Host ('             ' + $_.Exception.Message); exit 1 }"
call :zipok
if "%ZIPOK%"=="1" goto havezip

:dl_bits
where bitsadmin >nul 2>nul
if errorlevel 1 goto dl_browser
echo            trying BITS, the Windows download service
echo            it uses the same proxy settings as your browser
if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
bitsadmin /reset >nul 2>&1
bitsadmin /transfer BTILCupdate /download /priority normal "%ZIPURL%" "%ZIP%" >nul 2>&1
call :zipok
if "%ZIPOK%"=="1" goto havezip

rem ---- last resort: the browser does the download, this finishes it ------
:dl_browser
echo.
echo            this window is not allowed out to GitHub, but your browser is.
echo            opening the download now.
echo.
echo            save it anywhere in Downloads. this window watches for it
echo            and starts the game as soon as it is complete - you do not
echo            have to come back here or run anything else.
echo.
start "" "%ZIPURL%"
echo            waiting for the zip ...
set /a WAIT=0
:bwait
timeout /t 5 /nobreak >nul
set /a WAIT+=5
call :findzip
if defined FOUNDZIP goto bapply
if %WAIT% LSS 1200 goto bwait
echo            nothing arrived after 20 minutes.
goto downloadfailed

:bapply
echo            got it: %FOUNDZIP%
copy /Y "%FOUNDZIP%" "%ZIP%" >nul
call :zipok
if "%ZIPOK%"=="1" goto havezip
goto downloadfailed

rem ---- unpack and copy ---------------------------------------------------
:havezip
echo.
echo   [ 3/4 ]  copying the game files over this folder
if exist "%CACHE%\unpack" rd /s /q "%CACHE%\unpack" >nul 2>&1
mkdir "%CACHE%\unpack" 2>nul
where tar >nul 2>nul
if errorlevel 1 goto unzip_ps
tar -xf "%ZIP%" -C "%CACHE%\unpack"
goto unpacked

:unzip_ps
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force -LiteralPath '%ZIP%' -DestinationPath '%CACHE%\unpack'"

:unpacked
for /d %%D in ("%CACHE%\unpack\*") do set "SRC=%%~fD"
if not defined SRC goto downloadfailed
if not "%WHICH%"=="git" set "WHICH=zip"

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
start "" "%EXE%" -config "save\config.ini"
timeout /t 8 /nobreak >nul
tasklist /fi "imagename eq %EXE%" 2>nul | findstr /i /c:"%EXE%" >nul
if errorlevel 1 goto launchfail
echo   running. have fun.
timeout /t 3 /nobreak >nul
exit /b 0

:launchfail
echo   the game did not stay open. start it by hand to see the engine's
echo   message, and check docs/INSTALL.md - the renderer setting is the
echo   usual reason, and deleting save\config.ini resets it.
echo.
pause
exit /b 1

:wrongfolder
echo   this file belongs in your game folder - the one that has
echo   BigTroubleInLittleChinaTheGame.exe in it.
echo.
pause
exit /b 1

:downloadfailed
echo.
echo   could not get the files automatically.
echo.
echo   the last resort, which always works:
echo     1. download this in your browser
echo        %ZIPURL%
echo     2. save the zip in this folder
echo     3. run "Apply main.zip.bat"
echo.
pause
exit /b 1

rem ===========================================================================
rem  curl, in the background, so the arriving bytes can be counted
rem ===========================================================================
:cfetch
set "ZIPOK=0"
if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
if exist "%CACHE%\cf.done" del /q "%CACHE%\cf.done" >nul 2>&1
if exist "%CACHE%\curl.err" del /q "%CACHE%\curl.err" >nul 2>&1
>"%CACHE%\run.bat" echo @echo off
>>"%CACHE%\run.bat" echo "%SystemRoot%\System32\curl.exe" -sS -L --fail --ssl-no-revoke --connect-timeout 30 --max-time 900 --speed-time 90 --speed-limit 2048 -o "%ZIP%" "%~1" 2^>"%CACHE%\curl.err"
>>"%CACHE%\run.bat" echo echo %%ERRORLEVEL%%^>"%CACHE%\cf.done"
echo            curl is fetching. this line grows while it works:
start "" /b "%CACHE%\run.bat"
set /a SECS=0
:cfpoll
timeout /t 5 /nobreak >nul
set /a SECS+=5
set "SZ=0"
for %%A in ("%ZIP%") do set "SZ=%%~zA"
set /a MB=SZ/1048576
set /a MINS=SECS/60
set /a REST=SECS%%60
set "CLOCK=%MINS%:%REST%"
if %REST% LSS 10 set "CLOCK=%MINS%:0%REST%"
echo            %MB% of about 190 MB   -   %CLOCK% elapsed
if exist "%CACHE%\cf.done" goto cfdone
if %SECS% LSS 960 goto cfpoll
echo            no transfer after 16 minutes. moving on.
exit /b 0

:cfdone
set "CODE=?"
if exist "%CACHE%\cf.done" set /p CODE=<"%CACHE%\cf.done"
call :zipok
if "%ZIPOK%"=="1" exit /b 0
echo            that attempt did not finish. curl said:
if exist "%CACHE%\curl.err" type "%CACHE%\curl.err"
exit /b 0

rem ===========================================================================
rem  helpers
rem ===========================================================================
:zipok
set "ZIPOK=0"
if not exist "%ZIP%" exit /b 0
for %%A in ("%ZIP%") do set "ZIPSIZE=%%~zA"
if not defined ZIPSIZE exit /b 0
if %ZIPSIZE% LSS 20000000 exit /b 0
set "ZIPOK=1"
exit /b 0

:findzip
set "FOUNDZIP="
set "CAND="
for %%D in ("%USERPROFILE%\Downloads" "%~dp0" "%CACHE%") do (
  for /f "delims=" %%Z in ('dir /b /a-d /o-d "%%~D\*bigtrouble*.zip" 2^>nul') do (
    if not defined CAND set "CAND=%%~D\%%Z"
  )
)
if not defined CAND exit /b 0
for %%A in ("%CAND%") do set "CANDSZ=%%~zA"
if not defined CANDSZ exit /b 0
if %CANDSZ% LSS 20971520 exit /b 0
if "%CAND%"=="%PREVCAND%" if "%CANDSZ%"=="%PREVSZ%" set "FOUNDZIP=%CAND%"
set "PREVCAND=%CAND%"
set "PREVSZ=%CANDSZ%"
exit /b 0
