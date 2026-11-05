@echo off
rem ===========================================================================
rem  BIG TROUBLE IN LITTLE CHINA - Updater v26
rem
rem  Put this file in the game folder you already play from: the one with
rem  BigTroubleInLittleChinaTheGame.exe (or Ikemen_GO.exe) in it.
rem
rem  Double-click it. It gets the newest files on main, updates data\ chars\
rem  stages\ font\ external\ sound\ in this folder, leaves save\ and the
rem  engine alone, then starts the game and closes. Where git is installed
rem  the folder itself is compared against main, so only the files that
rem  really differ are downloaded; without git it falls back to the archive.
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
title Big Trouble in Little China: The Game - Updater

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

rem One bar, rewritten in place, needs a terminal that understands ANSI: Windows
rem Terminal always does, conhost does once VirtualTerminalLevel is on. Without
rem it the same information is printed as ordinary lines and the bar is never
rem rewritten, because a rewrite an older console cannot read prints escapes
rem across the screen instead.
set "VT=0"
if defined WT_SESSION set "VT=1"
if defined TERM_PROGRAM set "VT=1"
if not "%VT%"=="1" call :vtdetect
if "%VT%"=="1" for /f %%e in ('echo prompt $E ^| cmd') do set "ESC=%%e"

echo.
echo   ==============================================================
echo.
echo        B I G   T R O U B L E   I N   L I T T L E   C H I N A
echo.
echo                        T H E   G A M E
echo                        Updater v26
echo.
echo   ==============================================================
echo.
echo   Folder:  %~dp0
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
rem A cache folder that cannot be created takes every redirect with it: the
rem run file is written to a path that is not there, curl never starts, and
rem the bar sits at zero for twenty minutes saying nothing about it.
if not exist "%CACHE%" set "CACHE=%TEMP%\btilc-updater"
if not exist "%CACHE%" mkdir "%CACHE%" 2>nul
if not exist "%CACHE%" set "CACHE=%TEMP%"
if not exist "%CACHE%" mkdir "%CACHE%" 2>nul
set "ZIP="
set "SRC="
set "WHICH="
set "ZIPOK=0"
set "PREVCAND="
set "PREVSZ="
set "LAUNCHARED="
set "CHANGED="
set "BASE="
set "NCOP=0"
set "NDEL=0"
set "FOUNDZIP="

rem This window first makes sure it IS the current launcher. Until now the
rem launcher was not in the six folders the update writes, so a fix to it
rem could never reach a folder running an older copy - a window on v19 was
rem still failing against a repository already fixed at v24. Nothing else
rem here is worth doing with an out-of-date script.
call :selfupdate %1

echo   [ 1/4 ]  Looking for the newest files
if exist "%~dp0main.zip" goto manualzip
if exist "%~dp0bigtroubleinlittlechinathegame-main.zip" goto manualzip2
rem nothing left over from an interrupted run may be mistaken for an archive
if exist "%CACHE%\main-1.zip" del /q "%CACHE%\main-1.zip" >nul 2>&1
if exist "%CACHE%\main-2.zip" del /q "%CACHE%\main-2.zip" >nul 2>&1
if exist "%CACHE%\main.zip" del /q "%CACHE%\main.zip" >nul 2>&1
if not exist "%WHERE%" goto download
"%WHERE%" git >nul 2>&1
if errorlevel 1 goto probe
goto trygit

:manualzip
echo            Using main.zip from this folder - no download needed.
set "ZIP=%CACHE%\main-1.zip"
copy /Y "%~dp0main.zip" "%ZIP%" >nul
call :zipcheck
if "%ZIPOK%"=="1" goto havezip
echo            That main.zip is incomplete - downloading instead.
goto download

:manualzip2
echo            Using main.zip from this folder - no download needed.
set "ZIP=%CACHE%\main-1.zip"
copy /Y "%~dp0bigtroubleinlittlechinathegame-main.zip" "%ZIP%" >nul
call :zipcheck
if "%ZIPOK%"=="1" goto havezip
echo            That zip is incomplete - downloading instead.
goto download

