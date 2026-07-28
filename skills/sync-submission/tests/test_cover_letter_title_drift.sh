#!/usr/bin/env bash
# Regression for cover_letter_drift_check.py TITLE_DRIFT (Phase 4 cover-letter gate).
# A manuscript title must appear verbatim in the cover letter and match the project
# config; three different live titles at once is a guaranteed desk-check flag.
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

echo "test_cover_letter_title_drift: $((6-fail)) passed, $fail failed"
[[ "$fail" -eq 0 ]] || exit 1
