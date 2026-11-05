@echo off
rem ===========================================================================
rem  BIG TROUBLE IN LITTLE CHINA - updater v16
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
echo                        updater v16
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
set "CHANGED="
set "BASE="
set "NCOP=0"
set "NDEL=0"
set "FOUNDZIP="

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

rem ---- transport 1: git, which moves only the objects that differ ---------
rem Depth 1 plus a blob filter: the first run still has to bring the art, but
rem every run after that transfers only what a commit touched, usually a few
rem small files. Sparse checkout also leaves out the folders the game never
rem copies - artifacts, concept_art, art_src, tools - which is 128 MB of the
rem committed tree.
:trygit
echo            Git found - comparing with main.
if exist "%CACHE%\repo\.git" goto gitpull
if exist "%CACHE%\repo" rd /s /q "%CACHE%\repo" >nul 2>&1
echo            First run: building the local copy. This is the big one.
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
rem What differs, so the copy can be as small as the fix. The base is the
rem revision this folder last applied, not what the local clone had: the
rem folder can be further behind than the clone, and copying only the
rem clone's own delta would leave those commits unapplied. A shallow clone
rem usually cannot resolve an older base, which just means a whole copy.
set "CHANGED="
set "BASE="
if exist "%CACHE%\applied.txt" set /p BASE=<"%CACHE%\applied.txt"
if not defined BASE set "BASE=%OLDSHA%"
if not defined BASE goto gitdiffdone
if /i "%BASE%"=="%NEWSHA%" goto gitdiffdone
git -C "%CACHE%\repo" diff --name-only --no-renames "%BASE%" "%NEWSHA%" >"%CACHE%\changed.txt" 2>nul
if errorlevel 1 goto gitdiffdone
set "CHANGED=%CACHE%\changed.txt"
:gitdiffdone
if "%OLDSHA%"=="%NEWSHA%" echo            Main has not moved - nothing to download.
if not "%OLDSHA%"=="%NEWSHA%" echo            Fetched only the files that changed.

:gitdone
if not exist "%CACHE%\repo\data\fight.def" goto gitfail
set "SRC=%CACHE%\repo"
set "WHICH=git"
for /f %%s in ('git -C "%CACHE%\repo" rev-parse --short HEAD 2^>nul') do set "VER=%%s"
if not defined VER goto gitapply
rem if this exact revision is already in the game folder, do not copy 340 MB
rem over the top of itself just to launch
set "APPLIED="
if exist "%CACHE%\applied.txt" set /p APPLIED=<"%CACHE%\applied.txt"
if not "%APPLIED%"=="%VER%" goto gitapply
if not exist "%~dp0data\fight.def" goto gitapply
echo   files  : main @ %VER%
echo            Already up to date - launching what is here.
goto launch

:gitapply
rem The clone holds main; this is the step that puts it into the game folder.
rem It was missing: with git installed the launcher fetched and then went
rem straight on to launching, so the copy only ever happened on the zip path.
call :synctree

rem what the folder should contain once this copy is done: the archive path
rem reads the same list, so a later archive update deletes exactly the files
rem main dropped, and never a file the player added
git -C "%CACHE%\repo" ls-files data chars stages font external sound >"%CACHE%\applied.files" 2>nul
goto copied

:gitfail
echo            Git could not fetch. It said:
if not exist "%CACHE%\git.log" goto download
"%FINDSTR%" /i /c:"fatal" /c:"error" /c:"unable" "%CACHE%\git.log"
echo            Trying a direct download instead.
goto probe

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
if not defined APPLIED goto download
call :atoms
if not defined RSHA7 goto probe_api
if not "%RSHA7%"=="%APPLIED%" goto download
echo   files  : main @ %APPLIED%
echo            Main has not moved - nothing to download.
goto launch

:probe_api
rem Fallback only. The API answers the same question but counts against an
rem hourly quota, so it is asked when the feed could not answer, not always.
call :headsha
if not defined RSHA7 goto download
if not "%RSHA7%"=="%APPLIED%" goto download
echo   files  : main @ %APPLIED%
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
echo            About 190 MB. The archive is built fresh for each commit and
echo            cannot be continued part-way, so leave this window open until
echo            it finishes.
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
if "%WHICH%"=="git" for /f %%v in ('git -C "%CACHE%\repo" rev-parse --short HEAD 2^>nul') do set "VER=%%v"
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
if errorlevel 1 echo   HUD    : OLD - the copy did not land
if not errorlevel 1 echo   HUD    : dragon - back is health, belly is audacity
if defined VER echo   files  : main @ %VER%
if not defined VER echo   files  : main, from the zip
echo.

:launch
echo   [ 4/4 ]  Starting the game
echo.
start "" "%EXE%" -config "save\config.ini"
call :sleep 8
"%TASKLIST%" /fi "imagename eq %EXE%" 2>nul | "%FINDSTR%" /i /c:"%EXE%" >nul
if errorlevel 1 goto launchfail
echo   Running. Have fun.
call :sleep 2
exit /b 0

