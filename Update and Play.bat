@echo off
rem ===========================================================================
rem  BIG TROUBLE IN LITTLE CHINA - updater  v8
rem
rem  Put this file in the game folder you already play from: the one with
rem  BigTroubleInLittleChinaTheGame.exe (or Ikemen_GO.exe) in it.
rem
rem  Double-click it. It gets the newest files on main, copies data\ chars\
rem  stages\ font\ external\ sound\ over this folder, leaves save\ and the
rem  engine alone, then starts the game and closes.
rem
rem  Every Windows tool below is called by full path on purpose. A Git for
rem  Windows install that puts its usr\bin on PATH shadows System32 with MSYS
rem  builds, and those are not the same programs: `timeout /t` answers
rem  "invalid time interval", tar reads H:\... as a remote host and answers
rem  "Cannot connect to H:", and curl looks for its CA bundle at
rem  /usr/ssl/certs/ca-bundle.crt. Full paths avoid all three.
rem ===========================================================================
setlocal EnableExtensions DisableDelayedExpansion
color 0E
cd /d "%~dp0"
title Big Trouble in Little China - updater

set "SYS=%SystemRoot%\System32"
set "PING=%SYS%\ping.exe"
set "TAR=%SYS%\tar.exe"
set "CURL=%SYS%\curl.exe"
set "FINDSTR=%SYS%\findstr.exe"
set "TASKLIST=%SYS%\tasklist.exe"
set "ROBOCOPY=%SYS%\robocopy.exe"
set "WHERE=%SYS%\where.exe"
set "POWERSHELL=%SYS%\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%TAR%" set "TAR="
if not exist "%CURL%" set "CURL="
if not exist "%POWERSHELL%" set "POWERSHELL="
if not exist "%WHERE%" set "WHERE="

rem Git Bash can also leave these set, pointing at a path that only exists
rem inside its own filesystem. They are cleared for this window only.
set "CURL_CA_BUNDLE="
set "CURL_CA_PATH="
set "SSL_CERT_FILE="
set "SSL_CERT_DIR="
set "GIT_SSL_CAINFO="
set "GIT_SSL_CAPATH="
set "GIT_CONFIG_NOSYSTEM=1"
set "GIT_TERMINAL_PROMPT=0"
set "GIT_CONFIG_PARAMETERS="

echo.
echo   ==============================================================
echo.
echo        B I G   T R O U B L E   I N   L I T T L E   C H I N A
echo.
echo                        t h e   g a m e
echo                        updater  v8
echo.
echo   ==============================================================
echo.
echo   folder : %~dp0
echo.

set "EXE="
if exist "BigTroubleInLittleChinaTheGame.exe" set "EXE=BigTroubleInLittleChinaTheGame.exe"
if not defined EXE if exist "Ikemen_GO.exe" set "EXE=Ikemen_GO.exe"
if not defined EXE goto wrongfolder

set "REPO=jackrabbit72380/bigtroubleinlittlechinathegame"
set "ZIPURL=https://codeload.github.com/%REPO%/zip/refs/heads/main"
set "ZIPURL2=https://github.com/%REPO%/archive/refs/heads/main.zip"
set "GITURL=https://github.com/%REPO%.git"
set "CACHE=%~dp0.update-cache"
if not exist "%CACHE%" mkdir "%CACHE%" 2>nul
set "ZIP="
set "SRC="
set "WHICH="
set "ZIPOK=0"
set "PREVCAND="
set "PREVSZ="
set "FOUNDZIP="

echo   [ 1/4 ]  looking for the newest files
if exist "%~dp0main.zip" goto manualzip
if exist "%~dp0bigtroubleinlittlechinathegame-main.zip" goto manualzip2
rem nothing left over from an interrupted run may be mistaken for an archive
if exist "%CACHE%\main-1.zip" del /q "%CACHE%\main-1.zip" >nul 2>&1
if exist "%CACHE%\main-2.zip" del /q "%CACHE%\main-2.zip" >nul 2>&1
if exist "%CACHE%\main.zip" del /q "%CACHE%\main.zip" >nul 2>&1
if not exist "%WHERE%" goto download
"%WHERE%" git >nul 2>&1
if errorlevel 1 goto download
goto trygit

:manualzip
echo            using main.zip from this folder - no download needed
set "ZIP=%CACHE%\main-1.zip"
copy /Y "%~dp0main.zip" "%ZIP%" >nul
call :zipcheck
if "%ZIPOK%"=="1" goto havezip
echo            that main.zip is incomplete - downloading instead
goto download

