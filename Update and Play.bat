@echo off
if /i "%~1"=="--body" goto body
rem ---------------------------------------------------------------------------
rem  A batch file that runs off its own end leaves nothing behind: no message,
rem  no prompt - the window simply closes. Every "it showed the pistol and then
rem  went away" is that, and there is nothing left to read afterwards. So this
rem  file runs the rest of itself as a child. If the child reaches one of its
rem  own endings it decides what the window does: a finished run closes it and a
rem  reported failure waits for its pause. If it does not, this window is still
rem  here to say where it stopped, and to read its log back.
rem ---------------------------------------------------------------------------
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Big Trouble in Little China: The Game - Updater
set "REPO=jackrabbit72380/bigtroubleinlittlechinathegame"
set "BOOT=%TEMP%\btilc-updater"
if not exist "%BOOT%" mkdir "%BOOT%" 2>nul
rem The run log goes beside the game, in save\logs, where it is found by
rem looking in the folder the player already knows. A folder that refuses
rem writes falls back to the temp copy, and the window says which one it wrote.
set "LOGDIR=%~dp0save\logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%" 2>nul
set "LOG="
if exist "%LOGDIR%" set "LOG=%LOGDIR%\btilc-updater.log"
if not defined LOG if exist "%BOOT%" set "LOG=%BOOT%\last-run.log"
if not defined LOG set "LOG=%TEMP%\btilc-updater.log"
set "LOGQ=%LOG:'=''%"
rem The last line of the previous run is read before this run replaces the
rem file: it is the step that run stopped on, and it is the first thing the
rem new log says, so one file carries both runs and the one before them.
set "PREV="
if exist "%LOG%" for /f "usebackq delims=" %%L in ("%LOG%") do set "PREV=%%L"
>"%LOG%" echo [%DATE% %TIME%] launcher start  arg=%~1 2>nul
if defined PREV call :say previous run stopped after: %PREV%
rem Everything the rest of the file does is added under these two lines.
call "%~f0" --body %*
goto stopped
:stopped
set "RC=%ERRORLEVEL%"
echo.
echo The updater stopped before it started the game, and nothing it printed says
echo why: a batch file that runs off its own end leaves no message behind.
echo.
"%SystemRoot%\System32\findstr.exe" /c:"btilc-launcher-end" "%~f0" >nul 2>&1
if errorlevel 1 goto stopped_cut
echo It ran off the end of a whole file, so its log says where it got to:
echo.
if not exist "%LOG%" goto stopped_nolog
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -Command "Get-Content -LiteralPath '%LOGQ%' -Tail 16" 2>nul
goto stopped_tail
:stopped_nolog
echo   (no log was written)
:stopped_tail
echo.
echo   saved as  %LOG%
echo.
pause
exit /b 1
:stopped_cut
echo This file is cut short: it stops part way through itself, which is why the
echo window closes here with nothing to show.
echo.
echo Save a whole one over this file:
echo.
echo   https://raw.githubusercontent.com/%REPO%/main/Update%%20and%%20Play.bat
echo.
pause
exit /b 1
:body
shift
rem ===========================================================================
rem  BIG TROUBLE IN LITTLE CHINA - Updater v55
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
rem The version the title bar, the banner and the run log all read, so the
rem three cannot drift apart when the script is bumped.
set "UPDVER=71"
title Big Trouble in Little China: The Game - Updater v%UPDVER%

rem ---------------------------------------------------------------------------
rem  The run log first: before the pistol, before the console is asked for its
rem  mode, before a single thing is looked for. It used to be opened sixty lines
rem  below the pistol, and every step in between - the exe check, the write test,
rem  six hash snapshots, the cache folder - ran with no log at all. A window that
rem  closed in there left nothing behind to read, which is what "it drew the gun
rem  and went away, and there is no log" was.
rem ---------------------------------------------------------------------------
rem Everything this launcher writes goes to the temp folder. A game folder can
rem be read only, on a drive with no room, or behind a path cmd will not take, and
rem a cache that cannot be written breaks every redirect after it - which is what
rem left the download sitting at zero with no curl running behind it.
set "CACHE=%TEMP%\btilc-updater"
rem What an update writes. The launchers and tools are in here because they
rem ARE the delivery: a fix to Play Big Trouble.bat or
rem tools\test_local.py could never reach a folder that only refreshed the
rem game folders, which is how the launcher kept a console open over the game
rem long after the fix for it was on main.
set "GAMEPATHS=data chars stages font external sound tools "Update and Play.bat" "Play Big Trouble.bat" "Apply main.zip.bat" "Dump Stage Art.bat""
rem The helpers below take their paths inside PowerShell single quotes, where
rem an apostrophe ends the string. Doubling it is how PowerShell writes the
rem character itself, so this is the copy they are given.
set "CQ=%CACHE:'=''%"
if not exist "%CACHE%" mkdir "%CACHE%" 2>nul
if not exist "%CACHE%" set "CACHE=%TEMP%"
rem The log sits beside the game, in save\logs, where it is found without
rem knowing about the temp folder; the wrapper has already opened it there and
rem quoted the last run's final line. A folder that refuses writes falls back
rem to the temp copy.
set "LOGDIR=%~dp0save\logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%" 2>nul
if not exist "%LOGDIR%" set "LOGDIR=%CACHE%"
set "LOG=%LOGDIR%\btilc-updater.log"
if not exist "%LOG%" set "LOG=%CACHE%\last-run.log"
>>"%LOG%" echo [%DATE% %TIME%] launcher v%UPDVER% running, folder %~dp0 2>nul
call :log step 1 folder "%~dp0"

set "SYS=%SystemRoot%\System32"
set "PING=%SYS%\ping.exe"
set "TAR=%SYS%\tar.exe"
set "CURL=%SYS%\curl.exe"
set "FINDSTR=%SYS%\findstr.exe"
set "FIND=%SYS%\find.exe"
set "TASKLIST=%SYS%\tasklist.exe"
set "ROBOCOPY=%SYS%\robocopy.exe"
set "WHERE=%SYS%\where.exe"
set "POWERSHELL=%SYS%\WindowsPowerShell\v1.0\powershell.exe"
set "CERT=%SYS%\certutil.exe"
if not exist "%TAR%" set "TAR="
if not exist "%CURL%" set "CURL="
if not exist "%POWERSHELL%" set "POWERSHELL="
if not exist "%WHERE%" set "WHERE="
if not exist "%FIND%" set "FIND="
if not exist "%CERT%" set "CERT="
call :log step 2 windows tools looked up
if not defined CURL call :log   no curl here: PowerShell or the archive is used
if not defined POWERSHELL call :log   no PowerShell here

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


call :say "=============================================================="
call :say "BIG TROUBLE IN LITTLE CHINA  -  THE GAME  -  Updater v%UPDVER%"
call :say "=============================================================="
rem The number that counts the run is written at the end of the pistol's
rem barrel, so the console is asked for cursor control before the drawing.
call :vt
call :log step 3 console mode vt=%VTOK%
call :gun
call :log step 4 pistol drawn

set "EXE="
if exist "BigTroubleInLittleChinaTheGame.exe" set "EXE=BigTroubleInLittleChinaTheGame.exe"
if not defined EXE if exist "Ikemen_GO.exe" set "EXE=Ikemen_GO.exe"
call :log step 5 exe beside the launcher: %EXE%
if not defined EXE goto wrongfolder
call :log folder "%~dp0"  exe %EXE%
rem A refused write here means every write below will be refused too, one file
rem at a time with the same "Access is denied" line. But a scanner can hold a
rem file that was created a moment ago, and a copied folder carries a read-only
rem flag, so this is tried three times and the flag cleared before believing it.
rem Whatever Windows says is kept, so the message can name the real reason.
set "WT=%~dp0.btilc-write-test"
set "WERR=%TEMP%\btilc-wtest.err"
if exist "%WERR%" del /q "%WERR%" >nul 2>&1
attrib -r "%~dp0." >nul 2>&1
set /a WTRY=0
:writecheck
set /a WTRY+=1
>"%WT%" echo x 2>"%WERR%"
if exist "%WT%" goto writeok
attrib -r "%WT%" >nul 2>&1
if %WTRY% GEQ 3 goto folder_denied
call :sleep 1
goto writecheck
:writeok
del /q "%WT%" >nul 2>&1
attrib -r "%WT%" >nul 2>&1
del /q "%WT%" >nul 2>&1
set "WT="
call :log folder accepts writes (try %WTRY%)

rem Hash the data files this run reports on at the end. Taken before
rem anything is written, so the report can say which of them this update
rem actually changed - a file count cannot tell you that data\fight.def
rem arrived, and a commit id cannot either.
set "H1="
set "H2="
set "H3="
set "H4="
set "H5="
set "H6="
call :snap "data\fight.def" H1
call :snap "data\music.json" H2
call :snap "data\select.def" H3
call :snap "data\ikemen1\system.def" H4
call :snap "external\mods\musicselect.lua" H5
call :snap "external\mods\modnotice.lua" H6

set "REPO=jackrabbit72380/bigtroubleinlittlechinathegame"
set "ZIPURL=https://codeload.github.com/%REPO%/zip/refs/heads/main"
set "ZIPURL2=https://github.com/%REPO%/archive/refs/heads/main.zip"
set "GITURL=https://github.com/%REPO%.git"
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
set "DLOK="
set "GITTRIED="
set "GITFIXED="
set "GITQUIET="
set "GITLOCKED="
set "GWAIT=0"
rem The updater's repository is kept here from now on: per user, writable,
rem and outside the game folder, which is the folder a scanner, a backup
rem tool or the running game holds open. Temp is only the fallback.
set "GITSTORE=%LOCALAPPDATA%\BigTroubleInLittleChina\updater-git"
if not defined LOCALAPPDATA set "GITSTORE=%CACHE%"

rem This window first makes sure it IS the current launcher. Until now the
rem launcher was not in the six folders the update writes, so a fix to it
rem could never reach a folder running an older copy - a window on v19 was
rem still failing against a repository already fixed at v24. Nothing else
rem here is worth doing with an out-of-date script.
call :selfupdate %1
call :log step 6 launcher check returned

call :log step 7 checking for updates
call :pct 2 "Checking for updates"
call :log step 7 done, no archive waiting in this folder
if exist "%~dp0main.zip" goto manualzip
if exist "%~dp0bigtroubleinlittlechinathegame-main.zip" goto manualzip2
rem nothing left over from an interrupted run may be mistaken for an archive
if exist "%CACHE%\main-1.zip" del /q "%CACHE%\main-1.zip" >nul 2>&1
if exist "%CACHE%\main-2.zip" del /q "%CACHE%\main-2.zip" >nul 2>&1
if exist "%CACHE%\main.zip" del /q "%CACHE%\main.zip" >nul 2>&1
call :log step 8 looking for git
if not exist "%WHERE%" goto download
"%WHERE%" git >nul 2>&1
if errorlevel 1 goto probe
set "GITOK=1"
goto trygit

:manualzip
call :barflush
call :say "Using main.zip from this folder - no download needed."
set "ZIP=%CACHE%\main-1.zip"
copy /Y "%~dp0main.zip" "%ZIP%" >nul
call :zipcheck
if "%ZIPOK%"=="1" goto havezip
call :say "That main.zip is incomplete - downloading instead."
goto download

:manualzip2
call :barflush
call :say "Using main.zip from this folder - no download needed."
set "ZIP=%CACHE%\main-1.zip"
copy /Y "%~dp0bigtroubleinlittlechinathegame-main.zip" "%ZIP%" >nul
call :zipcheck
if "%ZIPOK%"=="1" goto havezip
call :say "That zip is incomplete - downloading instead."
goto download

rem ---- transport 1: git, working on this folder's own files --------------
rem The art already here is the thing being compared. Git is pointed at the
rem folder and hashes what is in it, so a file that already matches main is
rem never downloaded: only the blobs whose content really differs are fetched,
rem and they are fetched straight into place. No second copy of the art is
rem kept, and the folders the game never uses - artifacts, art_src, tools -
rem are outside the paths below and are left alone.
:trygit
call :log step 9 git route
call :pct 4 "Contacting GitHub"

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
call :barflush
rem A bundle git names but cannot read fails every fetch, and git can sit on
rem the connection for a long time before it says so. That is knowable here: if
rem git points at a file this machine does not have and no bundle was found
rem beside it, the archive is taken straight away instead of stalling.
set "GITCAFILE="
for /f "delims=" %%c in ('git config --get http.sslCAInfo 2^>nul') do set "GITCAFILE=%%c"
if not defined GITCAFILE goto gitca_checked
if defined GITBUNDLE goto gitca_checked
if exist "%GITCAFILE%" goto gitca_checked
call :say "Git cannot read its certificate bundle: %GITCAFILE%"
call :say "Using the verified download instead."
goto probe
:gitca_checked
if exist ".git" goto githere

