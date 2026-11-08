@echo off
setlocal EnableExtensions
title Big Trouble in Little China - online check
rem Writes online-check.txt beside this file: which build each folder holds, which
rem engine version its own log reports, whether the lobby pack is installed, what
rem the NETWORK submenu offers, and the netplay settings in use. Nothing here
rem starts a game or changes a file.
cd /d "%~dp0"
set "OUT=%~dp0online-check.txt"
set "SYS=%SystemRoot%\System32"
set "FINDSTR=%SYS%\findstr.exe"
set "PS=%SYS%\WindowsPowerShell\v1.0\powershell.exe"
>"%OUT%" echo Online check   %DATE% %TIME%
>>"%OUT%" echo.
call :one "This folder" "%~dp0"
for %%I in ("%~dp0..\Big Trouble Online") do call :one "Big Trouble Online" "%%~fI\"
>>"%OUT%" echo.
>>"%OUT%" echo --- what the NETWORK submenu offers (from each folder's screenpack) ---
call :net "%~dp0"
for %%I in ("%~dp0..\Big Trouble Online") do call :net "%%~fI\"
>>"%OUT%" echo.
>>"%OUT%" echo --- how to play online: HOST GAME opens a port, JOIN GAME calls one ---
>>"%OUT%" echo HOST GAME opens a TCP port and waits; JOIN GAME needs that machine's
>>"%OUT%" echo address and the same game. The room list (ONLINE LOBBY) comes only
>>"%OUT%" echo from the Online Lobby Pack, which installs into external of that build.
echo.
echo Written: %OUT%
echo.
start "" notepad "%OUT%"
exit /b 0

:one
rem %1 = name, %2 = folder ending in a backslash
set "NEWLOG="
set "F=%2"
>>"%OUT%" echo [%~1]  %F%
if exist "%F%" goto one_exists
>>"%OUT%" echo    MISSING - this folder does not exist
goto :eof
:one_exists
if exist "%F%Ikemen_GO.exe" >>"%OUT%" echo    engine: Ikemen_GO.exe
if exist "%F%BigTroubleInLittleChinaTheGame.exe" >>"%OUT%" echo    engine: BigTroubleInLittleChinaTheGame.exe
if exist "%F%Ikemen_GO.exe" call :sha "%F%Ikemen_GO.exe"
if exist "%F%BigTroubleInLittleChinaTheGame.exe" call :sha "%F%BigTroubleInLittleChinaTheGame.exe"
if exist "%F%external\script\lobby.lua" >>"%OUT%" echo    lobby script: external\script\lobby.lua
for /f "delims=" %%F in ('dir /b /a-d "%~2external\script\lobby*.lua" "%~2external\script\online*.lua" "%~2external\mods\*lobby*.lua" 2^>nul') do >>"%OUT%" echo    pack file: %%F
if exist "%~2data\online\servers.json" >>"%OUT%" echo    server profile: data\online\servers.json
for /f "delims=" %%L in ('dir /b /a-d /o-d "%~2save\logs\Ikemen_*.log" 2^>nul') do if not defined NEWLOG set "NEWLOG=%~2save\logs\%%L"
if not defined NEWLOG goto one_nonlog
>>"%OUT%" echo    newest engine log: %NEWLOG%
"%FINDSTR%" /b /c:"Version:" /c:"Build Time:" /c:"Engine error" /c:"Error:" "%NEWLOG%" >>"%OUT%" 2>nul
goto one_cfg
:one_nonlog
>>"%OUT%" echo    newest engine log: none in save\logs
:one_cfg
if exist "%~2save\config.ini" "%FINDSTR%" /i /c:"ListenPort" /c:"Rollback" "%~2save\config.ini" >>"%OUT%" 2>nul
goto :eof

:sha
rem %1 = an engine exe. One line, so the same build can be recognised on
rem both PCs, and a file Defender names can be checked against the table in
rem ONLINE-SETUP.md.
if not exist "%PS%" goto :eof
for /f "usebackq delims=" %%H in (`"%PS%" -NoProfile -Command "(Get-FileHash -LiteralPath '%~1' -Algorithm SHA256).Hash" 2^>nul`) do >>"%OUT%" echo    sha256: %%H
goto :eof

:net
rem %1 = folder ending in a backslash
if not exist "%~1data\ikemen1\system.def" goto net_none
>>"%OUT%" echo [%~1]
"%FINDSTR%" /i /c:"menu.itemname.menunetwork" "%~1data\ikemen1\system.def" >>"%OUT%" 2>nul
goto :eof
:net_none
>>"%OUT%" echo [%~1]  no data\ikemen1\system.def
goto :eof
