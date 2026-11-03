@echo off
rem Double-click this to start the game on the renderer that boots.
rem
rem The engine reads save\config.ini and nothing else (src/main.go fixes that
rem path), so a config.ini sitting next to the exe is ignored unless the game is
rem launched with -config. This copies it into save\ first, then starts the game
rem from this folder, then shows the newest crash log if it did not come up.
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

if not exist "config.ini" (
  echo.
  echo config.ini is missing from this folder:
  echo   %~dp0
  echo.
  echo Save the config.ini text into this folder next to the exe, then run this again.
  echo.
  pause
  exit /b 1
)

if not exist "save" mkdir "save"
copy /y "config.ini" "save\config.ini" >nul
if errorlevel 1 (
  echo.
  echo Could not write save\config.ini. Is the folder read-only, or under Program Files?
  echo Move the game somewhere like C:\Games\ and try again.
  echo.
  pause
  exit /b 1
)

echo.
echo Folder : %~dp0
echo Engine : %EXE%
if exist "VERSION.txt" type "VERSION.txt"
echo Settings being used:
findstr /i /c:"RenderMode" /c:"WindowTitle" "save\config.ini"
echo.
echo Starting the game...
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