:gitinit
call :pct 6 "Preparing the index"
rem Also reached when the updater's own repository has to be rebuilt. It holds
rem no player data - the game folder is the working tree - so throwing it away
rem costs a re-read of the folders, never a download.
rem
rem It is kept in the per-user folder rather than in the game folder. Git
rem writes to its repository constantly: an index on every diff, a config when
rem a setting is set. In a game folder those writes are exactly what Windows
rem refuses with "being used by another process" while the game, an antivirus
rem or a backup tool has the folder open, and every one of those failures used
rem to end in a 190 MB download. The game folder is only the working tree now,
rem so the only thing ever written into it is a file whose content changed.
set "GIT_DIR="
set "GIT_WORK_TREE="
if not exist "%GITSTORE%" mkdir "%GITSTORE%" 2>nul
if exist "%GITSTORE%\.git\HEAD" goto gitinit_have
git init -q "%GITSTORE%" >"%CACHE%\git.log" 2>&1
if errorlevel 1 goto gitfail
:gitinit_have
set "GIT_DIR=%GITSTORE%\.git"
set "GIT_WORK_TREE=%~dp0"
git config --local ikemen.updater 1 >>"%CACHE%\git.log" 2>&1
git symbolic-ref HEAD refs/heads/main >>"%CACHE%\git.log" 2>&1
git remote add origin "%GITURL%" >>"%CACHE%\git.log" 2>&1
git config --local remote.origin.promisor true >>"%CACHE%\git.log" 2>&1
git config --local remote.origin.partialclonefilter blob:none >>"%CACHE%\git.log" 2>&1
git config --local core.longpaths true >>"%CACHE%\git.log" 2>&1
git config --local http.version HTTP/1.1 >>"%CACHE%\git.log" 2>&1
goto gitfetch

:gitmigrate
call :pct 8 "Moving the index"
rem An older launcher kept its repository in the game folder. That is the copy
rem a scanner, a backup tool or the game itself holds open, and a file held
rem open is what turned an update into "The process cannot access the file
rem because it is being used by another process" and then into the 190 MB
rem archive. The repository lives outside the game folder now, so the one here
rem is removed; nothing in it is player-visible, and if it cannot be removed it
rem is simply ignored, because every git command below names the new one.
rd /s /q "%~dp0.git" >nul 2>&1
goto gitinit

:githere
call :pct 10 "Reading the index"
rem A folder somebody cloned themselves is their checkout: this launcher
rem will not fetch into it, check anything out, or overwrite uncommitted
rem work. It only says so and starts the game.
set "MINE="
for /f %%m in ('git config --local --get ikemen.updater 2^>nul') do set "MINE=%%m"
if "%MINE%"=="1" goto gitmigrate
git rev-parse --verify -q HEAD >nul 2>&1
if errorlevel 1 goto gitfetch
call :barflush
echo This is your own git checkout - run: git pull
goto launch

rem ---- transport 1: git ----------------------------------------------------
rem Only main's commit and its file list are fetched, a few hundred KB. The art
rem is fetched later, one blob at a time, and only for the files that differ.
:gitfetch
call :pct 12 "Fetching the list"
if exist "%CACHE%\git.log" del /q "%CACHE%\git.log" >nul 2>&1
rem The fetch runs in a helper so this window can show that it is waiting and
rem for how long, instead of sitting on one line while the network answers.
rem The helper inherits GIT_DIR and GIT_WORK_TREE from this shell, so it works
rem on the same repository and the same folder.
set "FOK=%CACHE%\fetch.ok"
set "FBAD=%CACHE%\fetch.bad"
if exist "%FOK%" del /q "%FOK%" >nul 2>&1
if exist "%FBAD%" del /q "%FBAD%" >nul 2>&1
set "FBAT=%CACHE%\fetch.bat"
>  "%FBAT%" echo @echo off
>> "%FBAT%" echo cd /d "%~dp0."
>> "%FBAT%" echo git -c core.longpaths=true -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=60 fetch --depth 1 --filter=blob:none --no-tags origin main ^>"%CACHE%\fetch.out" 2^>^>"%CACHE%\git.log"
>> "%FBAT%" echo if errorlevel 1 (echo x^>"%FBAD%") else (echo x^>"%FOK%")
if not exist "%FBAT%" goto gitfetch_plain
start "" /b cmd /c ""%FBAT%""
call :spinwait "%FOK%" "%FBAD%" "asking main for the file list (about 300 KB)" 900
goto gitfetch_checked
:gitfetch_plain
git -c core.longpaths=true -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=60 fetch --depth 1 --filter=blob:none --no-tags origin main >>"%CACHE%\git.log" 2>&1
:gitfetch_checked
if errorlevel 1 call :gitfetch_retry
if errorlevel 1 goto gitfail
set "NEWSHORT="
for /f %%s in ('git rev-parse --short FETCH_HEAD 2^>nul') do set "NEWSHORT=%%s"
call :log main is %NEWSHORT%
call :gamelock
git -c core.quotepath=false ls-tree -r FETCH_HEAD -- %GAMEPATHS% >"%CACHE%\tree.txt" 2>>"%CACHE%\git.log"
if errorlevel 1 goto gitfail
call :plan
rem a comparison that could not run must never pass as "already current"
if errorlevel 1 goto gitfail
if not exist "%CACHE%\changed.txt" goto gitfail
set "NCH=0"
for /f "usebackq delims=" %%c in ("%CACHE%\changed.txt") do set /a NCH+=1
call :log %NCH% file(s) differ from main
if "%NCH%"=="0" goto gitnone
set /a NDONE=0
set /a BCOUNT=0
set /a BSTEP=NCH/10
if %BSTEP% LSS 1 set "BSTEP=1"
set "BATCH="
set "WRITEFAIL="
del /q "%CACHE%\todo.txt" >nul 2>&1
for /f "usebackq delims=" %%c in ("%CACHE%\changed.txt") do call :gitone "%%c"
call :gitflush
if defined WRITEFAIL goto gitfail
call :bar %NDONE% %NCH%
call :barflush
call :confirm
goto gitdrop_list
:gitnone
rem the manifest compares main with main; the stamp compares main with this
rem folder, so a folder that never received the last update is caught here
call :stamp
if not defined STALE goto gitnone_ok
if exist "%CACHE%\manifest.txt" del /q "%CACHE%\manifest.txt" >nul 2>&1
call :barflush
call :say "This folder does not match main - comparing the files themselves."
goto gitfetch
:gitnone_ok
call :pct 100 "Already up to date"
call :barflush
call :say "Already up to date - nothing to download"
goto gitdrop_list
:plan
call :pct 16 "Comparing with main"
rem A file is fetched only when main's hash for it differs from the hash this
rem launcher recorded when it last wrote the folder. Nothing on disk is read,
rem so an unchanged folder is two small lists compared as text - a second or
rem two, where the old build re-hashed 190 MB of art on every launch.
if not defined POWERSHELL goto plan_first
if not exist "%CACHE%\manifest.txt" goto plan_first
call :plan_ps
if errorlevel 1 goto plan_first
exit /b 0
:plan_first
call :pct 18 "Reading this folder"
rem Nothing recorded yet - the first run on this folder. Prime git's index in
rem ONE pass: that hashes the files already here instead of downloading them,
rem and then git can say exactly which of them differ from main. It runs in a
rem helper for the same reason the fetch does: so the window shows it working.
set "QOK=%CACHE%\plan.ok"
set "QBAD=%CACHE%\plan.bad"
if exist "%QOK%" del /q "%QOK%" >nul 2>&1
if exist "%QBAD%" del /q "%QBAD%" >nul 2>&1
set "QBAT=%CACHE%\plan.bat"
>  "%QBAT%" echo @echo off
>> "%QBAT%" echo cd /d "%~dp0."
>> "%QBAT%" echo git ls-tree -r --name-only FETCH_HEAD -- %GAMEPATHS% ^>"%CACHE%\paths.txt" 2^>^>"%CACHE%\git.log"
>> "%QBAT%" echo if errorlevel 1 (echo x^>"%QBAD%") ^& exit /b 1
>> "%QBAT%" echo git update-index --add --replace --stdin ^<"%CACHE%\paths.txt" ^>^>"%CACHE%\git.log" 2^>^&1
>> "%QBAT%" echo git -c core.quotepath=false diff-index --name-only FETCH_HEAD -- %GAMEPATHS% ^>"%CACHE%\changed.txt" 2^>^>"%CACHE%\git.log"
>> "%QBAT%" echo if errorlevel 1 (echo x^>"%QBAD%") ^& exit /b 1
>> "%QBAT%" echo echo.^>"%CACHE%\dropped.txt"
>> "%QBAT%" echo echo x^>"%QOK%"
if not exist "%QBAT%" goto plan_first_direct
start "" /b cmd /c ""%QBAT%""
call :spinwait "%QOK%" "%QBAD%" "reading the files already here (one pass, no download)" 1800
if not errorlevel 1 exit /b 0
exit /b 1
:plan_first_direct
git ls-tree -r --name-only FETCH_HEAD -- %GAMEPATHS% >"%CACHE%\paths.txt" 2>>"%CACHE%\git.log"
if errorlevel 1 exit /b 1
git update-index --add --replace --stdin <"%CACHE%\paths.txt" >>"%CACHE%\git.log" 2>&1
git -c core.quotepath=false diff-index --name-only FETCH_HEAD -- %GAMEPATHS% >"%CACHE%\changed.txt" 2>>"%CACHE%\git.log"
if errorlevel 1 exit /b 1
echo.>"%CACHE%\dropped.txt"
exit /b 0
:plan_ps
call :pct 20 "Comparing the file lists"
set "PLANPS=%CACHE%\plan.ps1"
>  "%PLANPS%" echo param([string]$Tree, [string]$Old, [string]$Changed, [string]$Dropped)
>> "%PLANPS%" echo $ErrorActionPreference = 'Stop'
>> "%PLANPS%" echo $prev = @{}
>> "%PLANPS%" echo foreach ($l in (Get-Content -LiteralPath $Old)) { $i = $l.IndexOf([char]9); if ($i -gt 0) { $prev[$l.Substring($i + 1)] = $l.Substring(0, $i) } }
>> "%PLANPS%" echo $new = @{}
>> "%PLANPS%" echo $chg = New-Object System.Collections.ArrayList
>> "%PLANPS%" echo foreach ($l in (Get-Content -LiteralPath $Tree)) { $i = $l.IndexOf([char]9); if ($i -lt 1) { continue }; $meta = $l.Substring(0, $i).Split(' '); $sha = $meta[$meta.Length - 1]; $p = $l.Substring($i + 1); $new[$p] = $sha; if ($prev.ContainsKey($p) -and $prev[$p] -eq $sha) { continue }; [void]$chg.Add($p) }
>> "%PLANPS%" echo $drop = New-Object System.Collections.ArrayList
>> "%PLANPS%" echo foreach ($p in $prev.Keys) { if (-not $new.ContainsKey($p)) { [void]$drop.Add($p) } }
>> "%PLANPS%" echo Set-Content -LiteralPath $Changed -Value @($chg) -Encoding ASCII
>> "%PLANPS%" echo Set-Content -LiteralPath $Dropped -Value @($drop) -Encoding ASCII
if not exist "%PLANPS%" exit /b 1
rem Run in a helper that writes a marker, the way the fetch and the index pass
rem already do: the window then says it is working every five seconds, and a
rem helper that never returns cannot leave the run sitting on 20% for ever. A
rem late marker counts as a failure and :plan compares the files themselves
rem instead - slower, but always right.
set "POK=%CACHE%\planps.ok"
set "PBAD=%CACHE%\planps.bad"
if exist "%POK%" del /q "%POK%" >nul 2>&1
if exist "%PBAD%" del /q "%PBAD%" >nul 2>&1
set "PBAT=%CACHE%\planps.bat"
>  "%PBAT%" echo @echo off
>> "%PBAT%" echo cd /d "%~dp0."
>> "%PBAT%" echo "%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%PLANPS%" -Tree "%CACHE%\tree.txt" -Old "%CACHE%\manifest.txt" -Changed "%CACHE%\changed.txt" -Dropped "%CACHE%\dropped.txt" ^>^>"%CACHE%\git.log" 2^>^&1
>> "%PBAT%" echo if errorlevel 1 (echo x^>"%PBAD%") else (echo x^>"%POK%")
if not exist "%PBAT%" goto plan_ps_direct
start "" /b cmd /c ""%PBAT%""
call :spinwait "%POK%" "%PBAD%" "comparing with main" 120
if errorlevel 1 exit /b 1
exit /b 0
:plan_ps_direct
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%PLANPS%" -Tree "%CACHE%\tree.txt" -Old "%CACHE%\manifest.txt" -Changed "%CACHE%\changed.txt" -Dropped "%CACHE%\dropped.txt" 2>>"%CACHE%\git.log"
if errorlevel 1 exit /b 1
exit /b 0
:gitone
rem %1 = one path. Paths are collected into one checkout of a dozen files: one
rem git process per file is what made a first run crawl.
set /a NDONE+=1
rem The last name in the batch is kept so a batch that will not land can say
rem which file it was working on, instead of a percentage and nothing else.
set "BLAST=%~nx1"
set "BATCH=%BATCH% "%~1""
>>"%CACHE%\todo.txt" echo %~1
set /a BCOUNT+=1
if %BCOUNT% GEQ 12 call :gitflush
set /a BMOD=NDONE %% BSTEP
if %BMOD%==0 call :bar %NDONE% %NCH%
exit /b 0
:gitflush
rem %BATCH% = the files waiting to be written, at most twelve. One git call for
rem twelve files is quicker than twelve calls, but the batch runs in a helper that
rem writes a marker, so the window says it is working every five seconds and a
rem file that will not land cannot leave the run on 79% looking exactly like a
rem slow one. Five minutes is well past a slow download of the biggest art here;
rem past that the batch is named, written to stuck.txt, and the run carries on -
rem :confirm hashes what landed and writes the rest again.
if not defined BATCH exit /b 0
call :log flush %BCOUNT% file(s), last %BLAST%
set "GOK=%CACHE%\flush.ok"
set "GBAD=%CACHE%\flush.bad"
if exist "%GOK%" del /q "%GOK%" >nul 2>&1
if exist "%GBAD%" del /q "%GBAD%" >nul 2>&1
rem The batch is written in this window. It used to be handed to a started
rem helper, and the wait on the helper's marker is where the run stopped: a
rem marker that never came, and a started batch file the shell could not find,
rem both ended the update with a message and no line in the log. Twelve files
rem are one quick checkout, and git says why in git.log when it refuses - with
rem the same low-speed limit the fetch carries, so a stalled transfer gives up
rem on its own instead of holding the window.
type nul > "%CACHE%\git.log"
git -c core.longpaths=true -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=60 checkout FETCH_HEAD -- %BATCH% >>"%CACHE%\git.log" 2>&1
if errorlevel 1 goto gitflush_retry
call :log wrote %NDONE% of %NCH% file(s)