:manualzip2
echo            using bigtroubleinlittlechinathegame-main.zip here
set "ZIP=%CACHE%\main-1.zip"
copy /Y "%~dp0bigtroubleinlittlechinathegame-main.zip" "%ZIP%" >nul
call :zipcheck
if "%ZIPOK%"=="1" goto havezip
echo            that zip is incomplete - downloading instead
goto download

rem ---- transport 1: git, which moves only the objects that differ ---------
rem Depth 1 plus a blob filter: the first run still has to bring the art, but
rem every run after that transfers only what a commit touched, usually a few
rem small files. Sparse checkout also leaves out the folders the game never
rem copies - artifacts, concept_art, art_src, tools - which is 128 MB of the
rem committed tree.
:trygit
echo            git found - comparing with main
if exist "%CACHE%\repo\.git" goto gitpull
if exist "%CACHE%\repo" rd /s /q "%CACHE%\repo" >nul 2>&1
echo            first run: building the local copy. this one is the big one
git -c core.longpaths=true -c http.sslBackend=schannel -c http.schannelCheckRevoke=false -c http.version=HTTP/1.1 clone --depth 1 --filter=blob:none --sparse --quiet "%GITURL%" "%CACHE%\repo" >"%CACHE%\git.log" 2>&1
if errorlevel 1 goto gitplain
git -C "%CACHE%\repo" sparse-checkout set data chars stages font external sound >>"%CACHE%\git.log" 2>&1
if errorlevel 1 git -C "%CACHE%\repo" checkout --quiet >>"%CACHE%\git.log" 2>&1
goto gitdone

:gitplain
rem older git, or a server without partial clone: take the whole tree once
git -c core.longpaths=true -c http.sslBackend=schannel -c http.schannelCheckRevoke=false -c http.version=HTTP/1.1 clone --depth 1 --quiet "%GITURL%" "%CACHE%\repo" >"%CACHE%\git.log" 2>&1
if errorlevel 1 goto gitfail
goto gitdone

:gitpull
for /f %%s in ('git -C "%CACHE%\repo" rev-parse HEAD 2^>nul') do set "OLDSHA=%%s"
git -c http.sslBackend=schannel -c http.schannelCheckRevoke=false -C "%CACHE%\repo" fetch --depth 1 --quiet origin main >"%CACHE%\git.log" 2>&1
if errorlevel 1 goto gitfail
git -C "%CACHE%\repo" reset --hard --quiet FETCH_HEAD >>"%CACHE%\git.log" 2>&1
for /f %%s in ('git -C "%CACHE%\repo" rev-parse FETCH_HEAD 2^>nul') do set "NEWSHA=%%s"
if not defined NEWSHA goto gitdone
if "%OLDSHA%"=="%NEWSHA%" echo            main has not moved - nothing to download
if not "%OLDSHA%"=="%NEWSHA%" echo            fetched only the files that changed

:gitdone
if not exist "%CACHE%\repo\data\fight.def" goto gitfail
set "SRC=%CACHE%\repo"
set "WHICH=git"
for /f %%s in ('git -C "%CACHE%\repo" rev-parse --short HEAD 2^>nul') do set "VER=%%s"
if not defined VER goto sync
rem if this exact revision is already in the game folder, do not copy 340 MB
rem over the top of itself just to launch
set "APPLIED="
if exist "%CACHE%\applied.txt" set /p APPLIED=<"%CACHE%\applied.txt"
if not "%APPLIED%"=="%VER%" goto sync
if not exist "%~dp0data\fight.def" goto sync
echo   files  : main @ %VER%
echo            already up to date - launching what is here
goto launch

:gitfail
echo            git could not fetch. it said:
if not exist "%CACHE%\git.log" goto download
"%FINDSTR%" /i /c:"fatal" /c:"error" /c:"unable" "%CACHE%\git.log"
echo            trying a direct download instead
goto download

rem ---- transports 2 to 4 -------------------------------------------------
:download
echo.
echo   [ 2/4 ]  downloading the game files
echo            about 190 MB. the count below only goes up.
echo.
set "ATT=0"

:curl_try
set /a ATT+=1
if %ATT% GTR 2 goto dl_ps
if not defined CURL goto dl_ps
set "ZIP=%CACHE%\main-%ATT%.zip"
if %ATT%==2 (call :cfetch "%ZIPURL2%") else (call :cfetch "%ZIPURL%")
call :zipcheck
if "%ZIPOK%"=="1" goto havezip
goto curl_try

