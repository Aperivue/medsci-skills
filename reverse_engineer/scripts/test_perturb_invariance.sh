#!/usr/bin/env bash
# Self-test for the Q7 severity probe: the perturbation generator and the invariance report.
#
# The real corpus is gitignored published papers, so CI can never run the real measurement. What CI
# CAN prove is that the probe is honest about what it did: that a perturbation which would change
# the paper's meaning is REFUSED rather than measured, that the exemption list is applied and not
# quietly ignored, and — the one that matters — that a moved verdict is actually detected and
# named. A probe that reports 1.000 because it cannot see movement is worse than no probe.
#
# Network-free. Builds its own synthetic corpus and its own synthetic run artifacts.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERTURB="$HERE/perturb_corpus.py"
REPORT="$HERE/invariance_report.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }

mkdir -p "$TMP/corpus"
cat > "$TMP/corpus/alpha_2024.md" <<'EOF'
# A Study of Something

## Abstract
We enrolled 405 patients with non-small cell lung cancer (NSCLC) and measured 12 outcomes [1].

## Methods
NSCLC staging followed standard criteria. Computed tomography (CT) was performed in 405 cases.
CT findings were reviewed by two readers [2].

## Results
Sensitivity was 0.88 (95% CI 0.83-0.92) across 405 NSCLC cases.

## Discussion
The CT protocol is described elsewhere [3].

## Data Availability
All data are available on request.

## Conflict of Interest
The authors declare none.
EOF

echo "== 1. each perturbation applies, and proves it preserved the paper =="
for K in house-vocab rename-abbrev reorder-sections; do
  python3 "$PERTURB" --corpus "$TMP/corpus" --out "$TMP/$K" --perturbation "$K" \
      --report "$TMP/rep_$K.json" >"$TMP/out_$K.txt" 2>&1 \
    || fail "$K: validity guard excluded the fixture — the perturbation damaged the paper"
  [ -s "$TMP/$K/alpha_2024.md" ] || fail "$K: wrote no paper"
  python3 - "$TMP/rep_$K.json" "$K" <<'PY' || exit 1
import json, sys
rep = json.load(open(sys.argv[1]))
assert rep["n_excluded"] == 0, rep["excluded"]
assert rep["total_edits"] > 0, "%s was a no-op: a perturbation that changes nothing measures nothing" % sys.argv[2]
PY
done

# The numbers and citations are the paper's content; a perturbation that moves them is not
# semantics-preserving, and every downstream claim would be about our corruption.
for K in house-vocab rename-abbrev reorder-sections; do
  for pat in '405' '0.88' '\[1\]' '\[3\]'; do
    grep -qE "$pat" "$TMP/$K/alpha_2024.md" || fail "$K: lost $pat from the paper"
  done
done

echo "== 2. house-vocab really rewrites the house, and rename-abbrev really renames =="
# The swap must land on a GENUINELY different wording. Rotating to the ring neighbour once produced
# "Data Availability" -> "Data Availability Statement", which differs by one appended token and
# which any substring-keyed detector sails straight through: a probe that measures nothing while
# reporting perfect invariance. The target is now the most distant member of the ring.
grep -qE "^## (Data Sharing Statement|Availability of data and materials)$" \
     "$TMP/house-vocab/alpha_2024.md" \
  || fail "house-vocab did not rewrite the heading into a distant publisher's wording"
grep -qE "^## Data Availability" "$TMP/house-vocab/alpha_2024.md" \
  && fail "house-vocab left the original heading in place — the probe would measure nothing"
grep -qE "^## (Competing interests|Declaration of competing interest)$" \
     "$TMP/house-vocab/alpha_2024.md" \
  || fail "house-vocab did not rewrite the COI heading"
grep -q "NSCLC" "$TMP/rename-abbrev/alpha_2024.md" \
  && fail "rename-abbrev left the original abbreviation in place"
grep -q "non-small cell lung cancer" "$TMP/rename-abbrev/alpha_2024.md" \
  || fail "rename-abbrev dropped the DEFINITION — the rename is only meaning-preserving with it"

