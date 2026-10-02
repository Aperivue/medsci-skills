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
# finetune is a softmax CrossEntropy head, so it needs >= 2 classes (see (g) below)
task_args() { [ "$1" = finetune ] && echo "--out-channels 2"; }
clean_repo() { python3 "$SCAFFOLD" --manifest "$WORK/m.csv" --task "$1" $(task_args "$1") --out "$WORK/$1" --seed 42 --quiet >/dev/null 2>&1; }
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

# (f) zero-case guard: a generated evaluate.py must not exit 0 having predicted nothing. An
#     empty or mis-pointed test split (or a self-configuring CLI that found "0 cases") ran to
#     completion, wrote an empty predictions file and exited 0. Every task's evaluate.py must
#     call assert_case_count(...) in main(), and the emitted guard itself must reject an empty
#     prediction set and a partial one. Run with no torch: the guard is extracted by AST.
case_guard() { python3 - "$WORK/$1/evaluate.py" <<'PY'
import ast, sys
src = open(sys.argv[1]).read()
tree = ast.parse(src)
fn = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "assert_case_count"), None)
assert fn is not None, "evaluate.py defines no assert_case_count"
main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
calls = [n for n in ast.walk(main) if isinstance(n, ast.Call)
         and getattr(n.func, "id", None) == "assert_case_count"]
assert calls, "main() never calls assert_case_count"
ns = {}
exec(compile(ast.Module(body=[fn], type_ignores=[]), "evaluate.py", "exec"), ns)
guard = ns["assert_case_count"]
for n_pred, n_test in ((0, 0), (0, 3), (2, 3)):
    try:
        guard(n_pred, n_test)
    except SystemExit as e:
        assert e.code not in (None, 0), f"guard exited 0 for {n_pred}/{n_test}"
    else:
        raise AssertionError(f"guard accepted {n_pred} predictions for {n_test} test cases")
guard(3, 3)  # a complete prediction set passes
PY
}
check "segmentation evaluate.py fails on an empty prediction set" case_guard clean
for t in classification detection synthesis ssl finetune; do
    check "$t evaluate.py fails on an empty prediction set" case_guard "$t"
done

# (g) finetune is a softmax CrossEntropy head: one output gives every case a score of 1.0 and a
#     loss of 0. The scaffold must refuse it (exit 2) instead of emitting that model.
python3 "$SCAFFOLD" --manifest "$WORK/m.csv" --task finetune --out "$WORK/ft1" --quiet >/dev/null 2>&1
check "finetune with the default single output exits 2" test "$?" -eq 2
check "finetune with 1 output emits no repo" test ! -e "$WORK/ft1/model.py"
python3 "$SCAFFOLD" --manifest "$WORK/m.csv" --task classification --out "$WORK/cls1" --quiet >/dev/null 2>&1
check "classification (BCE) keeps its single-output default" test "$?" -eq 0

# (h) a finetune model asked for pretrained weights must not silently train a random-init
#     stand-in when timm is missing (PRETRAINED.md / best.pt would then name weights never
#     loaded). The backbone builder is extracted by AST and run with timm made unimportable.
check "pretrained=True without timm raises; pretrained=False builds the stand-in" python3 - "$WORK/finetune/model.py" <<'PY'
import ast, sys
tree = ast.parse(open(sys.argv[1]).read())
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_build_backbone")
ns = {"PRETRAINED_SOURCE": "timm:resnet50.a1_in1k", "_SmallBackbone": lambda c, b: "stand-in"}
exec(compile(ast.Module(body=[fn], type_ignores=[]), "model.py", "exec"), ns)
sys.modules["timm"] = None          # `import timm` now raises ImportError
try:
    got = ns["_build_backbone"](1, 16, True)
except ImportError:
    pass
else:
    raise AssertionError(f"pretrained=True without timm returned {got!r}")
assert ns["_build_backbone"](1, 16, False) == "stand-in"
PY
check "finetune checkpoint records the backbone class actually built" python3 - "$WORK/finetune/train.py" <<'PY'
import ast, sys
keys = {k.value for n in ast.walk(ast.parse(open(sys.argv[1]).read())) if isinstance(n, ast.Dict)
        for k in n.keys if isinstance(k, ast.Constant)}
assert {"pretrained_source", "backbone_class"} <= keys, keys
PY

# (i) IDs are compared after stripping whitespace: 'P01' and 'P01 ' are one patient, so they
#     land in one split, and the generated dataset.py puts every manifest row in exactly one
#     partition (run with a stub torch; no torch needed).
{ echo "patient_id,image,label"
  for i in 01 02 03 04 05 06 07 08 09 10 11 12; do echo "P$i,a$i,0"; echo "P$i ,b$i,1"; done; } > "$WORK/ws.csv"
