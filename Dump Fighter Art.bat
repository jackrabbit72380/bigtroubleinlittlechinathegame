@echo off
rem Double-click this to unpack every fighter's sprites into PNG files.
rem They land in artifacts\fighter_art\<fighter>\ and Explorer opens when it is done.
setlocal
cd /d "%~dp0"

py -3 -c "import PIL" >nul 2>&1
if %errorlevel%==0 (set "PY=py -3" & goto run)

python -c "import PIL" >nul 2>&1
if %errorlevel%==0 (set "PY=python" & goto run)

echo.
echo Python 3 with Pillow was not found.
echo Install Python from https://www.python.org/downloads/ (tick "Add Python to PATH"),
echo then run this once in a command prompt:
echo.
echo     python -m pip install pillow
echo.
pause
exit /b 1

:run
%PY% "tools\dump_fighter_art.py" %*
if errorlevel 1 (
  echo.
  pause
  exit /b 1
)
start "" "artifacts\fighter_art"