:dl_ps
if not defined POWERSHELL goto dl_bits
set "ZIP=%CACHE%\main-ps.zip"
if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
echo            trying PowerShell. this step is silent, so it may sit a while:
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $c = New-Object Net.WebClient; $c.Headers.Add('User-Agent','btilc-updater'); $c.DownloadFile('%ZIPURL%','%ZIP%'); exit 0 } catch { Write-Host ('             ' + $_.Exception.Message); exit 1 }"
call :zipcheck
if "%ZIPOK%"=="1" goto havezip

:dl_bits
if not exist "%SYS%\bitsadmin.exe" goto dl_browser
set "ZIP=%CACHE%\main-bits.zip"
if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
echo            trying BITS, the Windows download service
echo            it uses the same proxy settings as your browser
"%SYS%\bitsadmin.exe" /reset >nul 2>&1
"%SYS%\bitsadmin.exe" /transfer BTILCupdate /download /priority normal "%ZIPURL%" "%ZIP%" >nul 2>&1
call :zipcheck
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
call :sleep 5
set /a WAIT+=5
call :findzip
if defined FOUNDZIP goto bapply
if %WAIT% LSS 1200 goto bwait
echo            nothing arrived after 20 minutes.
goto downloadfailed

:bapply
echo            got it: %FOUNDZIP%
set "ZIP=%CACHE%\main-1.zip"
copy /Y "%FOUNDZIP%" "%ZIP%" >nul
call :zipcheck
if "%ZIPOK%"=="1" goto havezip
goto downloadfailed

rem ---- unpack and copy ---------------------------------------------------
:havezip
echo.
echo   ==============================================================
echo.
echo   [ 3/4 ]  copying the game files over this folder
echo.
if exist "%CACHE%\unpack" rd /s /q "%CACHE%\unpack" >nul 2>&1
mkdir "%CACHE%\unpack" 2>nul
if not defined TAR goto un_ps
"%TAR%" -xf "%ZIP%" -C "%CACHE%\unpack"
if errorlevel 1 goto un_ps
goto unpacked

:un_ps
if not defined POWERSHELL goto unpacked
if exist "%CACHE%\unpack" rd /s /q "%CACHE%\unpack" >nul 2>&1
mkdir "%CACHE%\unpack" 2>nul
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force -LiteralPath '%ZIP%' -DestinationPath '%CACHE%\unpack'"

:unpacked
for /d %%D in ("%CACHE%\unpack\*") do set "SRC=%%~fD"
if not defined SRC goto downloadfailed
if not "%WHICH%"=="git" set "WHICH=zip"
for %%F in (data chars stages font external sound) do (
  if exist "%SRC%\%%F" echo            %%F
  if exist "%SRC%\%%F" "%ROBOCOPY%" "%SRC%\%%F" "%~dp0%%F" /E /NFL /NDL /NJH /NJS /NP >nul
)
if not exist "%SRC%\config.ini" goto copied
copy /Y "%SRC%\config.ini" "%~dp0config.ini" >nul
if not exist "%~dp0save" mkdir "%~dp0save" 2>nul
if not exist "%~dp0save\config.ini" copy /Y "%SRC%\config.ini" "%~dp0save\config.ini" >nul

:copied
set "VER="
if not "%WHICH%"=="git" goto skipver
for /f %%v in ('git -C "%CACHE%\repo" rev-parse --short HEAD 2^>nul') do set "VER=%%v"
if defined VER (>"%CACHE%\applied.txt" echo %VER%)

:sync
if not "%WHICH%"=="git" goto skipver2

:skipver
echo.
"%FINDSTR%" /c:"bg1.spr = 20,0" "%~dp0data\fight.def" >nul 2>nul
if errorlevel 1 echo   HUD    : OLD - the copy did not land
if not errorlevel 1 echo   HUD    : dragon - back is health, belly is audacity
if defined VER echo   files  : main @ %VER%
if not defined VER echo   files  : main, from the zip
echo.

:launch
echo   [ 4/4 ]  starting the game
echo.
start "" "%EXE%" -config "save\config.ini"
call :sleep 8
"%TASKLIST%" /fi "imagename eq %EXE%" 2>nul | "%FINDSTR%" /i /c:"%EXE%" >nul
if errorlevel 1 goto launchfail
echo   running. have fun.
call :sleep 2
exit /b 0