del /q "%CACHE%\todo.txt" >nul 2>&1
set "BATCH="
set /a BCOUNT=0
exit /b 0
:gitflush_retry
rem The batch did not finish. That is nearly always one file - one the game still
rem has open, or one an antivirus is reading - so its files are tried one at a
rem time and the window names the one that will not go, instead of a dozen names
rem and a percentage. Whatever fails is written to stuck.txt, and the recheck at
rem the end hashes everything that landed and writes the rest again.
call :gitflush_log
call :says "the batch did not finish - trying its files one at a time"
call :says "git refused - what it said is in btilc-updater.log"
for /f "usebackq delims=" %%f in ("%CACHE%\todo.txt") do call :gitfile "%%f"
del /q "%CACHE%\todo.txt" >nul 2>&1
set "BATCH="
set /a BCOUNT=0
exit /b 0
:gitfile
rem %1 = one path. Only reached after a batch refused, so it can afford a wait
rem of its own: the point here is the name, not the speed. Written in this
rem window, like the batch above, so a helper that cannot start cannot end the
rem run either.
call :log writing %~1
git -c core.longpaths=true -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=60 checkout FETCH_HEAD -- "%~1" >>"%CACHE%\git.log" 2>&1
set "G1OK=%CACHE%\flush1.ok"
set "G1BAD=%CACHE%\flush1.bad"
if exist "%G1OK%" del /q "%G1OK%" >nul 2>&1
if exist "%G1BAD%" del /q "%G1BAD%" >nul 2>&1

exit /b 0
:gitfile_stuck
set "WRITEFAIL=1"
>>"%CACHE%\stuck.txt" echo %~1
call :says "could not write %~nx1 - close the game, then run this again"
exit /b 0
:vt
rem The percentage is written on the barrel line itself, which means coming back
rem to a line that was printed earlier. cmd can only append, so the console is
rem asked for the mode that makes escape sequences work: up to the barrel, along
rem it to the muzzle, write, and back to the line under the drawing. Where a
rem console refuses - an older Windows, or this window's output going to a file -
rem VT stays unset and the number stays in the title bar.
if defined VTDONE exit /b 0
set "VTDONE=1"
if not defined POWERSHELL exit /b 0
rem The helper is one encoded call. Written out it is the text below, kept here
rem so it can be read; encoded because the same lines echoed into a file go
rem through cmd's parser, where a bracket or a parenthesis can turn a line into a
rem redirection and put "filename syntax is incorrect" on the art instead.
rem   $ErrorActionPreference = 'Stop'
rem   $sig = '[DllImport("kernel32.dll")] public static extern IntPtr GetStdHandle(int n); [DllImport("kernel32.dll")] public static extern bool GetConsoleMode(IntPtr h, out uint m); [DllImport("kernel32.dll")] public static extern bool SetConsoleMode(IntPtr h, uint m);'
rem   $k = Add-Type -MemberDefinition $sig -Name CM -Namespace Btilc -PassThru
rem   $h = $k::GetStdHandle(-11)
rem   $m = [uint32]0
rem   if (-not $k::GetConsoleMode($h, [ref]$m)) { exit 2 }
rem   $on = [uint32]($m -bor 4)
rem   if (-not $k::SetConsoleMode($h, $on)) { exit 3 }
rem   try { [IO.File]::WriteAllText("$env:TEMP\btilc-width.txt", "$([Console]::WindowWidth)") } catch { }
rem   exit 0
rem The width file from an earlier window would be a lie about this one.
if exist "%TEMP%\btilc-width.txt" del /q "%TEMP%\btilc-width.txt" >nul 2>&1
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -EncodedCommand JABFAHIAcgBvAHIAQQBjAHQAaQBvAG4AUAByAGUAZgBlAHIAZQBuAGMAZQAgAD0AIAAnAFMAdABvAHAAJwANAAoAJABzAGkAZwAgAD0AIAAnAFsARABsAGwASQBtAHAAbwByAHQAKAAiAGsAZQByAG4AZQBsADMAMgAuAGQAbABsACIAKQBdACAAcAB1AGIAbABpAGMAIABzAHQAYQB0AGkAYwAgAGUAeAB0AGUAcgBuACAASQBuAHQAUAB0AHIAIABHAGUAdABTAHQAZABIAGEAbgBkAGwAZQAoAGkAbgB0ACAAbgApADsAIABbAEQAbABsAEkAbQBwAG8AcgB0ACgAIgBrAGUAcgBuAGUAbAAzADIALgBkAGwAbAAiACkAXQAgAHAAdQBiAGwAaQBjACAAcwB0AGEAdABpAGMAIABlAHgAdABlAHIAbgAgAGIAbwBvAGwAIABHAGUAdABDAG8AbgBzAG8AbABlAE0AbwBkAGUAKABJAG4AdABQAHQAcgAgAGgALAAgAG8AdQB0ACAAdQBpAG4AdAAgAG0AKQA7ACAAWwBEAGwAbABJAG0AcABvAHIAdAAoACIAawBlAHIAbgBlAGwAMwAyAC4AZABsAGwAIgApAF0AIABwAHUAYgBsAGkAYwAgAHMAdABhAHQAaQBjACAAZQB4AHQAZQByAG4AIABiAG8AbwBsACAAUwBlAHQAQwBvAG4AcwBvAGwAZQBNAG8AZABlACgASQBuAHQAUAB0AHIAIABoACwAIAB1AGkAbgB0ACAAbQApADsAJwANAAoAJABrACAAPQAgAEEAZABkAC0AVAB5AHAAZQAgAC0ATQBlAG0AYgBlAHIARABlAGYAaQBuAGkAdABpAG8AbgAgACQAcwBpAGcAIAAtAE4AYQBtAGUAIABDAE0AIAAtAE4AYQBtAGUAcwBwAGEAYwBlACAAQgB0AGkAbABjACAALQBQAGEAcwBzAFQAaAByAHUADQAKACQAaAAgAD0AIAAkAGsAOgA6AEcAZQB0AFMAdABkAEgAYQBuAGQAbABlACgALQAxADEAKQANAAoAJABtACAAPQAgAFsAdQBpAG4AdAAzADIAXQAwAA0ACgBpAGYAIAAoAC0AbgBvAHQAIAAkAGsAOgA6AEcAZQB0AEMAbwBuAHMAbwBsAGUATQBvAGQAZQAoACQAaAAsACAAWwByAGUAZgBdACQAbQApACkAIAB7ACAAZQB4AGkAdAAgADIAIAB9AA0ACgAkAG8AbgAgAD0AIABbAHUAaQBuAHQAMwAyAF0AKAAkAG0AIAAtAGIAbwByACAANAApAA0ACgBpAGYAIAAoAC0AbgBvAHQAIAAkAGsAOgA6AFMAZQB0AEMAbwBuAHMAbwBsAGUATQBvAGQAZQAoACQAaAAsACAAJABvAG4AKQApACAAewAgAGUAeABpAHQAIAAzACAAfQANAAoAdAByAHkAIAB7ACAAWwBJAE8ALgBGAGkAbABlAF0AOgA6AFcAcgBpAHQAZQBBAGwAbABUAGUAeAB0ACgAIgAkAGUAbgB2ADoAVABFAE0AUABcAGIAdABpAGwAYwAtAHcAaQBkAHQAaAAuAHQAeAB0ACIALAAgACIAJAAoAFsAQwBvAG4AcwBvAGwAZQBdADoAOgBXAGkAbgBkAG8AdwBXAGkAZAB0AGgAKQAiACkAIAB9ACAAYwBhAHQAYwBoACAAewAgAH0ADQAKAGUAeABpAHQAIAAwAA== >nul 2>&1
if errorlevel 1 exit /b 0
rem The console took the mode. The escape character is the one byte below, in the
rem file itself, so nothing is read back, guessed, or lost on the way.
set "ESC="
set "VTOK=1"
exit /b 0

