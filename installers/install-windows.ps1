$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "MedSci Skills Installer for Windows"
Write-Host ""

if (Get-Command py -ErrorAction SilentlyContinue) {
    py -3 installers/install.py --target all --desktop-launcher
    # Turn on the in-app "update available" reminder for this turnkey install (disable later with --disable-update-notify).
    try { py -3 installers/install.py --enable-update-notify } catch {}
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python installers/install.py --target all --desktop-launcher
    try { python installers/install.py --enable-update-notify } catch {}
} else {
    Write-Host "Python was not found."
    Write-Host "Please install Python 3 from https://www.python.org/downloads/ and run this installer again."
}

Write-Host ""
Read-Host "Press Enter to close"
