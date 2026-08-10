#!/usr/bin/env bash
# Challenge card for check_checklist_provenance.py
#
# Fixtures are built at runtime in a temp directory so this repository ships no
# deliberately-undeclared checklist of its own. Every case asserts the gate's
# EXIT CODE, not its chatter — a gate that prints a complaint and exits 0 is the
# failure this repository keeps re-learning.
#
# The negative controls are the two shapes that actually occurred:
#   * a file claiming "Verified" with nothing named as the object of the check
#   * a file that says nothing at all about verification
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATE="$HERE/../check_checklist_provenance.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0; fail=0
check() { # name expected_rc actual_rc
  if [ "$2" = "$3" ]; then printf '  PASS  %s (rc=%s)\n' "$1" "$3"; pass=$((pass+1))
  else printf '  FAIL  %s (expected rc=%s, got %s)\n' "$1" "$2" "$3"; fail=$((fail+1)); fi
}

run() { python3 "$GATE" --strict --dir "$1" >/dev/null 2>&1; echo $?; }

# ---------------------------------------------------------------- positive
mkdir -p "$TMP/good"
cat > "$TMP/good/GOOD.md" <<'EOF'
# Good Checklist
Version: GOOD 2020 — 3 items.
Source: Someone A, Someone B. A guideline. *Journal* 2020;1:1-2 (DOI 10.1000/example.1).
Licence: CC BY 4.0.
Verification: all 3 items compared against the official checklist table in the statement.
EOF
check "compliant file passes" 0 "$(run "$TMP/good")"

# ------------------------------------------------- negative control 1: bare claim
mkdir -p "$TMP/bare"
cat > "$TMP/bare/BARE.md" <<'EOF'
# Bare Claim Checklist
Version: BARE 2020.
Source: Someone A. A guideline. *Journal* 2020;1:1-2 (DOI 10.1000/example.2).
Licence: CC BY 4.0.
Verified 2026-06-30.
EOF
check "bare 'Verified' with no object FAILS" 1 "$(run "$TMP/bare")"

# ------------------------------------------- negative control 2: silent on verification
mkdir -p "$TMP/silent"
cat > "$TMP/silent/SILENT.md" <<'EOF'
# Silent Checklist
Version: SILENT 2020.
Source: Someone A. A guideline. *Journal* 2020;1:1-2 (DOI 10.1000/example.3).
Licence: CC BY 4.0.
EOF
check "silence about verification FAILS" 1 "$(run "$TMP/silent")"

# ------------------------------------------- negative control 3: no licence, no DOI
mkdir -p "$TMP/thin"
cat > "$TMP/thin/THIN.md" <<'EOF'
# Thin Checklist
Reference: Someone A. A guideline. Journal 2020.
Verification: compared against the published statement table.
EOF
check "missing version, DOI and licence FAILS" 1 "$(run "$TMP/thin")"

# ------------------------------------------------------ honest 'not verified' passes
mkdir -p "$TMP/honest"
cat > "$TMP/honest/HONEST.md" <<'EOF'
# Honest Checklist
Version: HONEST 2020.
Source: Someone A. A guideline. *Journal* 2020;1:1-2 (DOI 10.1000/example.4).
Licence: no open licence found.
This file has **not** been compared against the published statement.
EOF
check "explicit 'not compared' passes (honesty is the point)" 0 "$(run "$TMP/honest")"

# ----------------------------------------- notation the repo actually uses is accepted
mkdir -p "$TMP/notation"
cat > "$TMP/notation/NOTATION.md" <<'EOF'
# Notation Checklist

**Preferred Reporting Items**
- **Version:** NOTATION 2021
- **Citation:** Someone A. *Journal* 2021;2:3-4. doi:10.1000/example.5
- **Licence:** CC BY 4.0

> **Fidelity.** Every item was **compared** against the official **checklist** table.
EOF
check "bold/list label notation is accepted" 0 "$(run "$TMP/notation")"

# ------------------------------------------------ an empty set must not report success
mkdir -p "$TMP/empty"
check "empty directory refuses to pass" 2 "$(run "$TMP/empty")"

# ----------------------------------------------------------- backlog ratchet self-test
python3 "$GATE" --audit-backlog >/dev/null 2>&1
check "backlog ratchet: no entry has silently become compliant" 0 "$?"

printf '\nSummary: %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
