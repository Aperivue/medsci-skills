#!/usr/bin/env bash
# MedSci Skills — double-click updater for macOS. All logic lives in update.py, next to this file.
#
# An update that fails quietly is worse than no updater at all: the person stays on an old version
# and believes they are current. So the interpreter is verified BEFORE anything runs (a `python`
# that exists is not necessarily a Python 3, and a Python 3.8 dies mid-run instead of saying why).
set -u
cd "$(dirname "$0")"

echo "MedSci Skills Updater for macOS"
echo

MIN_MAJOR=3
MIN_MINOR=9

usable() {
  command -v "$1" >/dev/null 2>&1 || return 1
  "$1" -c "import sys; raise SystemExit(0 if sys.version_info >= ($MIN_MAJOR, $MIN_MINOR) else 1)" \
    >/dev/null 2>&1
}

PY=""
for candidate in python3 python; do
  if usable "$candidate"; then PY="$candidate"; break; fi
done

if [ -z "$PY" ]; then
  if command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1; then
    echo "The Python on this Mac is too old (MedSci Skills needs ${MIN_MAJOR}.${MIN_MINOR} or newer)."
  else
    echo "Python was not found on this Mac."
  fi
  echo
  echo "  1. Go to  https://www.python.org/downloads/"
  echo "  2. Install the latest Python for macOS."
  echo "  3. Double-click this updater again."
  echo
  echo "Your current installation has not been touched."
  echo
  read -r -p "Press Enter to close..."
  exit 1
fi

"$PY" update.py "$@"
rc=$?

if [ "$rc" -ne 0 ]; then
  echo
  echo "The update did not finish (error $rc). Your current installation is unchanged —"
  echo "the updater verifies a download before it replaces anything."
  echo
  echo "Tell us what the message above said and we will fix it:"
  echo "  https://github.com/Aperivue/medsci-skills/issues/new"
fi

echo
read -r -p "Press Enter to close..."
exit $rc
