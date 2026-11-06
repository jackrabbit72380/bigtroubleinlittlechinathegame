@echo off
rem ===========================================================================
rem  BIG TROUBLE IN LITTLE CHINA - Updater v37
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
set "FIND=%SYS%\find.exe"
set "TASKLIST=%SYS%\tasklist.exe"
set "ROBOCOPY=%SYS%\robocopy.exe"
set "WHERE=%SYS%\where.exe"
set "POWERSHELL=%SYS%\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%TAR%" set "TAR="
if not exist "%CURL%" set "CURL="
if not exist "%POWERSHELL%" set "POWERSHELL="
if not exist "%WHERE%" set "WHERE="
if not exist "%FIND%" set "FIND="

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
echo        /\                                      /\
echo       /  \                                    /  \
echo      /    \__________________________________/    \
echo     /  o   \                                /   o  \
echo    /        \______________________________/        \
echo   /________________________________________________\
echo.
echo   ==============================================================
echo    B I G   T R O U B L E   I N   L I T T L E   C H I N A
echo                     THE GAME
echo              Updater v37   -   dragon edition
echo   ==============================================================
echo    Folder:  %~dp0
echo   ==============================================================
echo.

set "EXE="
if exist "BigTroubleInLittleChinaTheGame.exe" set "EXE=BigTroubleInLittleChinaTheGame.exe"
if not defined EXE if exist "Ikemen_GO.exe" set "EXE=Ikemen_GO.exe"
if not defined EXE goto wrongfolder

set "REPO=jackrabbit72380/bigtroubleinlittlechinathegame"
set "ZIPURL=https://codeload.github.com/%REPO%/zip/refs/heads/main"
set "ZIPURL2=https://github.com/%REPO%/archive/refs/heads/main.zip"
set "GITURL=https://github.com/%REPO%.git"
rem Everything this launcher writes goes to the temp folder. A game folder can
rem be read only, on a drive with no room, or behind a path cmd will not take, and
rem a cache that cannot be written breaks every redirect after it - which is what
rem left the download sitting at zero with no curl running behind it.
set "CACHE=%TEMP%\btilc-updater"
if not exist "%CACHE%" mkdir "%CACHE%" 2>nul
if not exist "%CACHE%" set "CACHE=%TEMP%"
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

echo.
echo   --------------------------------------------------------------
echo     1/3   Checking main
if exist "%~dp0main.zip" goto manualzip
if exist "%~dp0bigtroubleinlittlechinathegame-main.zip" goto manualzip2
rem nothing left over from an interrupted run may be mistaken for an archive
if exist "%CACHE%\main-1.zip" del /q "%CACHE%\main-1.zip" >nul 2>&1
if exist "%CACHE%\main-2.zip" del /q "%CACHE%\main-2.zip" >nul 2>&1
if exist "%CACHE%\main.zip" del /q "%CACHE%\main.zip" >nul 2>&1
if not exist "%WHERE%" goto download
"%WHERE%" git >nul 2>&1
if errorlevel 1 goto probe
set "GITOK=1"
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

:gitinit
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
rem An older launcher kept its repository in the game folder. That is the copy
rem a scanner, a backup tool or the game itself holds open, and a file held
rem open is what turned an update into "The process cannot access the file
rem because it is being used by another process" and then into the 190 MB
rem archive. The repository lives outside the game folder now, so the one here
rem is removed; nothing in it is player-visible, and if it cannot be removed it
rem is simply ignored, because every git command below names the new one.
echo            Moving the updater's git data out of the game folder.
rd /s /q "%~dp0.git" >nul 2>&1
goto gitinit

:githere
rem A folder somebody cloned themselves is their checkout: this launcher
rem will not fetch into it, check anything out, or overwrite uncommitted
rem work. It only says so and starts the game.
set "MINE="
for /f %%m in ('git config --local --get ikemen.updater 2^>nul') do set "MINE=%%m"
if "%MINE%"=="1" goto gitmigrate
git rev-parse --verify -q HEAD >nul 2>&1
if errorlevel 1 goto gitfetch
echo            This folder is your own git checkout - left untouched.
echo            Bring it up to date yourself with:  git pull
goto launch

