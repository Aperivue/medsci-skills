#!/usr/bin/env bash
# Self-test for scripts/check_phase_budget.py.
#
# The point of this gate is that a SKILL.md is loaded IN FULL on every invocation, so an
# over-budget phase is a bill the user pays whether or not the run ever reaches it. The test
# therefore has to prove two things, and the second is the one that matters:
#
#   1. the gate is SILENT on the fixed tree (no false positives -> nobody switches it off), and
#   2. the gate FAILS on the real defect restored (a 200-line phase). A test that only proves
#      "passes on clean input" proves nothing: a gate that never fires passes that test too.
#
# It also pins the two properties that make the measurement honest:
#   - fence-awareness: a `## heading` inside a code fence is NOT a section boundary, so a long
#     phase cannot hide by embedding an output template that chops it in two;
#   - EXEMPT: a listed section is tolerated, so a long section is a decision on the record.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DET="$ROOT/scripts/check_phase_budget.py"

pass=0
fail() { echo "FAIL: $1" >&2; exit 1; }

# ---------------------------------------------------------------- 1. live repo is silent
python3 "$DET" --strict >/dev/null 2>&1 \
  || fail "the live repo must be within budget (run: python3 scripts/check_phase_budget.py)"
pass=$((pass + 1))

tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/skills/good" "$tmp/skills/bloated"

# ------------------------------------------- NEGATIVE FIXTURE: good work the gate must not flag
# A skill with a short phase and a proper trigger table. If the gate fires on this, it fires on
# correct work, gets switched off, and takes the honest gates with it.
{
  echo "# Good Skill"
  echo
  echo "## Phase 1: Init"
  echo
  echo "Ask for the manuscript and its type."
  echo
  echo "| File | Read it when | Cost if read blindly |"
  echo "|---|---|---|"
  echo "| \`references/detail.md\` | you know the paper type | ~2,000 tokens |"
} > "$tmp/skills/good/SKILL.md"

python3 "$DET" --skills-dir "$tmp/skills" --strict >/dev/null 2>&1 \
  || fail "NEGATIVE fixture: the gate fired on a compliant SKILL.md"
pass=$((pass + 1))

# ------------------------- REGRESSION 1: the REAL defect, frozen. The gate must FAIL on it.
# tests/fixtures/phase_budget/ holds self-review Phase 2 exactly as it shipped at a36c79e:
# a 209-line body loaded in full on every /self-review invocation. This is the bug the gate
# exists for, pinned so it stays regressed even after the live tree is fixed.
REAL="$ROOT/tests/fixtures/phase_budget/skills"
if python3 "$DET" --skills-dir "$REAL" --strict >/dev/null 2>&1; then
  fail "REGRESSION: the real 209-line self-review Phase 2 did NOT fail the gate"
fi
python3 "$DET" --skills-dir "$REAL" --json 2>/dev/null | grep -q '"body_lines": 209' \
  || fail "REGRESSION: the real defect was not measured at its true 209 lines"
pass=$((pass + 1))

# ---------------------------------------- REGRESSION 2: restore the defect shape, assert it FAILS
# A phase 200 lines long, loaded in full on every invocation before the agent knows whether it
# is relevant. A test that only proves "passes on clean input" would pass with the gate deleted.
{
  echo "# Bloated Skill"
  echo
  echo "## Phase 2: Systematic Check"
  echo
  for i in $(seq 1 200); do echo "- check item $i, which the agent may never need"; done
} > "$tmp/skills/bloated/SKILL.md"

if python3 "$DET" --skills-dir "$tmp/skills" --strict >/dev/null 2>&1; then
  fail "REGRESSION: a 200-line phase did NOT fail the gate — the gate is not watching anything"
fi
pass=$((pass + 1))

# the failure must NAME the offender and TEACH the fix, not just exit 1
out="$(python3 "$DET" --skills-dir "$tmp/skills" 2>&1 || true)"
grep -q "Phase 2: Systematic Check" <<<"$out" || fail "failure output does not name the over-budget section"
grep -q "BEFORE it knows what the user wants" <<<"$out" || fail "failure output does not print the deciding question"
grep -q "Read it when" <<<"$out" || fail "failure output does not print the trigger-table shape"
pass=$((pass + 1))

# ---------------------------------------------- FENCE-AWARENESS: the evasion the gate must resist
# A `## heading` inside a code fence is an output template, not a section boundary. A fence-blind
# parser would split this 200-line phase into two ~100-line halves and report BOTH as under a
# 120-line budget -- i.e. a long phase could hide behind an embedded template. Assert it does not.
mkdir -p "$tmp/fence/skills/sneaky"
{
  echo "# Sneaky Skill"
  echo
  echo "## Phase 9: Long"
  echo
  for i in $(seq 1 100); do echo "line $i"; done
  echo '```'
  echo "## Output Template (this is NOT a real heading)"
  echo '```'
  for i in $(seq 101 200); do echo "line $i"; done
} > "$tmp/fence/skills/sneaky/SKILL.md"

if python3 "$DET" --skills-dir "$tmp/fence/skills" --max-lines 120 --strict >/dev/null 2>&1; then
  fail "FENCE: a 200-line phase hid behind a '## ...' inside a code fence (fence-blind parsing)"
fi
python3 "$DET" --skills-dir "$tmp/fence/skills" --max-lines 120 --json 2>/dev/null \
  | grep -q '"section": "Phase 9: Long"' \
  || fail "FENCE: the section was not measured as one whole body"
pass=$((pass + 1))

# --------------------------------------------------------------------- JSON shape is machine-readable
python3 - "$DET" "$tmp/skills" <<'PY' || fail "--json did not emit a usable verdict"
import json, subprocess, sys
det, skills = sys.argv[1], sys.argv[2]
r = subprocess.run([sys.executable, det, "--skills-dir", skills, "--json"],
                   capture_output=True, text=True)
d = json.loads(r.stdout)
assert d["verdict"] == "PHASE_BUDGET_EXCEEDED", d["verdict"]
assert d["budget"] == 80
over = d["over_budget"]
assert len(over) == 1, over
assert over[0]["skill"] == "bloated", over[0]
assert over[0]["body_lines"] >= 200, over[0]
assert over[0]["over_by"] == over[0]["body_lines"] - 80, over[0]
PY
pass=$((pass + 1))

echo "PASS: phase-budget gate — $pass checks."
echo "  live repo silent - negative fixture silent - 200-line phase FAILS -"
echo "  message teaches the fix - fence-hidden phase still caught - JSON verdict usable."
