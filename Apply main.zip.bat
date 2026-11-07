@echo off
rem ===========================================================================
rem  BIG TROUBLE IN LITTLE CHINA - apply main.zip  (no internet needed)
rem
rem  1. in your browser, download
rem     https://codeload.github.com/jackrabbit72380/bigtroubleinlittlechinathegame/zip/refs/heads/main
rem  2. save the zip in this folder
rem  3. double-click this file
rem
rem  Windows tools are called by full path: a Git for Windows install that puts
rem  its usr\bin on PATH shadows System32, and its tar reads H:\... as a remote
rem  host ("Cannot connect to H:").
rem ===========================================================================
setlocal EnableExtensions DisableDelayedExpansion
color 07
cd /d "%~dp0"
title Big Trouble in Little China: The Game - Zip Applier

set "SYS=%SystemRoot%\System32"
set "TAR=%SYS%\tar.exe"
set "CURL=%SYS%\curl.exe"
set "FINDSTR=%SYS%\findstr.exe"
set "TASKLIST=%SYS%\tasklist.exe"
set "ROBOCOPY=%SYS%\robocopy.exe"
set "POWERSHELL=%SYS%\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%TAR%" set "TAR="
if not exist "%CURL%" set "CURL="
if not exist "%POWERSHELL%" set "POWERSHELL="

echo.
echo Big Trouble in Little China - The Game  -  Apply update
echo.
echo Folder: %~dp0
echo.

set "EXE="
if exist "BigTroubleInLittleChinaTheGame.exe" set "EXE=BigTroubleInLittleChinaTheGame.exe"
if not defined EXE if exist "Ikemen_GO.exe" set "EXE=Ikemen_GO.exe"

set "ZIP="
if exist "%~dp0main.zip" set "ZIP=%~dp0main.zip"
if not defined ZIP if exist "%~dp0bigtroubleinlittlechinathegame-main.zip" set "ZIP=%~dp0bigtroubleinlittlechinathegame-main.zip"
rem a zip the browser dropped in Downloads is used too, newest first
if not defined ZIP call :fromdownloads
if defined ZIP goto unzip
echo   [ ! ]  no zip found
echo.
echo   checking the launcher on its own
call :fixlauncher
echo.
echo   download the zip in your browser from:
echo     https://codeload.github.com/jackrabbit72380/bigtroubleinlittlechinathegame/zip/refs/heads/main
echo   save it here, then run this file again
echo.
pause
exit /b 1

:unzip
echo   [1/3]  unpacking
echo            %ZIP%
set "SRC="
set "TMP=%~dp0.update-cache"
if not exist "%TMP%" mkdir "%TMP%" 2>nul
if exist "%TMP%\unpack" rd /s /q "%TMP%\unpack" >nul 2>&1
mkdir "%TMP%\unpack" 2>nul
if not defined TAR goto unzip_ps
"%TAR%" -xf "%ZIP%" -C "%TMP%\unpack"
if errorlevel 1 goto unzip_ps
goto unpacked

:unzip_ps
if not defined POWERSHELL goto badzip
if exist "%TMP%\unpack" rd /s /q "%TMP%\unpack" >nul 2>&1
mkdir "%TMP%\unpack" 2>nul
set "ZQ=%ZIP:'=''%"
set "TQ=%TMP:'=''%"
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force -LiteralPath '%ZQ%' -DestinationPath '%TQ%\unpack'"

:unpacked
for /d %%D in ("%TMP%\unpack\*") do set "SRC=%%~fD"
if not defined SRC goto badzip
echo.
echo   [2/3]  copying the game files over this folder
for %%F in (data chars stages font external sound) do (
  if exist "%SRC%\%%F" echo            %%F
  if exist "%SRC%\%%F" "%ROBOCOPY%" "%SRC%\%%F" "%~dp0%%F" /E /NFL /NDL /NJH /NJS /NP >nul
)
if not exist "%SRC%\config.ini" goto copied
copy /Y "%SRC%\config.ini" "%~dp0config.ini" >nul
if not exist "%~dp0save" mkdir "%~dp0save" 2>nul
if not exist "%~dp0save\config.ini" copy /Y "%SRC%\config.ini" "%~dp0save\config.ini" >nul

