@echo off
rem MedSci Skills - "what else does this PC need?", as a file you double-click.
rem
rem Same rule as the installer: an interpreter is only accepted after it proves, BY RUNNING, that
rem it is Python 3.9 or newer. On a PC with no Python, `python` still exists as a Microsoft Store
rem stub that opens a shop page -- asking `where` would be fooled by it.
setlocal EnableDelayedExpansion
cd /d "%~dp0\.."

set "PY="
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
if !errorlevel!==0 set "PY=py -3"

if not defined PY (
  python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
  if !errorlevel!==0 set "PY=python"
)

if not defined PY (
  echo Python 3.9 or newer is not on this PC, so MedSci Skills is not installed yet.
  echo Run the installer first:  installers\install-windows.cmd
  echo.
  pause
  exit /b 1
)

%PY% installers\doctor.py --fix

echo.
pause
