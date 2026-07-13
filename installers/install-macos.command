#!/usr/bin/env bash
# MedSci Skills — double-click installer for macOS.
#
# The person running this is a clinician who double-clicked a file. Every failure must end in a
# sentence they can act on — never a Python traceback, and never a silent "done" that installed
# nothing. Two things had to change for that to be true:
#
#   * `python` is not necessarily Python 3. Handing the installer to whatever `command -v python`
#     finds could hand it to a Python 2 that dies on the first f-string.
#   * Python 3.8 is worse than Python 2, not better: install.py *parses* there, so instead of a
#     clean "wrong version" it dies halfway through with a wall of traceback.
#
# So the interpreter is checked for a real version BEFORE anything runs.
set -u

cd "$(dirname "$0")/.."

echo "MedSci Skills Installer for macOS"
echo

MIN_MAJOR=3
MIN_MINOR=9

usable() {  # true only if $1 is really Python >= 3.9
  command -v "$1" >/dev/null 2>&1 || return 1
  "$1" -c "import sys; raise SystemExit(0 if sys.version_info >= ($MIN_MAJOR, $MIN_MINOR) else 1)" \
    >/dev/null 2>&1
}

PY=""
for candidate in python3 python; do
  if usable "$candidate"; then
    PY="$candidate"
    break
  fi
done

if [ -z "$PY" ]; then
  # "No Python" and "too old a Python" need different actions, and a clinician cannot be expected
  # to work out which one they have from a version string.
  if command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1; then
    # No pipe to `head` — an installer must not depend on tools that may not be on PATH in a
    # stripped-down environment. `python --version` prints one line anyway.
    FOUND="$( python3 --version 2>/dev/null || python --version 2>/dev/null )"
    echo "The Python on this Mac is too old for MedSci Skills."
    echo "  Found:  ${FOUND:-an older version}"
    echo "  Needed: Python ${MIN_MAJOR}.${MIN_MINOR} or newer"
  else
    echo "Python was not found on this Mac."
  fi
  echo
  echo "  1. Go to  https://www.python.org/downloads/"
  echo "  2. Download and install the latest Python for macOS."
  echo "  3. Double-click this installer again."
  echo
  echo "Nothing has been changed on your computer."
  echo
  read -r -p "Press Enter to close..."
  exit 1
fi

"$PY" installers/install.py --target all --desktop-launcher
STATUS=$?

if [ "$STATUS" -ne 0 ]; then
  echo
  echo "The installation did not finish (it stopped with error $STATUS)."
  echo "Nothing was left half-installed — the installer undoes its own work if it cannot complete."
  echo
  echo "If you tell us what the message above said, we can fix it:"
  echo "  https://github.com/Aperivue/medsci-skills/issues/new"
  echo
  read -r -p "Press Enter to close..."
  exit "$STATUS"
fi

# Turn on the in-app "update available" reminder for this turnkey install, so you are told when a
# new version ships instead of staying on this one forever. Best-effort: a failure here is not a
# failed install. Turn it off later with `install.py --disable-update-notify`.
"$PY" installers/install.py --enable-update-notify >/dev/null 2>&1 || true

echo
read -r -p "Press Enter to close..."
