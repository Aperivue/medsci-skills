#!/usr/bin/env bash
# Regression test for verify-refs corporate/collective-author handling (B1).
# Offline (no network): a guideline body double-braced in BibTeX
# (`author = {{EASL} and {EASD}}`, `{{KDIGO CKD Work Group}}`) must be detected as
# a corporate author and EXEMPTED from the personal-name family cross-check — it
# must never be a MISMATCH (which would abort render_pandoc.sh on every
# guideline-citing cohort manuscript). A normal personal-author entry is not
# corporate. Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/verify_refs.py"
BIB="$HERE/fixtures/corporate_author.bib"
ROOT="$(mktemp -d -t vrc_XXXX)"
trap 'rm -rf "$ROOT"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }
[[ -f "$BIB" ]]    || { echo "ENV-ERR: fixture missing" >&2; exit 2; }

python3 "$SCRIPT" "$BIB" --project-root "$ROOT" --offline >/dev/null 2>&1
AUDIT="$ROOT/qc/reference_audit.json"
check "audit JSON written" test -s "$AUDIT"

assert_py() { python3 -c "
import json
d = json.load(open('$AUDIT'))
recs = {r['ref_id']: r for r in d['records']}
$1
"; }

# Double-braced guideline bodies detected as corporate, annotated, never MISMATCH.
for ref in easl2024masld kdigo2024ckd; do
    check "$ref corporate_author True" \
        assert_py "assert recs['$ref']['corporate_author'] is True, recs['$ref']"
    check "$ref annotated corporate (note)" \
        assert_py "assert 'corporate' in recs['$ref'].get('note','').lower(), recs['$ref']"
    check "$ref NOT a MISMATCH / no author-mismatch" \
        assert_py "assert recs['$ref']['status'] != 'MISMATCH' and 'AUTHOR MISMATCH' not in recs['$ref'].get('evidence',''), recs['$ref']"
done

# A normal personal-author entry must NOT be flagged corporate.
check "personal-author entry corporate_author False" \
    assert_py "assert recs['smith2024cohort']['corporate_author'] is False, recs['smith2024cohort']"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