rem ---- transport 1: git, working on this folder's own files --------------
rem The art already here is the thing being compared. Git is pointed at the
rem folder and hashes what is in it, so a file that already matches main is
rem never downloaded: only the blobs whose content really differs are fetched,
rem and they are fetched straight into place. No second copy of the art is
rem kept, and the folders the game never uses - artifacts, art_src, tools -
rem are outside the paths below and are left alone.
:trygit
echo            Git found. Comparing this folder with main.
rem Git can be handed a certificate bundle path that only exists inside a Git
rem Bash install - /usr/ssl/certs/ca-bundle.crt - and then every fetch dies with
rem "error setting certificate file". The bundle that belongs to the git that is
rem actually running is found here and passed to the fetch. Verification stays
rem on: if no bundle turns up, git is left to fail and the verified download
rem below takes over rather than being told to trust anything.
set "GITBUNDLE="
set "GITDIR="
for /f "delims=" %%g in ('"%WHERE%" git 2^>nul') do if not defined GITDIR set "GITDIR=%%~dpg"
if defined GITDIR if exist "%GITDIR%..\mingw64\ssl\certs\ca-bundle.crt" set "GITBUNDLE=%GITDIR%..\mingw64\ssl\certs\ca-bundle.crt"
if not defined GITBUNDLE if defined GITDIR if exist "%GITDIR%..\usr\ssl\certs\ca-bundle.crt" set "GITBUNDLE=%GITDIR%..\usr\ssl\certs\ca-bundle.crt"
if not defined GITBUNDLE if exist "%ProgramFiles%\Git\mingw64\ssl\certs\ca-bundle.crt" set "GITBUNDLE=%ProgramFiles%\Git\mingw64\ssl\certs\ca-bundle.crt"
if not defined GITBUNDLE if exist "%ProgramFiles%\Git\usr\ssl\certs\ca-bundle.crt" set "GITBUNDLE=%ProgramFiles%\Git\usr\ssl\certs\ca-bundle.crt"
if not defined GITBUNDLE if exist "%LOCALAPPDATA%\Programs\Git\mingw64\ssl\certs\ca-bundle.crt" set "GITBUNDLE=%LOCALAPPDATA%\Programs\Git\mingw64\ssl\certs\ca-bundle.crt"
rem an MSYS2-style install keeps git in usr\bin and the bundle two levels up
if not defined GITBUNDLE if defined GITDIR if exist "%GITDIR%..\..\usr\ssl\certs\ca-bundle.crt" set "GITBUNDLE=%GITDIR%..\..\usr\ssl\certs\ca-bundle.crt"
if not defined GITBUNDLE if defined GITDIR if exist "%GITDIR%..\..\mingw64\ssl\certs\ca-bundle.crt" set "GITBUNDLE=%GITDIR%..\..\mingw64\ssl\certs\ca-bundle.crt"
if not defined GITBUNDLE if defined GITDIR if exist "%GITDIR%..\ssl\certs\ca-bundle.crt" set "GITBUNDLE=%GITDIR%..\ssl\certs\ca-bundle.crt"
set "GITCA="
if not defined GITBUNDLE goto gitca_done
set "GIT_SSL_CAINFO=%GITBUNDLE%"
set GITCA=-c http.sslCAInfo="%GITBUNDLE%"
:gitca_done
rem A bundle git names but cannot read fails every fetch, and git can sit on
rem the connection for a long time before it says so. That is knowable here: if
rem git points at a file this machine does not have and no bundle was found
rem beside it, the archive is taken straight away instead of stalling.
set "GITCAFILE="
for /f "delims=" %%c in ('git config --get http.sslCAInfo 2^>nul') do set "GITCAFILE=%%c"
if not defined GITCAFILE goto gitca_checked
if defined GITBUNDLE goto gitca_checked
if exist "%GITCAFILE%" goto gitca_checked
echo            Git cannot read its certificate bundle: %GITCAFILE%
echo            Using the verified download instead.
goto probe
:gitca_checked
if exist ".git" goto githere
echo            First run: reading what is already here, so only changes are downloaded.
echo            This reads the art already in this folder; it does not download it.
echo            This can take a minute before the bar moves.
git init -q . >"%CACHE%\git.log" 2>&1
if errorlevel 1 goto gitfail
git config --local ikemen.updater 1 >>"%CACHE%\git.log" 2>&1
git symbolic-ref HEAD refs/heads/main >>"%CACHE%\git.log" 2>&1
git remote add origin "%GITURL%" >>"%CACHE%\git.log" 2>&1
git config --local remote.origin.promisor true >>"%CACHE%\git.log" 2>&1
git config --local remote.origin.partialclonefilter blob:none >>"%CACHE%\git.log" 2>&1
git config --local core.longpaths true >>"%CACHE%\git.log" 2>&1
git config --local http.version HTTP/1.1 >>"%CACHE%\git.log" 2>&1
goto gitfetch

:githere
rem A folder somebody cloned themselves is their checkout: this launcher
rem will not fetch into it, check anything out, or overwrite uncommitted
rem work. It only says so and starts the game.
set "MINE="
for /f %%m in ('git config --local --get ikemen.updater 2^>nul') do set "MINE=%%m"
if "%MINE%"=="1" goto gitfetch
git rev-parse --verify -q HEAD >nul 2>&1
if errorlevel 1 goto gitfetch
echo            This folder is your own git checkout - left untouched.
echo            Bring it up to date yourself with:  git pull
goto launch