:gun
rem Jack's pistol, in the characters the concept art was drawn with, drawn once
rem under the game's title and left standing: the barrel fills with one pipe for
rem every percent of the run, and the count follows the last pipe, so the job
rem reads as rounds leaving the gun and ends on a full barrel at 100%.
rem The barrel ends at column 39 and the bar starts two columns later: one space
rem so the pipes do not touch the muzzle, and one so the count that follows the
rem last pipe does not touch the bar either. tools/check_launchers.py measures
rem both from the drawing, so a changed picture cannot leave them floating.
set "MUZZLE=53"
rem How many pipes this window has room for. One per percent, with the space and
rem the four characters of the count, needs a hundred and forty-six columns,
rem which a maximised window has; a narrower one gets the same bar squeezed into
rem the room it does have, because a line that wrapped would crawl down over the
rem drawing. :vt leaves the width in a file; without it the bar falls back to a
rem width every console has.
set "BARMAX=60"
if exist "%TEMP%\btilc-width.txt" for /f "usebackq delims=" %%w in ("%TEMP%\btilc-width.txt") do set /a BARMAX=%%w-%MUZZLE%-6
if %BARMAX% GTR 100 set "BARMAX=100"
if %BARMAX% LSS 10 set "BARMAX=10"
echo.
rem The title sits on the drawing's own left edge - four spaces in, where the
rem top line of the pistol starts - and carries the version the log records.
echo    BIG TROUBLE IN LITTLE CHINA  -  THE GAME  -  UPDATER v%UPDVER%
echo    ..._...^|..____________________, ,
echo    ....../ '---___________----_____^|##########^|]=
echo    ...../_=^(O^)^(O^)^(O^);;;_______.:/^|##########^|
echo    .....^), ---.^(_^(__^) /\
echo    ....// ^(..^) ^), ----"
echo    ...//___//
echo    ..//___//
echo    .//___//
set "GUNSHOWN=1"
rem The per cent sign is made once, here. The digits are given it later, so
rem no variable that holds a sign is ever read a second time by call, and no
rem sign sits against another in this file - the two things that once turned
rem the count into the letters of an escape sequence.
set "PCT=%%"
rem The full barrel is built once here and sliced per percent below, so a console
rem without cursor control redraws the picture without a loop per redraw.
if not defined BARFULL for /l %%P in (1,1,%BARMAX%) do call set "BARFULL=%%BARFULL%%="
rem The line under the drawing is remembered, so every percentage can write at
rem the muzzle and come straight back here. The messages that follow print
rem below the pistol, never over it.
if defined VTOK set /p "=%ESC%[s" <nul
rem The anchor sits on the blank row under the drawing: :ui writes the status
rem line one row below it and comes straight back, so the panel never scrolls.
set "SPCTX=0%%"
set "SSTEP=Starting up"
set "SDETAIL="
call :stext
call :panel_foot
rem A console that refused the cursor mode would otherwise sit on a bare picture
rem until the first step reports, which on a slow first check can be a while.
if not defined VTOK call :gunredraw 0 0
exit /b 0

:gauge
rem %1 = percent for the whole run. %2 is the name of the step: the callers still
rem pass it, and :pct says it in the window once per step.
rem
rem One pipe on the barrel for every percent, counting 1, 2, 3 ... 100, with the
rem number following the last pipe, and the game starts on a full barrel. A
rem console that takes cursor moves gets the bar; one that does not keeps the
rem number in the title bar, so an old Windows still shows how far the run is.
rem
rem A step that jumps from 12 to 25 fills in 13 to 24 as well, so no number is
rem skipped, and a step that re-reports the number it just showed prints nothing.
if "%~1"=="" exit /b 0
call :log pct %~1 vt=%VTOK%
set "GPCT=%~1"
if %GPCT% LSS 0 set "GPCT=0"
if %GPCT% GTR 100 set "GPCT=100"
rem One run, one number. A step that reports less than the one before it is a
rem label arriving late, not a rewind: the whole-process percentage only climbs.
if defined GMAXPCT if %GPCT% LSS %GMAXPCT% set "GPCT=%GMAXPCT%"
set "GMAXPCT=%GPCT%"
if not defined GLASTPCT goto gauge_print
set /a GADV=GPCT-GLASTPCT
if %GADV% GEQ 1 goto gauge_print
exit /b 0
:gauge_print
if not defined GLASTPCT set "GLASTPCT=0"
set /a GFROM=GLASTPCT+1
set /a GTO=GPCT
if %GTO% LSS %GFROM% set /a GFROM=GTO
for /l %%P in (%GFROM%,1,%GTO%) do call :gaugeone %%P "%~2"
set "GLASTPCT=%GTO%"
call :ui
exit /b 0

:gaugeone
rem %1 = the percent to show. This step adds the pipe for it to the barrel and
rem writes the count in the space right after the last pipe, so the bar and the
rem number grow together and 100% is a barrel filled end to end. Where the window
rem cannot hold a hundred pipes, two percentages share one and the bar still ends
rem full. Only one character and three digits change: the pistol is not redrawn.
set "GNUM=%~1"
call :log paint %~1 vt=%VTOK%
rem Padded while it is digits and nothing else. Nothing about the count is
rem handed to call: call reads its line a second time, and a per cent sign
rem read a second time has no partner left - that is the line cmd cannot
rem parse, and it answers by running the tail of it as an unknown command.
if %GNUM% LSS 10 set "GNUM=  %GNUM%"
if %GNUM% GEQ 10 if %GNUM% LSS 100 set "GNUM= %GNUM%"
set "PCTX=%GNUM%%PCT%"
if not defined VTOK goto gaugeone_plain
set /a GPOS=%~1*%BARMAX%/100
if %GPOS% LSS 1 set "GPOS=1"
set /a GCOL=%MUZZLE%+GPOS-1
rem Back to the line under the drawing, seven lines up to the barrel, along it to
rem this percent's pipe, the pipe itself, then the count after the bar, and the
rem rest of the line cleared so the number from the step before cannot leave a
rem digit standing past the new one.
rem
rem The write is assembled in three steps, each of which ends on a variable name.
rem A count written as a bare variable and then a per cent sign puts an escaped
rem percent straight against the next escape variable: cmd pairs the two and reads
rem the pair as text, so the cursor came back mid-sequence and the rest of the
rem line was printed as letters instead of a number.
rem Holding the per cent sign in PCTX and appending one piece at a time leaves no
rem such pair anywhere, and the finished string is expanded from GWRITE in one
rem go, so nothing in it is read as a variable again.
set "GWRITE=%ESC%[u%ESC%[7A%ESC%[%GCOL%G= "
set "GWRITE=%GWRITE%%PCTX%"
set "GWRITE=%GWRITE%%ESC%[K%ESC%[u"
set /p "=%GWRITE%" <nul
call :log painted %~1 on the barrel
title Big Trouble in Little China: The Game - Updater - %~1 percent
exit /b 0
:gaugeone_plain
rem No cursor control here, so the count cannot be written back onto the
rem barrel the way the cursor version does it. The barrel line is drawn again
rem instead, with the count it has now at the muzzle, so the number counts up
rem where it belongs and nothing scrolls past underneath it. The bar is drawn
rem from "=" characters and never from pipes: a pipe arriving through a
rem variable inside a called label is read a second time as a pipeline, which
rem stopped a run dead at its very first percent.
set /a RPOS=%~1*%BARMAX%/100
if %~1 GTR 0 if %RPOS% LSS 1 set "RPOS=1"
call :gunredraw %~1 %RPOS%
:gaugeone_plain_title
call :log painted %~1 in the title
title Big Trouble in Little China: The Game - Updater - %~1 percent
exit /b 0

:gunredraw
call :log art %~1 pipes %~2
rem %1 = percent, %2 = how many pipes that is. The art is :gun's, with the barrel
rem filled and the count beside it, so a console that will not take cursor moves
rem still shows the run the way the window is meant to look. The pipes start two
rem columns past the drawn barrel's end, where the muzzle write puts them.
set "RBAR="
if defined BARFULL call set "RBAR=%%BARFULL:~0,%~2%%"
if not defined PCT set "PCT=%%"
set "RNUM=%~1"
if %RNUM% LSS 10 set "RNUM=  %RNUM%"
if %RNUM% GEQ 10 if %RNUM% LSS 100 set "RNUM= %RNUM%"
set "RPCT=%RNUM%%PCT%"
cls
echo.
echo    BIG TROUBLE IN LITTLE CHINA  -  THE GAME  -  UPDATER v%UPDVER%
echo    ..._...^|..____________________, ,
echo    ....../ '---___________----_____^|##########^|]=  %RBAR% %RPCT%
echo    ...../_=^(O^)^(O^)^(O^);;;_______.:/^|##########^|
echo    .....^), ---.^(_^(__^) /\
echo    ....// ^(..^) ^), ----"
echo    ...//___//
echo    ..//___//
echo    .//___//
rem The foot of the panel, drawn again with the art on a console that cannot
rem write in place: the status line, and the last thing said.
call :panel_foot
if defined SAY6 echo %SAY6%
call :log art %~1 drawn
exit /b 0

:bar
rem %1 = files written, %2 = files to write. Writing is 25-80% of the job.
if "%~2"=="0" exit /b 0
set /a GSTEP=%~1*55/%~2
set /a GOPCT=25+GSTEP
set "SPCTX=%GOPCT%%PCT%"
set "SSTEP=Writing files %~1 - %~2"
set "SDETAIL="
call :gauge %GOPCT% "Writing files"
exit /b 0

:pct
rem %1 = percent, %2 = the label for it. Both go on the panel's one status
rem line: the number says how far and the label says what it is counting.
if not "%~1"=="" set "SPCTX=%~1%PCT%"
if not "%~2"=="" set "SSTEP=%~2"
if not "%~2"=="" set "SDETAIL="
call :gauge %~1 "%~2"
call :ui
exit /b 0

:barflush
rem Every line ends itself now, so there is nothing to flush.
exit /b 0

:panel_foot
rem The status line under the drawing, in one place: :gun
rem draws it once when the window opens, :gunredraw redraws it on a console that
rem cannot write in place. It sits in a label of its own so the drawing above
rem stays the only echo block in :gun - the checker measures the muzzle column,
rem and the row the count comes back from, out of that block.
echo.
echo %STEXT%
exit /b 0

:stext
rem The panel's one line: the step, and the detail of the step. There is no
rem clock on it - a ticking time is noise next to the barrel. The count of
rem percent is not repeated here either: it is written at the muzzle, on the
rem barrel, where it moves with the pipes instead of sitting in two places.
set "STEXT="
if defined SSTEP set "STEXT=%SSTEP%"
if defined SDETAIL set "STEXT=%STEXT%   %SDETAIL%"
if not defined STEXT set "STEXT=Starting up"
exit /b 0

:ui
rem Writes that line where it belongs: the anchor :gun left is the rule under
rem the drawing and the status is one row below it. Nothing else prints there -
rem the old run stacked a line under the art for every step and every five
rem seconds of every wait, and that pile is what read as noise.
if not defined VTOK goto ui_plain
call :stext
set "UISEQ=%ESC%[u%ESC%[B%ESC%[1G%STEXT%%ESC%[K%ESC%[u"
set /p "=%UISEQ%" <nul
exit /b 0
:ui_plain
rem No cursor control, so the panel is drawn again from the top - and only
rem when the line has actually changed, or it would clear once a second.
call :stext
if defined UIPLAINLAST if "%UIPLAINLAST%"=="%STEXT%" exit /b 0
set "UIPLAINLAST=%STEXT%"
if not defined GPCT set "GPCT=0"
set /a RPOS=GPCT*BARMAX/100
call :gunredraw %GPCT% %RPOS%
exit /b 0

rem %1 = seconds waited, %2 = what is being waited for. One plain line every
rem five seconds: a spinner would have to redraw in place, which is the cursor
rem movement that broke the old progress bar on this console.
:spin
rem %1 = seconds waited, %2 = what is being waited for. The step named on the
rem panel is the one being waited for, so a slow step reads as work and never
rem as a freeze - which is how the 20% and the 79% stalls read before. The
rem seconds are kept in the title and the log, not on the panel.
if not "%~2"=="" set "SSTEP=%~2"
call :ui
exit /b 0
:spin_plain
if not "%~2"=="" set "SSTEP=%~2"
call :ui
exit /b 0

:spinwait
rem %1 ok marker, %2 bad marker, %3 label, %4 seconds before giving up.
rem The helper writes a marker instead of its exit code being read back: a
rem window that never starts, or a marker that cannot be written, must not look
rem like a step that succeeded.
set /a SW=0
:spinwait_loop
call :sleep 1
set /a SW+=1
if %SW% GEQ 15 if not exist "%~1" if not exist "%~2" call :spinwait_beat %SW% "%~3"
call :spin %SW% "%~3"
if exist "%~1" goto spinwait_ok
if exist "%~2" goto spinwait_bad
if %SW% GEQ %~4 goto spinwait_late
goto spinwait_loop
:spinwait_ok
exit /b 0
:spinwait_bad
exit /b 1
:spinwait_late
exit /b 2

:spinwait_beat
rem A wait that prints nothing reads as a hang, and a window with no new line
rem in it is closed before the work is done. The log keeps one line every
rem fifteen seconds, the title counts the seconds, and the window itself says
rem so once a minute.
title Big Trouble in Little China: The Game - Updater v%UPDVER% - %~2 %~1s
call :log still %~2 - %~1s
set /a SBMOD=%~1 %% 60
if %SBMOD%==0 call :says "still %~2 - %~1s"
exit /b 0

:gitflush_log
rem The lines git wrote while it refused. Echo, not call: a line of git output
rem is re-read by call, and a per cent sign in it is the class of line that ends
rem a batch.
if not defined LOG exit /b 0
if not exist "%CACHE%\git.log" exit /b 0
>>"%LOG%" echo git: %CACHE%\git.log
for /f "usebackq delims=" %%L in ("%CACHE%\git.log") do >>"%LOG%" echo git: %%L
exit /b 0
:confirm
call :pct 82 "Checking the writes"
rem A file that was just written is checked against main by CONTENT: it is
rem hashed and compared with the hash main holds for that exact path. A name, a
rem size or a timestamp that looks right is not evidence, and a write that
rem landed wrong is fetched again rather than being called done.
if not "%WHICH%"=="git" exit /b 0
if not defined POWERSHELL exit /b 0
if not exist "%CACHE%\changed.txt" exit /b 0
if not exist "%CACHE%\tree.txt" exit /b 0
set /a NCONF=0
for /f "usebackq delims=" %%c in ("%CACHE%\changed.txt") do set /a NCONF+=1
if "%NCONF%"=="0" exit /b 0
git hash-object --stdin-paths <"%CACHE%\changed.txt" >"%CACHE%\hashes.txt" 2>>"%CACHE%\git.log"
if errorlevel 1 exit /b 0
if not exist "%CACHE%\hashes.txt" exit /b 0
call :confirm_ps
if not exist "%CACHE%\bad.txt" exit /b 0
set /a NBAD=0
for /f "usebackq delims=" %%b in ("%CACHE%\bad.txt") do set /a NBAD+=1
if "%NBAD%"=="0" exit /b 0
call :pct 82 "Rechecking the writes"
copy /Y "%CACHE%\bad.txt" "%CACHE%\changed.txt" >nul
set "NCH=%NBAD%"
set /a NDONE=0
set /a BCOUNT=0
set /a BSTEP=NBAD/10
if %BSTEP% LSS 1 set "BSTEP=1"
set "BATCH="
set "WRITEFAIL="
del /q "%CACHE%\todo.txt" >nul 2>&1
for /f "usebackq delims=" %%c in ("%CACHE%\changed.txt") do call :gitone "%%c"
call :gitflush
git hash-object --stdin-paths <"%CACHE%\changed.txt" >"%CACHE%\hashes.txt" 2>>"%CACHE%\git.log"
call :confirm_ps
set /a NBAD=0
for /f "usebackq delims=" %%b in ("%CACHE%\bad.txt") do set /a NBAD+=1
if not "%NBAD%"=="0" echo %NBAD% file(s) still do not match - run this launcher again.
exit /b 0

:confirm_ps
set "CPS=%CACHE%\confirm.ps1"
set "BADL=%CACHE%\bad.txt"
if exist "%BADL%" del /q "%BADL%" >nul 2>&1
>  "%CPS%" echo param([string]$Tree, [string]$Paths, [string]$Hashes, [string]$Bad)
>> "%CPS%" echo $ErrorActionPreference = 'Stop'
>> "%CPS%" echo $want = @{}
>> "%CPS%" echo foreach ($l in (Get-Content -LiteralPath $Tree)) { $i = $l.IndexOf([char]9); if ($i -lt 1) { continue }; $m = $l.Substring(0, $i).Split(' '); $want[$l.Substring($i + 1)] = $m[$m.Length - 1] }
>> "%CPS%" echo $ps = @(Get-Content -LiteralPath $Paths)
>> "%CPS%" echo $hs = @(Get-Content -LiteralPath $Hashes)
>> "%CPS%" echo $mismatch = New-Object System.Collections.ArrayList
>> "%CPS%" echo for ($k = 0; $k -lt $ps.Count; $k++) { $p = $ps[$k]; if (-not $want.ContainsKey($p)) { continue }; if ($k -ge $hs.Count) { continue }; if ($hs[$k] -ne $want[$p]) { [void]$mismatch.Add($p) } }
>> "%CPS%" echo Set-Content -LiteralPath $Bad -Value @($mismatch) -Encoding ASCII
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%CPS%" -Tree "%CACHE%\tree.txt" -Paths "%CACHE%\changed.txt" -Hashes "%CACHE%\hashes.txt" -Bad "%BADL%" >nul 2>&1
exit /b 0

:gitdrop_list
call :pct 88 "Checking extra files"
rem Paths main no longer has, and which this launcher wrote, are removed. Only
rem the six game folders are ever touched - see :gitdrop.
if not exist "%CACHE%\dropped.txt" goto gitref
set /a NDR=0
for /f "usebackq delims=" %%p in ("%CACHE%\dropped.txt") do set /a NDR+=1
if %NDR% GTR 200 goto gitdrop_many
for /f "usebackq delims=" %%p in ("%CACHE%\dropped.txt") do call :gitdrop "%%p"
goto gitref
:gitdrop_many
call :barflush
rem Two hundred files do not disappear from main in one update. A list this
rem long means the comparison itself went wrong, and deleting on it would take
rem the game apart - which is exactly how external\script\main.lua once went
rem missing and the engine panicked on the next start.
echo %NDR% file(s) would be removed - that looks wrong, so nothing is deleted.
:gitref
rem Record what this folder now holds: main's file list with the hash of each.
rem The next launch compares against it as text, so it never re-reads the art.
if exist "%CACHE%\tree.txt" move /Y "%CACHE%\tree.txt" "%CACHE%\manifest.txt" >nul 2>&1
if defined NEWSHORT >"%CACHE%\applied.txt" echo %NEWSHORT%
git update-ref refs/heads/main FETCH_HEAD >>"%CACHE%\git.log" 2>&1
git symbolic-ref HEAD refs/heads/main >>"%CACHE%\git.log" 2>&1
set "WHICH=git"
if exist "%CACHE%\repo" rd /s /q "%CACHE%\repo" >nul 2>&1
goto copied

:gitwhy
rem Reads the log git just wrote and decides whether the failure was a file
rem another process holds. Those are worth retrying and are never worth a
rem download: the archive takes the same locks and fails the same way.
set "GITLOCKED="
if not exist "%CACHE%\git.log" exit /b 0
for %%w in ("being used by another process" "Access is denied" "Permission denied" "index.lock" "could not lock config file" "unable to create file") do (
  "%FINDSTR%" /i /c:%%w "%CACHE%\git.log" >nul 2>&1
  if not errorlevel 1 set "GITLOCKED=1"
)
exit /b 0

:gitunlock
rem Lock files are markers, never data. One left by an interrupted git, or one
rem a scanner is still holding, makes every later write fail with the same
rem message; clearing them is the whole repair.
if not exist "%GITSTORE%" exit /b 0
del /q "%GITSTORE%\.git\index.lock" >nul 2>&1
del /q "%GITSTORE%\.git\HEAD.lock" >nul 2>&1
del /q "%GITSTORE%\.git\config.lock" >nul 2>&1
del /q "%GITSTORE%\.git\shallow.lock" >nul 2>&1
del /q "%GITSTORE%\.git\FETCH_HEAD.lock" >nul 2>&1
del /q "%GITSTORE%\.git\packed-refs.lock" >nul 2>&1
del /q "%GITSTORE%\.git\gc.pid" >nul 2>&1
del /q "%GITSTORE%\.git\refs\heads\main.lock" >nul 2>&1
del /q "%GITSTORE%\.git\refs\remotes\origin\main.lock" >nul 2>&1
exit /b 0

:exehead
rem tasklist prints only the first 25 characters of an image name, so a search
rem for BigTroubleInLittleChinaTheGame.exe never matched the process this window
rem had just started - the update sat over a running game. The start of the name
rem is what tasklist prints in full, and it is what gets searched for now.
set "EXEHEAD="
if not defined EXE exit /b 0
for %%A in ("%EXE%") do set "EXEHEAD=%%~nA"
if defined EXEHEAD set "EXEHEAD=%EXEHEAD:~0,20%"
exit /b 0

:gamelock
call :exehead
call :barflush
rem The engine keeps its data files open while it runs and Windows will not let
rem git replace one. Updating under a running game fails with "being used by
rem another process", so this waits for it to close rather than writing into a
rem folder that cannot be written.
if not defined EXE exit /b 0
if not defined TASKLIST exit /b 0
"%TASKLIST%" /fi "imagename eq %EXE%" /nh 2>nul | "%FINDSTR%" /i /c:"%EXEHEAD%" >nul 2>&1
if errorlevel 1 exit /b 0
echo.
echo The game is running. Close it - this window continues by itself.
set /a GWAIT=0
:gamelock_wait
call :sleep 3
set /a GWAIT+=3
"%TASKLIST%" /fi "imagename eq %EXE%" /nh 2>nul | "%FINDSTR%" /i /c:"%EXEHEAD%" >nul 2>&1
if errorlevel 1 (
  echo            Closed - carrying on.
  exit /b 0
)
if %GWAIT% LSS 60 goto gamelock_wait
echo Still running after %GWAIT% seconds - continuing.
exit /b 0

:gitfail
rem A failed git step used to mean two things at once: rebuild .git from
rem scratch, and, if that failed too, download the whole 190 MB. Neither fits
rem the failure that actually happens - a file another process is holding,
rem the game still open, a second updater window, a scanner reading the folder
rem - because rebuilding does not release that handle and a download cannot
rem take it either. So the cheap repair comes first, the rebuild second, and a
rem lock is reported instead of being spent on an archive that would fail the
rem same way.
call :gitwhy
if not defined GITFIXED goto gitfail_fix
if not defined GITTRIED goto gitfail_rebuild
if defined GITLOCKED goto gitlocked
goto gitfail_final

:gitfail_fix
call :barflush
set "GITFIXED=1"
set "GITQUIET=1"
call :say
call :say "A file was in use - clearing git's lock files and retrying."
call :gitunlock
call :sleep 3
goto gitfetch

:gitfail_rebuild
call :barflush
set "GITTRIED=1"
set "MINE="
for /f %%m in ('git config --local --get ikemen.updater 2^>nul') do set "MINE=%%m"
if not "%MINE%"=="1" goto gitfail_final
call :say
call :say "Rebuilding the updater's index and retrying once."
call :gitunlock
if exist "%GITSTORE%" rd /s /q "%GITSTORE%" >nul 2>&1
goto gitinit

:gitlocked
call :barflush
echo.
echo A file in this folder is open in another program.
echo Close the game, any other copy of this updater, and any editor,
echo git window or backup tool here, then run this launcher again.
echo An antivirus can hold a file for a few seconds after it is
echo written, so a second run often just works.
echo.
call :close_soon 20
exit 1

:gitfail_final
call :barflush
echo.
echo Git could not finish this update. Its reason is in the lines above.
if exist "%CACHE%\git.log" if defined POWERSHELL "%POWERSHELL%" -NoProfile -Command "Get-Content -LiteralPath '%CQ%\git.log' -Tail 8" 2>nul
if exist "%CACHE%\git.log" if not defined POWERSHELL "%FINDSTR%" /i /c:"fatal" /c:"error:" "%CACHE%\git.log" >nul 2>&1
if exist "%CACHE%\git.log" if not defined POWERSHELL if not errorlevel 1 type "%CACHE%\git.log"
set "GITFAILED=1"
echo.
echo Falling back to the archive download (about 190 MB).
goto probe

:gitfetch_retry
call :barflush
rem The fetch above runs with GIT_SSL_CAINFO pointing at a bundle this
rem script went looking for on disk. When that bundle belongs to another
rem git install - or to one that reads the Windows store instead - every
rem fetch dies on it, and that failure used to mean the 190 MB archive.
rem Two cheaper answers are tried first: no bundle at all, then the
rem Windows certificate store, which is where a normal install looks.
call :say "Fetch failed. Retrying without the bundle this script found."
set "GIT_SSL_CAINFO="
set "GITBUNDLE="
git -c core.longpaths=true -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=60 fetch --depth 1 --filter=blob:none --no-tags --progress origin main
if not errorlevel 1 exit /b 0
call :say "Retrying with the Windows certificate store."
git -c core.longpaths=true -c http.sslBackend=schannel -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=60 fetch --depth 1 --filter=blob:none --no-tags --progress origin main
if not errorlevel 1 exit /b 0
exit /b 1

:verify
call :pct 90 "Verifying every file"
rem A file the engine needs that is missing here is silent until the game
rem panics on it, so after updating the folder is checked against main's own
rem list and anything absent is fetched by name before the game is started.
if not defined POWERSHELL exit /b 0
if not exist "%CACHE%\manifest.txt" if not exist "%CACHE%\applied.files" exit /b 0
set "VPS=%CACHE%\verify.ps1"
set "MISS=%CACHE%\missing.txt"
>  "%VPS%" echo param([string]$Tree, [string]$Root, [string]$Missing)
>> "%VPS%" echo $ErrorActionPreference = 'Stop'
>> "%VPS%" echo $out = New-Object System.Collections.ArrayList
>> "%VPS%" echo foreach ($l in (Get-Content -LiteralPath $Tree)) { $i = $l.IndexOf([char]9); if ($i -lt 1) { $p = $l } else { $p = $l.Substring($i + 1) }; if (-not $p) { continue }; $f = $Root + ($p -replace '/', [char]92); if ($f.Length -gt 250) { continue }; if (-not (Test-Path -LiteralPath $f)) { [void]$out.Add($p) } }
>> "%VPS%" echo Set-Content -LiteralPath $Missing -Value @($out) -Encoding ASCII
set "LIST=%CACHE%\manifest.txt"
if not exist "%LIST%" set "LIST=%CACHE%\applied.files"
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%VPS%" -Tree "%LIST%" -Root "%~dp0" -Missing "%MISS%" >nul 2>&1
if errorlevel 1 exit /b 0
if not exist "%MISS%" exit /b 0
set /a NMISS=0
for /f "usebackq delims=" %%p in ("%MISS%") do set /a NMISS+=1
if "%NMISS%"=="0" exit /b 0
if "%WHICH%"=="git" call :pct 86 "Fetching missing files"
if not "%WHICH%"=="git" call :say "Fetching %NMISS% files"
set "NCH=%NMISS%"
set /a NDONE=0
set /a BCOUNT=0
set /a BSTEP=NMISS/10
if %BSTEP% LSS 1 set "BSTEP=1"
set "BATCH="
set "WRITEFAIL="
if "%WHICH%"=="git" goto verify_git
for /f "usebackq delims=" %%p in ("%MISS%") do call :fetchraw "%%p"
goto verify_again
:verify_git
rem checkout writes the file whether or not the comparison thought it had
rem changed, and a partial clone fetches that one blob on demand
del /q "%CACHE%\todo.txt" >nul 2>&1
for /f "usebackq delims=" %%p in ("%MISS%") do call :gitone "%%p"
call :gitflush
:verify_again
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%VPS%" -Tree "%LIST%" -Root "%~dp0" -Missing "%MISS%" >nul 2>&1
set /a NMISS=0
for /f "usebackq delims=" %%p in ("%MISS%") do set /a NMISS+=1
call :log missing after repair: %NMISS%
if not "%NMISS%"=="0" echo         still missing %NMISS% file(s) - run this again before playing
exit /b 0

:fetchraw
rem %1 = a repo path. One small file straight from main, by name. Used only by
rem the archive path, which has no git objects to check a file out of.
set "REL=%~1"
if not defined REL exit /b 0
if not defined CURL exit /b 0
set "URLP=%REL:\=/%"
for %%d in ("%~dp0%REL%") do if not exist "%%~dpd" mkdir "%%~dpd" >nul 2>&1
"%CURL%" -sS -L --fail --ssl-no-revoke --connect-timeout 15 --max-time 120 -H "User-Agent: btilc-updater" -o "%~dp0%REL%" "https://raw.githubusercontent.com/%REPO%/main/%URLP%" >nul 2>&1
exit /b 0

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
rem ---- is this folder actually main? -------------------------------------
rem applied.txt records the commit the last run believed it applied, and the
rem manifest records main's file list - neither is the folder. One run cut short,
rem one file the game or a scanner held open, and both keep saying current while
rem the files stay old: every later launch then reports up to date, starts the stale
rem build, and the engine prints warnings that were fixed releases ago.
rem data/build_stamp.py writes a SHA-256 line per launch-critical file, so main's
rem copy of that file decides - it is a few KB and needs no git.
:stamp
set "STALE="
if not defined CURL exit /b 0
set "MSTAMP=%CACHE%\main.stamp"
if exist "%MSTAMP%" del /q "%MSTAMP%" >nul 2>&1
"%CURL%" -sS -L --fail --ssl-no-revoke --connect-timeout 10 --max-time 30 -H "User-Agent: btilc-updater" -o "%MSTAMP%" "https://raw.githubusercontent.com/%REPO%/main/data/build_stamp.txt" >nul 2>&1
if errorlevel 1 exit /b 0
if not exist "%MSTAMP%" exit /b 0
if not exist "%~dp0data\build_stamp.txt" goto stamp_stale
"%SYS%\fc.exe" /b "%MSTAMP%" "%~dp0data\build_stamp.txt" >nul 2>&1
if errorlevel 1 goto stamp_stale
call :log stamp matches main
exit /b 0
:stamp_stale
set "STALE=1"
call :log stamp differs from main
exit /b 0

rem ---- has main moved? ---------------------------------------------------
rem The zip path used to fetch the whole ~190 MB archive on every launch: it
rem recorded nothing about what it had applied, and nothing compared the
rem folder against main. The head commit is a few KB and answers the same
rem question, so an unchanged build costs one small request instead.
:probe
call :log step 9 archive route
set "RSHA7="
if not exist "%CACHE%\applied.txt" goto download
if not exist "%~dp0data\fight.def" goto download
set "APPLIED="
set /p APPLIED=<"%CACHE%\applied.txt"
if not defined APPLIED goto probe_first
call :atoms
if not defined RSHA7 goto probe_api
if not "%RSHA7%"=="%APPLIED%" goto probe_offer
call :stamp
if defined STALE goto download
call :pct 100 "Already up to date"
call :barflush
call :say "Already up to date - main @ %APPLIED%"
goto launch

:probe_offer
goto download

:probe_first
rem nothing recorded for this folder yet, so there is no build to compare with
set "APPLIED="
call :atoms
goto download

:probe_api
rem Fallback only. The API answers the same question but counts against an
rem hourly quota, so it is asked when the feed could not answer, not always.
call :headsha
if not defined RSHA7 goto probe_offer
if not "%RSHA7%"=="%APPLIED%" goto probe_offer
call :stamp
if defined STALE goto download
call :pct 100 "Already up to date"
call :barflush
call :say "Already up to date - main @ %APPLIED%"
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
call :log step 10 downloading the archive
call :pct 50 "Downloading 190 MB"
call :say
call :say
if not defined CURL goto dl_browser
set "ZIP=%CACHE%\main.zip"
if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
rem A percentage on a bar needs the size before the bytes arrive, and only the
rem request knows it: the total is read from the response and the bar is drawn
rem from bytes received against it. PowerShell does that; curl is the fallback
rem when there is no PowerShell to draw it.
if defined POWERSHELL call :dl_ps "%ZIPURL%"
if not defined DLOK if defined POWERSHELL call :say "Trying GitHub's other archive address."
if not defined DLOK if defined POWERSHELL call :dl_ps "%ZIPURL2%"
if not defined DLOK call :dl_curl
call :zipcheck
if "%ZIPOK%"=="1" goto havezip
if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
echo The archive did not arrive in one piece.
call :say
:dl_browser
echo.
echo Opening the download in your browser.
echo Save it anywhere in Downloads - this window finishes the update
echo and starts the game by itself once the file arrives.
echo.
start "" "%ZIPURL%"
set /a WAIT=0
set /a TICK=0
:bwait
call :sleep 5
set /a WAIT+=5
set /a TICK+=1
if %TICK% LSS 6 goto bwait_check
call :pct 55 "Watching Downloads %WAIT%s"
set /a TICK=0
:bwait_check
call :findzip
if defined FOUNDZIP goto bapply
if %WAIT% LSS 1200 goto bwait
echo Nothing arrived after 20 minutes.
goto downloadfailed

:bapply
call :barflush
call :say "Got it: %FOUNDZIP%"
set "ZIP=%CACHE%\main-1.zip"
copy /Y "%FOUNDZIP%" "%ZIP%" >nul
call :zipcheck
if "%ZIPOK%"=="1" goto havezip
goto downloadfailed

rem ---- unpack and copy ---------------------------------------------------
:havezip
call :pct 85 "Installing the archive"
call :say
call :gamelock
call :say
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
set "ZQ=%ZIP:'=''%"
set "UQ=%CACHE:'=''%"
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force -LiteralPath '%ZQ%' -DestinationPath '%UQ%\unpack'"

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
call :verify

:sync
rem The files are written. One word for the end of it, said once, instead of
rem a line per file under the drawing.
call :says "Done"
call :pct 95 "Finishing up"
if not "%WHICH%"=="git" goto skipver2

:skipver
"%FINDSTR%" /c:"bg1.spr = 20,0" "%~dp0data\fight.def" >nul 2>nul
if errorlevel 1 echo Warning: data\fight.def does not match the new build.
if defined VER call :say "main @ %VER%"
if not defined VER call :say "main @ local archive"

call :datareport

:launch
call :retired
call :pct 100 "Starting the game"
call :barflush
rem The engine runs in a helper of its own, so this window can close as soon as
rem the game is up - but its output is kept instead of being thrown away. A
rem game that dies on a missing file or a renderer setting used to write its
rem reason to nul and leave the window closing over it, which read as "it did
rem nothing". Now the game has a few seconds to appear, and if it does not its
rem own words are printed here and the window waits so they can be read.
set "RUN=%CACHE%\play.bat"
set "RUNQ=%RUN:'=''%"
set "GLOG=%CACHE%\game.log"
set "GCODE=%CACHE%\game.code"
if exist "%GLOG%" del /q "%GLOG%" >nul 2>&1
if exist "%GCODE%" del /q "%GCODE%" >nul 2>&1
>"%RUN%" echo @echo off
>>"%RUN%" echo cd /d "%~dp0."
>>"%RUN%" echo "%~dp0%EXE%" -config "save\config.ini" ^>"%GLOG%" 2^>^&1
>>"%RUN%" echo echo %%errorlevel%% ^>"%GCODE%"
call :log starting %EXE%
if defined POWERSHELL "%POWERSHELL%" -NoProfile -Command "Start-Process -FilePath 'cmd.exe' -ArgumentList '/c',([char]34 + '%RUNQ%' + [char]34) -WindowStyle Hidden" >nul 2>&1
rem Without PowerShell there is no hidden helper to run the game in, and a
rem batch started here would keep a window open for the whole session with
rem the game attached to it: closing that window ends the game. The engine
rem is started on its own instead - it owns its window, so nothing left
rem over can take it down.
if not defined POWERSHELL start "" /d "%~dp0" "%EXE%" -config "save\config.ini"
rem Without tasklist there is no way to tell whether the game came up, so
rem the window closes as it did before rather than reporting a false failure.
call :exehead
if not exist "%TASKLIST%" exit 0
set /a LW=0
:launch_wait
call :sleep 1
set /a LW+=1
rem The helper writes the engine's exit code when the engine ends, so its
rem absence is the plainest sign that the game is up: a first load of 190 MB of
rem art can take minutes, and the old wait called that a game that did not start.
if exist "%GCODE%" goto launch_died
"%TASKLIST%" /fi "imagename eq %EXE%" /nh 2>nul | "%FINDSTR%" /i /c:"%EXEHEAD%" >nul 2>&1
if not errorlevel 1 goto launch_ok
rem A game still loading has already written to its log, because the helper
rem redirects the engine's output there before the engine runs. Twelve seconds
rem was shorter than a first load of 190 MB of art, so a game that came up was
rem called a game that did not, and this window waited over it. The window now
rem gives the engine 45 seconds and treats any output as "it is running".
if exist "%GLOG%" for %%A in ("%GLOG%") do if %%~zA GTR 0 goto launch_ok
if %LW% GEQ 20 goto launch_slow
goto launch_wait
:launch_ok
call :log game is running after %LW%s
exit 0

:launch_slow
rem Twenty seconds with no exit code and no trace of the process is a slow
rem load, not a failure: the engine shows its own reason in its own window and
rem the run log has it. This window closes instead of sitting over the game.
call :log no sign of the game after %LW%s - closing, it has its own window
exit 0
:launch_died
call :barflush
call :log game did not stay open
echo.
echo The game did not stay open. Its own output:
echo.
if exist "%GLOG%" type "%GLOG%"
if not exist "%GLOG%" echo   (the engine wrote nothing at all)
if exist "%GCODE%" echo.
if exist "%GCODE%" echo   Exit code:
if exist "%GCODE%" type "%GCODE%"
echo.
echo This is also saved as:  %GLOG%
echo and the run log:        %LOG%
echo.
echo If a game window is behind this one, close this window and play.
echo.
call :close_soon 20
exit 1
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
if not defined CURL if not defined POWERSHELL exit /b 0
rem The launcher is not in the six folders the update writes, so before this it
rem could never be refreshed - a folder running v19 stayed on v19 no matter what
rem main fixed. It is fetched on its own here, a few KB.
rem
rem curl.exe only reached the system folder in Windows 1803, so an older machine
rem could not refresh this file at all and stayed on whichever copy it was first
rem given. The same file is fetched through PowerShell when curl is missing or
rem fails, and only when neither of them has it does this copy carry on as it is.
set "LAUNCHURL=https://raw.githubusercontent.com/%REPO%/main/Update%%20and%%20Play.bat"
set "NEWB=%CACHE%\launcher-new.bat"
set "STAGE=%~dp0Update and Play.new"
if exist "%NEWB%" del /q "%NEWB%" >nul 2>&1
if defined CURL "%CURL%" -sS -L --fail --ssl-no-revoke --connect-timeout 15 --max-time 40 -H "User-Agent: btilc-updater" -o "%NEWB%" "%LAUNCHURL%" >nul 2>&1
if not exist "%NEWB%" if defined POWERSHELL call :selfupdate_ps
if exist "%NEWB%" goto selfupdate_got
call :say "Could not fetch a newer launcher - using this copy."
goto selfupdate_nofetch
:selfupdate_got
if not exist "%NEWB%" exit /b 0
rem A truncated file, an error page or anything else that is not the launcher
rem must never be copied over a working one. Size alone is the weakest test, so
rem the title and the last line the file is shipped with have to be there too: a
rem download that stopped half way holds neither.
for %%A in ("%NEWB%") do if %%~zA LSS 20000 goto selfupdate_partial
"%FINDSTR%" /c:"BIG TROUBLE IN LITTLE CHINA" "%NEWB%" >nul 2>&1
if errorlevel 1 goto selfupdate_partial
"%FINDSTR%" /c:"btilc-launcher-end" "%NEWB%" >nul 2>&1
if errorlevel 1 goto selfupdate_partial
"%SYS%\fc.exe" /b "%NEWB%" "%~f0" >nul 2>&1
set "FCRC=%ERRORLEVEL%"
call :log launcher compare returned %FCRC%
if "%FCRC%"=="0" goto selfupdate_current
rem 2 is "could not compare", not "differs": treating it as a difference
rem staged a refresh on every launch, and a staged copy that never lands
rem leaves the folder on the same old launcher run after run.
if not "%FCRC%"=="1" goto selfupdate_current
echo.
echo This launcher is not the current one - it is replaced for the next launch.
rem cmd reads a batch file while it runs it, so this file cannot be written over
rem by the window that is executing it. A write in place either loses the race or
rem cuts the file short under the reader, and the next read runs a fragment of a
rem line: the window answers with a piece of text it cannot find as a command and
rem stops there. The new copy is landed beside this one first and put in place
rem with a rename, which is either the old file or the whole new one and never a
rem half-written one. A detached helper waits for this window to close and then
rem renames it into place, so the run itself never waits for it and the current
rem one is used for the rest of this launch.
rem If the rename loses the race this launch carries on as it is: the next one
rem tries again, and nothing here can loop.
rem A read-only file, a folder under Windows' control or a scanner holding it can
rem refuse the rename outright. Three launches is enough: past that this copy
rem runs the update as it is instead of closing, fetching and closing again on
rem every double-click.
rem The count is per launch. Kept in a file across launches it locked a folder
rem out of every newer launcher: three crashed runs left a four in swap.attempts
rem and every launch after that refused to fetch, on the very copy that was
rem crashing, so nothing the repository fixed could ever reach it. It is cleared
rem here, and the three tries below are three tries in this launch.
del /q "%CACHE%\swap.attempts" >nul 2>&1
set "SWN=0"
set /a SWN+=1
>"%CACHE%\swap.attempts" echo %SWN% 2>nul
if %SWN% GTR 3 goto selfupdate_stuck
call :log launcher refresh attempt %SWN%, staging a new copy
copy /Y "%NEWB%" "%STAGE%" >nul 2>&1
if not exist "%STAGE%" goto selfupdate_nostage
for %%A in ("%STAGE%") do if %%~zA LSS 20000 goto selfupdate_partial
set "SWAP=%CACHE%\swap.bat"
>"%SWAP%" echo @echo off
rem The staged copy sits in the same folder as the launcher, so the rename swaps
rem one directory entry for another: no byte is rewritten, and the window still
rem reading the old file keeps reading it to its last line. Eight tries, a few
rem seconds apart, is far more than that window needs to close, and it ends
rem itself when it is done so no prompt is left behind.
>>"%SWAP%" echo set "N=0"
>>"%SWAP%" echo :try
>>"%SWAP%" echo move /Y "%STAGE%" "%~f0" ^>nul 2^>^&1
>>"%SWAP%" echo if not exist "%STAGE%" goto run
>>"%SWAP%" echo set /a N+=1
>>"%SWAP%" echo if %%N%% GEQ 40 goto give
>>"%SWAP%" echo "%PING%" -n 3 127.0.0.1 ^>nul
>>"%SWAP%" echo goto try
>>"%SWAP%" echo :give
>>"%SWAP%" echo del /q "%STAGE%" ^>nul 2^>^&1
>>"%SWAP%" echo :run
rem The console this runs in is cmd /K, which keeps the window open after
rem the script ends - a blank prompt sitting in the task bar for no reason.
>>"%SWAP%" echo exit
if not exist "%SWAP%" goto selfupdate_nostage
rem A window of its own, minimised: a /b child shares this console and would go
rem with it when this script exits. This one outlives the window, renames the
rem staged copy the moment the file is free, and then goes away.
start "btilc launcher update" /min "%SWAP%"
call :say "launcher refresh staged - renamed into place when this window closes"
exit /b 0
:selfupdate_ps
rem The fetch curl could not make, for a machine that has no curl.exe. A script
rem of its own rather than a -Command line, because the address has to be passed
rem without the quoting a command line would eat.
set "SUPS=%CACHE%\launcher.ps1"
>  "%SUPS%" echo param([string]$Url, [string]$Out)
>> "%SUPS%" echo $ErrorActionPreference = 'Stop'
>> "%SUPS%" echo [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
>> "%SUPS%" echo $wc = New-Object Net.WebClient
>> "%SUPS%" echo $wc.Headers.Add('User-Agent', 'btilc-updater')
>> "%SUPS%" echo $wc.DownloadFile($Url, $Out)
if not exist "%SUPS%" exit /b 0
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%SUPS%" -Url "%LAUNCHURL%" -Out "%NEWB%" >nul 2>&1
exit /b 0
:selfupdate_nostage
call :say "Could not stage the new launcher - using this copy."
exit /b 0
:selfupdate_partial
echo.
echo The new launcher did not arrive whole, so this copy is doing the update.
echo.
call :say "launcher download incomplete, running this copy"
exit /b 0
:selfupdate_nofetch
echo.
echo Could not download the current launcher, so this copy is doing the
echo update. The game files are still brought up to date.
echo.
call :say "could not download the launcher, running this copy"
exit /b 0
:selfupdate_current
rem this copy is the current one: forget any failed attempts at replacing it
if exist "%CACHE%\swap.attempts" del /q "%CACHE%\swap.attempts" >nul 2>&1
exit /b 0

:selfupdate_stuck
echo Launcher file is read-only - running this copy, game files still update.
call :log self-update refused, running this copy
exit /b 0

:launchfail
call :barflush
echo The game did not stay open. Start it by hand to see the engine's
echo message, and check docs/INSTALL.md - the renderer setting is the
echo usual reason, and deleting save\config.ini resets it.
echo.
call :close_soon 20
exit 1

:folder_denied
call :barflush
echo.
echo This folder will not let anything be written into it:
echo     %~dp0
if exist "%WERR%" type "%WERR%"
echo Tried three times. The files here are left exactly as they are - so they
echo may be older than main. Starting the game with what is installed.
call :log folder refused writes after %WTRY% tries: "%~dp0"
if not exist "%~dp0%EXE%" goto folder_denied_noexe
goto launch
:folder_denied_noexe
echo There is no %EXE% here either, so there is nothing to start.
echo.
call :close_soon 20
exit 1

:wrongfolder
call :log wrong folder: no BigTroubleInLittleChinaTheGame.exe and no Ikemen_GO.exe in "%~dp0"
call :barflush
echo This file belongs in your game folder - the one that has
echo BigTroubleInLittleChinaTheGame.exe in it.
echo.
call :close_soon 20
exit 1

:downloadfailed
call :barflush
echo.
echo Could not get the files automatically.
echo.
echo The last resort, which always works:
echo     1. Download this in your browser.
echo        %ZIPURL%
echo     2. Save the zip in this folder.
echo     3. Run "Apply main.zip.bat".
echo.
call :close_soon 20
exit 1

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
rem inside it - drops to unpack-and-copy. The paths below are the doubled
rem copies, so a folder with an apostrophe takes this path as well.
set "PSOK=0"
if not defined POWERSHELL goto ziptree_done
if not defined ZIP goto ziptree_done
if not exist "%ZIP%" goto ziptree_done
set "ZQ=%ZIP:'=''%"
set "RQ=%~dp0"
set "RQ=%RQ:'=''%"
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; Add-Type -AssemblyName System.IO.Compression.FileSystem; $zip=[IO.Compression.ZipFile]::OpenRead('%ZQ%'); $root='%RQ%'; $tops=@('data','chars','stages','font','external','sound'); $mf='%CQ%\applied.files'; $old=@(); if (Test-Path -LiteralPath $mf) { $old=@(Get-Content -LiteralPath $mf) }; $keep=New-Object 'System.Collections.Generic.HashSet[string]'; $n=0; $gone=0; Write-Host ('            ' + $zip.Entries.Count + ' entries in the archive'); try { foreach ($e in $zip.Entries) { if ($e.FullName.EndsWith('/')) { continue }; $rel=$e.FullName.Substring($e.FullName.IndexOf('/')+1); if ($rel -eq 'config.ini') { $c=$root+'config.ini'; if (-not (Test-Path -LiteralPath $c)) { [IO.Compression.ZipFileExtensions]::ExtractToFile($e,$c,$true) }; continue }; if ($tops -notcontains ($rel -split '/')[0]) { continue }; [void]$keep.Add($rel); $dst=$root+($rel -replace '/','\'); $fi=New-Object System.IO.FileInfo($dst); if ($fi.Exists -and $fi.Length -eq $e.Length -and $fi.LastWriteTimeUtc.Ticks -eq $e.LastWriteTime.UtcDateTime.Ticks) { continue }; $dir=Split-Path -Parent $dst; if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }; [System.IO.Compression.ZipFileExtensions]::ExtractToFile($e,$dst,$true); $n++; Write-Host ('             ' + $n + ') ' + $rel) } } finally { $zip.Dispose() }; foreach ($p in $old) { if ($keep.Count -lt 500) { break }; if ($keep.Contains($p)) { continue }; $x=$root+($p -replace '/','\'); if (Test-Path -LiteralPath $x) { Remove-Item -LiteralPath $x -Force; $gone++; Write-Host ('             - ' + $p) } }; Set-Content -LiteralPath $mf -Value @($keep) -Encoding ASCII; Write-Host ('Installed ' + $n + ' file(s), removed ' + $gone)"
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
call :barflush
call :say "Updated %NCOP% files, removed %NDEL%."
exit /b 0

:synctree_full
rem No list means no git history to diff - a first run, or a folder updated
rem from the archive. robocopy still skips every file whose size and time
rem already match, so only the files that changed are actually written; the
rem scan is the cost, not the bytes.

for %%F in (data chars stages font external sound tools) do (
  if exist "%SRC%\%%F" call :say "%%F"
  if exist "%SRC%\%%F" "%ROBOCOPY%" "%SRC%\%%F" "%~dp0%%F" /E /FFT /NFL /NDL /NJH /NJS /NP >nul
)
rem The launchers sit at the root, so they are copied by name: a launcher
rem fix that never arrived is what kept a console open over the game.
for %%F in ("Update and Play.bat" "Play Big Trouble.bat" "Apply main.zip.bat" "Dump Stage Art.bat") do (
  if exist "%SRC%\%%~F" if not "%%~F"=="%~nx0" copy /Y "%SRC%\%%~F" "%~dp0%%~F" >nul 2>&1
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
if /i "%TOP%"=="tools" goto syncfile_go
if /i "%TOP%"=="Update and Play.bat" goto syncfile_go
if /i "%TOP%"=="Play Big Trouble.bat" goto syncfile_go
if /i "%TOP%"=="Apply main.zip.bat" goto syncfile_go
if /i "%TOP%"=="Dump Stage Art.bat" goto syncfile_go
exit /b 0

:syncfile_go
if not exist "%SRC%\%REL%" goto syncfile_gone
rem a new build can add folders, so the parent has to exist first
for %%d in ("%~dp0%REL%") do if not exist "%%~dpd" mkdir "%%~dpd" 2>nul
copy /Y "%SRC%\%REL%" "%~dp0%REL%" >nul 2>&1
if not errorlevel 1 call :say "%REL%"
if not errorlevel 1 set /a NCOP+=1
exit /b 0

:syncfile_gone
rem a path main no longer has was deleted there: drop the local copy too
if not exist "%~dp0%REL%" exit /b 0
del /q "%~dp0%REL%" >nul 2>&1
if not errorlevel 1 set /a NDEL+=1
exit /b 0

:dl_ps
rem %1 = the archive address. Sets DLOK when the file arrived whole.
set "DLOK="
set "DFROM=50"
rem The bar the download draws carries on from where the run already is: a
rem git attempt that failed after 80% must not make the number drop to 50.
if defined GMAXPCT set "DFROM=%GMAXPCT%"
if %DFROM% LSS 50 set "DFROM=50"
if not exist "%DLSCRIPT%" call :dl_make
if not exist "%DLSCRIPT%" exit /b 0
if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
rem The download fills the same barrel with the same pipe per percent, so its
rem bytes count on the pistol rather than in a meter of its own; where the
rem console has no cursor control it leaves the number in the title bar.
set "VTFLAG=0"
if defined VTOK set "VTFLAG=1"
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%DLSCRIPT%" -Url "%~1" -Out "%ZIP%" -From %DFROM% -Vt %VTFLAG% -Col %MUZZLE% -Bar %BARMAX%
if errorlevel 1 exit /b 0
set "DLOK=1"
exit /b 0

:dl_make
rem The renderer lives in a file of its own: a twenty-line PowerShell script
rem cannot be passed on a command line without a quoting argument, and every
rem line below is plain text with no character cmd would eat.
rem
rem It fills the run's own barrel, not a meter of its own: the same pipe per
rem percent the rest of the run draws, extended as the bytes land.
rem Downloading is 50-80% of the run, so the number it leaves behind is where
rem the next step carries on instead of a second count starting over.
set "DLSCRIPT=%CACHE%\download.ps1"
>  "%DLSCRIPT%" echo param([string]$Url, [string]$Out, [int]$From = 50, [int]$Vt = 0, [int]$Col = 41, [int]$Bar = 60)
>> "%DLSCRIPT%" echo $ErrorActionPreference = 'Stop'
>> "%DLSCRIPT%" echo [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
>> "%DLSCRIPT%" echo $req = [Net.HttpWebRequest]::Create($Url)
>> "%DLSCRIPT%" echo $req.UserAgent = 'btilc-updater'
>> "%DLSCRIPT%" echo $req.Timeout = 60000
>> "%DLSCRIPT%" echo $res = $req.GetResponse()
>> "%DLSCRIPT%" echo $total = $res.ContentLength
>> "%DLSCRIPT%" echo $stream = $res.GetResponseStream()
>> "%DLSCRIPT%" echo $file = [IO.File]::Create($Out)
>> "%DLSCRIPT%" echo $buffer = New-Object byte[] 262144
>> "%DLSCRIPT%" echo $got = 0
>> "%DLSCRIPT%" echo $start = Get-Date
>> "%DLSCRIPT%" echo $drawn = 0.0
>> "%DLSCRIPT%" echo $pipe = [char]124
>> "%DLSCRIPT%" echo while (($read = $stream.Read($buffer, 0, $buffer.Length)) -gt 0) {
>> "%DLSCRIPT%" echo   $file.Write($buffer, 0, $read)
>> "%DLSCRIPT%" echo   $got = $got + $read
>> "%DLSCRIPT%" echo   $elapsed = ((Get-Date) - $start).TotalSeconds
>> "%DLSCRIPT%" echo   if (($elapsed - $drawn) -lt 0.25 -and ($total -le 0 -or $got -lt $total)) { continue }
>> "%DLSCRIPT%" echo   $drawn = $elapsed
>> "%DLSCRIPT%" echo   $whole = $From
>> "%DLSCRIPT%" echo   if ($From -lt 80) { if ($total -gt 0) { $whole = $From + [int]((80 - $From) * $got / $total) } }
>> "%DLSCRIPT%" echo   $pct = '   ?'
>> "%DLSCRIPT%" echo   if ($total -gt 0) { $pct = $whole.ToString().PadLeft(3) + '%%' }
>> "%DLSCRIPT%" echo   $pos = [int]($whole * $Bar / 100)
>> "%DLSCRIPT%" echo   if ($pos -lt 1) { $pos = 1 }
>> "%DLSCRIPT%" echo   $barcol = $Col + $pos - 1
>> "%DLSCRIPT%" echo   if ($Vt -eq 1) { $line = [char]27 + '[u' + [char]27 + '[7A' + [char]27 + '[' + $barcol + 'G' + $pipe + ' ' + $pct + [char]27 + '[K' + [char]27 + '[u' }
>> "%DLSCRIPT%" echo   if ($Vt -ne 1) { $line = [char]13 + '  ' + $pct }
>> "%DLSCRIPT%" echo   Write-Host -NoNewline $line
>> "%DLSCRIPT%" echo }
>> "%DLSCRIPT%" echo $file.Close()
>> "%DLSCRIPT%" echo $stream.Close()
>> "%DLSCRIPT%" echo $res.Close()
>> "%DLSCRIPT%" echo Write-Host ''
>> "%DLSCRIPT%" echo if ($total -gt 0 -and $got -lt $total) { throw 'incomplete download' }
exit /b 0

:dl_curl
rem No PowerShell, or it could not fetch: curl's own meter still reports the
rem percentage and the speed, and both archive addresses are tried.
if not defined CURL exit /b 0
if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
"%CURL%" -L --fail --ssl-no-revoke --retry 2 --retry-delay 3 --connect-timeout 30 --max-time 1800 -o "%ZIP%" "%ZIPURL%"
call :zipcheck
if "%ZIPOK%"=="1" set "DLOK=1"
if defined DLOK exit /b 0
if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
"%CURL%" -L --fail --ssl-no-revoke --retry 2 --retry-delay 3 --connect-timeout 30 --max-time 1800 -o "%ZIP%" "%ZIPURL2%"
call :zipcheck
if "%ZIPOK%"=="1" set "DLOK=1"
exit /b 0

:say
rem %1 = a routine line. It goes to the run log, not the window: the window is
rem the pistol and the number at its muzzle, and nothing else. Failures still
rem print, because a reason nobody can read is not a reason.
if not defined LOG exit /b 0
if "%~1"=="" goto say_blank
>>"%LOG%" echo %~1 2>nul
exit /b 0
:say_blank
>>"%LOG%" echo. 2>nul
exit /b 0

:says
rem %1 = a line for the window as well as the run log. The window used to be the
rem pistol and the number at its muzzle and nothing else, so a step that took
rem minutes - the 20% comparison did - sat there in silence, with no way to tell
rem working from hung. These lines are kept in six slots so a redraw can put them
rem back: the redraw starts with cls on a console without cursor control, and
rem that is what made a message appear and vanish a moment later.
if "%~1"=="" exit /b 0
rem The log line goes through :say, which owns the redirect: written here it
rem would need a branch of its own, and a second label inside this one would
rem leave the echo below belonging to that label instead of this one.
call :say "%~1"
set "SAY1=%SAY2%"
set "SAY2=%SAY3%"
set "SAY3=%SAY4%"
set "SAY4=%SAY5%"
set "SAY5=%SAY6%"
set "SAY6=%~1"
echo %~1
exit /b 0
:log
rem Appends one line to the run log. Cheap enough to call at every step.
if not defined LOG exit /b 0
>>"%LOG%" echo [%TIME%] %* 2>nul
exit /b 0

:retired
rem Root files main used to ship and has since dropped are deleted here, so a
rem folder that has updated for years does not keep what the project removed.
rem The list is data\retired.txt, delivered by the update like the other data
rem files; tools\validate.py keeps it equal to this repository's history, so a
rem root file deleted from main cannot be forgotten.
if not exist "%~dp0data\retired.txt" exit /b 0
for /f "usebackq delims=" %%R in ("%~dp0data\retired.txt") do call :retiredone "%%R"
exit /b 0

:retiredone
set "R=%~1"
if not defined R exit /b 0
if exist "%~dp0%R%" del /q "%~dp0%R%" >nul 2>&1
if not exist "%~dp0%R%" call :log removed %R% - main no longer ships it
exit /b 0


:snap
rem %1 = a path from this folder, %2 = the variable that keeps its hash.
rem certutil prints a header line, the hash, then a footer. Its output goes to a
rem file and the hash is read from there: the pipeline this used to run sent a
rem "filename syntax is incorrect" line to the window for every file when the
rem tool it piped into was missing, and those lines landed on the art.
set "%~2="
if not defined CERT exit /b 0
if not exist "%~dp0%~1" exit /b 0
set "SNAPT=%TEMP%\btilc-hash.txt"
>"%SNAPT%" 2>nul "%CERT%" -hashfile "%~dp0%~1" SHA256
for /f "usebackq skip=1 tokens=1" %%h in ("%SNAPT%") do if not defined %~2 set "%~2=%%h"
del /q "%SNAPT%" >nul 2>&1
exit /b 0

:note
rem %1 = a path from this folder, %2 = the hash it had before this update.
rem The word comes from the content, so a checkout that rewrote the
rem timestamp of a file it did not change still reads as unchanged.
set "NOWH="
call :snap "%~1" NOWH
if not defined CERT goto note_unchecked
if not defined NOWH goto note_absent
if "%~2"=="" goto note_added
if "%NOWH%"=="%~2" goto note_same
call :say "%~1   refreshed"
set "NREF=1"
exit /b 0
:note_added
call :say "%~1   added"
set "NREF=1"
exit /b 0
:note_same
call :say "%~1   already current"
exit /b 0
:note_absent
call :say "%~1   is missing after the update"
set "NFAIL=1"
exit /b 0
:note_unchecked
exit /b 0

:datareport
rem What this update changed, by name: the answer to "did the fix arrive".
rem data\fight.def carries the power bar font and data\music.json is the
rem album list the music browser reads; neither shows up in a file count.
set "NREF="
set "NFAIL="
if not defined CERT exit /b 0
call :say
call :say "Data files:"
call :note "data\fight.def" "%H1%"
call :note "data\music.json" "%H2%"
call :note "data\select.def" "%H3%"
call :note "data\ikemen1\system.def" "%H4%"
call :note "external\mods\musicselect.lua" "%H5%"
call :note "external\mods\modnotice.lua" "%H6%"
if defined NREF goto datareport_done
call :say "all of these already matched main"
:datareport_done
if defined NFAIL call :say "a file above is missing - run this launcher again"
call :say
exit /b 0

:close_soon
rem Nothing here waits for a key. A window that has said its piece counts
rem down and closes, and everything it printed is also in the log on disk.
echo This window closes by itself in %~1 seconds.
call :sleep %~1
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
rem Reached when Escape is pressed: nothing has been fetched, copied or deleted.
echo Nothing was changed. Closing.
call :sleep 3
exit 0

:zipcheck_ps
if not defined POWERSHELL exit /b 0
set "ZQ=%ZIP:'=''%"
"%POWERSHELL%" -NoProfile -Command "try { Add-Type -AssemblyName System.IO.Compression.FileSystem; $z=[IO.Compression.ZipFile]::OpenRead('%ZQ%'); $n=($z.Entries | Where-Object { $_.FullName -like '*data/fight.def' }).Count; $z.Dispose(); if ($n -ge 1) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if errorlevel 1 exit /b 0
set "ZIPOK=1"
exit /b 0
rem btilc-launcher-end