:skipver2
goto skipver

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
rem  curl in the background, so the arriving bytes can be counted
rem ===========================================================================
:cfetch
rem %1 = url. %ZIP% already points at this attempt's own file, so a leftover
rem process from an earlier attempt can never lock it.
set "CFURL=%~1"
set "DONE=%CACHE%\done-%RANDOM%.txt"
set "ERRF=%CACHE%\err-%RANDOM%.txt"
set "RUNB=%CACHE%\get-%RANDOM%.bat"
if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
>"%RUNB%" echo @echo off
>>"%RUNB%" echo "%CURL%" -sS -L --fail --ssl-no-revoke --connect-timeout 30 --max-time 900 --speed-time 120 --speed-limit 1024 -o "%ZIP%" "%CFURL%" 2^>"%ERRF%"
>>"%RUNB%" echo echo %%ERRORLEVEL%%^>"%DONE%"
start "" /b "%RUNB%"
set /a SECS=0
call :drawdl 0 0:00
:cfpoll
call :sleep 5
set /a SECS+=5
set "SZ=0"
for %%A in ("%ZIP%") do set "SZ=%%~zA"
set /a MB=SZ/1048576
set /a MINS=SECS/60
set /a REST=SECS%%60
set "CLOCK=%MINS%:%REST%"
if %REST% LSS 10 set "CLOCK=%MINS%:0%REST%"
call :drawdl %MB% %CLOCK%
if exist "%DONE%" goto cfdone
if %SECS% LSS 900 goto cfpoll
echo            no complete transfer after 15 minutes. moving on.
exit /b 0

:cfdone
if exist "%DONE%" set /p CODE=<"%DONE%"
call :zipcheck
if "%ZIPOK%"=="1" exit /b 0
echo            that attempt did not finish. curl said:
if exist "%ERRF%" type "%ERRF%"
exit /b 0

rem ===========================================================================
rem  helpers
rem ===========================================================================
:dragonbar
rem %1 = done, %2 = total -> BAR: 32 cells, a body of = and a head at the tip
setlocal EnableDelayedExpansion
set /a "C=(%~1)*32/(%~2)"
if !C! LSS 1 set "C=1"
if !C! GTR 32 set "C=32"
set "BAR="
for /l %%i in (1,1,32) do (
  if %%i LSS !C! set "BAR=!BAR!="
  if %%i EQU !C! set "BAR=!BAR!>"
  if %%i GTR !C! set "BAR=!BAR!-"
)
endlocal & set "BAR=%BAR%"
exit /b 0

:drawdl
rem %1 = MB so far, %2 = elapsed clock. Redrawn in place, so the screen stays
rem one panel instead of a growing list of lines.
call :dragonbar %~1 190
cls
echo.
echo   ==============================================================
echo        B I G   T R O U B L E   I N   L I T T L E   C H I N A
echo   ==============================================================
echo.
echo   fetching the newest build of the game
echo.
echo     [%BAR%]
echo.
echo        %~1 of about 190 MB           %~2 elapsed
echo.
echo   keep this window open - it starts the game by itself when
echo   the download is done.
exit /b 0

:sleep
rem ping is the only delay Windows always has, whatever is on PATH
set /a "P=%~1+1"
"%PING%" -n %P% 127.0.0.1 >nul 2>&1
exit /b 0

:zipcheck
rem A download that stopped early still has a plausible size, so the archive
rem itself is listed and data/fight.def has to be inside it.
set "ZIPOK=0"
set "ZS=0"
if not defined ZIP exit /b 0
if not exist "%ZIP%" exit /b 0
for %%A in ("%ZIP%") do set "ZS=%%~zA"
if not defined ZS exit /b 0
if %ZS% LSS 20000000 exit /b 0
if not defined TAR goto zipcheck_ps
"%TAR%" -tf "%ZIP%" >"%CACHE%\zlist.txt" 2>nul
if errorlevel 1 exit /b 0
"%FINDSTR%" /c:"data/fight.def" "%CACHE%\zlist.txt" >nul 2>&1
if errorlevel 1 exit /b 0
set "ZIPOK=1"
exit /b 0

:zipcheck_ps
if not defined POWERSHELL exit /b 0
"%POWERSHELL%" -NoProfile -Command "try { Add-Type -AssemblyName System.IO.Compression.FileSystem; $z=[IO.Compression.ZipFile]::OpenRead('%ZIP%'); $n=($z.Entries | Where-Object { $_.FullName -like '*data/fight.def' }).Count; $z.Dispose(); if ($n -ge 1) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if errorlevel 1 exit /b 0
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