rem ---- transport 1: git ----------------------------------------------------
rem Only main's commit and its file list are fetched, a few hundred KB. The art
rem is fetched later, one blob at a time, and only for the files that differ.
:gitfetch
if exist "%CACHE%\git.log" del /q "%CACHE%\git.log" >nul 2>&1
echo         asking main for the file list (about 300 KB)
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
echo         main @ %NEWSHORT%
call :gamelock
git -c core.quotepath=false ls-tree -r FETCH_HEAD -- data chars stages font external sound >"%CACHE%\tree.txt" 2>>"%CACHE%\git.log"
if errorlevel 1 goto gitfail
call :plan
rem a comparison that could not run must never pass as "already current"
if errorlevel 1 goto gitfail
if not exist "%CACHE%\changed.txt" goto gitfail
set "NCH=0"
for /f "usebackq delims=" %%c in ("%CACHE%\changed.txt") do set /a NCH+=1
if "%NCH%"=="0" goto gitnone
echo.
echo   --------------------------------------------------------------
echo     2/3   Updating %NCH% file(s)
set /a NDONE=0
set /a BCOUNT=0
set /a BSTEP=NCH/10
if %BSTEP% LSS 1 set "BSTEP=1"
set "BATCH="
set "WRITEFAIL="
for /f "usebackq delims=" %%c in ("%CACHE%\changed.txt") do call :gitone "%%c"
call :gitflush
if defined WRITEFAIL goto gitfail
call :bar %NDONE% %NCH%
if "%VT%"=="1" echo.
call :confirm
goto gitdrop_list
:gitnone
echo         already current - nothing to download
goto gitdrop_list
:plan
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
rem Nothing recorded yet - the first run on this folder. Prime git's index in
rem ONE pass: that hashes the files already here instead of downloading them,
rem and then git can say exactly which of them differ from main. It runs in a
rem helper for the same reason the fetch does: so the window shows it working.
echo         first run here - one read of this folder, nothing downloaded
set "QOK=%CACHE%\plan.ok"
set "QBAD=%CACHE%\plan.bad"
if exist "%QOK%" del /q "%QOK%" >nul 2>&1
if exist "%QBAD%" del /q "%QBAD%" >nul 2>&1
set "QBAT=%CACHE%\plan.bat"
>  "%QBAT%" echo @echo off
>> "%QBAT%" echo cd /d "%~dp0."
>> "%QBAT%" echo git ls-tree -r --name-only FETCH_HEAD -- data chars stages font external sound ^>"%CACHE%\paths.txt" 2^>^>"%CACHE%\git.log"
>> "%QBAT%" echo if errorlevel 1 (echo x^>"%QBAD%") ^& exit /b 1
>> "%QBAT%" echo git update-index --add --replace --stdin ^<"%CACHE%\paths.txt" ^>^>"%CACHE%\git.log" 2^>^&1
>> "%QBAT%" echo git -c core.quotepath=false diff-index --name-only FETCH_HEAD -- data chars stages font external sound ^>"%CACHE%\changed.txt" 2^>^>"%CACHE%\git.log"
>> "%QBAT%" echo if errorlevel 1 (echo x^>"%QBAD%") ^& exit /b 1
>> "%QBAT%" echo echo.^>"%CACHE%\dropped.txt"
>> "%QBAT%" echo echo x^>"%QOK%"
if not exist "%QBAT%" goto plan_first_direct
start "" /b cmd /c ""%QBAT%""
call :spinwait "%QOK%" "%QBAD%" "reading the files already here (one pass, no download)" 1800
if not errorlevel 1 exit /b 0
exit /b 1
:plan_first_direct
git ls-tree -r --name-only FETCH_HEAD -- data chars stages font external sound >"%CACHE%\paths.txt" 2>>"%CACHE%\git.log"
if errorlevel 1 exit /b 1
git update-index --add --replace --stdin <"%CACHE%\paths.txt" >>"%CACHE%\git.log" 2>&1
git -c core.quotepath=false diff-index --name-only FETCH_HEAD -- data chars stages font external sound >"%CACHE%\changed.txt" 2>>"%CACHE%\git.log"
if errorlevel 1 exit /b 1
echo.>"%CACHE%\dropped.txt"
exit /b 0
:plan_ps
set "PLANPS=%CACHE%\plan.ps1"
>  "%PLANPS%" echo param([string]$Tree, [string]$Old, [string]$Changed, [string]$Dropped)
>> "%PLANPS%" echo $ErrorActionPreference = 'Stop'
>> "%PLANPS%" echo $old = @{}
>> "%PLANPS%" echo foreach ($l in (Get-Content -LiteralPath $Old)) { $i = $l.IndexOf([char]9); if ($i -gt 0) { $old[$l.Substring($i + 1)] = $l.Substring(0, $i) } }
>> "%PLANPS%" echo $new = @{}
>> "%PLANPS%" echo $chg = New-Object System.Collections.ArrayList
>> "%PLANPS%" echo foreach ($l in (Get-Content -LiteralPath $Tree)) { $i = $l.IndexOf([char]9); if ($i -lt 1) { continue }; $meta = $l.Substring(0, $i).Split(' '); $sha = $meta[$meta.Length - 1]; $p = $l.Substring($i + 1); $new[$p] = $sha; if ($old.ContainsKey($p) -and $old[$p] -eq $sha) { continue }; [void]$chg.Add($p) }
>> "%PLANPS%" echo $drop = New-Object System.Collections.ArrayList
>> "%PLANPS%" echo foreach ($p in $old.Keys) { if (-not $new.ContainsKey($p)) { [void]$drop.Add($p) } }
>> "%PLANPS%" echo Set-Content -LiteralPath $Changed -Value @($chg) -Encoding ASCII
>> "%PLANPS%" echo Set-Content -LiteralPath $Dropped -Value @($drop) -Encoding ASCII
>> "%PLANPS%" echo Write-Host ('         ' + $chg.Count + ' to write, ' + $drop.Count + ' to remove')
if not exist "%PLANPS%" exit /b 1
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%PLANPS%" -Tree "%CACHE%\tree.txt" -Old "%CACHE%\manifest.txt" -Changed "%CACHE%\changed.txt" -Dropped "%CACHE%\dropped.txt"
if errorlevel 1 exit /b 1
exit /b 0
:gitone
rem %1 = one path. Paths are collected into one checkout of a dozen files: one
rem git process per file is what made a first run crawl.
set /a NDONE+=1
set "BATCH=%BATCH% "%~1""
set /a BCOUNT+=1
if %BCOUNT% GEQ 12 call :gitflush
set /a BMOD=NDONE %% BSTEP
if %BMOD%==0 call :bar %NDONE% %NCH%
exit /b 0
:gitflush
if not defined BATCH exit /b 0
git -c core.longpaths=true checkout FETCH_HEAD -- %BATCH% >>"%CACHE%\git.log" 2>&1
if errorlevel 1 set "WRITEFAIL=1"
set "BATCH="
set /a BCOUNT=0
exit /b 0
:bar
rem %1 = done, %2 = total. Twenty-four cells; redrawn on the same line where
rem the console reads ANSI so a long update never scrolls, printed as ordinary
rem lines where it does not.
if "%~2"=="0" exit /b 0
set /a BFILL=%~1*24/%~2
if %BFILL% GTR 24 set /a BFILL=24
if %BFILL% LSS 0 set "BFILL=0"
set "CHARS=########################"
set "GAPS=........................"
call set "BFILLED=%%CHARS:~0,%BFILL%%%"
set /a BGAP=24-BFILL
call set "BEMPTY=%%GAPS:~0,%BGAP%%%"
set /a BPCT=%~1*100/%~2
set "BARLINE=      |%BFILLED%%BEMPTY%|  %BPCT%%  %~1/%~2"
if "%VT%"=="1" ( <nul set /p "=%ESC%[2K%BARLINE%" ) else ( echo %BARLINE% )
exit /b 0

