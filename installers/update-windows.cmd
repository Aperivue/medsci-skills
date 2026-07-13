@echo off
rem MedSci Skills - double-click updater for Windows. All logic lives in update.py, next to this file.
rem
rem The old version of this file ran `python` directly. On a Windows machine without Python that is
rem not an error: it is the Microsoft Store App Execution Alias, which opens a Store page and exits.
rem The user saw a Store window, no update, and no explanation. So an interpreter is only accepted
rem after it proves BY RUNNING that it is Python 3.9 or newer.
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo MedSci Skills Updater for Windows
echo.

set "PY="
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
if !errorlevel!==0 set "PY=py -3"

if not defined PY (
  python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
  if !errorlevel!==0 set "PY=python"
)

if not defined PY (
  echo Python 3.9 or newer was not found on this computer.
  echo.
  echo   1. Go to  https://www.python.org/downloads/
  echo   2. Install the latest Python for Windows ^(tick "Add python.exe to PATH"^).
  echo   3. Double-click this updater again.
  echo.
  echo If a Microsoft Store page opened when you tried Python before, that page is a
  echo placeholder, not Python. Install it from python.org instead.
  echo.
  echo Your current installation has not been touched.
  echo.
  pause
  exit /b 1
)

%PY% "%~dp0update.py" %*
set "rc=!errorlevel!"

if not !rc!==0 (
  echo.
  echo The update did not finish ^(error !rc!^). Your current installation is unchanged -
  echo the updater verifies a download before it replaces anything.
  echo.
  echo Tell us what the message above said and we will fix it:
  echo   https://github.com/Aperivue/medsci-skills/issues/new
)

echo.
pause
exit /b !rc!
