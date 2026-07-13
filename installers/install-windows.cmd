@echo off
rem MedSci Skills - double-click installer for Windows.
rem
rem Windows is where most of these downloads go, and it has a trap the old script fell into.
rem
rem   THE MICROSOFT STORE STUB. On a Windows machine with no Python, `python` still EXISTS: it is an
rem   App Execution Alias that opens the Microsoft Store. So `where python` succeeds, errorlevel is
rem   0, the script cheerfully runs it -- and a Store page opens, nothing is installed, and the
rem   installer reports it is done. The clinician is told everything worked and has nothing.
rem
rem   A TOO-OLD PYTHON. install.py PARSES on 3.8, so it does not fail cleanly: it dies partway
rem   through with a traceback instead of saying "wrong version".
rem
rem So an interpreter is only accepted after it proves, BY RUNNING, that it is Python 3.9 or newer.
rem Asking `where` only proves a name exists.
setlocal EnableDelayedExpansion
cd /d "%~dp0\.."

echo MedSci Skills Installer for Windows
echo.

set "PY="

rem The py launcher is the reliable path when it exists.
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
if !errorlevel!==0 set "PY=py -3"

rem Fall back to `python` -- but only if it actually runs. The Store stub fails this test, which is
rem the entire reason for testing instead of asking `where`.
if not defined PY (
  python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
  if !errorlevel!==0 set "PY=python"
)

if not defined PY (
  echo Python 3.9 or newer was not found on this computer.
  echo.
  echo   1. Go to  https://www.python.org/downloads/
  echo   2. Download and install the latest Python for Windows.
  echo      IMPORTANT: on the first screen, tick "Add python.exe to PATH".
  echo   3. Double-click this installer again.
  echo.
  echo If a Microsoft Store page opened when you tried Python before, that page is a
  echo placeholder, not Python. Install it from python.org instead.
  echo.
  echo Nothing has been changed on your computer.
  echo.
  pause
  exit /b 1
)

%PY% installers\install.py --target all --desktop-launcher
if not !errorlevel!==0 (
  set "RC=!errorlevel!"
  echo.
  echo The installation did not finish ^(it stopped with error !RC!^).
  echo Nothing was left half-installed - the installer undoes its own work if it cannot complete.
  echo.
  echo If you tell us what the message above said, we can fix it:
  echo   https://github.com/Aperivue/medsci-skills/issues/new
  echo.
  pause
  exit /b !RC!
)

rem Turn on the in-app "update available" reminder for this turnkey install, so you are told when a
rem new version ships instead of staying on this one forever. Best-effort: a failure here is not a
rem failed install.
%PY% installers\install.py --enable-update-notify >nul 2>nul

echo.
pause
