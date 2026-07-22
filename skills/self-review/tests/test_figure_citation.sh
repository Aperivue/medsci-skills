#!/usr/bin/env bash
# Regression test for the orphan figure/table gate (Phase 2.5d).
# (orphan) Figure 3 and Table 2 have captions but no in-text citation -> flagged;
# (clean) every captioned float is cited in the body -> no flag.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_figure_citation.py"
ORPHAN="$HERE/fixtures/figure_orphan.md"
CLEAN="$HERE/fixtures/figure_clean.md"
OUT="$(mktemp -t figcite_XXXX).json"
trap 'rm -f "$OUT"' EXIT
fail=0
check() { local label="$1"; shift
  if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
  else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi; }
has_verdict() { python3 -c "
import json
d=json.load(open('$OUT'))
assert any(c['verdict']=='$1' for c in d['claims']), '$1 not found'
"; }
[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

python3 "$SCRIPT" --manuscript "$ORPHAN" --out "$OUT" --quiet >/dev/null 2>&1
check "FIGURE_ORPHAN on uncited Figure 3" has_verdict FIGURE_ORPHAN
check "TABLE_ORPHAN on uncited Table 2"   has_verdict TABLE_ORPHAN
check "no orphan for cited Figure 1 / Table 1" python3 -c "
import json
d=json.load(open('$OUT'))
orphans={(c['verdict'], c['detail'].split(' has')[0]) for c in d['claims']}
assert ('FIGURE_ORPHAN','Figure 1') not in orphans and ('TABLE_ORPHAN','Table 1') not in orphans
"
python3 "$SCRIPT" --manuscript "$CLEAN" --out "$OUT" --quiet >/dev/null 2>&1
check "no orphans/embed flags when every float is cited AND embedded" python3 -c "
import json
d=json.load(open('$OUT'))
assert not d['claims'], d['claims']
"

# FIGURE_NOT_EMBEDDED: captions present, cited, but no image link anywhere.
NE="$HERE/fixtures/figcite_not_embedded.md"
python3 "$SCRIPT" --manuscript "$NE" --out "$OUT" --quiet >/dev/null 2>&1
check "FIGURE_NOT_EMBEDDED when no image is embedded" has_verdict FIGURE_NOT_EMBEDDED
# advisory (Minor) by default -> exit 0 even under --strict
python3 "$SCRIPT" --manuscript "$NE" --strict --quiet >/dev/null 2>&1
check "advisory Minor by default (exit 0 under --strict)" test "$?" -eq 0
# submission context: --require-embedded escalates to Major -> exit 1 under --strict
python3 "$SCRIPT" --manuscript "$NE" --require-embedded --strict --quiet >/dev/null 2>&1
check "Major under --require-embedded (exit 1 under --strict)" test "$?" -eq 1
# a manuscript that embeds its figures stays silent
EMB="$HERE/fixtures/figcite_embedded.md"
python3 "$SCRIPT" --manuscript "$EMB" --require-embedded --strict --quiet >/dev/null 2>&1
check "silent when figures are embedded (even --require-embedded)" test "$?" -eq 0

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