:skipver2
goto skipver

:launchfail
echo   The game did not stay open. Start it by hand to see the engine's
echo   message, and check docs/INSTALL.md - the renderer setting is the
echo   usual reason, and deleting save\config.ini resets it.
echo.
pause
exit /b 1

:wrongfolder
echo   This file belongs in your game folder - the one that has
echo   BigTroubleInLittleChinaTheGame.exe in it.
echo.
pause
exit /b 1

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
exit /b 1

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
start "" /b "%RUNB%"
set /a SECS=0
set /a LASTKB=0
call :drawdl 0 ""
:cfpoll
call :sleep 5
set /a SECS+=5
set "SZ=0"
for %%A in ("%ZIP%") do set "SZ=%%~zA"
set /a KB=SZ/1024
set /a DELTA=KB-LASTKB
set /a LASTKB=KB
rem The first reading has nothing to compare against, so it would read as a
rem huge burst. Two polls are enough to average over.
if %SECS% LSS 10 set /a DELTA=0
set /a RATE=DELTA/5
set "DLINFO="
if %RATE% GTR 0 set /a LEFT=(194560-KB)/RATE
if %RATE% GTR 0 call :clock %LEFT% LEFTCLOCK
if %RATE% GTR 0 set "DLINFO=%RATE% KB/s   %LEFTCLOCK% left"
if %SECS% GEQ 15 if %RATE% LSS 1 set "DLINFO=no data arriving"
call :drawdl %KB% "%DLINFO%"
if exist "%DONE%" goto cfdone
if %SECS% LSS 1200 goto cfpoll
echo.
echo            No complete transfer after 20 minutes. The archive has to
echo            start again, so run the updater once the connection is back.
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
rem %1 = done, %2 = total -> BAR: 32 cells, a body of = and a head at the tip
rem The head must not be a redirect character: cmd parses redirection after
rem variable expansion, so echoing a bar whose tip was > wrote the left half
rem of the bar into a file named after its right half, every redraw. That is
rem what filled the game folder with progress-bar files.
setlocal EnableDelayedExpansion
set /a "C=(%~1)*32/(%~2)"
if !C! LSS 1 set "C=1"
if !C! GTR 32 set "C=32"
set "BAR="
for /l %%i in (1,1,32) do (
  if %%i LSS !C! set "BAR=!BAR!="
  if %%i EQU !C! set "BAR=!BAR!#"
  if %%i GTR !C! set "BAR=!BAR!-"
)
endlocal & set "BAR=%BAR%"
exit /b 0

:drawdl
rem %1 = kilobytes so far, %2 = rate and time left, once there is enough of a
rem sample for them to mean anything. Only this one line is rewritten, where it
rem stands: clearing the window every five seconds made the whole screen blink
rem and threw the cursor back to the top each time.
call :dragonbar %~1 194560
if not defined DLHEAD goto drawdl_head
set /a DLMB=%~1/1024
set /a DLTENTH=%~1*10/1024-DLMB*10
set "DLTEXT=     [%BAR%]  %DLMB%.%DLTENTH%/190 MB"
if not "%~2"=="" set "DLTEXT=     [%BAR%]  %DLMB%.%DLTENTH%/190 MB   %~2"
set "DLTEXT=%DLTEXT%%PAD%"
set "DLTEXT=%DLTEXT:~0,76%"
if "%DLTEXT%"=="%DLLAST%" exit /b 0
set "DLLAST=%DLTEXT%"
call :dlwrite
exit /b 0

:drawdl_head
set "DLHEAD=1"
set "PAD=                                                                                "
echo.
echo   Fetching the newest build of the game.
echo.
echo   Keep this window open - the game starts by itself when the download is
echo   done. The archive is rebuilt for every commit, so a transfer that stops
echo   starts again from the beginning.
echo.
set /a DLMB=%~1/1024
set /a DLTENTH=%~1*10/1024-DLMB*10
set "DLTEXT=     [%BAR%]  %DLMB%.%DLTENTH%/190 MB"
set "DLTEXT=%DLTEXT%%PAD%"
set "DLTEXT=%DLTEXT:~0,76%"
set "DLLAST=%DLTEXT%"
call :dlwrite
exit /b 0

:dlwrite
rem Written without a trailing newline and led by a carriage return, so it lands
rem on top of the previous reading instead of under it.
if defined CR (
  <nul set /p "=%CR%%DLTEXT%"
  exit /b 0
)
echo %DLTEXT%
exit /b 0

:clock
rem %1 = seconds, %2 = the variable to leave m:ss in.
set /a "CK_M=%~1/60"
set /a "CK_S=%~1%%60"
set "CK_T=%CK_M%:%CK_S%"
if %CK_S% LSS 10 set "CK_T=%CK_M%:0%CK_S%"
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
