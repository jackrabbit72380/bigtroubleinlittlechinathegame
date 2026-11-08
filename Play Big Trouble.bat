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
rem into. Options > Video > Window sets the window and Options > Video > Resolution
rem sets the render, so a card that cannot fill a 4K window can still draw the game
rem at 1080p and let the picture stretch to the window's edges - that is the
rem quality dial. A size chosen in the game's own menu is kept and used on the
rem next launch.
rem
rem KeepAspect off fills the window whatever shape it is; on, a window that is not
rem 16:9 (a maximised one on a widescreen desktop, say) leaves black bars beside the
rem picture. It is forced off here rather than kept from the last launch, because
rem every build until now wrote true: a true on disk is that old forcing, not a
rem choice the player made. Options > Video > Keep Aspect Ratio turns the bars
rem back on for that session.
rem Window size when this folder has none saved yet: the largest of the 16:9
rem sizes in Options > Video > Resolution that fits the desktop - 1280x720,
rem 1920x1080, 2560x1440 (2K), 3840x2160 (4K) - so a small laptop gets a 720p
rem window it can show whole instead of a 1080p one running off the screen, and
rem a 4K desktop is not handed a quarter-size window. The render size then follows
rem the window, so each of those sizes is drawn at its own pixels.
set "GW="
set "GH="
set "WW="
set "WH="
set "FS=false"
if exist "%CFG%" (
  for /f "tokens=2 delims==" %%v in ('findstr /b /c:"WindowWidth" "%CFG%" 2^>nul') do set "WW=%%v"
  for /f "tokens=2 delims==" %%v in ('findstr /b /c:"WindowHeight" "%CFG%" 2^>nul') do set "WH=%%v"
  for /f "tokens=2 delims==" %%v in ('findstr /b /c:"Fullscreen" "%CFG%" 2^>nul') do set "FS=%%v"
)
rem "WindowWidth = 1920" leaves the value with its leading space on it.
set "WW=%WW: =%"
set "WH=%WH: =%"
set "FS=%FS: =%"
rem The window is settled first, because the render size is taken from it: a size
rem saved by Options > Video > Resolution, else the largest 16:9 size the screen
rem can show (see :screenfit at the end).
if "%WW%"=="" call :screenfit
if "%WW%"=="" set "WW=1920"
if "%WH%"=="" set "WH=1080"
rem Draw at the window's own pixels instead of 1920x1080 stretched over it, so a
rem 2K or 4K window is rendered at 2K or 4K and nothing is resampled twice. The
rem render is capped at 2160 lines: the art is painted at 1080p, and past 4K a
rem bigger render only costs frame time. Two arguments still override it:
rem
rem   "Play Big Trouble.bat" 2560 1440
rem A render the player picked in Options > Video > Resolution is kept, so a 4K
rem window can draw at 1080p; with none saved the window's own pixels are used.
rem It is never bigger than the window it is shown in, and never smaller than a
rem usable picture, so a stale size from an old install cannot shrink the game.
if defined GW set /a "GW=GW" 2>nul
if errorlevel 1 set "GW="
if defined GH set /a "GH=GH" 2>nul
if errorlevel 1 set "GH="
if not defined GW set "GW=%WW%"
if not defined GH set "GH=%WH%"
if %GW% GTR %WW% set "GW=%WW%"
if %GH% GTR %WH% set "GH=%WH%"
if %GW% LSS 640 set "GW=%WW%"
if %GH% LSS 480 set "GH=%WH%"
if %GW% GTR 3840 set "GW=3840"
if %GH% GTR 2160 set "GH=2160"
if not "%~1"=="" set "GW=%~1"
if not "%~2"=="" set "GH=%~2"
set "GW=%GW: =%"
set "GH=%GH: =%"
if "%FS%"=="" set "FS=false"

>  "%CFG%" echo [Video]
>> "%CFG%" echo GameWidth = %GW%
>> "%CFG%" echo GameHeight = %GH%
>> "%CFG%" echo WindowWidth = %WW%
>> "%CFG%" echo WindowHeight = %WH%
>> "%CFG%" echo KeepAspect = false
>> "%CFG%" echo Fullscreen = %FS%
>> "%CFG%" echo.
>> "%CFG%" echo [Config]
>> "%CFG%" echo WindowTitle = Big Trouble in Little China: The Game
>> "%CFG%" echo RenderMode = OpenGL 3.3

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

