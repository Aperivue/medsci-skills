$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "MedSci Skills Installer for Windows"
Write-Host ""

if (Get-Command py -ErrorAction SilentlyContinue) {
    # --enable-update-notify also turns on the in-app "update available" reminder (disable later with --disable-update-notify).
    py -3 installers/install.py --target all --desktop-launcher --enable-update-notify
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python installers/install.py --target all --desktop-launcher --enable-update-notify
} else {
    Write-Host "Python was not found."
    Write-Host "Please install Python 3 from https://www.python.org/downloads/ and run this installer again."
}

Write-Host ""
Read-Host "Press Enter to close"