:spin
rem %1 = seconds waited, %2 = what is being waited for. One line, rewritten.
set /a SMOD=%~1 %% 4
set "SPIN=|/-\"
call set "SCH=%%SPIN:~%SMOD%,1%%"
if "%VT%"=="1" <nul set /p "=%ESC%[2K      %SCH%   %~2   %~1s"
if not "%VT%"=="1" set /a SDOT=%~1 %% 5
if not "%VT%"=="1" if %SDOT%==0 echo       %SCH%   %~2   %~1s
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
call :spin %SW% "%~3"
if exist "%~1" goto spinwait_ok
if exist "%~2" goto spinwait_bad
if %SW% GEQ %~4 goto spinwait_late
goto spinwait_loop
:spinwait_ok
if "%VT%"=="1" echo.
exit /b 0
:spinwait_bad
if "%VT%"=="1" echo.
exit /b 1
:spinwait_late
if "%VT%"=="1" echo.
exit /b 2
:confirm
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
echo         %NBAD% written file(s) do not match main - fetching them again
copy /Y "%CACHE%\bad.txt" "%CACHE%\changed.txt" >nul
set "NCH=%NBAD%"
set /a NDONE=0
set /a BCOUNT=0
set /a BSTEP=NBAD/10
if %BSTEP% LSS 1 set "BSTEP=1"
set "BATCH="
set "WRITEFAIL="
for /f "usebackq delims=" %%c in ("%CACHE%\changed.txt") do call :gitone "%%c"
call :gitflush
git hash-object --stdin-paths <"%CACHE%\changed.txt" >"%CACHE%\hashes.txt" 2>>"%CACHE%\git.log"
call :confirm_ps
set /a NBAD=0
for /f "usebackq delims=" %%b in ("%CACHE%\bad.txt") do set /a NBAD+=1
if "%NBAD%"=="0" echo         every written file now matches main
if not "%NBAD%"=="0" echo         %NBAD% file(s) still do not match main - run this again
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
>> "%CPS%" echo $bad = New-Object System.Collections.ArrayList
>> "%CPS%" echo for ($k = 0; $k -lt $ps.Count; $k++) { $p = $ps[$k]; if (-not $want.ContainsKey($p)) { continue }; if ($k -ge $hs.Count) { continue }; if ($hs[$k] -ne $want[$p]) { [void]$bad.Add($p) } }
>> "%CPS%" echo Set-Content -LiteralPath $Bad -Value @($bad) -Encoding ASCII
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%CPS%" -Tree "%CACHE%\tree.txt" -Paths "%CACHE%\changed.txt" -Hashes "%CACHE%\hashes.txt" -Bad "%BADL%" >nul 2>&1
exit /b 0

