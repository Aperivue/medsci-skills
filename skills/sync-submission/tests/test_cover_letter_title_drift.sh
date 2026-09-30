#!/usr/bin/env bash
# Regression for cover_letter_drift_check.py TITLE_DRIFT (Phase 4 cover-letter gate).
# A manuscript title must appear verbatim in the cover letter and match the project
# config; three different live titles at once is a guaranteed desk-check flag.
# Also: a body word count declared at a stated journal cap is held to its headroom.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/cover_letter_drift_check.py"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
OUT="$T/o.json"
fail=0
check() { local label="$1"; shift
  if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
  else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi; }
has_field() { python3 -c "
import json
d=json.load(open('$OUT'))
assert any(x['field']=='$1' for x in d['drifts']), '$1 not in drifts'
"; }
no_drift() { python3 -c "
import json
d=json.load(open('$OUT'))
assert d['submission_safe'] and not d['drifts'], d['drifts']
"; }
[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

cat > "$T/manuscript.md" <<'MD'
---
title: Adjunctive ablation halves local recurrence
---
## Introduction
Body text citing Table 1 and Figure 1.
MD

# POSITIVE: cover letter states a DRIFTED title + config carries a THIRD title.
cat > "$T/cover_bad.md" <<'MD'
Dear Editor, we submit our manuscript entitled "Adjunctive ablation reduces local recurrence".
MD
cat > "$T/ssot_bad.yaml" <<'MD'
title_working: Adjunctive thermal ablation and recurrence
MD
python3 "$SCRIPT" --manuscript "$T/manuscript.md" --cover-letter "$T/cover_bad.md" \
    --config "$T/ssot_bad.yaml" --out "$OUT" >/dev/null 2>&1
check "exit 2 on title drift" test "$?" -eq 2
check "TITLE_DRIFT (cover letter) reported"  has_field title
check "TITLE_DRIFT (config) reported"        has_field "title(config)"

# NEGATIVE: cover letter states the title verbatim, config matches -> silent.
cat > "$T/cover_ok.md" <<'MD'
Dear Editor, we submit our manuscript entitled "Adjunctive ablation halves local recurrence".
MD
cat > "$T/ssot_ok.yaml" <<'MD'
title_working: Adjunctive ablation halves local recurrence
MD
python3 "$SCRIPT" --manuscript "$T/manuscript.md" --cover-letter "$T/cover_ok.md" \
    --config "$T/ssot_ok.yaml" --out "$OUT" >/dev/null 2>&1
check "exit 0 when title agrees everywhere" test "$?" -eq 0
check "no drifts when title agrees"         no_drift

# NEGATIVE: no --config given, title verbatim in cover letter -> silent (no config FP).
python3 "$SCRIPT" --manuscript "$T/manuscript.md" --cover-letter "$T/cover_ok.md" \
    --out "$OUT" >/dev/null 2>&1
check "exit 0 without --config when cover letter carries the title" test "$?" -eq 0

# --- WORD CAP: a body count declared at the cap must match the measured count ------------
# Declared "3,998" against a stated 4,000 cap, measured 3,940: the 5% "approximately" slack
# (197 words) passed it, and the stated cap was even read AS the count ("4,000 words" is the
# largest number). A count declared that close to the cap is a claim of being under it.
python3 - "$T/cap_ms.md" <<'PY'
import sys
row = "alpha beta gamma delta epsilon zeta eta theta iota kappa"  # 10 words
body = "\n".join([row] * 394)                                     # 3,940 body words
open(sys.argv[1], "w").write(
    "---\ntitle: Synthetic word cap fixture\n---\n## Introduction\n" + body + "\n")
PY
cap_run() {
  printf 'Dear Editor, we submit "Synthetic word cap fixture". %s\n' "$1" > "$T/cap_cover.md"
  python3 "$SCRIPT" --manuscript "$T/cap_ms.md" --cover-letter "$T/cap_cover.md" --out "$OUT" >/dev/null 2>&1
}
truth_is_3940() { python3 -c "
import json; d=json.load(open('$OUT')); assert d['truth']['body_words']==3940, d['truth']"; }

# MUST FIRE: 3,998 declared, 4,000 cap stated beside it, 3,940 measured.
cap_run "The main text contains 3,998 words (limit: 4,000 words)."
check "exit 2: 3,998 declared at a 4,000 cap vs 3,940"   test "$?" -eq 2
check "cap fixture measures 3,940 body words"            truth_is_3940
check "body_words drift reported at the cap"             has_field body_words
cap_run "Word count: 3,998/4,000 words."
check "exit 2: '3,998/4,000 words' form vs 3,940"        test "$?" -eq 2

# MUST PASS: declared at the cap but agreeing with the measurement (headroom 56, off by 4).
cap_run "The main text contains 3,944 words (limit: 4,000 words)."
check "exit 0: 3,944 declared at a 4,000 cap vs 3,940"   test "$?" -eq 0
# MUST PASS: far from the cap the "approximately" slack still applies (off by 40).
cap_run "The manuscript is approximately 3,900 words, within the 5,000-word limit."
check "exit 0: approximate count far below the cap"      test "$?" -eq 0
check "no drifts for an approximate count below the cap" no_drift

echo "test_cover_letter_title_drift: $fail failed"
[[ "$fail" -eq 0 ]] || exit 1
