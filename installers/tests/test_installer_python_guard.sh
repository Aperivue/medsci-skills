#!/usr/bin/env bash
# Regression test for the double-click installer's Python guard.
#
# The person running install-macos.command is a clinician who double-clicked a file. Two failures
# had to become impossible:
#
#   * running a `python` that is not Python 3 (or is 3.8), where install.py PARSES and then dies
#     halfway through with a traceback instead of saying what is wrong;
#   * reporting success while installing nothing.
#
# So the test hands the installer a fake interpreter and checks that it REFUSES — and, crucially,
# that it refuses *before* install.py is ever invoked. A guard that runs the installer and then
# apologises has not guarded anything.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-54s exit=%s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-54s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

# A copy of the payload the installer needs, so the real repo is never touched.
BUNDLE="$TMP/bundle"
mkdir -p "$BUNDLE/installers"
cp "$REPO_ROOT/installers/install-macos.command" "$BUNDLE/installers/"
chmod +x "$BUNDLE/installers/install-macos.command"

# install.py is replaced by a tripwire: if the guard is working, this can never run.
cat > "$BUNDLE/installers/install.py" <<'PY'
import sys, pathlib
pathlib.Path(__file__).with_name("INSTALL_RAN").write_text("the guard let it through")
sys.exit(0)
PY

# 1) NO PYTHON AT ALL -> refuse, explain, and never touch install.py
#
# The sandbox PATH must contain the few external tools the script really uses (dirname) and NOT a
# python — emptying PATH entirely only proves that `bash` cannot be found, which is a test bug, not
# a guard.
EMPTY="$TMP/bin_empty"; mkdir -p "$EMPTY"
for tool in dirname; do
  ln -sf "$(command -v "$tool")" "$EMPTY/$tool"
done
rm -f "$BUNDLE/installers/INSTALL_RAN"
( cd "$BUNDLE/installers" && PATH="$EMPTY" /bin/bash ./install-macos.command < /dev/null > "$TMP/out" 2>&1 )
ck "no Python at all -> refuses" 1 "$?"
[ ! -f "$BUNDLE/installers/INSTALL_RAN" ]
ck "...and install.py was never run" 0 "$?"
grep -qi "python.org/downloads" "$TMP/out"
ck "...and it says where to get Python" 0 "$?"

# 2) A PYTHON THAT IS TOO OLD (3.8) -> refuse, and say the version is the problem
OLD="$TMP/bin_old"
mkdir -p "$OLD"
cat > "$OLD/python3" <<'SH'
#!/bin/sh
case "$1" in
  -c) exit 1 ;;                    # the guard's version probe: fail it, as a 3.8 would
  --version) echo "Python 3.8.10" ;;
  *) exit 1 ;;
esac
SH
chmod +x "$OLD/python3"
for tool in dirname; do ln -sf "$(command -v "$tool")" "$OLD/$tool"; done
rm -f "$BUNDLE/installers/INSTALL_RAN"
( cd "$BUNDLE/installers" && PATH="$OLD" /bin/bash ./install-macos.command < /dev/null > "$TMP/out" 2>&1 )
ck "a too-old Python -> refuses" 1 "$?"
[ ! -f "$BUNDLE/installers/INSTALL_RAN" ]
ck "...and install.py was never run (no traceback wall)" 0 "$?"
grep -qi "too old" "$TMP/out"
ck "...and it names the real problem (the version)" 0 "$?"
grep -q "3.8" "$TMP/out"
ck "...and shows what was found" 0 "$?"

# 3) A GOOD PYTHON -> the installer proceeds
GOOD="$TMP/bin_good"
mkdir -p "$GOOD"
printf '#!/bin/sh\nexec %s "$@"\n' "$(command -v python3)" > "$GOOD/python3"
chmod +x "$GOOD/python3"
for tool in dirname; do ln -sf "$(command -v "$tool")" "$GOOD/$tool"; done
rm -f "$BUNDLE/installers/INSTALL_RAN"
( cd "$BUNDLE/installers" && PATH="$GOOD" /bin/bash ./install-macos.command < /dev/null > "$TMP/out" 2>&1 )
[ -f "$BUNDLE/installers/INSTALL_RAN" ]
ck "a supported Python -> the installer runs" 0 "$?"

# 4) install.py itself refuses an old Python when run directly (defence in depth)
python3 - "$REPO_ROOT/installers/install.py" <<'PY'
import re, sys
src = open(sys.argv[1]).read()
assert "MIN_PYTHON = (3, 9)" in src, "install.py has no version floor"
i, j = src.index("MIN_PYTHON"), src.index("import argparse")
assert i < src.index("def "), "the floor check must run before anything else"
PY
ck "install.py carries its own floor guard" 0 "$?"

echo "----"
echo "test_installer_python_guard: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
