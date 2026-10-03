#!/usr/bin/env bash
# Regression test for the split-leakage gate (model-assessment).
# Synthetic, PII-free fixtures reproduce: (a) a patient that crosses train/test,
# (b) column auto-detection (subject_id / partition), (c) a missing split seed,
# (d) the --no-require-seed / --seed downgrades, (e) a single-partition file, and
# (f) a seed read from a column, (g) the printed id/split columns and the Minor advisory for
# an auto-picked ID column that is not patient-level (image_id / study_id; exit code
# unchanged), and (h) patient attribute or label columns that span partitions stay clean.
# Stdlib-only (python3).
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

# (8) F1: the ID column the gate audits is printed, and an auto-picked column whose name does
#     not say it is patient-level (image_id / study_id) gets a Minor ID_COL_NOT_PATIENT_LEVEL
#     advisory pointing at --id-col. The decision is main's: overlap is computed on the chosen
#     column only, so the exit code is unchanged (no guessing from other columns).
check "chosen ID column printed on stdout" bash -c "python3 '$SCRIPT' --splits '$F/clean_imageid_case.csv' --seed 1 | grep -q 'id_col=image_id  split_col=split'"
python3 "$SCRIPT" --splits "$F/leak_imageid_case.csv" --seed 1 --out "$OUT" --strict --quiet >/dev/null 2>&1
check "image_id + case (P1 crosses): exit 0, as on main (advisory only)" test "$?" -eq 0
check "image_id auto-picked: ID_COL_NOT_PATIENT_LEVEL advisory" has_verdict ID_COL_NOT_PATIENT_LEVEL
check "ID_COL_NOT_PATIENT_LEVEL is Minor and suggests --id-col" python3 -c "
import json; d=json.load(open('$OUT'))
c=[c for c in d['claims'] if c['verdict']=='ID_COL_NOT_PATIENT_LEVEL'][0]
assert c['severity']=='Minor' and '--id-col' in c['detail'], c
assert d['summary']['n_major']==0, d['summary']"
python3 "$SCRIPT" --splits "$F/leak_studyid_mrn.csv" --seed 1 --out "$OUT" --strict --quiet >/dev/null 2>&1
check "study_id + patient_mrn (M1 crosses): exit 0, as on main (advisory only)" test "$?" -eq 0
check "study_id auto-picked: ID_COL_NOT_PATIENT_LEVEL advisory" has_verdict ID_COL_NOT_PATIENT_LEVEL
python3 "$SCRIPT" --splits "$F/leak_imageid_case.csv" --id-col case --seed 1 --out "$OUT" --strict --quiet >/dev/null 2>&1
check "--id-col case: exit 1 (PATIENT_OVERLAP)" test "$?" -eq 1
check "--id-col case: PATIENT_OVERLAP" has_verdict PATIENT_OVERLAP
check "--id-col given: no ID_COL_NOT_PATIENT_LEVEL advisory" no_verdict ID_COL_NOT_PATIENT_LEVEL
python3 "$SCRIPT" --splits "$F/leak_studyid_mrn.csv" --id-col patient_mrn --seed 1 --out "$OUT" --strict --quiet >/dev/null 2>&1
check "--id-col patient_mrn: exit 1 (PATIENT_OVERLAP)" test "$?" -eq 1
python3 "$SCRIPT" --splits "$F/clean_imageid_case.csv" --seed 1 --out "$OUT" --strict --quiet >/dev/null 2>&1
check "image_id + case, disjoint: exit 0" test "$?" -eq 0
check "image_id + case, disjoint: no PATIENT_OVERLAP" no_verdict PATIENT_OVERLAP
python3 "$SCRIPT" --splits "$F/only_image_study_ids.csv" --seed 1 --strict --quiet >/dev/null 2>&1
check "image_id + study_id, no patient column: exit 0 (unchanged)" test "$?" -eq 0
python3 "$SCRIPT" --splits "$CHF/splits_clean.csv" --out "$OUT" --quiet >/dev/null 2>&1
check "patient_id auto-picked: no ID_COL_NOT_PATIENT_LEVEL advisory" no_verdict ID_COL_NOT_PATIENT_LEVEL

# (9) Reviewer counter-examples, all clean on main: a clean patient column beside a patient
#     attribute column that spans partitions, and image-level splits beside a label column
#     named 'case' (binary, 3-class over train/test, 4-class over train/val/test). Each stays
#     exit 0 under --strict with no Major; a patient-named ID column gets no advisory.
for fx in clean_patient_visit_no clean_subject_sex_code clean_participant_site_id; do
  python3 "$SCRIPT" --splits "$F/$fx.csv" --seed 42 --out "$OUT" --strict --quiet >/dev/null 2>&1
  check "$fx: exit 0 (patient attribute column not compared)" test "$?" -eq 0
  check "$fx: no Major" python3 -c "
import json; d=json.load(open('$OUT')); assert d['summary']['n_major']==0, d['summary']"
  check "$fx: no ID_COL_NOT_PATIENT_LEVEL advisory" no_verdict ID_COL_NOT_PATIENT_LEVEL
done
for fx in clean_imageid_casecontrol clean_imageid_case3class clean_imageid_case4class; do
  python3 "$SCRIPT" --splits "$F/$fx.csv" --seed 42 --out "$OUT" --strict --quiet >/dev/null 2>&1
  check "$fx: exit 0 (label column 'case' not compared)" test "$?" -eq 0
  check "$fx: no Major" python3 -c "
import json; d=json.load(open('$OUT')); assert d['summary']['n_major']==0, d['summary']"
done

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
