#!/usr/bin/env bash
# Regression test for the supplement assembler / structural validator (G42).
# Synthetic, PII-free fixtures: a clean supplement (index↔file 1:1, contiguous
# sub-sections) and a broken one (index declares S3 with no file, S2 duplicated,
# S1.2 sub-section gap, S6 orphan not in index). Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/assemble_supplement.py"
CLEAN="$HERE/fixtures/suppl_clean"
BAD="$HERE/fixtures/suppl_bad"
MS="$HERE/fixtures/suppl_manuscript.md"
OUT="$(mktemp -t supp_XXXX).json"
COMB="$(mktemp -t comb_XXXX).md"
trap 'rm -f "$OUT" "$COMB"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
has_kind() { python3 -c "
import json,sys
d=json.load(open('$OUT'))
assert any(p['kind']=='$1' for p in d['problems']), '$1 not found'
"; }

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# (1) clean supplement -> exit 0, rebuilds _combined in index order
python3 "$SCRIPT" --dir "$CLEAN" --out "$COMB" --strict --quiet >/dev/null 2>&1
check "exit 0 on clean supplement" test "$?" -eq 0
check "_combined rebuilt + non-empty" test -s "$COMB"
check "rebuild is in index order (S1 before S3)" python3 -c "
t=open('$COMB').read(); assert t.index('S1.')<t.index('S3.'), 'order wrong'"

# (2) broken supplement -> exit 1 with all four structural problem kinds
python3 "$SCRIPT" --dir "$BAD" --json "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 on broken supplement" test "$?" -eq 1
check "INDEX_WITHOUT_FILE (S3 declared, no file)" has_kind INDEX_WITHOUT_FILE
check "FILE_WITHOUT_INDEX (S6 orphan)"            has_kind FILE_WITHOUT_INDEX
check "DUPLICATE_SECTION (S2 a+b)"                has_kind DUPLICATE_SECTION
check "SUBSECTION_GAP (S1.2 missing)"             has_kind SUBSECTION_GAP

# (3) coverage: clean sections cited only S1/S2 -> S3 SECTION_UNCITED (advisory, no --strict fail)
python3 "$SCRIPT" --dir "$CLEAN" --manuscript "$MS" --json "$OUT" --quiet >/dev/null 2>&1
check "SECTION_UNCITED flagged for S3" has_kind SECTION_UNCITED
check "coverage is advisory (exit 0 without structural problem)" bash -c "
  python3 '$SCRIPT' --dir '$CLEAN' --manuscript '$MS' --strict --quiet >/dev/null 2>&1; test \$? -eq 0"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
