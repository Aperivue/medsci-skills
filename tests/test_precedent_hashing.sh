#!/usr/bin/env bash
# Regression tests for scripts/check_precedent.py (self-doxxing-safe precedent scan).
#
# Deliberately uses SYNTHETIC terms only (via PRECEDENT_HASH_FILE override). Real
# blocklisted identifiers are never embedded here — that would re-introduce the
# cleartext leak this mechanism exists to remove.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/check_precedent.py"
HASHES="$REPO_ROOT/scripts/precedent_hashes.txt"
AUTHOR_HASHES="$REPO_ROOT/scripts/precedent_author_hashes.txt"
TMP="$(mktemp -d -t precedent.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

fail=0
ran=0
check() {
    local label="$1" expected="$2" actual="$3"
    ran=$((ran + 1))
    if [[ "$expected" == "$actual" ]]; then
        printf '  PASS  %-52s exit=%s\n' "$label" "$actual"
    else
        printf '  FAIL  %-52s expected=%s actual=%s\n' "$label" "$expected" "$actual"
        fail=$((fail + 1))
    fi
}
ec() { python3 "$SCRIPT" "$@" >/dev/null 2>&1; echo $?; }      # exit code only
ec_in() { printf '%s' "$1" | python3 "$SCRIPT" - >/dev/null 2>&1; echo $?; }

# ---- 1. Structural patterns (generic shapes, real default hash file) ----
check "structural CK-<n>"            3 "$(ec_in 'see CK-12 for context')"
check "structural MA-<n>"            3 "$(ec_in 'pooled in MA-7')"
check "structural MA0<n>"            3 "$(ec_in 'cohort MA03')"
check "structural CAC><n>"           3 "$(ec_in 'the CAC>100 group')"
check "structural Consensus_Sheet"   3 "$(ec_in 'attached X12_Consensus_Sheet today')"
check "structural edit_plan.md"      3 "$(ec_in 'draft v3_edit_plan.md')"
check "structural Korean honorific"  3 "$(ec_in '김철수 교수님 reviewed it')"
check "structural VIF Diag"          3 "$(ec_in 'ran VIF  Diag')"

# ---- 2. Clean text must NOT trigger (false-positive guard) ----
check "clean prose"                  0 "$(ec_in 'STROBE checklist for observational studies')"
check "clean common surname alone"   0 "$(ec_in 'Kim and Lee analysed 12 sites')"
check "clean stats line"             0 "$(ec_in 'AUC 0.89 (95% CI 0.85-0.93)')"

# ---- 3. Hashed n-gram path via SYNTHETIC digest set ----
syn_term="acme widget corporation"
printf '%s\n' "$(printf '%s' "$syn_term" | shasum -a 256 | cut -d' ' -f1)" > "$TMP/syn_hashes.txt"
syn_run() { PRECEDENT_HASH_FILE="$TMP/syn_hashes.txt" PRECEDENT_AUTHOR_HASH_FILE="$TMP/none.txt" \
            python3 "$SCRIPT" - >/dev/null 2>&1; }
ran=$((ran + 1)); printf '%s' "context $syn_term here" | { syn_run; }; rc=$?
[[ "$rc" -eq 3 ]] && printf '  PASS  %-52s exit=3\n' "hashed synthetic 3-gram detected" \
                  || { printf '  FAIL  %-52s exit=%s\n' "hashed synthetic 3-gram detected" "$rc"; fail=$((fail+1)); }
ran=$((ran + 1)); printf '%s' "context unrelated text here" | { syn_run; }; rc=$?
[[ "$rc" -eq 0 ]] && printf '  PASS  %-52s exit=0\n' "hashed synthetic clean" \
                  || { printf '  FAIL  %-52s exit=%s\n' "hashed synthetic clean" "$rc"; fail=$((fail+1)); }

# ---- 4. --allow-author exemption via SYNTHETIC author digest ----
auth_term="jane q tester"
printf '%s\n' "$(printf '%s' "$auth_term" | shasum -a 256 | cut -d' ' -f1)" > "$TMP/auth_main.txt"
printf '%s\n' "$(printf '%s' "$auth_term" | shasum -a 256 | cut -d' ' -f1)" > "$TMP/auth_only.txt"
# main set also carries the synthetic org term, so "author at org" must still trip on the org.
printf '%s\n' "$(printf '%s' "$syn_term" | shasum -a 256 | cut -d' ' -f1)" >> "$TMP/auth_main.txt"
au() { PRECEDENT_HASH_FILE="$TMP/auth_main.txt" PRECEDENT_AUTHOR_HASH_FILE="$TMP/auth_only.txt" \
       python3 "$SCRIPT" "$@" - >/dev/null 2>&1; }
ran=$((ran + 1)); printf '%s' "by $auth_term" | au; rc=$?
[[ "$rc" -eq 3 ]] && printf '  PASS  %-52s exit=3\n' "author term caught without --allow-author" \
                  || { printf '  FAIL  %-52s exit=%s\n' "author no-flag" "$rc"; fail=$((fail+1)); }
ran=$((ran + 1)); printf '%s' "by $auth_term" | au --allow-author; rc=$?
[[ "$rc" -eq 0 ]] && printf '  PASS  %-52s exit=0\n' "author term exempted with --allow-author" \
                  || { printf '  FAIL  %-52s exit=%s\n' "author allow" "$rc"; fail=$((fail+1)); }
ran=$((ran + 1)); printf '%s' "by $auth_term at $syn_term" | au --allow-author; rc=$?
[[ "$rc" -eq 3 ]] && printf '  PASS  %-52s exit=3\n' "non-author term still caught with --allow-author" \
                  || { printf '  FAIL  %-52s exit=%s\n' "author allow + other" "$rc"; fail=$((fail+1)); }

# ---- 5. Digest files are cleartext-free (hash-only invariant) ----
hexcheck() {
    local f="$1" label="$2" bad
    ran=$((ran + 1))
    bad=$(grep -vE '^(#.*|[0-9a-f]{64})?$' "$f" || true)
    if [[ -z "$bad" ]]; then printf '  PASS  %-52s\n' "$label (hash-only, no cleartext)"
    else printf '  FAIL  %-52s offending: %s\n' "$label" "$(echo "$bad" | head -1)"; fail=$((fail+1)); fi
}
hexcheck "$HASHES" "precedent_hashes.txt"
hexcheck "$AUTHOR_HASHES" "precedent_author_hashes.txt"

printf '\n%d/%d checks passed\n' "$((ran - fail))" "$ran"
[[ "$fail" -eq 0 ]] || exit 1
