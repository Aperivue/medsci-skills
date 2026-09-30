#!/usr/bin/env bash
# Regression test for the split-leakage gate (model-validation).
# Synthetic, PII-free fixtures reproduce: (a) a patient that crosses train/test,
# (b) column auto-detection (subject_id / partition), (c) a missing split seed,
# (d) the --no-require-seed / --seed downgrades, (e) a single-partition file, and
# (f) a seed read from a column. Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_split_leakage.py"
F="$HERE/fixtures"
CHF="$HERE/../scripts/check_split_leakage_challenge/fixture"
OUT="$(mktemp -t spl_XXXX).json"
trap 'rm -f "$OUT"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
has_verdict() { python3 -c "
import json
d=json.load(open('$OUT'))
assert any(c['verdict']=='$1' for c in d['claims']), '$1 not found'
"; }
no_verdict() { python3 -c "
import json
d=json.load(open('$OUT'))
assert not any(c['verdict']=='$1' for c in d['claims']), '$1 unexpectedly present'
"; }

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# (1) challenge leak fixture: P03/P07 cross partitions, seed auto-detected -> PATIENT_OVERLAP, exit 1
python3 "$SCRIPT" --splits "$CHF/splits_leak.csv" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 under --strict (patient overlap)" test "$?" -eq 1
check "PATIENT_OVERLAP detected" has_verdict PATIENT_OVERLAP
check "two overlapping subjects reported" python3 -c "
import json; d=json.load(open('$OUT'))
assert d['summary']['n_overlapping_subjects']==2, d['summary']"
check "seed auto-detected from split_seed.txt" python3 -c "
import json; d=json.load(open('$OUT')); assert d['seed']=='42', d['seed']"

# (2) clean challenge fixture: synonyms collapse, disjoint -> exit 0, no overlap
python3 "$SCRIPT" --splits "$CHF/splits_clean.csv" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0 on disjoint split (synonyms collapsed)" test "$?" -eq 0
check "no PATIENT_OVERLAP on clean split" no_verdict PATIENT_OVERLAP

# (3) column auto-detection (subject_id / partition) + --seed isolates the overlap
python3 "$SCRIPT" --splits "$F/leak_subject.csv" --seed 1 --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 with auto-detected subject_id/partition columns" test "$?" -eq 1
check "PATIENT_OVERLAP via auto-detect (S1)" has_verdict PATIENT_OVERLAP
check "no MISSING_SEED when --seed supplied" no_verdict MISSING_SEED

# (4) explicit --id-col / --split-col also resolve
python3 "$SCRIPT" --splits "$F/leak_subject.csv" --id-col subject_id --split-col partition --seed 1 --out "$OUT" --quiet >/dev/null 2>&1
check "explicit --id-col/--split-col" has_verdict PATIENT_OVERLAP

# (5) missing seed on an otherwise-disjoint split -> MISSING_SEED (Major), exit 1
python3 "$SCRIPT" --splits "$F/noseed_clean.csv" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 when seed missing" test "$?" -eq 1
check "MISSING_SEED detected" has_verdict MISSING_SEED
check "no PATIENT_OVERLAP on disjoint split" no_verdict PATIENT_OVERLAP

# (6) --no-require-seed downgrades the missing seed -> exit 0
python3 "$SCRIPT" --splits "$F/noseed_clean.csv" --no-require-seed --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0 with --no-require-seed" test "$?" -eq 0
check "MISSING_SEED suppressed by --no-require-seed" no_verdict MISSING_SEED

# (7) single-partition file with a seed column -> SINGLE_PARTITION (Minor only), exit 0
python3 "$SCRIPT" --splits "$F/single_partition.csv" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0 on single-partition (Minor only)" test "$?" -eq 0
check "SINGLE_PARTITION detected" has_verdict SINGLE_PARTITION
check "seed read from column" python3 -c "
import json; d=json.load(open('$OUT')); assert d['seed']=='7', d['seed']"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
