#!/usr/bin/env bash
# Regression test for the training-hygiene linter + the scaffold generator
# (model-scaffold). Synthetic, PII-free. Stdlib + numpy only (no torch).
#   (a) a freshly scaffolded repo is clean (all RNGs seeded, cuDNN deterministic,
#       eval()+no_grad(), train-only loader) -> exit 0;
#   (b) bad train/eval fixtures fire SEED_INCOMPLETE, TRAIN_ON_NONTRAIN_SPLIT,
#       MISSING_EVAL_MODE (Major) + CUDNN_NONDETERMINISTIC, EVAL_SHUFFLE (Minor);
#   (c) scaffold.py emits a patient-disjoint, seed-locked split (deterministic).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKD="$HERE/../scripts"
HYGIENE="$SKD/check_training_hygiene.py"
SCAFFOLD="$SKD/scaffold.py"
F="$HERE/fixtures"
WORK="$(mktemp -d)"
OUT="$WORK/out.json"
trap 'rm -rf "$WORK"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
has() { python3 -c "
import json
d=json.load(open('$OUT'))
assert any(c['verdict']=='$1' for c in d['claims']), '$1 not found'
"; }
no() { python3 -c "
import json
d=json.load(open('$OUT'))
assert not any(c['verdict']=='$1' for c in d['claims']), '$1 unexpectedly present'
"; }

[[ -f "$HYGIENE" && -f "$SCAFFOLD" ]] || { echo "ENV-ERR: scripts missing" >&2; exit 2; }

# (a) scaffold a clean repo -> hygiene clean, exit 0
printf 'patient_id,image,label\nP1,a,m\nP2,b,n\nP3,c,o\nP4,d,p\n' > "$WORK/m.csv"
python3 "$SCAFFOLD" --manifest "$WORK/m.csv" --out "$WORK/clean" --seed 42 --quiet >/dev/null 2>&1
python3 "$HYGIENE" --repo "$WORK/clean" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "scaffolded repo passes hygiene (exit 0)" test "$?" -eq 0
check "no SEED_INCOMPLETE on clean repo" no SEED_INCOMPLETE
check "no MISSING_EVAL_MODE on clean repo" no MISSING_EVAL_MODE

# (b) bad fixtures -> Major verdicts, exit 1
python3 "$HYGIENE" --train "$F/bad_train.py" --eval "$F/bad_evaluate.py" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 on bad train/eval (Major present)" test "$?" -eq 1
check "SEED_INCOMPLETE detected"          has SEED_INCOMPLETE
check "TRAIN_ON_NONTRAIN_SPLIT detected"  has TRAIN_ON_NONTRAIN_SPLIT
check "MISSING_EVAL_MODE detected"        has MISSING_EVAL_MODE
check "CUDNN_NONDETERMINISTIC detected"   has CUDNN_NONDETERMINISTIC
check "EVAL_SHUFFLE detected"             has EVAL_SHUFFLE
check "reports numpy as the only seed found" python3 -c "
import json; d=json.load(open('$OUT'))
c=next(c for c in d['claims'] if c['verdict']=='SEED_INCOMPLETE')
assert 'found: numpy' in c['detail'], c['detail']"

# (c) scaffold emits a patient-disjoint, seed-locked split (deterministic)
check "split_assignment.csv emitted" test -f "$WORK/clean/splits/split_assignment.csv"
check "split seed recorded = 42" bash -c "[ \"\$(cat '$WORK/clean/splits/split_seed.txt')\" = '42' ]"
check "split is patient-disjoint" python3 -c "
import csv
seen={}
for r in csv.DictReader(open('$WORK/clean/splits/split_assignment.csv')):
    seen.setdefault(r['patient_id'],set()).add(r['split'])
assert all(len(s)==1 for s in seen.values()), 'patient crosses splits'"

# (d) breadth: every task scaffolds to valid Python with hygiene-clean train/eval
clean_repo() { python3 "$SCAFFOLD" --manifest "$WORK/m.csv" --task "$1" --out "$WORK/$1" --seed 42 --quiet >/dev/null 2>&1; }
hygiene_ok() { python3 "$HYGIENE" --repo "$WORK/$1" --strict --quiet >/dev/null 2>&1; }
valid_py()  { for f in "$WORK/$1"/*.py; do python3 -c "import ast,sys;ast.parse(open(sys.argv[1]).read())" "$f" || return 1; done; }
for t in classification detection synthesis ssl finetune; do
    if clean_repo "$t" && hygiene_ok "$t" && valid_py "$t"; then
        printf '  PASS  scaffold %s: hygiene-clean + valid Python\n' "$t"
    else
        printf '  FAIL  scaffold %s\n' "$t"; fail=$((fail+1))
    fi
done

# (e) fine-tuning provenance: the scaffold records provenance by construction (no fire),
#     a pretrained-load repo WITHOUT a provenance record fires PRETRAINED_PROVENANCE_MISSING.
check "finetune scaffold emits PRETRAINED.md" test -f "$WORK/finetune/PRETRAINED.md"
check "finetune config.yaml has a pretrained: block" grep -q "^pretrained:" "$WORK/finetune/config.yaml"
python3 "$HYGIENE" --repo "$WORK/finetune" --out "$OUT" --quiet >/dev/null 2>&1
check "no PRETRAINED_PROVENANCE_MISSING on finetune scaffold" no PRETRAINED_PROVENANCE_MISSING
python3 "$HYGIENE" --repo "$F/finetune_no_provenance" --out "$OUT" --quiet >/dev/null 2>&1
check "PRETRAINED_PROVENANCE_MISSING on pretrained-load repo lacking provenance" has PRETRAINED_PROVENANCE_MISSING
check "provenance verdict is Minor" python3 -c "
import json; d=json.load(open('$OUT'))
c=next(c for c in d['claims'] if c['verdict']=='PRETRAINED_PROVENANCE_MISSING')
assert c['severity']=='Minor', c['severity']"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
