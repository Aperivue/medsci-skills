#!/usr/bin/env bash
# Regression test for the setup check (installers/doctor.py).
#
# The failure this guards against is subtle: a setup check that always says "everything is fine".
# It would pass every test that merely runs it, ship, and tell a clinician with no pandoc that they
# can render a manuscript. So the test does not ask whether the script runs — it TAKES A TOOL AWAY
# and demands that the report notices.
#
# It also pins the two promises the doctor makes:
#   * it never installs anything on its own (plain and --brief must not shell out to pip/brew);
#   * a missing OPTIONAL tool is not a failure (exit 0), or every Mac without R would be "broken".
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DOCTOR="$REPO_ROOT/installers/doctor.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-58s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-58s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

py() { python3 -B "$@"; }

# --- 1. It runs, and a missing optional tool is not an error -------------------------------------
py "$DOCTOR" > "$TMP/plain" 2>&1
ck "plain run succeeds" 0 "$?"
grep -q "MedSci Skills — setup check" "$TMP/plain"
ck "...and prints a report" 0 "$?"

# --- 2. THE ONE THAT MATTERS: hide pandoc, and the render capability must go missing -------------
#
# A PATH containing everything the doctor needs (python3) but NOT pandoc. If the probe is real, the
# "render" capability flips to not-ready and pandoc is named as the missing piece.
SANDBOX="$TMP/bin"; mkdir -p "$SANDBOX"
for tool in python3 uname sw_vers; do
  src="$(command -v "$tool" 2>/dev/null)" && ln -sf "$src" "$SANDBOX/$tool"
done

PATH="$SANDBOX" py "$DOCTOR" --json > "$TMP/nopandoc.json" 2>/dev/null
ck "runs with pandoc hidden" 0 "$?"

py - "$TMP/nopandoc.json" <<'PY'
import json, sys
caps = {c["key"]: c for c in json.load(open(sys.argv[1]))["capabilities"]}
render = caps["render"]
assert render["ready"] is False, "pandoc was hidden and the doctor still called rendering READY"
assert any("pandoc" in t for t in render["missing_tools"]), render
assert render["fix"], "it noticed pandoc was missing but offered no way to fix it"
# The stdlib-only core must NEVER be reported as broken: it needs nothing, so nothing can break it.
assert caps["core"]["ready"] is True, "the core capability claims to need something"
PY
ck "...pandoc gone => 'render to Word' reported MISSING, with a fix" 0 "$?"

# --- 3. A missing optional tool is not a failure; a missing essential one is (only with --strict) -
PATH="$SANDBOX" py "$DOCTOR" >/dev/null 2>&1
ck "missing tools alone do not fail the check" 0 "$?"

PATH="$SANDBOX" py "$DOCTOR" --strict >/dev/null 2>&1
ck "--strict fails when an essential tool is missing" 1 "$?"

# --- 4. It installs nothing by itself -------------------------------------------------------------
#
# pip / brew / winget are replaced by tripwires. Running the doctor (and the --brief summary the
# installer prints) must never touch them: a setup check that installs software the moment you look
# at it is not a check.
TRIP="$TMP/trip"; mkdir -p "$TRIP"
for tool in python3 uname sw_vers; do
  src="$(command -v "$tool" 2>/dev/null)" && ln -sf "$src" "$TRIP/$tool"
done
for tool in brew winget pip pip3 apt; do
  printf '#!/bin/sh\ntouch "%s/INSTALLED_SOMETHING"\n' "$TMP" > "$TRIP/$tool"
  chmod +x "$TRIP/$tool"
done
rm -f "$TMP/INSTALLED_SOMETHING"

PATH="$TRIP" py "$DOCTOR" >/dev/null 2>&1
PATH="$TRIP" py "$DOCTOR" --brief >/dev/null 2>&1
[ ! -f "$TMP/INSTALLED_SOMETHING" ]
ck "the check installs nothing on its own" 0 "$?"

# --- 5. --brief is the installer's tail: it must never raise -------------------------------------
py - "$REPO_ROOT" <<'PY'
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(sys.argv[1]) / "installers"))
import doctor
lines = []
doctor.brief_summary(lines.append)          # what install.py calls
assert isinstance(lines, list)
# Every capability must name at least one skill, or the report tells you something is missing
# without telling you what it was for.
for cap in doctor.CAPABILITIES:
    assert cap.skills, cap.key
    assert cap.title, cap.key
PY
ck "brief_summary() (the installer's tail) never raises" 0 "$?"

echo "----"
echo "test_doctor: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
