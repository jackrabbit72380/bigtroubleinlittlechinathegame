@echo off
setlocal EnableExtensions
title Big Trouble in Little China - let Windows Defender leave the game alone
rem Windows Defender reports the Ikemen GO engine as Trojan:Win32/Tecabans.A!cl
rem every time it meets a freshly downloaded, unsigned copy of it. The engine's
rem own authors answered exactly this report as a false alarm (Ikemen GO issue
rem 2811, "IKEMEN nightly is trojan?"): the binary is unsigned and rebuilt for
rem every release, which is what Defender's cloud detector reacts to.
rem This adds this game folder and the online folder beside it to Defender's
rem exclusion list, so a good copy is not removed again. Run it once per PC.
cd /d "%~dp0"
set "GAME=%~dp0"
for %%I in ("%~dp0..\Big Trouble Online") do set "ONLINE=%%~fI"
set "PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"

echo.
echo   Game folder  : %GAME%
echo   Online folder: %ONLINE%
echo.
echo   Both go on Windows Defender's exclusion list. Nothing else changes:
echo   Defender keeps protecting the rest of the PC as before.
echo.

net session >nul 2>&1
if not errorlevel 1 goto apply
echo   Asking Windows for administrator rights ...
"%PS%" -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
if errorlevel 1 goto noadmin
exit /b 0

:noadmin
echo.
echo   Windows did not allow it. Right-click this file and choose
echo   "Run as administrator", then run it again.
echo.
pause
exit /b 1

:apply
"%PS%" -NoProfile -ExecutionPolicy Bypass -Command "$want=@('%GAME%','%ONLINE%'); foreach($i in $want){ try { Add-MpPreference -ExclusionPath $i -ErrorAction Stop } catch { } }; $have=@((Get-MpPreference).ExclusionPath); foreach($i in $want){ $n=$i.TrimEnd('\'); if(@($have | Where-Object { $_.TrimEnd('\') -ieq $n }).Count -gt 0){ 'excluded:     '+$i } else { 'NOT excluded: '+$i } }"
echo.
echo   If Defender already took the engine, put it back:
echo     Windows Security - Virus and threat protection - Protection history,
echo     the Trojan:Win32/Tecabans.A!cl entry - Actions - Restore.
echo   If it was deleted outright, run Update and Play.bat again after this:
echo   it fetches the engine once more, and this time it is left alone.
echo.
choice /c YN /n /m "Open Protection history now? [Y/N] "
if errorlevel 2 goto done
start "" "windowsdefender://threat" 2>nul
if errorlevel 1 echo   Could not open it; use the steps above by hand.
:done
echo.
echo   Done. Notes for both players are in ONLINE-SETUP.md and
echo   TEST-ONLINE-WITH-A-FRIEND.md.
echo.
pause
exit /b 0
