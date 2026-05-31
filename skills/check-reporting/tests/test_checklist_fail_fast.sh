#!/usr/bin/env bash
# Regression tests for check-reporting check_checklist_exists.py (fail-fast guard).

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SCRIPT="$REPO_ROOT/skills/check-reporting/scripts/check_checklist_exists.py"

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

fail=0
ran=0

assert_exit() {
    local label="$1" expected="$2" actual="$3"
    ran=$((ran + 1))
    if [[ "$expected" == "$actual" ]]; then
        printf '  PASS  %-52s exit=%s\n' "$label" "$actual"
    else
        printf '  FAIL  %-52s expected=%s actual=%s\n' "$label" "$expected" "$actual"
        fail=$((fail + 1))
    fi
}

assert_contains() {
    local label="$1" needle="$2" haystack="$3"
    ran=$((ran + 1))
    if [[ "$haystack" == *"$needle"* ]]; then
        printf '  PASS  %-52s\n' "$label"
    else
        printf '  FAIL  %-52s (missing: %s)\n' "$label" "$needle"
        fail=$((fail + 1))
    fi
}

run() { python3 "$SCRIPT" "$@" >/dev/null 2>&1; echo $?; }

# 1. Vendored checklists that exist on disk -> exit 0.
assert_exit "STROBE present" 0 "$(run --guideline STROBE)"
assert_exit "STARD-AI alias present" 0 "$(run --guideline STARD-AI)"
assert_exit "TRIPOD+AI alias present" 0 "$(run --guideline 'TRIPOD+AI')"
assert_exit "AMSTAR 2 alias present" 0 "$(run --guideline 'AMSTAR 2')"
assert_exit "RoB 2 alias present" 0 "$(run --guideline 'RoB 2')"
assert_exit "QUADAS-C alias present" 0 "$(run --guideline QUADAS-C)"

# 2. Advertised-but-unvendored guidelines -> exit 1 (contract violation).
assert_exit "CONSORT 2010 missing" 1 "$(run --guideline 'CONSORT 2010')"
assert_exit "CARE missing" 1 "$(run --guideline CARE)"
assert_exit "SPIRIT missing" 1 "$(run --guideline SPIRIT)"
assert_exit "CLAIM 2024 missing" 1 "$(run --guideline 'CLAIM 2024')"

# 3. Unrecognised guideline -> exit 2.
assert_exit "unknown guideline" 2 "$(run --guideline NOT-A-REAL-GUIDELINE)"

# 4. Explicit opt-in downgrades missing/unknown to exit 0 but warns (never silent).
assert_exit "opt-in missing -> 0" 0 "$(run --guideline CARE --allow-from-memory)"
assert_exit "opt-in unknown -> 0" 0 "$(run --guideline NOPE --allow-from-memory)"
optin_out="$(python3 "$SCRIPT" --guideline CARE --allow-from-memory 2>&1)"
assert_contains "opt-in emits NON-AUTHORITATIVE warning" "NON-AUTHORITATIVE" "$optin_out"

# 5. Contract-test simulation (codex Improvement B "Prove" step).
sim_out="$(python3 "$SCRIPT" --simulate-missing-checklist 2>&1)"
assert_exit "simulate-missing-checklist" 1 "$(run --simulate-missing-checklist)"
assert_contains "simulate emits standard violation code" "MISSING_CHECKLIST_CONTRACT_VIOLATION" "$sim_out"

# 6. Violation message carries the standardized machine-greppable code.
viol_out="$(python3 "$SCRIPT" --guideline 'CONSORT 2010' 2>&1)"
assert_contains "missing emits standard violation code" "MISSING_CHECKLIST_CONTRACT_VIOLATION" "$viol_out"

printf '\n%d/%d checks passed\n' "$((ran - fail))" "$ran"
[[ "$fail" -eq 0 ]] || exit 1