rem The engine leaves this file behind when a saved setting needs the program
rem started again. The runner below watches it: while it is there after the game
rem closes, the runner deletes it and starts the engine once more, so a change in
rem Options comes back by itself instead of sending the player back to the icon.
set "BTILC_FLAG=%CFG%"
set "BTILC_FLAG=%BTILC_FLAG:config.ini=restart.flag%"

rem What runs the game: a batch of its own, so the engine is not attached to this
rem window. The engine is a console program: run from here it takes this window for
rem its own log, and the window then has to stay open for as long as the game runs -
rem that is the black box that sat over the game. The helper is started hidden
rem (below), so the game gets a hidden console, nothing visible is left running,
rem and closing this window cannot end the game.
set "RUN=%TEMP%\btilc-play.bat"
>"%RUN%" echo @echo off
>>"%RUN%" echo cd /d "%~dp0."
>>"%RUN%" echo del "%BTILC_FLAG%" ^>nul 2^>^&1
>>"%RUN%" echo :btilc_again
>>"%RUN%" echo "%~dp0%EXE%" -config "%CFG%" ^>nul 2^>^&1
>>"%RUN%" echo if not exist "%BTILC_FLAG%" goto btilc_done
>>"%RUN%" echo del "%BTILC_FLAG%" ^>nul 2^>^&1
>>"%RUN%" echo goto btilc_again
>>"%RUN%" echo :btilc_done

rem WScript.Shell.Run with a window style of 0 starts that helper hidden and
rem returns at once, so this window can close while the game runs. The paths are
rem handed over in the environment, so no quoting of paths with spaces has to be
rem got right in the script itself.
set "BTILC_DIR=%~dp0."
set "BTILC_RUN=%RUN%"
set "RUNV=%TEMP%\btilc-play.vbs"
> "%RUNV%" echo Set sh = CreateObject("WScript.Shell")
>> "%RUNV%" echo Set env = sh.Environment("PROCESS")
>> "%RUNV%" echo q = Chr(34)
>> "%RUNV%" echo sh.CurrentDirectory = env("BTILC_DIR")
>> "%RUNV%" echo sh.Run "cmd /c " ^& q ^& env("BTILC_RUN") ^& q, 0, False
set "WSCRIPT=%SystemRoot%\System32\wscript.exe"
if exist "%WSCRIPT%" if exist "%RUNV%" (
  "%WSCRIPT%" //nologo "%RUNV%" >nul 2>&1
  if not errorlevel 1 exit /b 0
)

rem Two fallbacks, for a Windows where the script host is locked down. They run
rem the same helper, so a restart works there too.
set "RUNQ=%RUN:'=''%"
set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE="
if defined PSEXE "%PSEXE%" -NoProfile -Command "Start-Process -FilePath 'cmd.exe' -ArgumentList '/c',([char]34 + '%RUNQ%' + [char]34) -WindowStyle Hidden" >nul 2>&1
if not defined PSEXE start "" /min "%RUN%"
exit /b 0
exit /b 0

:screenfit
rem Ask Windows for the primary screen's size, then take the largest 16:9 window
rem from the resolution menu that fits inside it. The whole screen rather than the
rem space above the taskbar, so a 1080p desktop still gets a 1080p window: a
rem window that tall reaching under the taskbar is what every build before this
rem one did anyway, and a smaller screen no longer gets a window it cannot show.
set "SCRW="
set "SCRH="
set "PS1=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%PS1%" for /f "usebackq tokens=1,2" %%a in (`"%PS1%" -NoProfile -ExecutionPolicy Bypass -Command "Add-Type -AssemblyName System.Windows.Forms; $a=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds; $a.Width.ToString() + ' ' + $a.Height.ToString()" 2^>nul`) do (
  set "SCRW=%%a"
  set "SCRH=%%b"
)
rem Only a plain number is trusted. No PowerShell, a policy that blocks it or an
rem error message instead of a size leaves both at 0, and the 720p window below.
set /a "SCRW=SCRW" 2>nul
if errorlevel 1 set /a "SCRW=0"
set /a "SCRH=SCRH" 2>nul
if errorlevel 1 set /a "SCRH=0"
set "WW=1280"
set "WH=720"
if %SCRW% GEQ 1920 if %SCRH% GEQ 1080 (
  set "WW=1920"
  set "WH=1080"
)
if %SCRW% GEQ 2560 if %SCRH% GEQ 1440 (
  set "WW=2560"
  set "WH=1440"
)
if %SCRW% GEQ 3840 if %SCRH% GEQ 2160 (
  set "WW=3840"
  set "WH=2160"
)
exit /b 0