:gitfetch
rem The fetch used to run with no output and no limit: on a stalled line the
rem window sat blinking with nothing to show. It now runs beside the launcher,
rem the seconds are counted where the bar goes, git aborts itself after thirty
rem seconds of under 1 KB/s, and this gives up asking after three minutes.
set "GDONE=%CACHE%\gitdone-%RANDOM%.txt"
set "GERR=%CACHE%\giterr-%RANDOM%.txt"
set "GRUN=%CACHE%\gitrun-%RANDOM%.bat"
if exist "%GDONE%" del /q "%GDONE%" >nul 2>&1
echo            Asking main for its latest commit - a few KB.
>"%GRUN%" echo @echo off
>>"%GRUN%" echo git %GITCA% -c core.longpaths=true -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=30 fetch --depth 1 --progress origin main 2^>"%GERR%"
>>"%GRUN%" echo echo %%ERRORLEVEL%%^>"%GDONE%"
if not exist "%GRUN%" goto probe
start "" /b "%GRUN%"
set /a GW=0
:gitpoll
call :sleep 2
set /a GW+=2
if exist "%GDONE%" goto gitpoll_done
set "DLTLINE=[ git ]  waiting for GitHub ... %GW% seconds"
call :dltxt "%DLTLINE%"
if %GW% LSS 180 goto gitpoll
call :dlend
echo            GitHub did not answer within three minutes.
echo            Trying a direct download instead.
del /q "%GRUN%" >nul 2>&1
goto probe
:gitpoll_done
call :dlend
del /q "%GRUN%" >nul 2>&1
set "GRC="
set /p GRC=<"%GDONE%"
del /q "%GDONE%" >nul 2>&1
if not "%GRC%"=="0" goto gitfail
rem What the fetch just found, before the folder is read or anything is
rem written: one sentence and a Continue/Exit choice.
set "NEWSHORT="
for /f %%s in ('git rev-parse --short FETCH_HEAD 2^>nul') do set "NEWSHORT=%%s"
set "HAVE="
if exist "%CACHE%\applied.txt" set /p HAVE=<"%CACHE%\applied.txt"
call :sayupdate "%NEWSHORT%" "%HAVE%"
call :choose
if errorlevel 1 goto quit
git read-tree FETCH_HEAD >>"%CACHE%\git.log" 2>&1
if errorlevel 1 goto gitfail
rem The index now holds main and the working tree still holds this folder's
rem files. diff names the paths whose content differs - hashing what is here
rem instead of fetching it - and checkout-index writes exactly those, pulling
rem each missing blob on demand.
git -c core.quotepath=false diff --name-only -- data chars stages font external sound >"%CACHE%\changed.txt" 2>>"%CACHE%\git.log"
if errorlevel 1 goto gitfail
set "NCH=0"
for /f "usebackq delims=" %%c in ("%CACHE%\changed.txt") do set /a NCH+=1
if "%NCH%"=="0" echo            Already current - nothing to download.
if "%NCH%"=="0" goto gitdel
echo            %NCH% file(s) differ - fetching them, named as they land.
if "%VT%"=="1" echo.
set /a NDONE=0
for /f "usebackq delims=" %%c in ("%CACHE%\changed.txt") do call :gitone "%%c"
call :dlend
if defined GITBAD goto gitfail
goto gitdel

:gitone
rem %1 = one path. Written on its own, so the name of the file being fetched is
rem on the bar while it is fetched instead of a silent pause.
set /a NDONE+=1
set "GTXT=%~1"
call :dragonbar %NDONE% %NCH%
set "GITTXT=[%BAR%]  %NDONE%/%NCH%  %GTXT%"
call :dltxt "%GITTXT%"
git checkout-index -f -- "%GTXT%" >>"%CACHE%\git.log" 2>&1
if errorlevel 1 set "GITBAD=1"
exit /b 0

:gitdel
rem Files main dropped would otherwise sit here for ever. Only paths this
rem launcher installed are deleted - the list in applied.files - so a
rem character the player added themselves is never touched.
git ls-files -- data chars stages font external sound >"%CACHE%\applied.new" 2>>"%CACHE%\git.log"
if errorlevel 1 goto gitref
if not exist "%CACHE%\applied.files" goto gitref
"%FINDSTR%" /v /x /l /g:"%CACHE%\applied.new" "%CACHE%\applied.files" >"%CACHE%\dropped.txt" 2>nul
if not exist "%CACHE%\dropped.txt" goto gitref
for /f "usebackq delims=" %%p in ("%CACHE%\dropped.txt") do call :gitdrop "%%p"

:gitref
if exist "%CACHE%\applied.new" move /Y "%CACHE%\applied.new" "%CACHE%\applied.files" >nul 2>&1
git update-ref refs/heads/main FETCH_HEAD >>"%CACHE%\git.log" 2>&1
git symbolic-ref HEAD refs/heads/main >>"%CACHE%\git.log" 2>&1
set "WHICH=git"
rem an older version of this launcher kept a second copy of the whole art
rem here; the folder itself is the working tree now, so it is dead weight
if exist "%CACHE%\repo" rd /s /q "%CACHE%\repo" >nul 2>&1
goto copied

:gitfail
call :dlend
echo            Git could not fetch.
set "GITSAID=0"
if defined GERR if exist "%GERR%" for %%A in ("%GERR%") do if %%~zA GTR 0 set "GITSAID=1"
if "%GITSAID%"=="1" echo            It said:
if "%GITSAID%"=="1" type "%GERR%"
if "%GITSAID%"=="0" echo            It printed nothing - exit code %GRC%.
if "%GITSAID%"=="0" if exist "%CACHE%\git.log" echo            What git logged:
if "%GITSAID%"=="0" if exist "%CACHE%\git.log" type "%CACHE%\git.log"
if "%GITSAID%"=="0" if not exist "%CACHE%\git.log" echo            It left no log either.
echo            Trying a direct download instead.
goto probe

