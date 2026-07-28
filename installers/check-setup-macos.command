#!/usr/bin/env bash
# MedSci Skills — "what else does this Mac need?", as a file you double-click.
#
# The same person who could not install from a terminal cannot run the setup check from one either.
# This is that check, and it will offer to install what is missing — asking before each one, and
# never installing anything large without being told to.
set -u

cd "$(dirname "$0")/.."

PY=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 &&
     "$candidate" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)" >/dev/null 2>&1; then
    PY="$candidate"
    break
  fi
done

if [ -z "$PY" ]; then
  echo "Python 3.9 or newer is not on this Mac, so MedSci Skills is not installed yet."
  echo "Run the installer first:  installers/install-macos.command"
  echo
  read -r -p "Press Enter to close..."
  exit 1
fi

"$PY" installers/doctor.py --fix
STATUS=$?

echo
read -r -p "Press Enter to close..."
exit "$STATUS"
