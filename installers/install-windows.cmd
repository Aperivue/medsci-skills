@echo off
setlocal
cd /d "%~dp0\.."

echo MedSci Skills Installer for Windows
echo.

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 installers\install.py --target all
  goto done
)

where python >nul 2>nul
if %errorlevel%==0 (
  python installers\install.py --target all
  goto done
)

echo Python was not found.
echo Please install Python 3 from https://www.python.org/downloads/ and run this installer again.
echo.

:done
echo.
pause