:gitdrop
rem %1 = a path this launcher installed before, which main no longer has
set "REL=%~1"
if not defined REL exit /b 0
set "REL=%REL:/=\%"
for /f "tokens=1 delims=\" %%t in ("%REL%") do set "TOP=%%t"
if /i "%TOP%"=="data" goto gitdrop_do
if /i "%TOP%"=="chars" goto gitdrop_do
if /i "%TOP%"=="stages" goto gitdrop_do
if /i "%TOP%"=="font" goto gitdrop_do
if /i "%TOP%"=="external" goto gitdrop_do
if /i "%TOP%"=="sound" goto gitdrop_do
exit /b 0
:gitdrop_do
if not exist "%~dp0%REL%" exit /b 0
del /q "%~dp0%REL%" >nul 2>&1
exit /b 0
rem ---- has main moved? ---------------------------------------------------
rem The zip path used to fetch the whole ~190 MB archive on every launch: it
rem recorded nothing about what it had applied, and nothing compared the
rem folder against main. The head commit is a few KB and answers the same
rem question, so an unchanged build costs one small request instead.
:probe
set "RSHA7="
if not exist "%CACHE%\applied.txt" goto download
if not exist "%~dp0data\fight.def" goto download
set "APPLIED="
set /p APPLIED=<"%CACHE%\applied.txt"
if not defined APPLIED goto probe_first
call :atoms
if not defined RSHA7 goto probe_api
if not "%RSHA7%"=="%APPLIED%" goto probe_offer
echo   Version: main @ %APPLIED%
call :sayupdate "%RSHA7%" "%APPLIED%"
call :choose
if errorlevel 1 goto quit
goto launch

:probe_offer
call :sayupdate "%RSHA7%" "%APPLIED%"
call :choose
if errorlevel 1 goto quit
goto download

:probe_first
rem nothing recorded for this folder yet, so there is no build to compare with
set "APPLIED="
call :atoms
call :sayupdate "%RSHA7%" ""
call :choose
if errorlevel 1 goto quit
goto download

:probe_api
rem Fallback only. The API answers the same question but counts against an
rem hourly quota, so it is asked when the feed could not answer, not always.
call :headsha
if not defined RSHA7 goto probe_offer
if not "%RSHA7%"=="%APPLIED%" goto probe_offer
echo   Version: main @ %APPLIED%
echo            Main has not moved - nothing to download.
goto launch

:atoms
rem Sets RSHA7 to main's head commit from the public commit feed. The feed
rem is a few tens of KB, needs no token, and is not counted against the hourly
rem quota api.github.com enforces - that quota is what answered 403 and sent a
rem one-line fix through the whole 190 MB archive on every launch.
set "RSHA7="
set "ASHA="
if not defined CURL exit /b 0
"%CURL%" -sS -L --fail --ssl-no-revoke --connect-timeout 15 --max-time 40 -H "User-Agent: btilc-updater" -o "%CACHE%\main.atom" "https://github.com/%REPO%/commits/main.atom" >nul 2>&1
if errorlevel 1 exit /b 0
if not exist "%CACHE%\main.atom" exit /b 0
for /f "tokens=2 delims=/" %%a in ('"%FINDSTR%" /c:"Grit::Commit/" "%CACHE%\main.atom"') do if not defined ASHA set "ASHA=%%a"
if not defined ASHA exit /b 0
set "ASHA=%ASHA:</id>=%"
set "ASHA=%ASHA:~0,40%"
if not defined ASHA exit /b 0
set "RSHA7=%ASHA:~0,7%"
exit /b 0

:headsha
rem Sets RSHA7 to the short head commit of main. Left empty on any doubt, so
rem a failed probe always falls through to the download it was avoiding.
set "RSHA7="
set "RSHA="
if not defined CURL exit /b 0
"%CURL%" -sS -L --fail --ssl-no-revoke --connect-timeout 20 --max-time 60 -H "User-Agent: btilc-updater" -o "%CACHE%\head.json" "https://api.github.com/repos/%REPO%/commits/main" >nul 2>&1
if errorlevel 1 exit /b 0
if not exist "%CACHE%\head.json" exit /b 0
for /f "tokens=2 delims=:" %%a in ('"%FINDSTR%" /c:sha "%CACHE%\head.json"') do if not defined RSHA set "RSHA=%%a"
if not defined RSHA exit /b 0
set "RSHA=%RSHA: =%"
set RSHA=%RSHA:"=%
set "RSHA=%RSHA:,=%"
if defined RSHA set "RSHA7=%RSHA:~0,7%"
exit /b 0
rem ---- transports 2 to 4 -------------------------------------------------
:download
echo.
echo   [ 2/4 ]  Downloading the game files
echo            About 190 MB. Leave this window open; a transfer that stops
echo            starts again from the beginning.
echo.
set "ATT=0"

:curl_try
set /a ATT+=1
if %ATT% GTR 2 goto dl_ps
if not defined CURL goto dl_ps
if %ATT%==2 (call :cfetch "%ZIPURL2%") else (call :cfetch "%ZIPURL%")
call :zipcheck
if "%ZIPOK%"=="1" goto havezip
goto curl_try


:dl_ps
if not defined POWERSHELL goto dl_bits
set "ZIP=%CACHE%\main-ps.zip"
if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
echo            Trying PowerShell. This step is silent, so it may sit a while:
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $c = New-Object Net.WebClient; $c.Headers.Add('User-Agent','btilc-updater'); $c.DownloadFile('%ZIPURL%','%ZIP%'); exit 0 } catch { Write-Host ('             ' + $_.Exception.Message); exit 1 }"
call :zipcheck
if "%ZIPOK%"=="1" goto havezip

:dl_bits
if not exist "%SYS%\bitsadmin.exe" goto dl_browser
set "ZIP=%CACHE%\main-bits.zip"
if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
echo            Trying BITS, the Windows download service.
echo            It uses the same proxy settings as your browser.
"%SYS%\bitsadmin.exe" /reset >nul 2>&1
"%SYS%\bitsadmin.exe" /transfer BTILCupdate /download /priority normal "%ZIPURL%" "%ZIP%" >nul 2>&1
call :zipcheck
if "%ZIPOK%"=="1" goto havezip