echo "== 3. the validity guard REFUSES a perturbation that changes the paper =="
# Not a hypothetical: the first rename-abbrev numbered its replacements ZQX00, ZQX01, which put
# digits into the document's number multiset, and matched single capitals so it renamed every
# standalone "A" and "P". The guard caught both. This asserts it still would.
python3 - "$PERTURB" <<'PY' || exit 1
import importlib.util, sys
spec = importlib.util.spec_from_file_location("perturb", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

before = "We enrolled 405 patients and found 12 events [1]."
assert "numbers changed" in m.validity(before, "We enrolled 406 patients and found 12 events [1].",
                                       "house-vocab", 1)
assert "citation markers changed" in m.validity(before, "We enrolled 405 patients and found 12 events [9].",
                                                "house-vocab", 1)
assert any("no-op" in p for p in m.validity(before, before, "house-vocab", 0))
# A pure reordering may not gain or lose a single word.
assert any("word multiset" in p for p in
           m.validity("## A\nx\n## B\ny\n", "## B\ny\n## A\nz\n", "reorder-sections", 1))
# A rename must move exactly two words per rename; anything else touched something it did not name.
assert any("did not name" in p for p in
           m.validity("AA bb cc", "ZZ dd ee", "rename-abbrev", 1))
assert not m.validity("AA bb AA", "ZZ bb ZZ", "rename-abbrev", 2), \
    "a correct 2-instance rename was rejected"
PY

echo "== 4. the invariance report detects a moved verdict and NAMES it =="
# The test that matters. A probe reporting 1.000 because it cannot see movement is worse than none.
mk_run() {  # $1 out  $2... "detector:paper:code" triples
  python3 - "$@" <<'PY'
import json, sys
out, triples = sys.argv[1], sys.argv[2:]
fires, findings = [], []
for t in triples:
    det, paper, code = t.split(":")
    fires.append({"detector": det, "paper": paper, "verdict": code, "bar": "strict"})
    findings.append({"detector": det, "paper": paper, "code": code, "severity": "major",
                     "tier": "blocking", "message": code, "parsed": True})
json.dump({"fires": fires, "findings": findings}, open(out, "w"))
PY
}
mk_run "$TMP/base.json"  d1:p1:CODE_A d1:p2:CODE_A d2:p1:CODE_B
mk_run "$TMP/same.json"  d1:p1:CODE_A d1:p2:CODE_A d2:p1:CODE_B
mk_run "$TMP/moved.json" d1:p1:CODE_A               d2:p1:CODE_B   # d1 went silent on p2
mk_run "$TMP/claim.json" d1:p1:CODE_A d1:p2:CODE_A d2:p1:CODE_Z    # d2 fires for a new reason

OUT="$(python3 "$REPORT" --baseline "$TMP/base.json" --perturbed x="$TMP/same.json" 2>&1)"
grep -q "OUTCOME INVARIANCE: 1.000" <<<"$OUT" || fail "identical runs did not report full invariance"

OUT="$(python3 "$REPORT" --baseline "$TMP/base.json" --perturbed x="$TMP/moved.json" 2>&1)"
grep -q "OUTCOME INVARIANCE: 0.667" <<<"$OUT" \
  || fail "a verdict that moved on 1 of 3 pairs was not reported as 0.667: $OUT"
grep -q "MOVED d1 on 1 paper" <<<"$OUT" || fail "the moved detector was not named"

OUT="$(python3 "$REPORT" --baseline "$TMP/base.json" --perturbed x="$TMP/claim.json" 2>&1)"
grep -q "OUTCOME INVARIANCE: 1.000" <<<"$OUT" \
  || fail "a same-outcome run should keep outcome invariance at 1.000"
grep -q "CLAIM INVARIANCE  : 0.667" <<<"$OUT" \
  || fail "a fire that changed WHICH claim it made was not caught by claim invariance: $OUT"

echo "== 5. an exempt detector's movement is expected, and its STILLNESS is a finding =="
cat > "$TMP/rep_exempt.json" <<'EOF'
{"exempt_detectors": ["d1"], "excluded": []}
EOF
OUT="$(python3 "$REPORT" --baseline "$TMP/base.json" --perturbed x="$TMP/moved.json" \
        --perturb-report x="$TMP/rep_exempt.json" 2>&1)"
grep -q "OUTCOME INVARIANCE: 1.000" <<<"$OUT" \
  || fail "an exempt detector's movement was counted against invariance: $OUT"
grep -q "of these, 1 moved as expected" <<<"$OUT" || fail "expected movement was not reported"
grep -q "DID NOT MOVE d1 x p1" <<<"$OUT" \
  || fail "an order-policing detector that ignored a reordering was not flagged"

echo "== 6. a paper the guard excluded is excluded from the RATE, not silently measured =="
cat > "$TMP/rep_excl.json" <<'EOF'
{"exempt_detectors": [], "excluded": [{"paper": "p2", "problems": ["numbers changed"]}]}
EOF
OUT="$(python3 "$REPORT" --baseline "$TMP/base.json" --perturbed x="$TMP/moved.json" \
        --perturb-report x="$TMP/rep_excl.json" 2>&1)"
grep -q "OUTCOME INVARIANCE: 1.000" <<<"$OUT" \
  || fail "a paper excluded by the validity guard still entered the invariance rate: $OUT"
grep -q "excluded by the validity guard: p2" <<<"$OUT" || fail "the excluded paper was not named"

echo "PASS: perturbations preserve numbers/citations/definitions, the guard refuses corruption,"
echo "      and a moved verdict is detected, named, and correctly exempted or excluded."