:gitdrop_list
rem Paths main no longer has, and which this launcher wrote, are removed. Only
rem the six game folders are ever touched - see :gitdrop.
if not exist "%CACHE%\dropped.txt" goto gitref
set /a NDR=0
for /f "usebackq delims=" %%p in ("%CACHE%\dropped.txt") do set /a NDR+=1
if %NDR% GTR 200 goto gitdrop_many
for /f "usebackq delims=" %%p in ("%CACHE%\dropped.txt") do call :gitdrop "%%p"
goto gitref
:gitdrop_many
rem Two hundred files do not disappear from main in one update. A list this
rem long means the comparison itself went wrong, and deleting on it would take
rem the game apart - which is exactly how external\script\main.lua once went
rem missing and the engine panicked on the next start.
echo         %NDR% file(s) would be removed - that looks wrong, so nothing is deleted
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

:gamelock
rem The engine keeps its data files open while it runs and Windows will not let
rem git replace one. Updating under a running game fails with "being used by
rem another process", so this waits for it to close rather than writing into a
rem folder that cannot be written.
if not defined EXE exit /b 0
if not defined TASKLIST exit /b 0
"%TASKLIST%" /fi "imagename eq %EXE%" /nh 2>nul | "%FINDSTR%" /i /c:"%EXE%" >nul 2>&1
if errorlevel 1 exit /b 0
echo.
echo            The game is still running. Its files are open, so they cannot
echo            be replaced. Close the game - this window carries on by itself.
set /a GWAIT=0
:gamelock_wait
call :sleep 3
set /a GWAIT+=3
"%TASKLIST%" /fi "imagename eq %EXE%" /nh 2>nul | "%FINDSTR%" /i /c:"%EXE%" >nul 2>&1
if errorlevel 1 (
  echo            Closed - carrying on.
  exit /b 0
)
if %GWAIT% LSS 60 goto gamelock_wait
echo            Still open after %GWAIT% seconds - carrying on anyway.
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
set "GITFIXED=1"
set "GITQUIET=1"
echo.
echo            A file git needs was in use. Clearing the lock files it leaves
echo            behind and trying that step again - this costs a few hundred
echo            KB, not the archive.
call :gitunlock
call :sleep 3
goto gitfetch

