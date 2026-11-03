@echo off
rem Double-click this to start the game.
rem
rem It writes save\config.ini from scratch - the engine opens that exact path at
rem startup and panics if it is missing, so a deleted or corrupted file leaves
rem the game unable to start at all. Nothing else in this folder is required,
rem including config.ini: the settings are written here, with the renderer
rem pinned to the OpenGL path that boots.
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

if not exist "save" mkdir "save"
if errorlevel 1 (
  echo.
  echo Could not create the save folder in %~dp0
  echo Is it read-only, or inside Program Files? Move the game to C:\Games\ and retry.
  echo.
  pause
  exit /b 1
)

>  "save\config.ini" echo [Video]
>> "save\config.ini" echo GameWidth = 1920
>> "save\config.ini" echo GameHeight = 1080
>> "save\config.ini" echo WindowWidth = 1920
>> "save\config.ini" echo WindowHeight = 1080
>> "save\config.ini" echo KeepAspect = true
>> "save\config.ini" echo Fullscreen = false
>> "save\config.ini" echo RenderMode = OpenGL 3.3
>> "save\config.ini" echo.
>> "save\config.ini" echo [Config]
>> "save\config.ini" echo WindowTitle = Big Trouble in Little China: The Game
>> "save\config.ini" echo RenderMode = OpenGL 3.3
>> "save\config.ini" echo EnableModel = 1

echo.
echo Folder   : %~dp0
echo Engine   : %EXE%
echo Written  : save\config.ini
if exist "VERSION.txt" type "VERSION.txt"
findstr /i "RenderMode" "save\config.ini"
echo.
echo Starting the game - the window title should read
echo "Big Trouble in Little China: The Game".
echo.

"%EXE%"

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