rem ---- last resort: the browser does the download, this finishes it ------
:dl_browser
echo.
echo            This window is not allowed out to GitHub, but your browser is.
echo            Opening the download now.
echo.
echo            Save it anywhere in Downloads. This window watches for it
echo            and starts the game as soon as it is complete - you do not
echo            have to come back here or run anything else.
echo.
start "" "%ZIPURL%"
echo            Waiting for the zip ...
set /a WAIT=0
:bwait
call :sleep 5
set /a WAIT+=5
call :findzip
if defined FOUNDZIP goto bapply
if %WAIT% LSS 1200 goto bwait
echo            Nothing arrived after 20 minutes.
goto downloadfailed

:bapply
echo            Got it: %FOUNDZIP%
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
echo   [ 3/4 ]  Copying the game files over this folder
echo.
call :ziptree
if "%PSOK%"=="1" goto copied
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
call :synctree
if not exist "%SRC%\config.ini" goto copied
copy /Y "%SRC%\config.ini" "%~dp0config.ini" >nul
if not exist "%~dp0save" mkdir "%~dp0save" 2>nul
if not exist "%~dp0save\config.ini" copy /Y "%SRC%\config.ini" "%~dp0save\config.ini" >nul

:copied
rem the archive has been read; keeping it would only hold 190 MB of cache
if defined ZIP if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
set "VER="
if "%WHICH%"=="git" for /f %%v in ('git rev-parse --short HEAD 2^>nul') do set "VER=%%v"
rem a zip run knows the version from the probe, and a fresh one asks now;
rem without recording it the next launch cannot tell it is current. The feed
rem is asked first: on a first run applied.txt is missing, so the probe never
rem got this far and the API fallback could 403 and leave nothing recorded.
if not defined VER if not defined RSHA7 call :atoms
if not defined VER if not defined RSHA7 call :headsha
if not defined VER if defined RSHA7 set "VER=%RSHA7%"
if defined VER (>"%CACHE%\applied.txt" echo %VER%)

:sync
if not "%WHICH%"=="git" goto skipver2

:skipver
echo.
"%FINDSTR%" /c:"bg1.spr = 20,0" "%~dp0data\fight.def" >nul 2>nul
if errorlevel 1 echo   HUD:     old - the copy did not land
if not errorlevel 1 echo   HUD:     dragon - the back bar is health, the belly bar is audacity
if defined VER echo   Version: main @ %VER%
if not defined VER echo   Version: zip build
echo.

:launch
echo   [ 4/4 ]  Starting the game
echo.
start "" "%EXE%" -config "save\config.ini"
rem The engine attaches to the console that started it and writes its log
rem there, so this window becomes the game's log while the game runs. Closing
rem it takes the log - and possibly the game - with it, so it says what it is
rem and waits for a key instead of vanishing.
echo.
echo   The game is starting.
echo.
echo   This window is the game's log. The engine writes here, which is why the
echo   text below is about characters and states and not about the update.
echo   Leave it open while you play. Press any key here when you are done.
echo.
pause
exit 0

:skipver2
goto skipver

rem ===========================================================================
rem  the first thing this window does: become the current launcher
rem ===========================================================================
:selfupdate
rem %1 = the argument this script was started with. --updated means the swap
rem below already ran, so this window must not check again or the two would pass
rem the baton back and forth for ever.
if /i "%~1"=="--updated" exit /b 0
if defined LAUNCHARED exit /b 0
set "LAUNCHARED=1"
if not defined CURL exit /b 0
rem The launcher is not in the six folders the update writes, so before this it
rem could never be refreshed - a folder running v19 stayed on v19 no matter what
rem main fixed. It is fetched on its own here, a few KB.
"%CURL%" -sS -L --fail --ssl-no-revoke --connect-timeout 15 --max-time 40 -H "User-Agent: btilc-updater" -o "%CACHE%\launcher-new.bat" "https://raw.githubusercontent.com/%REPO%/main/Update%%20and%%20Play.bat" >nul 2>&1
if errorlevel 1 exit /b 0
if not exist "%CACHE%\launcher-new.bat" exit /b 0
rem A truncated file, an error page or anything else that is not the launcher
rem must never be copied over a working one.
for %%A in ("%CACHE%\launcher-new.bat") do if %%~zA LSS 5000 exit /b 0
"%FINDSTR%" /c:"BIG TROUBLE IN LITTLE CHINA" "%CACHE%\launcher-new.bat" >nul 2>&1
if errorlevel 1 exit /b 0
"%SYS%\fc.exe" /b "%CACHE%\launcher-new.bat" "%~f0" >nul 2>&1
if not errorlevel 1 exit /b 0
echo.
echo   This launcher is not the current one - updating it before anything else.
rem cmd reads a batch file while it runs it, so this file cannot be written over
rem by the window that is executing it. A detached helper waits for the window to
rem close, copies the new launcher into place and starts it again with --updated.
rem If the copy loses the race the restarted window carries on as it is: the next
rem launch tries again, and nothing here can loop.
set "SWAP=%CACHE%\swap.bat"
>"%SWAP%" echo @echo off
rem Three tries, a few seconds apart: the window that started this has to
rem close before the file it is running can be written over, and how long
rem that takes is not known here. Whatever happens the launcher is started
rem again at the end, so a copy that never lands costs one launch, not the
rem update itself.
>>"%SWAP%" echo copy /Y "%CACHE%\launcher-new.bat" "%~f0" ^>nul 2^>^&1
>>"%SWAP%" echo if not errorlevel 1 goto run
>>"%SWAP%" echo "%PING%" -n 4 127.0.0.1 ^>nul
>>"%SWAP%" echo copy /Y "%CACHE%\launcher-new.bat" "%~f0" ^>nul 2^>^&1
>>"%SWAP%" echo if not errorlevel 1 goto run
>>"%SWAP%" echo "%PING%" -n 5 127.0.0.1 ^>nul
>>"%SWAP%" echo copy /Y "%CACHE%\launcher-new.bat" "%~f0" ^>nul 2^>^&1
>>"%SWAP%" echo :run
>>"%SWAP%" echo start "" "%~f0" --updated
if not exist "%SWAP%" exit /b 0
rem A window of its own, minimised: a /b child shares this console and would
rem go with it when this script exits on the next line.
start "btilc launcher update" /min "%SWAP%"
echo   It restarts in a moment with the current one.
echo.
exit 0