python3 "$SCAFFOLD" --manifest "$WORK/ws.csv" --out "$WORK/ws" --seed 42 --quiet >/dev/null 2>&1
check "whitespace-variant IDs scaffold" test "$?" -eq 0
check "whitespace-variant IDs: one split row per patient, 12 patients" python3 -c "
import csv
rows=list(csv.DictReader(open('$WORK/ws/splits/split_assignment.csv')))
ids=[r['patient_id'] for r in rows]
assert len(ids)==len(set(ids))==12, ids
assert all(i==i.strip() for i in ids), ids"
check "generated dataset.py puts every manifest row in exactly one split" python3 - "$WORK/ws" "$WORK/ws.csv" <<'PY'
import sys, types, importlib.util
repo, man = sys.argv[1], sys.argv[2]
torch = types.ModuleType("torch"); tud = types.ModuleType("torch.utils.data")
tud.Dataset = object; torch.utils = types.ModuleType("torch.utils"); torch.utils.data = tud
sys.modules.update({"torch": torch, "torch.utils": torch.utils, "torch.utils.data": tud})
spec = importlib.util.spec_from_file_location("ds", f"{repo}/dataset.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
part = {}
for sp in ("train", "val", "test"):
    for r in m.ScaffoldDataset(man, repo, sp).rows:
        part.setdefault(r["patient_id"].strip(), set()).add(sp)
assert sum(len(m.ScaffoldDataset(man, repo, sp).rows) for sp in ("train", "val", "test")) == 24
assert all(len(v) == 1 for v in part.values()), part
PY

# (j) --preprocessing-manifest: reuse imaging-data's split (the one its leakage gate checked)
#     instead of drawing a new one; refuse a manifest that cannot be used (exit 2).
printf '{"split_seed": 7, "transforms": [], "split_assignment": [%s]}\n' \
  '{"patient_id":"P1","split":"test"},{"patient_id":"P2","split":"train"},{"patient_id":"P3","split":"val"},{"patient_id":"P4","split":"train"}' \
  > "$WORK/pm.json"
python3 "$SCAFFOLD" --manifest "$WORK/m.csv" --preprocessing-manifest "$WORK/pm.json" --out "$WORK/imp" --seed 42 --quiet >/dev/null 2>&1
check "imported split scaffolds" test "$?" -eq 0
check "imported split is the upstream one" python3 -c "
import csv
got={r['patient_id']:r['split'] for r in csv.DictReader(open('$WORK/imp/splits/split_assignment.csv'))}
assert got=={'P1':'test','P2':'train','P3':'val','P4':'train'}, got"
check "imported split records the upstream seed" bash -c "[ \"\$(cat '$WORK/imp/splits/split_seed.txt')\" = '7' ]"
pm_bad() { printf '%s\n' "$2" > "$WORK/$1.json"
    python3 "$SCAFFOLD" --manifest "$WORK/m.csv" --preprocessing-manifest "$WORK/$1.json" --out "$WORK/$1" --quiet >/dev/null 2>&1
    test "$?" -eq 2; }
check "imported split missing a manifest patient exits 2" pm_bad miss \
  '{"split_seed": 7, "split_assignment": [{"patient_id":"P1","split":"train"},{"patient_id":"P2","split":"test"}]}'
check "imported split with a patient in two splits exits 2" pm_bad dup \
  '{"split_seed": 7, "split_assignment": [{"patient_id":"P1","split":"train"},{"patient_id":"P1","split":"test"},{"patient_id":"P2","split":"train"},{"patient_id":"P3","split":"val"},{"patient_id":"P4","split":"train"}]}'
check "imported split without split_seed exits 2" pm_bad noseed \
  '{"split_assignment": [{"patient_id":"P1","split":"test"},{"patient_id":"P2","split":"train"},{"patient_id":"P3","split":"val"},{"patient_id":"P4","split":"train"}]}'
check "imported split with an unknown split label exits 2" pm_bad label \
  '{"split_seed": 7, "split_assignment": [{"patient_id":"P1","split":"holdout"},{"patient_id":"P2","split":"train"},{"patient_id":"P3","split":"val"},{"patient_id":"P4","split":"train"}]}'
check "missing --preprocessing-manifest file exits 2" bash -c \
  "python3 '$SCAFFOLD' --manifest '$WORK/m.csv' --preprocessing-manifest '$WORK/nope.json' --out '$WORK/nope' --quiet >/dev/null 2>&1; test \$? -eq 2"

# (k) hygiene counts only code a run reaches, resolves inline/positional/wrapped split
#     arguments, and never clears a script it did not find. Each positive has a clean twin.
G="$WORK/hyg"; mkdir -p "$G"
cat > "$G/seed_uncalled.py" <<'PY'
import random, numpy as np, torch
def seed_everything(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s); torch.cuda.manual_seed_all(s)
    torch.backends.cudnn.deterministic = True
def main():
    pass
if __name__ == "__main__":
    main()
PY
sed 's/^    pass$/    seed_everything(0)/' "$G/seed_uncalled.py" > "$G/seed_called.py"
python3 "$HYGIENE" --train "$G/seed_uncalled.py" --out "$OUT" --quiet >/dev/null 2>&1
check "seed_everything defined but never called -> SEED_INCOMPLETE" has SEED_INCOMPLETE
check "... and CUDNN_NONDETERMINISTIC" has CUDNN_NONDETERMINISTIC
python3 "$HYGIENE" --train "$G/seed_called.py" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "seed_everything called from main -> exit 0" test "$?" -eq 0
check "seed_everything called from main -> no SEED_INCOMPLETE" no SEED_INCOMPLETE
SEEDS='import random, numpy as np, torch
from torch.utils.data import DataLoader, ConcatDataset, Subset
random.seed(0); np.random.seed(0); torch.manual_seed(0); torch.cuda.manual_seed_all(0)
torch.backends.cudnn.deterministic = True'
loader_case() { printf '%s\n%s\n' "$SEEDS" "$2" > "$G/$1.py"
    python3 "$HYGIENE" --train "$G/$1.py" --out "$OUT" --quiet >/dev/null 2>&1; }
loader_case inline 'l = DataLoader(DS(M, ".", split="test"), batch_size=4, shuffle=True)'
check "inline DS(split=test) shuffled loader -> TRAIN_ON_NONTRAIN_SPLIT" has TRAIN_ON_NONTRAIN_SPLIT
loader_case positional 'ds = DS(M, ".", "val")
l = DataLoader(ds, shuffle=True)'
check "positional DS(..., \"val\") shuffled loader -> TRAIN_ON_NONTRAIN_SPLIT" has TRAIN_ON_NONTRAIN_SPLIT
loader_case concat 'both = ConcatDataset([DS(M, ".", split="train"), DS(M, ".", split="test")])
l = DataLoader(both, shuffle=True)'
check "ConcatDataset(train+test) shuffled loader -> TRAIN_ON_NONTRAIN_SPLIT" has TRAIN_ON_NONTRAIN_SPLIT
loader_case subset 'l = DataLoader(Subset(DS(M, ".", split="test"), [0, 1]), shuffle=True)'
check "Subset(test) shuffled loader -> TRAIN_ON_NONTRAIN_SPLIT" has TRAIN_ON_NONTRAIN_SPLIT
loader_case inline_train 'l = DataLoader(DS(M, ".", split="train"), batch_size=4, shuffle=True)
v = DataLoader(DS(M, ".", split="val"), batch_size=4, shuffle=False)'
check "inline train shuffled + val unshuffled -> no TRAIN_ON_NONTRAIN_SPLIT" no TRAIN_ON_NONTRAIN_SPLIT
loader_case rebound 'ds = DS(M, ".", split="test")
ds = DS(M, ".", split="train")
l = DataLoader(ds, shuffle=True)'
check "dataset variable rebound to train -> no TRAIN_ON_NONTRAIN_SPLIT" no TRAIN_ON_NONTRAIN_SPLIT
cat > "$G/eval_good.py" <<'PY'
import torch
def main(model, loader):
    model.eval()
    with torch.no_grad():
        return [model(x) for x in loader]
PY
cat > "$G/eval_unused_nograd.py" <<'PY'
import torch
def _unused():
    with torch.no_grad():
        pass
def main(model, loader):
    model.eval()
    return [model(x) for x in loader]
PY
python3 "$HYGIENE" --eval "$G/eval_unused_nograd.py" --out "$OUT" --quiet >/dev/null 2>&1
check "no_grad only in an unused helper -> MISSING_EVAL_MODE" has MISSING_EVAL_MODE
python3 "$HYGIENE" --eval "$G/eval_good.py" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "library-style eval with eval()+no_grad() in main -> exit 0" test "$?" -eq 0
mkdir -p "$G/notrain"; cp "$G/eval_good.py" "$G/notrain/evaluate.py"; printf 'import torch\nx = 1\n' > "$G/notrain/train_model.py"
python3 "$HYGIENE" --repo "$G/notrain" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "--repo with no train.py under --strict -> exit 2 (not a clearance)" test "$?" -eq 2
check "--repo with no train.py -> reported as NOT CHECKED" python3 -c "
import json; d=json.load(open('$OUT'))
assert d['unchecked'] and d['summary']['verdict']=='INCOMPLETE', d"
check "--repo with no train.py -> no 'seeds all RNGs' clean row" bash -c \
  "! python3 '$HYGIENE' --repo '$G/notrain' | grep -q 'seeds all RNGs'"
python3 "$HYGIENE" --repo "$G/notrain" --quiet >/dev/null 2>&1
check "--repo with no train.py without --strict -> exit 0 (report-only)" test "$?" -eq 0

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
