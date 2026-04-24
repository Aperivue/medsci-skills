#!/usr/bin/env bash
set -u

cd "$(dirname "$0")/.."

echo "MedSci Skills Installer for macOS"
echo

if command -v python3 >/dev/null 2>&1; then
  python3 installers/install.py --target all
elif command -v python >/dev/null 2>&1; then
  python installers/install.py --target all
else
  echo "Python was not found."
  echo "Install Python 3 from https://www.python.org/downloads/ and run this installer again."
fi

echo
read -r -p "Press Enter to close..."