:launchfail
echo   The game did not stay open. Start it by hand to see the engine's
echo   message, and check docs/INSTALL.md - the renderer setting is the
echo   usual reason, and deleting save\config.ini resets it.
echo.
pause
exit 1

:wrongfolder
echo   This file belongs in your game folder - the one that has
echo   BigTroubleInLittleChinaTheGame.exe in it.
echo.
pause
exit 1

:downloadfailed
echo.
echo   Could not get the files automatically.
echo.
echo   The last resort, which always works:
echo     1. Download this in your browser.
echo        %ZIPURL%
echo     2. Save the zip in this folder.
echo     3. Run "Apply main.zip.bat".
echo.
pause
exit 1

rem ===========================================================================
rem  curl in the background, so the arriving bytes can be counted
rem ===========================================================================
:cfetch
rem %1 = url. GitHub builds this archive fresh for each commit and does not serve
rem it in byte ranges - curl answers "HTTP server doesn't seem to support byte
rem ranges. Cannot resume." - so a half file can never be continued. It is
rem dropped before every attempt: a part from an earlier commit would only fail
rem the archive test at the end anyway.
set "CFURL=%~1"
set "ZIP=%CACHE%\main.part"
if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
set "DONE=%CACHE%\done-%RANDOM%.txt"
set "ERRF=%CACHE%\err-%RANDOM%.txt"
set "RUNB=%CACHE%\get-%RANDOM%.bat"
rem A carriage return, so the count is rewritten on its own line. Without it
rem each redraw would add a line and the window would scroll instead.
if not defined CR for /f %%a in ('copy /Z "%~f0" nul') do set "CR=%%a"
>"%RUNB%" echo @echo off
>>"%RUNB%" echo "%CURL%" -sS -L --fail --ssl-no-revoke --retry 2 --retry-delay 3 --connect-timeout 30 --max-time 1200 --speed-time 120 --speed-limit 1024 -o "%ZIP%" "%CFURL%" 2^>"%ERRF%"
>>"%RUNB%" echo echo %%ERRORLEVEL%%^>"%DONE%"
if not exist "%RUNB%" goto dl_ps
start "" /b "%RUNB%"
set /a SECS=0
set /a KB30=0
call :drawdl 0 ""
:cfpoll
call :sleep 5
set /a SECS+=5
set "SZ=0"
for %%A in ("%ZIP%") do set "SZ=%%~zA"
set /a KB=SZ/1024
set "DLINFO="
if %SECS% GEQ 30 call :rate
call :drawdl %KB% "%DLINFO%"
if exist "%DONE%" goto cfdone
if %SECS% LSS 1200 goto cfpoll
echo.
echo            No complete transfer after 20 minutes. The archive has to
echo            start again, so run the updater once the connection is back.
exit /b 0

:rate
rem Averaged over the last half minute, so one slow second does not swing it and
rem the first reading is left out: it has nothing to compare against.
set /a GAIN=KB-KB30
set /a KB30=KB
set /a RATE=GAIN/30
if %RATE% LSS 1 set "DLINFO=no data arriving"
if %RATE% LSS 1 exit /b 0
set /a LEFT=(194560-KB)/RATE
call :clock %LEFT% LEFTCLOCK
set "DLINFO=%RATE% KB/s   %LEFTCLOCK% left"
exit /b 0


:cfdone
echo.
call :zipcheck
if "%ZIPOK%"=="1" exit /b 0
echo            That attempt did not finish. Curl said:
if exist "%ERRF%" type "%ERRF%"
exit /b 0

