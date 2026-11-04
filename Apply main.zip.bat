@echo off
rem ===========================================================================
rem  Apply main.zip - no internet needed
rem
rem  1. In your browser, download:
rem     https://codeload.github.com/jackrabbit72380/bigtroubleinlittlechinathegame/zip/refs/heads/main
rem  2. Save it in this folder (main.zip, or the long name it arrives with)
rem  3. Double-click this file
rem
rem  It unpacks that zip, copies data\ chars\ stages\ font\ external\ sound\ over
rem  this folder, leaves save\ and the engine alone, and starts the game.
rem  Nothing here touches the network, so nothing here can hang on a proxy.
rem ===========================================================================
setlocal
cd /d "%~dp0"

echo Apply main.zip v1
echo folder : %~dp0
echo.

set "EXE="
if exist "BigTroubleInLittleChinaTheGame.exe" set "EXE=BigTroubleInLittleChinaTheGame.exe"
if not defined EXE if exist "Ikemen_GO.exe" set "EXE=Ikemen_GO.exe"

set "ZIP="
if exist "%~dp0main.zip" set "ZIP=%~dp0main.zip"
if not defined ZIP if exist "%~dp0bigtroubleinlittlechinathegame-main.zip" set "ZIP=%~dp0bigtroubleinlittlechinathegame-main.zip"
if defined ZIP goto unzip
echo No main.zip in this folder.
echo.
echo Download it in your browser from:
echo   https://codeload.github.com/jackrabbit72380/bigtroubleinlittlechinathegame/zip/refs/heads/main
echo Save it here, then run this file again.
echo.
pause
exit /b 1

:unzip
echo Using: %ZIP%
set "TMP=%~dp0.update-cache"
if not exist "%TMP%" mkdir "%TMP%"
if exist "%TMP%\unpack" rd /s /q "%TMP%\unpack"
mkdir "%TMP%\unpack" 2>nul
where tar >nul 2>nul
if errorlevel 1 goto unzip_ps
echo Unpacking ...
tar -xf "%ZIP%" -C "%TMP%\unpack"
goto unpacked

:unzip_ps
echo Unpacking with PowerShell ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force -LiteralPath '%ZIP%' -DestinationPath '%TMP%\unpack'"

:unpacked
set "SRC="
for /d %%D in ("%TMP%\unpack\*") do set "SRC=%%~fD"
if not defined SRC goto badzip
echo Copying the game files over this folder ...
for %%F in (data chars stages font external sound) do (
  if exist "%SRC%\%%F" echo   %%F
  if exist "%SRC%\%%F" robocopy "%SRC%\%%F" "%~dp0%%F" /E /NFL /NDL /NJH /NJS /NP >nul
)
if not exist "%SRC%\config.ini" goto copied
copy /Y "%SRC%\config.ini" "%~dp0config.ini" >nul
if not exist "%~dp0save" mkdir "%~dp0save" 2>nul
if not exist "%~dp0save\config.ini" copy /Y "%SRC%\config.ini" "%~dp0save\config.ini" >nul

:copied
echo.
findstr /c:"bg1.spr = 20,0" "%~dp0data\fight.def" >nul 2>nul
if errorlevel 1 echo HUD   : OLD - the copy did not land
if not errorlevel 1 echo HUD   : dragon - back is health, belly is audacity
echo.
if not defined EXE goto noexe
echo Starting the game ...
"%EXE%" -config "save\config.ini"
echo.
echo The game has closed.
pause
exit /b 0

:noexe
echo No game exe found here, so the files were copied but the game was not started.
pause
exit /b 0

:badzip
echo.
echo Could not unpack that zip - it is probably an incomplete download.
echo Delete it, download it again, and run this file.
echo.
pause
exit /b 1