:copied
call :fixlauncher
if not defined EXE goto noexe
echo   [3/3]  starting the game
echo.
start "" "%EXE%" -config "save\config.ini"
echo   started.
call :sleep 3
exit /b 0

:noexe
echo   no game exe here, so the files were copied but the game was not started
echo.
pause
exit /b 0

:badzip
echo.
echo   could not unpack that zip - it is probably an incomplete download.
echo   delete it, download it again, and run this file.
echo.
pause
exit /b 1

:fixlauncher
rem The launcher lives at the root of the archive, not in the six folders the
rem updater writes, so nothing here ever replaced it - and it is the one file
rem that cannot repair itself: a copy cut short stops at the cut, leaves a
rem prompt, and can never fetch the whole one. This tool is not the file being
rem written, so it can put a whole launcher here: from the archive when there is
rem one, and otherwise the few KB fetched on its own, so a folder with no zip
rem but a working connection still gets a launcher it can double-click.
set "NEWL=%~dp0Update and Play.new"
set "LURL=https://raw.githubusercontent.com/jackrabbit72380/bigtroubleinlittlechinathegame/main/Update%%20and%%20Play.bat"
if not exist "%SRC%\Update and Play.bat" goto fixlauncher_fetch
copy /Y "%SRC%\Update and Play.bat" "%~dp0Update and Play.bat" >nul 2>&1
if not exist "%~dp0Update and Play.bat" goto fixlauncher_fetch
echo            Update and Play.bat
exit /b 0
:fixlauncher_fetch
if exist "%NEWL%" del /q "%NEWL%" >nul 2>&1
if defined CURL "%CURL%" -sS -L --fail --ssl-no-revoke --connect-timeout 15 --max-time 40 -o "%NEWL%" "%LURL%" >nul 2>&1
if not exist "%NEWL%" if defined POWERSHELL call :fixlauncher_ps
if not exist "%NEWL%" goto fixlauncher_no
rem the last line every whole launcher carries: a transfer that stopped half
rem way does not have it, and installing that is how a folder ends up with a
rem copy that dies the moment it is double-clicked
"%FINDSTR%" /c:"btilc-launcher-end" "%NEWL%" >nul 2>&1
if errorlevel 1 goto fixlauncher_no
move /Y "%NEWL%" "%~dp0Update and Play.bat" >nul 2>&1
if exist "%NEWL%" del /q "%NEWL%" >nul 2>&1
echo            Update and Play.bat
exit /b 0
:fixlauncher_no
if exist "%NEWL%" del /q "%NEWL%" >nul 2>&1
echo   [ ! ]  could not put a whole Update and Play.bat here - the copy in this
echo          folder is left as it is, and the game files below still apply
exit /b 0
:fixlauncher_ps
set "LPS=%TEMP%\btilc-launcher.ps1"
>  "%LPS%" echo param([string]$Url, [string]$Out)
>> "%LPS%" echo $ErrorActionPreference = 'Stop'
>> "%LPS%" echo [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
>> "%LPS%" echo $wc = New-Object Net.WebClient
>> "%LPS%" echo $wc.Headers.Add('User-Agent', 'btilc-updater')
>> "%LPS%" echo $wc.DownloadFile($Url, $Out)
if not exist "%LPS%" exit /b 0
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%LPS%" -Url "%LURL%" -Out "%NEWL%" >nul 2>&1
exit /b 0

:sleep
set /a "P=%~1+1"
"%SYS%\ping.exe" -n %P% 127.0.0.1 >nul 2>&1
exit /b 0

:fromdownloads
for /f "delims=" %%Z in ('dir /b /a-d /o-d "%USERPROFILE%\Downloads\*bigtrouble*.zip" 2^>nul') do (
  if not defined ZIP set "ZIP=%USERPROFILE%\Downloads\%%Z"
)
if defined ZIP echo            using %ZIP%
exit /b 0
