@echo off
rem Double-click this to start the game.
rem
rem It does not care where the game lives. The engine reads its settings from
rem save\config.ini next to the exe unless it is told otherwise with -config,
rem so this script writes that file when the folder allows it, and falls back to
rem %LOCALAPPDATA%\BigTroubleInLittleChina\config.ini when it does not - Program
rem Files, a read-only drive, a network share. Either way the game is started
rem with -config pointing at the file just written, so a stale, missing or
rem unwritable save\config.ini cannot be what the game reads.
setlocal
cd /d "%~dp0"

set "EXE="
if exist "BigTroubleInLittleChinaTheGame.exe" set "EXE=BigTroubleInLittleChinaTheGame.exe"
if not defined EXE if exist "Ikemen_GO.exe" set "EXE=Ikemen_GO.exe"
if not defined EXE (
  echo.
  echo Could not find the game executable in this folder:
  echo   %~dp0
  echo.
  echo Right-click the shortcut you normally use, choose "Open file location",
  echo then run this file from that folder.
  echo.
  pause
  exit /b 1
)

rem Write the settings where they are allowed to live: beside the exe if that
rem folder is writable, otherwise per-user.
set "CFG=%~dp0save\config.ini"
if not exist "%~dp0save" mkdir "%~dp0save" 2>nul
2>nul > "%~dp0save\.wtest" echo x
if exist "%~dp0save\.wtest" (
  del "%~dp0save\.wtest" 2>nul
) else (
  set "CFG=%LOCALAPPDATA%\BigTroubleInLittleChina\config.ini"
  if not exist "%LOCALAPPDATA%\BigTroubleInLittleChina" mkdir "%LOCALAPPDATA%\BigTroubleInLittleChina" 2>nul
)

>  "%CFG%" echo [Video]
>> "%CFG%" echo GameWidth = 1920
>> "%CFG%" echo GameHeight = 1080
>> "%CFG%" echo WindowWidth = 1920
>> "%CFG%" echo WindowHeight = 1080
>> "%CFG%" echo KeepAspect = true
>> "%CFG%" echo Fullscreen = false
>> "%CFG%" echo RenderMode = OpenGL 3.3
>> "%CFG%" echo.
>> "%CFG%" echo [Config]
>> "%CFG%" echo WindowTitle = Big Trouble in Little China: The Game
>> "%CFG%" echo RenderMode = OpenGL 3.3
>> "%CFG%" echo EnableModel = 1

rem The resolution menu is built from data\system.base.def, not from the motif,
rem so a stale data\ folder shows the stock list - 320x240 up to 1080p and no
rem 2K/4K rows - even though the build being played is new. Say which one this
rem folder has, instead of leaving it to be guessed.
if exist "%~dp0data\system.base.def" (
  findstr /c:"menuvideo.resolution.2560x1440 = 2560x1440" "%~dp0data\system.base.def" >nul 2>nul
  if errorlevel 1 (
    echo Data      : data\system.base.def is OLD - no 2K/4K menu rows in it
  ) else (
    echo Data      : data\system.base.def carries the 2K/4K resolution rows
  )
) else (
  echo Data      : data\system.base.def is missing from this folder
)

echo.
echo Folder   : %~dp0
echo Engine   : %EXE%
echo Settings : %CFG%
if exist "%~dp0VERSION.txt" type "%~dp0VERSION.txt"
findstr /i "RenderMode" "%CFG%"
echo.
echo Starting the game - the window title should read
echo "Big Trouble in Little China: The Game".
echo.

"%EXE%" -config "%CFG%"

set "LOG="
for /f "delims=" %%f in ('dir /b /o-d "save\logs\*.log" 2^>nul') do if not defined LOG set "LOG=save\logs\%%f"
echo.
if defined LOG (
  echo ----- newest log: %LOG% -----
  type "%LOG%"
  echo ---------------------------------
) else (
  echo The game exited and left no log in save\logs.
)
echo.
pause
