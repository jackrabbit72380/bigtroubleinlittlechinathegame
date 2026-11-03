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

rem Where the picture is drawn. Video.GameWidth/GameHeight is the size the game
rem is actually rendered at - the art is painted at 1920x1080, so this is the
rem honest one - and Video.WindowWidth/WindowHeight is the window it is drawn
rem into. Options > Video > Resolution only sets the window. The values already
rem on disk are kept, so a size chosen in the game's own menu survives the next
rem launch; the defaults below apply only when there is nothing to keep. Two
rem arguments override the render size:
rem
rem   "Play Big Trouble.bat" 2560 1440
rem
set "GW=1920"
set "GH=1080"
set "WW=1920"
set "WH=1080"
set "FS=false"
if exist "%CFG%" (
  for /f "tokens=2 delims==" %%v in ('findstr /b /c:"GameWidth" "%CFG%" 2^>nul') do set "GW=%%v"
  for /f "tokens=2 delims==" %%v in ('findstr /b /c:"GameHeight" "%CFG%" 2^>nul') do set "GH=%%v"
  for /f "tokens=2 delims==" %%v in ('findstr /b /c:"WindowWidth" "%CFG%" 2^>nul') do set "WW=%%v"
  for /f "tokens=2 delims==" %%v in ('findstr /b /c:"WindowHeight" "%CFG%" 2^>nul') do set "WH=%%v"
  for /f "tokens=2 delims==" %%v in ('findstr /b /c:"Fullscreen" "%CFG%" 2^>nul') do set "FS=%%v"
)
if not "%~1"=="" set "GW=%~1"
if not "%~2"=="" set "GH=%~2"
rem "GameWidth = 1920" leaves the value with its leading space on it.
set "GW=%GW: =%"
set "GH=%GH: =%"
set "WW=%WW: =%"
set "WH=%WH: =%"
set "FS=%FS: =%"
if "%GW%"=="" set "GW=1920"
if "%GH%"=="" set "GH=1080"
if "%WW%"=="" set "WW=1920"
if "%WH%"=="" set "WH=1080"
if "%FS%"=="" set "FS=false"

>  "%CFG%" echo [Video]
>> "%CFG%" echo GameWidth = %GW%
>> "%CFG%" echo GameHeight = %GH%
>> "%CFG%" echo WindowWidth = %WW%
>> "%CFG%" echo WindowHeight = %WH%
>> "%CFG%" echo KeepAspect = true
>> "%CFG%" echo Fullscreen = %FS%
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
  findstr /c:"menuvideo.resolution.11520x2160 = 11520x2160" "%~dp0data\system.base.def" >nul 2>nul
  if errorlevel 1 (
    findstr /c:"menuvideo.resolution.3840x2160 = 3840x2160" "%~dp0data\system.base.def" >nul 2>nul
    if errorlevel 1 (
      echo Data      : data\system.base.def is OLD - no 2K/4K menu rows in it
    ) else (
      echo Data      : data\system.base.def carries 2K/4K but stops there
    )
  ) else (
    echo Data      : data\system.base.def carries the full 720p-8K resolution rows
  )
) else (
  echo Data      : data\system.base.def is missing from this folder
)

echo.
echo Folder   : %~dp0
echo Engine   : %EXE%
echo Settings : %CFG%
echo Render   : %GW% x %GH%  (internal resolution - "Play Big Trouble.bat" W H)
echo Window   : %WW% x %WH%  (Options ^> Video ^> Resolution)
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
