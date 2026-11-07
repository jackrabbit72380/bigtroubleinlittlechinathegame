@echo off
rem ===========================================================================
rem  BIG TROUBLE IN LITTLE CHINA - Updater v53
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
set "CERT=%SYS%\certutil.exe"
if not exist "%TAR%" set "TAR="
if not exist "%CURL%" set "CURL="
if not exist "%POWERSHELL%" set "POWERSHELL="
if not exist "%WHERE%" set "WHERE="
if not exist "%FIND%" set "FIND="
if not exist "%CERT%" set "CERT="

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


rem The version the title above the pistol and the run log both read, so the
rem two cannot drift apart when the script is bumped.
set "UPDVER=53"
call :say "=============================================================="
call :say "BIG TROUBLE IN LITTLE CHINA  -  THE GAME  -  Updater v%UPDVER%"
call :say "=============================================================="
rem The number that counts the run is written at the end of the pistol's
rem barrel, so the console is asked for cursor control before the drawing.
call :vt
call :gun

set "EXE="
if exist "BigTroubleInLittleChinaTheGame.exe" set "EXE=BigTroubleInLittleChinaTheGame.exe"
if not defined EXE if exist "Ikemen_GO.exe" set "EXE=Ikemen_GO.exe"
if not defined EXE goto wrongfolder
call :log folder %~dp0  exe %EXE%
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
rem Everything this launcher writes goes to the temp folder. A game folder can
rem be read only, on a drive with no room, or behind a path cmd will not take, and
rem a cache that cannot be written breaks every redirect after it - which is what
rem left the download sitting at zero with no curl running behind it.
set "CACHE=%TEMP%\btilc-updater"
if not exist "%CACHE%" mkdir "%CACHE%" 2>nul
if not exist "%CACHE%" set "CACHE=%TEMP%"
rem Progress counts every percent of the run, 1 to 100, at the muzzle of the
rem pistol: one number, replaced by the next, with nothing printed beside it.
rem Every run leaves this behind. When a window closes before the game appears,
rem this file is the only record of how far it got and why it stopped.
set "LOG=%CACHE%\last-run.log"
>"%LOG%" echo [%DATE% %TIME%] launcher start  arg=%1 2>nul
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

