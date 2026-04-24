$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "MedSci Skills Installer for Windows"
Write-Host ""

if (Get-Command py -ErrorAction SilentlyContinue) {
    py -3 installers/install.py --target all
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python installers/install.py --target all
} else {
    Write-Host "Python was not found."
    Write-Host "Please install Python 3 from https://www.python.org/downloads/ and run this installer again."
}

Write-Host ""
Read-Host "Press Enter to close"