:gitfail_rebuild
set "GITTRIED=1"
set "MINE="
for /f %%m in ('git config --local --get ikemen.updater 2^>nul') do set "MINE=%%m"
if not "%MINE%"=="1" goto gitfail_final
echo.
echo            The updater's git data is not usable, so it is rebuilt and the
echo            update tried once more. That folder holds no player data, so
echo            this costs a re-read of the folders, never a download.
call :gitunlock
if exist "%GITSTORE%" rd /s /q "%GITSTORE%" >nul 2>&1
goto gitinit

:gitlocked
echo.
echo            Git could not write a file because another program has it open.
echo.
echo            Nothing has been downloaded for this: the archive takes the
echo            same locks and would fail the same way, which is why the whole
echo            190 MB used to be spent here and change nothing.
echo.
echo            Close these and run this launcher again:
echo              - the game, if it is still open
echo              - any other copy of this updater
echo              - an editor, git window or backup tool in this folder
echo            An antivirus can hold a file for a few seconds after writing
echo            it, so running this a second time often just works.
echo.
pause
exit 1

:gitfail_final
echo.
echo            Git could not finish this update.
echo            Its reason is in git's own lines just above this - no
echo            connection, a proxy, or a blocked github.com are the usual ones.
if exist "%CACHE%\git.log" if defined POWERSHELL "%POWERSHELL%" -NoProfile -Command "Get-Content -LiteralPath '%CACHE%\git.log' -Tail 8" 2>nul
if exist "%CACHE%\git.log" if not defined POWERSHELL "%FINDSTR%" /i /c:"fatal" /c:"error:" "%CACHE%\git.log" >nul 2>&1
if exist "%CACHE%\git.log" if not defined POWERSHELL if not errorlevel 1 type "%CACHE%\git.log"
set "GITFAILED=1"
echo.
echo            Falling back to step 2, which downloads the whole 190 MB again.
goto probe

:gitfetch_retry
rem The fetch above runs with GIT_SSL_CAINFO pointing at a bundle this
rem script went looking for on disk. When that bundle belongs to another
rem git install - or to one that reads the Windows store instead - every
rem fetch dies on it, and that failure used to mean the 190 MB archive.
rem Two cheaper answers are tried first: no bundle at all, then the
rem Windows certificate store, which is where a normal install looks.
echo            Fetch failed. Retrying without the bundle this script found.
set "GIT_SSL_CAINFO="
set "GITBUNDLE="
git -c core.longpaths=true -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=60 fetch --depth 1 --filter=blob:none --no-tags --progress origin main
if not errorlevel 1 exit /b 0
echo            Retrying with the Windows certificate store.
git -c core.longpaths=true -c http.sslBackend=schannel -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=60 fetch --depth 1 --filter=blob:none --no-tags --progress origin main
if not errorlevel 1 exit /b 0
exit /b 1

