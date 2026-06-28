#!/usr/bin/env bash
set -u

cd "$(dirname "$0")/.."

echo "MedSci Skills Installer for macOS"
echo

PY=""
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
fi

if [ -n "$PY" ]; then
  "$PY" installers/install.py --target all --desktop-launcher
  # Turn on the in-app "update available" reminder for this turnkey install so you are told when a
  # new version is out (no terminal needed afterward). Best-effort; turn off later with
  # `install.py --disable-update-notify` or MEDSCI_NO_UPDATE_CHECK=1.
  "$PY" installers/install.py --enable-update-notify || true
else
  echo "Python was not found."
  echo "Install Python 3 from https://www.python.org/downloads/ and run this installer again."
fi

echo
read -r -p "Press Enter to close..."
