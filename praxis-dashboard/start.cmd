@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-live-dashboard.ps1" %*
if errorlevel 1 (
  echo Could not start the connected Praxis dashboard. Check the error above.
  pause
  exit /b 1
)
exit /b 0
