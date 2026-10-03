#!/usr/bin/env bash
# Regression test: an SSOT-native project must have a sanctioned path to qc/migration_complete.
#
# Phase 1C auto-enforce needs SSOT.yaml AND qc/migration_complete. `init_project.py --ssot`
# writes SSOT.yaml but not the marker, and the only writer of the marker,
# `migrate_project_to_ssot.py --mark-complete`, used to exit 2 ("project.yaml not found") before
# validating anything. A manual `touch` is forbidden by SKILL.md, so an `--ssot` project stayed
# warn-only forever while SKILL.md said `--ssot` made the hook block.
#
# Now `--mark-complete` on a project with SSOT.yaml and no project.yaml validates the existing
# SSOT.yaml and writes the marker only on PASS. The controls pin that nothing else moved:
# an invalid SSOT.yaml is not marked, an empty directory still exits 2, SSOT-only without
# --mark-complete still exits 2, SSOT.yaml is never rewritten, and the legacy migrate path is
# unchanged.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SCRIPTS="${MP_SCRIPTS_DIR:-$REPO_ROOT/skills/manage-project/scripts}"
INIT="$SCRIPTS/init_project.py"
MIGRATE="$SCRIPTS/migrate_project_to_ssot.py"
FIX="$REPO_ROOT/tests/fixtures"
WORK="$(mktemp -d -t mp_mark.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-60s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-60s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}
marker() { if [ -f "$1/qc/migration_complete" ]; then echo present; else echo absent; fi; }
exists() { if [ -e "$1" ]; then echo present; else echo absent; fi; }

echo "manage-project SSOT-native mark-complete regression"

# --- POSITIVE: init --ssot -> migrate --mark-complete -> marker (main: rc=2, no marker) ---
P="$WORK/native"
python3 "$INIT" --name native-proj --type original --journal RYAI --ssot --project-root "$P" >/dev/null 2>&1
ck "init --ssot rc" 0 "$?"
ck "init --ssot: marker not written by init" absent "$(marker "$P")"
before="$(cksum < "$P/SSOT.yaml")"
python3 "$MIGRATE" --project-root "$P" --mark-complete >/dev/null 2>&1
ck "ssot-native --mark-complete rc" 0 "$?"
ck "ssot-native --mark-complete: marker" present "$(marker "$P")"
ck "ssot-native: SSOT.yaml not rewritten" "$before" "$(cksum < "$P/SSOT.yaml")"
ck "ssot-native: no project.yaml created" absent "$(exists "$P/project.yaml")"

# The command SKILL.md documents (--write --mark-complete) also works on an SSOT-native project.
P2="$WORK/native_write"
python3 "$INIT" --name native-two --type meta --journal AJR --ssot --project-root "$P2" >/dev/null 2>&1
python3 "$MIGRATE" --project-root "$P2" --write --mark-complete >/dev/null 2>&1
ck "ssot-native --write --mark-complete rc" 0 "$?"
ck "ssot-native --write --mark-complete: marker" present "$(marker "$P2")"

# --- NEGATIVE: invalid SSOT.yaml (canonical manuscript missing) is NOT marked ---
P3="$WORK/native_bad"
python3 "$INIT" --name native-bad --type original --journal RYAI --ssot --project-root "$P3" >/dev/null 2>&1
rm -f "$P3/manuscript/index.qmd"
python3 "$MIGRATE" --project-root "$P3" --mark-complete >/dev/null 2>&1
rc=$?
if [ "$rc" -ne 0 ]; then rcv=nonzero; else rcv=zero; fi
ck "invalid ssot-native: rc non-zero" nonzero "$rcv"
ck "invalid ssot-native: marker" absent "$(marker "$P3")"

# --- NEGATIVE: SSOT-only without --mark-complete still exits 2, writes nothing ---
P4="$WORK/native_nomark"
python3 "$INIT" --name native-nomark --type original --journal RYAI --ssot --project-root "$P4" >/dev/null 2>&1
before="$(cksum < "$P4/SSOT.yaml")"
python3 "$MIGRATE" --project-root "$P4" --write >/dev/null 2>&1
ck "ssot-only --write (no --mark-complete) rc" 2 "$?"
ck "ssot-only --write: marker" absent "$(marker "$P4")"
ck "ssot-only --write: SSOT.yaml unchanged" "$before" "$(cksum < "$P4/SSOT.yaml")"

# --- NEGATIVE: neither contract file -> exit 2, no marker ---
P5="$WORK/empty"
mkdir -p "$P5"
python3 "$MIGRATE" --project-root "$P5" --write --mark-complete >/dev/null 2>&1
ck "empty dir --write --mark-complete rc" 2 "$?"
ck "empty dir: marker" absent "$(marker "$P5")"
ck "empty dir: no SSOT.yaml" absent "$(exists "$P5/SSOT.yaml")"

# --- CONTROL: legacy migrate path unchanged (fixture -> SSOT.yaml + marker) ---
P6="$WORK/legacy"
cp -R "$FIX/legacy_project" "$P6"
python3 "$MIGRATE" --project-root "$P6" --write --mark-complete >/dev/null 2>&1
ck "legacy --write --mark-complete rc" 0 "$?"
ck "legacy: SSOT.yaml written" present "$(exists "$P6/SSOT.yaml")"
ck "legacy: marker" present "$(marker "$P6")"

# --- CONTROL: both files present + --write still refuses to overwrite (rc 3) ---
python3 "$MIGRATE" --project-root "$P6" --write --mark-complete >/dev/null 2>&1
ck "legacy re-run --write (SSOT.yaml exists) rc" 3 "$?"

echo "  $pass passed, $fail failed"
[ "$fail" -eq 0 ]