rem ===========================================================================
rem  helpers
rem ===========================================================================
rem ===========================================================================
rem  copying: only the files main says changed
rem ===========================================================================
:ziptree
rem The archive is ~190 MB of art, but a fix changes a handful of files. Rather
rem than expand all of it and then compare, let PowerShell open the zip and write
rem only the entries that differ from the folder: no unpack tree, and no walking
rem the whole game afterwards. Anything unexpected - no PowerShell, an error
rem inside it, an apostrophe in the folder path - drops to unpack-and-copy.
set "PSOK=0"
if not defined POWERSHELL goto ziptree_done
if not defined ZIP goto ziptree_done
if not exist "%ZIP%" goto ziptree_done
echo %~dp0|"%FINDSTR%" /c:"'" >nul 2>&1
if not errorlevel 1 goto ziptree_done
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; Add-Type -AssemblyName System.IO.Compression.FileSystem; $zip=[IO.Compression.ZipFile]::OpenRead('%ZIP%'); $root='%~dp0'; $tops=@('data','chars','stages','font','external','sound'); $mf='%CACHE%\\applied.files'; $old=@(); if (Test-Path -LiteralPath $mf) { $old=@(Get-Content -LiteralPath $mf) }; $keep=New-Object 'System.Collections.Generic.HashSet[string]'; $n=0; $gone=0; $shown=0; try { foreach ($e in $zip.Entries) { if ($e.FullName.EndsWith('/')) { continue }; $rel=$e.FullName.Substring($e.FullName.IndexOf('/')+1); if ($rel -eq 'config.ini') { $c=$root+'config.ini'; if (-not (Test-Path -LiteralPath $c)) { [IO.Compression.ZipFileExtensions]::ExtractToFile($e,$c,$true) }; continue }; if ($tops -notcontains ($rel -split '/')[0]) { continue }; [void]$keep.Add($rel); $dst=$root+($rel -replace '/','\'); $fi=New-Object System.IO.FileInfo($dst); if ($fi.Exists -and $fi.Length -eq $e.Length -and $fi.LastWriteTimeUtc.Ticks -eq $e.LastWriteTime.UtcDateTime.Ticks) { continue }; $dir=Split-Path -Parent $dst; if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }; [System.IO.Compression.ZipFileExtensions]::ExtractToFile($e,$dst,$true); $n++; if ($shown -lt 25) { Write-Host ('             ' + $rel); $shown++ } } } finally { $zip.Dispose() }; foreach ($p in $old) { if ($keep.Contains($p)) { continue }; $x=$root+($p -replace '/','\'); if (Test-Path -LiteralPath $x) { Remove-Item -LiteralPath $x -Force; $gone++; Write-Host ('             - ' + $p) } }; Set-Content -LiteralPath $mf -Value @($keep) -Encoding ASCII; Write-Host ('            ' + $n + ' file(s) written, ' + $gone + ' removed')"
if errorlevel 1 goto ziptree_done
set "PSOK=1"
if exist "%~dp0config.ini" if not exist "%~dp0save" mkdir "%~dp0save" 2>nul
if exist "%~dp0config.ini" if not exist "%~dp0save\config.ini" copy /Y "%~dp0config.ini" "%~dp0save\config.ini" >nul
:ziptree_done
exit /b 0

:synctree
rem %CHANGED% lists repo-relative paths that differ. Writing only those keeps
rem a one-line fix to a one-file copy; the whole-tree copy stays underneath
rem as the fallback, because it is always correct even when it is slow.
set "NCOP=0"
set "NDEL=0"
if not defined CHANGED goto synctree_full
if not exist "%CHANGED%" goto synctree_full
for /f "usebackq delims=" %%p in ("%CHANGED%") do call :syncfile "%%p"
echo            %NCOP% file(s) updated, %NDEL% removed
exit /b 0

:synctree_full
rem No list means no git history to diff - a first run, or a folder updated
rem from the archive. robocopy still skips every file whose size and time
rem already match, so only the files that changed are actually written; the
rem scan is the cost, not the bytes.
for %%F in (data chars stages font external sound) do (
  if exist "%SRC%\%%F" echo            %%F
  if exist "%SRC%\%%F" "%ROBOCOPY%" "%SRC%\%%F" "%~dp0%%F" /E /FFT /NFL /NDL /NJH /NJS /NP >nul
)
exit /b 0

:syncfile
rem %1 = path relative to the repo root. Only the folders this launcher owns
rem are written: artifacts, tools and art_src stay out, and so do the
rem player's save and the engine files.
set "REL=%~1"
if not defined REL exit /b 0
set "REL=%REL:/=\%"
for /f "tokens=1 delims=\" %%t in ("%REL%") do set "TOP=%%t"
if /i "%TOP%"=="data" goto syncfile_go
if /i "%TOP%"=="chars" goto syncfile_go
if /i "%TOP%"=="stages" goto syncfile_go
if /i "%TOP%"=="font" goto syncfile_go
if /i "%TOP%"=="external" goto syncfile_go
if /i "%TOP%"=="sound" goto syncfile_go
exit /b 0

:syncfile_go
if not exist "%SRC%\%REL%" goto syncfile_gone
rem a new build can add folders, so the parent has to exist first
for %%d in ("%~dp0%REL%") do if not exist "%%~dpd" mkdir "%%~dpd" 2>nul
copy /Y "%SRC%\%REL%" "%~dp0%REL%" >nul 2>&1
if not errorlevel 1 echo              %REL%
if not errorlevel 1 set /a NCOP+=1
exit /b 0

:syncfile_gone
rem a path main no longer has was deleted there: drop the local copy too
if not exist "%~dp0%REL%" exit /b 0
del /q "%~dp0%REL%" >nul 2>&1
if not errorlevel 1 set /a NDEL+=1
exit /b 0

:dragonbar
rem %1 = kilobytes so far, %2 = total kilobytes -> BAR: 20 cells, a body of =
rem and a head at the tip. The head must not be a redirect character: cmd
rem parses redirection after variable expansion, so a bar whose tip was > wrote
rem the left half of the bar into a file named after its right half.
setlocal EnableDelayedExpansion
set /a "C=(%~1)*20/(%~2)"
if !C! LSS 0 set "C=0"
if !C! GTR 20 set "C=20"
set "BAR="
for /l %%i in (1,1,20) do (
  if %%i LEQ !C! set "BAR=!BAR!="
  if %%i GTR !C! set "BAR=!BAR!-"
)
endlocal & set "BAR=%BAR%"
exit /b 0

:drawdl
rem %1 = kilobytes so far, %2 = rate and time left. One status line, kept at
rem the bottom and rewritten where the terminal understands ANSI. Elsewhere the
rem same line is printed once every half minute, because neither a carriage
rem return through set /p nor clearing the window works there: the first ran
rem the bars together and the second blinked.
if not defined DLHEAD goto drawdl_head
call :dragonbar %~1 194560
set /a DLMB=%~1/1024
set /a DLTENTH=%~1*10/1024-DLMB*10
set "DLTLINE=[%BAR%]  %DLMB%.%DLTENTH%/190 MB"
if not "%~2"=="" set "DLTLINE=[%BAR%]  %DLMB%.%DLTENTH%/190 MB   %~2"
if "%VT%"=="1" call :dltxt "%DLTLINE%"
if "%VT%"=="1" exit /b 0
set /a TICK=SECS%%30
if not %TICK%==0 exit /b 0
echo      %DLTLINE%
exit /b 0

:drawdl_head
set "DLHEAD=1"
echo.
echo   Fetching the newest build of the game.
echo.
echo   Keep this window open - the game starts by itself when the download
echo   is done.
echo.
call :drawdl %~1 ""
exit /b 0

:dltxt
rem %1 = the whole status line. Where ANSI works the line is cleared and
rem rewritten, so there is exactly one bar and it stays where it is; the caller
rem prints ordinary lines where it does not.
if not "%VT%"=="1" echo      %~1
if not "%VT%"=="1" exit /b 0
<nul set /p "=%ESC%[2K%ESC%[1G      %~1"
exit /b 0

:dlend
rem finishes a status line that was written without a newline
if not "%VT%"=="1" exit /b 0
echo.
exit /b 0

:vtdetect
rem conhost understands ANSI once this is switched on; the value is a REG_DWORD
rem of 0x1, and anything else - or no key at all - leaves the plain display.
if not exist "%SYS%\reg.exe" exit /b 0
"%SYS%\reg.exe" query "HKCU\Console" /v VirtualTerminalLevel 2>nul | "%FINDSTR%" /c:"0x1" >nul
if errorlevel 1 exit /b 0
set "VT=1"
exit /b 0

:sayupdate
rem %1 = main's short commit (may be empty when the check could not ask),
rem %2 = the commit this folder last applied (may be empty). Says plainly
rem whether there is anything to fetch, so Continue/Exit is an informed choice.
echo   ==============================================================
echo.
if "%~2"=="" goto sayupdate_first
if "%~1"=="" goto sayupdate_unknown
if "%~1"=="%~2" goto sayupdate_same
echo   Update available: main @ %~1
echo   This folder has:  %~2
goto sayupdate_done
:sayupdate_same
echo   Up to date:       main @ %~1 is already in this folder.
echo   Nothing to download.
goto sayupdate_done
:sayupdate_first
if "%~1"=="" echo   Update available: could not read main's version.
if not "%~1"=="" echo   Update available: main @ %~1
echo   This folder has:  nothing recorded yet - the first update is the big one.
goto sayupdate_done
:sayupdate_unknown
echo   Update available: main's version could not be read, so this run would
echo                      fetch the whole archive (%APPLIED% is what is here).
:sayupdate_done
echo.
exit /b 0

:choose
rem Continue or leave: one keypress, no Enter. choice.exe ships with every
rem Windows since Vista; where it is missing, pause keeps the window open
rem instead of running past the question.
if defined ASKED exit /b 0
set "ASKED=1"
if not exist "%SYS%\choice.exe" goto choose_pause
"%SYS%\choice.exe" /c ce /n /m "   C = continue    E = exit   "
echo.
if errorlevel 2 exit /b 1
exit /b 0
:choose_pause
pause
exit /b 0

:clock
rem %1 = seconds, %2 = the variable to leave the time in. Hours once it runs
rem past one, so a slow line reads 2h 4m instead of 124:33.
set /a "CK_H=%~1/3600"
set /a "CK_M=(%~1%%3600)/60"
set /a "CK_S=%~1%%60"
set "CK_T=%CK_M%:%CK_S%"
if %CK_S% LSS 10 set "CK_T=%CK_M%:0%CK_S%"
if %CK_H% GEQ 1 set "CK_T=%CK_H%h %CK_M%m"
set "%~2=%CK_T%"
exit /b 0


:sleep
rem ping is the only delay Windows always has, whatever is on PATH - but if
rem it cannot run, every wait returns at once and the redraw loop spins at
rem full speed, blinking and writing a file per frame.
set /a "P=%~1+1"
if exist "%PING%" "%PING%" -n %P% 127.0.0.1 >nul 2>&1
if exist "%PING%" exit /b 0
if defined POWERSHELL "%POWERSHELL%" -NoProfile -Command "Start-Sleep -Seconds %~1" >nul 2>&1
if defined POWERSHELL exit /b 0
"%SYS%\timeout.exe" /t %~1 /nobreak >nul 2>&1
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

:quit
rem Reached when E is pressed: nothing has been fetched, copied or deleted.
echo   Nothing was changed. Closing.
call :sleep 3
exit 0