:verify
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
echo         %NMISS% file(s) main has are missing here - fetching them
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
for /f "usebackq delims=" %%p in ("%MISS%") do call :gitone "%%p"
call :gitflush
:verify_again
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%VPS%" -Tree "%LIST%" -Root "%~dp0" -Missing "%MISS%" >nul 2>&1
set /a NMISS=0
for /f "usebackq delims=" %%p in ("%MISS%") do set /a NMISS+=1
if "%NMISS%"=="0" echo         every file main lists is here
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
echo            Asking GitHub for main's latest build number.
call :atoms
if not defined RSHA7 goto probe_api
if not "%RSHA7%"=="%APPLIED%" goto probe_offer
echo   Version: main @ %APPLIED%
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
echo.
echo   --------------------------------------------------------------
echo     2/3   Downloading the game archive (about 190 MB)
if defined GITFAILED echo            Git could not apply the update, so this is the fallback.
if not defined GITOK echo            Git is not installed here, so this is the only way in.
echo.
echo            The bar below is the download: percentage, size and speed.
echo            File names appear in step 3 as each one is written.
echo            Leave this window open until it finishes.
echo.
if not defined CURL goto dl_browser
set "ZIP=%CACHE%\main.zip"
if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
rem A percentage on a bar needs the size before the bytes arrive, and only the
rem request knows it: the total is read from the response and the bar is drawn
rem from bytes received against it. PowerShell does that; curl is the fallback
rem when there is no PowerShell to draw it.
if defined POWERSHELL call :dl_ps "%ZIPURL%"
if not defined DLOK if defined POWERSHELL echo            Trying GitHub's other archive address.
if not defined DLOK if defined POWERSHELL call :dl_ps "%ZIPURL2%"
if not defined DLOK call :dl_curl
call :zipcheck
if "%ZIPOK%"=="1" goto havezip
if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
echo            The archive did not arrive in one piece.
echo.
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
set /a TICK=0
:bwait
call :sleep 5
set /a WAIT+=5
set /a TICK+=1
if %TICK% LSS 6 goto bwait_check
echo            still waiting ... %WAIT% seconds, watching Downloads
set /a TICK=0
:bwait_check
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
call :gamelock
if defined ZS echo            Downloaded %ZS% bytes - opening the archive now.
echo   ==============================================================
echo.
echo.
echo   --------------------------------------------------------------
echo     2/3   Copying the game files over this folder
echo            Every file that really differs is named as it is written.
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
call :verify

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
echo.
echo   --------------------------------------------------------------
echo     3/3   Starting the game
echo.
rem Start the game in a console of its own, minimised, with its output thrown
rem away. The engine attaches to whichever console launched it, so a child of
rem this window printed the whole engine log here and this window had to stay
rem open for the game to keep running - which read as the launcher hanging
rem around after the game was already up. The helper below owns the engine's
rem console instead, so this window closes as soon as the game starts and the
rem engine still writes save\logs\<date>.log exactly as it did before.
set "RUN=%CACHE%\play.bat"
>"%RUN%" echo @echo off
>>"%RUN%" echo cd /d "%~dp0."
>>"%RUN%" echo "%~dp0%EXE%" -config "save\config.ini" ^>nul 2^>^&1
start "" /min "%RUN%"
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
if not errorlevel 1 goto selfupdate_got
echo   Could not fetch a newer launcher - using this copy.
exit /b 0
:selfupdate_got
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
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; Add-Type -AssemblyName System.IO.Compression.FileSystem; $zip=[IO.Compression.ZipFile]::OpenRead('%ZIP%'); $root='%~dp0'; $tops=@('data','chars','stages','font','external','sound'); $mf='%CACHE%\\applied.files'; $old=@(); if (Test-Path -LiteralPath $mf) { $old=@(Get-Content -LiteralPath $mf) }; $keep=New-Object 'System.Collections.Generic.HashSet[string]'; $n=0; $gone=0; Write-Host ('            ' + $zip.Entries.Count + ' entries in the archive'); try { foreach ($e in $zip.Entries) { if ($e.FullName.EndsWith('/')) { continue }; $rel=$e.FullName.Substring($e.FullName.IndexOf('/')+1); if ($rel -eq 'config.ini') { $c=$root+'config.ini'; if (-not (Test-Path -LiteralPath $c)) { [IO.Compression.ZipFileExtensions]::ExtractToFile($e,$c,$true) }; continue }; if ($tops -notcontains ($rel -split '/')[0]) { continue }; [void]$keep.Add($rel); $dst=$root+($rel -replace '/','\'); $fi=New-Object System.IO.FileInfo($dst); if ($fi.Exists -and $fi.Length -eq $e.Length -and $fi.LastWriteTimeUtc.Ticks -eq $e.LastWriteTime.UtcDateTime.Ticks) { continue }; $dir=Split-Path -Parent $dst; if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }; [System.IO.Compression.ZipFileExtensions]::ExtractToFile($e,$dst,$true); $n++; Write-Host ('             ' + $n + ') ' + $rel) } } finally { $zip.Dispose() }; foreach ($p in $old) { if ($keep.Count -lt 500) { break }; if ($keep.Contains($p)) { continue }; $x=$root+($p -replace '/','\'); if (Test-Path -LiteralPath $x) { Remove-Item -LiteralPath $x -Force; $gone++; Write-Host ('             - ' + $p) } }; Set-Content -LiteralPath $mf -Value @($keep) -Encoding ASCII; Write-Host ('            ' + $n + ' file(s) written, ' + $gone + ' removed')"
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
echo            Robocopy compares the six game folders itself, so this
echo            fallback prints folder names and the count, not file names.
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

:dl_ps
rem %1 = the archive address. Sets DLOK when the file arrived whole.
set "DLOK="
if not exist "%DLSCRIPT%" call :dl_make
if not exist "%DLSCRIPT%" exit /b 0
if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%DLSCRIPT%" -Url "%~1" -Out "%ZIP%"
if errorlevel 1 exit /b 0
set "DLOK=1"
exit /b 0

:dl_make
rem The renderer lives in a file of its own: a twenty-line PowerShell script
rem cannot be passed on a command line without a quoting argument, and every
rem line below is plain text with no character cmd would eat.
set "DLSCRIPT=%CACHE%\download.ps1"
>  "%DLSCRIPT%" echo param([string]$Url, [string]$Out)
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
>> "%DLSCRIPT%" echo while (($read = $stream.Read($buffer, 0, $buffer.Length)) -gt 0) {
>> "%DLSCRIPT%" echo   $file.Write($buffer, 0, $read)
>> "%DLSCRIPT%" echo   $got = $got + $read
>> "%DLSCRIPT%" echo   $elapsed = ((Get-Date) - $start).TotalSeconds
>> "%DLSCRIPT%" echo   if (($elapsed - $drawn) -lt 0.25 -and ($total -le 0 -or $got -lt $total)) { continue }
>> "%DLSCRIPT%" echo   $drawn = $elapsed
>> "%DLSCRIPT%" echo   $width = 34
>> "%DLSCRIPT%" echo   $fill = 0
>> "%DLSCRIPT%" echo   if ($total -gt 0) { $fill = [int]($width * $got / $total) }
>> "%DLSCRIPT%" echo   $bar = ('#' * $fill).PadRight($width, '-')
>> "%DLSCRIPT%" echo   $pct = '   ?'
>> "%DLSCRIPT%" echo   if ($total -gt 0) { $pct = ([int](100 * $got / $total)).ToString().PadLeft(3) + '%' }
>> "%DLSCRIPT%" echo   $speed = 0.0
>> "%DLSCRIPT%" echo   if ($elapsed -gt 0) { $speed = $got / $elapsed }
>> "%DLSCRIPT%" echo   $line = [char]13 + '   [' + $bar + '] ' + $pct + '   ' + ($got / 1MB).ToString('N1') + ' / ' + ($total / 1MB).ToString('N1') + ' MB   ' + ($speed / 1MB).ToString('N1') + ' MB/s   '
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
echo   Nothing was changed. Closing.
call :sleep 3
exit 0

:zipcheck_ps
if not defined POWERSHELL exit /b 0
"%POWERSHELL%" -NoProfile -Command "try { Add-Type -AssemblyName System.IO.Compression.FileSystem; $z=[IO.Compression.ZipFile]::OpenRead('%ZIP%'); $n=($z.Entries | Where-Object { $_.FullName -like '*data/fight.def' }).Count; $z.Dispose(); if ($n -ge 1) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if errorlevel 1 exit /b 0
set "ZIPOK=1"
exit /b 0

:vtdetect
rem conhost understands ANSI once this is switched on; the value is a REG_DWORD
rem of 0x1, and anything else - or no key at all - leaves the plain display.
if not exist "%SYS%\reg.exe" exit /b 0
"%SYS%\reg.exe" query "HKCU\Console" /v VirtualTerminalLevel 2>nul | "%FINDSTR%" /c:"0x1" >nul
if errorlevel 1 exit /b 0
set "VT=1"
exit /b 0