call :pct 2 "Checking for updates"
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
git -c core.quotepath=false ls-tree -r FETCH_HEAD -- data chars stages font external sound >"%CACHE%\tree.txt" 2>>"%CACHE%\git.log"
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
call :pct 20 "Listing the files"
set "PLANPS=%CACHE%\plan.ps1"
>  "%PLANPS%" echo param([string]$Tree, [string]$Old, [string]$Changed, [string]$Dropped)
>> "%PLANPS%" echo $ErrorActionPreference = 'Stop'
>> "%PLANPS%" echo $prev = @{}
>> "%PLANPS%" echo foreach ($l in (Get-Content -LiteralPath $Old)) { $i = $l.IndexOf([char]9); if ($i -gt 0) { $old[$l.Substring($i + 1)] = $l.Substring(0, $i) } }
>> "%PLANPS%" echo $new = @{}
>> "%PLANPS%" echo $chg = New-Object System.Collections.ArrayList
>> "%PLANPS%" echo foreach ($l in (Get-Content -LiteralPath $Tree)) { $i = $l.IndexOf([char]9); if ($i -lt 1) { continue }; $meta = $l.Substring(0, $i).Split(' '); $sha = $meta[$meta.Length - 1]; $p = $l.Substring($i + 1); $new[$p] = $sha; if ($prev.ContainsKey($p) -and $prev[$p] -eq $sha) { continue }; [void]$chg.Add($p) }
>> "%PLANPS%" echo $drop = New-Object System.Collections.ArrayList
>> "%PLANPS%" echo foreach ($p in $prev.Keys) { if (-not $new.ContainsKey($p)) { [void]$drop.Add($p) } }
>> "%PLANPS%" echo Set-Content -LiteralPath $Changed -Value @($chg) -Encoding ASCII
>> "%PLANPS%" echo Set-Content -LiteralPath $Dropped -Value @($drop) -Encoding ASCII
if not exist "%PLANPS%" exit /b 1
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%PLANPS%" -Tree "%CACHE%\tree.txt" -Old "%CACHE%\manifest.txt" -Changed "%CACHE%\changed.txt" -Dropped "%CACHE%\dropped.txt" 2>>"%CACHE%\git.log"
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
set "ESC=
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
set "MUZZLE=42"
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
echo    ....../ '---___________----_____^|]=
echo    ...../_==o;;;;;;;;_______.:/
echo    .....), ---.(_(__) /
echo    ....// (..) ), ----"
echo    ...//___//
echo    ..//___//
echo    .//___//
set "GUNSHOWN=1"
rem The full barrel is built once here and sliced per percent below, so a console
rem without cursor control redraws the picture without a loop per redraw.
if not defined BARFULL for /l %%P in (1,1,%BARMAX%) do call set "BARFULL=%%BARFULL%%|"
rem The line under the drawing is remembered, so every percentage can write at
rem the muzzle and come straight back here. The messages that follow print
rem below the pistol, never over it.
if defined VTOK set /p "=%ESC%[s" <nul
rem A console that refused the cursor mode would otherwise sit on a bare picture
rem until the first step reports, which on a slow first check can be a while.
if not defined VTOK call :gunredraw 0 0
exit /b 0

:gauge
rem %1 = percent for the whole run. %2 is the name of the step: the callers still
rem pass it, nothing prints it - the window shows the number and nothing else.
rem
rem One pipe on the barrel for every percent, counting 1, 2, 3 ... 100, with the
rem number following the last pipe, and the game starts on a full barrel. A
rem console that takes cursor moves gets the bar; one that does not keeps the
rem number in the title bar, so an old Windows still shows how far the run is.
rem
rem A step that jumps from 12 to 25 fills in 13 to 24 as well, so no number is
rem skipped, and a step that re-reports the number it just showed prints nothing.
if "%~1"=="" exit /b 0
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
exit /b 0

:gaugeone
rem %1 = the percent to show. This step adds the pipe for it to the barrel and
rem writes the count in the space right after the last pipe, so the bar and the
rem number grow together and 100% is a barrel filled end to end. Where the window
rem cannot hold a hundred pipes, two percentages share one and the bar still ends
rem full. Only one character and three digits change: the pistol is not redrawn.
set "PCTX=  %~1%%"
call set "PCTX=%%PCTX:~-4%%"
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
set "GWRITE=%ESC%[u%ESC%[7A%ESC%[%GCOL%G| "
set "GWRITE=%GWRITE%%PCTX%"
set "GWRITE=%GWRITE%%ESC%[K%ESC%[u"
set /p "=%GWRITE%" <nul
title Big Trouble in Little China: The Game - Updater - %~1 percent
exit /b 0
:gaugeone_plain
rem No cursor control here. The title bar alone was all this did, and a run then
rem showed a picture with no number on it at all - the number went where nobody
rem looks. The pistol is drawn again with the barrel filled to this percent
rem instead. The art is nine lines and the bar only changes when a pipe is added,
rem so the screen is cleared once per pipe rather than once per percent.
set /a RPOS=%~1*%BARMAX%/100
if %~1 GTR 0 if %RPOS% LSS 1 set "RPOS=1"
if defined RPBAR if %RPOS% EQU %RPBAR% goto gaugeone_plain_title
set "RPBAR=%RPOS%"
call :gunredraw %~1 %RPOS%
:gaugeone_plain_title
title Big Trouble in Little China: The Game - Updater - %~1 percent
exit /b 0

:gunredraw
rem %1 = percent, %2 = how many pipes that is. The art is :gun's, with the barrel
rem filled and the count beside it, so a console that will not take cursor moves
rem still shows the run the way the window is meant to look. The pipes start two
rem columns past the drawn barrel's end, where the muzzle write puts them.
set "RBAR="
if defined BARFULL call set "RBAR=%%BARFULL:~0,%~2%%"
set "RPCT=  %~1%%"
call set "RPCT=%%RPCT:~-4%%"
cls
echo.
echo    BIG TROUBLE IN LITTLE CHINA  -  THE GAME  -  UPDATER v%UPDVER%
echo    ..._...^|..____________________, ,
echo    ....../ '---___________----_____^|]=  %RBAR% %RPCT%
echo    ...../_==o;;;;;;;;_______.:/
echo    .....), ---.(_(__) /\
echo    ....// (..) ), ----"
echo    ...//___//
echo    ..//___//
echo    .//___//
exit /b 0

:bar
rem %1 = files written, %2 = files to write. Writing is 25-80% of the job.
if "%~2"=="0" exit /b 0
set /a GSTEP=%~1*55/%~2
set /a GOPCT=25+GSTEP
call :gauge %GOPCT% "Writing files"
exit /b 0

:pct
rem %1 = percent, %2 = the label for it.
call :gauge %~1 "%~2"
exit /b 0

:barflush
rem Every line ends itself now, so there is nothing to flush.
exit /b 0

rem %1 = seconds waited, %2 = what is being waited for. One plain line every
rem five seconds: a spinner would have to redraw in place, which is the cursor
rem movement that broke the old progress bar on this console.
:spin
set /a SMOD=%~1 %% 5
if %SMOD% NEQ 0 exit /b 0
call :say "%~2 %~1s"
exit /b 0
:spin_plain
set /a SDOT=%~1 %% 5
if %SDOT%==0 call :say "%~2 %~1s"
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
exit /b 0
:spinwait_bad
exit /b 1
:spinwait_late
exit /b 2
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

:gamelock
call :barflush
rem The engine keeps its data files open while it runs and Windows will not let
rem git replace one. Updating under a running game fails with "being used by
rem another process", so this waits for it to close rather than writing into a
rem folder that cannot be written.
if not defined EXE exit /b 0
if not defined TASKLIST exit /b 0
"%TASKLIST%" /fi "imagename eq %EXE%" /nh 2>nul | "%FINDSTR%" /i /c:"%EXE%" >nul 2>&1
if errorlevel 1 exit /b 0
echo.
echo The game is running. Close it - this window continues by itself.
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
if exist "%CACHE%\git.log" if defined POWERSHELL "%POWERSHELL%" -NoProfile -Command "Get-Content -LiteralPath '%CACHE%\git.log' -Tail 8" 2>nul
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
call :pct 95 "Finishing up"
if not "%WHICH%"=="git" goto skipver2

:skipver
"%FINDSTR%" /c:"bg1.spr = 20,0" "%~dp0data\fight.def" >nul 2>nul
if errorlevel 1 echo Warning: data\fight.def does not match the new build.
if defined VER call :say "main @ %VER%"
if not defined VER call :say "main @ local archive"

call :datareport

:launch
call :pct 100 "Starting the game"
call :barflush
rem The engine runs in a helper of its own, so this window can close as soon as
rem the game is up - but its output is kept instead of being thrown away. A
rem game that dies on a missing file or a renderer setting used to write its
rem reason to nul and leave the window closing over it, which read as "it did
rem nothing". Now the game has a few seconds to appear, and if it does not its
rem own words are printed here and the window waits so they can be read.
set "RUN=%CACHE%\play.bat"
set "GLOG=%CACHE%\game.log"
set "GCODE=%CACHE%\game.code"
if exist "%GLOG%" del /q "%GLOG%" >nul 2>&1
if exist "%GCODE%" del /q "%GCODE%" >nul 2>&1
>"%RUN%" echo @echo off
>>"%RUN%" echo cd /d "%~dp0."
>>"%RUN%" echo "%~dp0%EXE%" -config "save\config.ini" ^>"%GLOG%" 2^>^&1
>>"%RUN%" echo echo %%errorlevel%% ^>"%GCODE%"
call :log starting %EXE%
if defined POWERSHELL "%POWERSHELL%" -NoProfile -Command "Start-Process -FilePath 'cmd.exe' -ArgumentList '/c','%RUN%' -WindowStyle Hidden" >nul 2>&1
if not defined POWERSHELL start "" /min "%RUN%"
rem Without tasklist there is no way to tell whether the game came up, so
rem the window closes as it did before rather than reporting a false failure.
if not exist "%TASKLIST%" exit 0
set /a LW=0
:launch_wait
call :sleep 1
set /a LW+=1
"%TASKLIST%" /fi "imagename eq %EXE%" /nh 2>nul | "%FINDSTR%" /i /c:"%EXE%" >nul 2>&1
if not errorlevel 1 goto launch_ok
rem A game still loading has already written to its log, because the helper
rem redirects the engine's output there before the engine runs. Twelve seconds
rem was shorter than a first load of 190 MB of art, so a game that came up was
rem called a game that did not, and this window waited over it. The window now
rem gives the engine 45 seconds and treats any output as "it is running".
if exist "%GLOG%" for %%A in ("%GLOG%") do if %%~zA GTR 0 goto launch_ok
if %LW% GEQ 45 goto launch_died
goto launch_wait
:launch_ok
call :log game is running after %LW%s
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
if not defined CURL exit /b 0
rem The launcher is not in the six folders the update writes, so before this it
rem could never be refreshed - a folder running v19 stayed on v19 no matter what
rem main fixed. It is fetched on its own here, a few KB.
"%CURL%" -sS -L --fail --ssl-no-revoke --connect-timeout 15 --max-time 40 -H "User-Agent: btilc-updater" -o "%CACHE%\launcher-new.bat" "https://raw.githubusercontent.com/%REPO%/main/Update%%20and%%20Play.bat" >nul 2>&1
if not errorlevel 1 goto selfupdate_got
call :say "Could not fetch a newer launcher - using this copy."
exit /b 0
:selfupdate_got
if not exist "%CACHE%\launcher-new.bat" exit /b 0
rem A truncated file, an error page or anything else that is not the launcher
rem must never be copied over a working one.
for %%A in ("%CACHE%\launcher-new.bat") do if %%~zA LSS 5000 exit /b 0
"%FINDSTR%" /c:"BIG TROUBLE IN LITTLE CHINA" "%CACHE%\launcher-new.bat" >nul 2>&1
if errorlevel 1 exit /b 0
"%SYS%\fc.exe" /b "%CACHE%\launcher-new.bat" "%~f0" >nul 2>&1
if not errorlevel 1 goto selfupdate_current
echo.
echo This launcher is not the current one - updating it before anything else.
rem cmd reads a batch file while it runs it, so this file cannot be written over
rem by the window that is executing it. A detached helper waits for the window to
rem close, copies the new launcher into place and starts it again with --updated.
rem If the copy loses the race the restarted window carries on as it is: the next
rem launch tries again, and nothing here can loop.
rem Replacing this file can be refused outright - a read-only file, a folder
rem under Windows' control, a scanner holding it. Three attempts is enough:
rem past that this copy runs the update as it is instead of closing, fetching
rem and closing again on every double-click.
set "SWN=0"
if exist "%CACHE%\swap.attempts" for /f "usebackq delims=" %%n in ("%CACHE%\swap.attempts") do set "SWN=%%n"
set /a SWN+=1
>"%CACHE%\swap.attempts" echo %SWN% 2>nul
if %SWN% GTR 3 goto selfupdate_stuck
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
echo It restarts in a moment with the current one.
echo.
exit 0

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
call :log folder refused writes after %WTRY% tries: %~dp0
if not exist "%~dp0%EXE%" goto folder_denied_noexe
goto launch
:folder_denied_noexe
echo There is no %EXE% here either, so there is nothing to start.
echo.
call :close_soon 20
exit 1

:wrongfolder
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
rem inside it, an apostrophe in the folder path - drops to unpack-and-copy.
set "PSOK=0"
if not defined POWERSHELL goto ziptree_done
if not defined ZIP goto ziptree_done
if not exist "%ZIP%" goto ziptree_done
echo %~dp0|"%FINDSTR%" /c:"'" >nul 2>&1
if not errorlevel 1 goto ziptree_done
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; Add-Type -AssemblyName System.IO.Compression.FileSystem; $zip=[IO.Compression.ZipFile]::OpenRead('%ZIP%'); $root='%~dp0'; $tops=@('data','chars','stages','font','external','sound'); $mf='%CACHE%\\applied.files'; $old=@(); if (Test-Path -LiteralPath $mf) { $old=@(Get-Content -LiteralPath $mf) }; $keep=New-Object 'System.Collections.Generic.HashSet[string]'; $n=0; $gone=0; Write-Host ('            ' + $zip.Entries.Count + ' entries in the archive'); try { foreach ($e in $zip.Entries) { if ($e.FullName.EndsWith('/')) { continue }; $rel=$e.FullName.Substring($e.FullName.IndexOf('/')+1); if ($rel -eq 'config.ini') { $c=$root+'config.ini'; if (-not (Test-Path -LiteralPath $c)) { [IO.Compression.ZipFileExtensions]::ExtractToFile($e,$c,$true) }; continue }; if ($tops -notcontains ($rel -split '/')[0]) { continue }; [void]$keep.Add($rel); $dst=$root+($rel -replace '/','\'); $fi=New-Object System.IO.FileInfo($dst); if ($fi.Exists -and $fi.Length -eq $e.Length -and $fi.LastWriteTimeUtc.Ticks -eq $e.LastWriteTime.UtcDateTime.Ticks) { continue }; $dir=Split-Path -Parent $dst; if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }; [System.IO.Compression.ZipFileExtensions]::ExtractToFile($e,$dst,$true); $n++; Write-Host ('             ' + $n + ') ' + $rel) } } finally { $zip.Dispose() }; foreach ($p in $old) { if ($keep.Count -lt 500) { break }; if ($keep.Contains($p)) { continue }; $x=$root+($p -replace '/','\'); if (Test-Path -LiteralPath $x) { Remove-Item -LiteralPath $x -Force; $gone++; Write-Host ('             - ' + $p) } }; Set-Content -LiteralPath $mf -Value @($keep) -Encoding ASCII; Write-Host ('Installed ' + $n + ' file(s), removed ' + $gone)"
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

for %%F in (data chars stages font external sound) do (
  if exist "%SRC%\%%F" call :say "%%F"
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
>> "%DLSCRIPT%" echo   if ($total -gt 0) { $pct = $whole.ToString().PadLeft(3) + '%' }
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

:log
rem Appends one line to the run log. Cheap enough to call at every step.
if not defined LOG exit /b 0
>>"%LOG%" echo [%TIME%] %* 2>nul
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
"%POWERSHELL%" -NoProfile -Command "try { Add-Type -AssemblyName System.IO.Compression.FileSystem; $z=[IO.Compression.ZipFile]::OpenRead('%ZIP%'); $n=($z.Entries | Where-Object { $_.FullName -like '*data/fight.def' }).Count; $z.Dispose(); if ($n -ge 1) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if errorlevel 1 exit /b 0
set "ZIPOK=1"
exit /b 0

