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
  echo MedSci Skills is written in Python, so Python has to be installed first.
  echo It is free, official, and takes a couple of minutes.
  echo.

  rem winget ships with Windows 10 ^(1809+^) and Windows 11, so on most hospital machines Python can
  rem simply be installed for the user -- no admin rights, no download page, no PATH checkbox to
  rem miss. We ASK first: installing software on someone's computer without asking is not ours to do.
  where winget >nul 2>nul
  if !errorlevel!==0 (
    echo This installer can install Python for you now, from the official Python
    echo repository, into your own user account ^(no administrator password needed^).
    echo.
    set /p "DOIT=Install Python now? [Y/N] "
    if /i "!DOIT!"=="Y" (
      echo.
      echo Installing Python. This takes a couple of minutes...
      echo.
      winget install --exact --id Python.Python.3.13 --scope user ^
        --accept-source-agreements --accept-package-agreements
      echo.
      if !errorlevel!==0 (
        echo Python is installed.
        echo.
        echo Windows only notices a new program in NEW windows, so this one cannot use it yet:
        echo.
        echo    ^>^>  Close this window and double-click the installer again.  ^<^<
        echo.
        echo Nothing else has been changed on your computer.
        echo.
        pause
        exit /b 1
      )
      echo Python could not be installed automatically ^(error !errorlevel!^).
      echo Use the download page instead - it is opening now.
      echo.
    )
  )

  echo   1. Download the latest Python for Windows ^(the page opens by itself in a moment^)
  echo   2. Run the file you downloaded.
  echo      IMPORTANT: on the FIRST screen, tick the box "Add python.exe to PATH"
  echo      before pressing Install. It is easy to miss, and nothing works without it.
  echo   3. Double-click THIS installer again.
  echo.
  echo If a Microsoft Store page opened when you tried Python before, that page is a
  echo placeholder, not Python. Use python.org instead.
  echo.
  echo Nothing has been changed on your computer.
  echo.
  start "" "https://www.python.org/downloads/"
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
