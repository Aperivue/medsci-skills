#!/usr/bin/env bash
# Regression test for the imaging-data -> model-scaffold QC handoff (scaffold.py).
# Synthetic, PII-free, stdlib + numpy only. The reports below are shaped exactly like the JSON
# imaging-data's gates write (detector + claims[{verdict, severity, detail}]).
#   (a) an unacknowledged Major claim refuses the scaffold: exit 1, every code + file listed,
#       nothing written;
#   (b) --ack-qc CODE=reason unblocks and the reason is recorded in IMAGING_QC.md;
#   (c) Minor / Flag claims never block and are carried forward into the generated repo;
#   (d) a manifest with no QC report next to it is recorded as NOT ASSESSED, never silent;
#   (e) a leakage report about a different manifest is skipped, not applied;
#   (f) --imaging-qc on an explicit file / directory; malformed input exits 2;
#   (g) without --preprocessing-manifest / --imaging-qc nothing about QC is emitted.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCAFFOLD="$HERE/../scripts/scaffold.py"
HYGIENE="$HERE/../scripts/check_training_hygiene.py"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
[[ -f "$SCAFFOLD" ]] || { echo "ENV-ERR: scaffold.py missing" >&2; exit 2; }

printf 'patient_id,image,label\nP1,a,m\nP2,b,n\nP3,c,o\nP4,d,p\n' > "$WORK/m.csv"
PM='{"split_seed": 7, "transforms": [], "split_assignment": [{"patient_id":"P1","split":"test"},{"patient_id":"P2","split":"train"},{"patient_id":"P3","split":"val"},{"patient_id":"P4","split":"train"}]}'
# A project laid out as imaging-data leaves it: manifest at the root, gate reports in qc/.
mk_project() { mkdir -p "$WORK/$1/qc"; printf '%s\n' "$PM" > "$WORK/$1/preprocessing_manifest.json"; }
profile_report() { cat > "$1" <<JSON
{"detector": "check_dataset_profile", "profile": "eda/profile.json",
 "claims": [$2], "summary": {"n_claims": 0, "n_major": 0, "n_flag": 0}}
JSON
}
MAJOR='{"verdict": "LABEL_EMPTY", "severity": "Major", "detail": "case is in a labelled split but its label contains no voxel of the target label 1", "cases": ["c07"], "n_cases": 1}'
MINOR='{"verdict": "INTENSITY_SCALE_INCONSISTENT", "severity": "Minor", "detail": "50/60 cases bottom out near air (<= -500) and the rest do not", "cases": [], "n_cases": 0}'
run() { local proj="$1"; shift
    python3 "$SCAFFOLD" --manifest "$WORK/m.csv" --preprocessing-manifest "$WORK/$proj/preprocessing_manifest.json" \
        --out "$WORK/$proj/repo" --quiet "$@" >"$WORK/$proj/stdout" 2>"$WORK/$proj/stderr"; }

# (a) Major blocks
mk_project major
profile_report "$WORK/major/qc/dataset_profile.json" "$MAJOR, $MINOR"
run major; rc=$?
check "unacknowledged Major refuses (exit 1)" test "$rc" -eq 1
check "refusal names the claim code" grep -q "LABEL_EMPTY" "$WORK/major/stderr"
check "refusal names the report file" grep -q "qc/dataset_profile.json" "$WORK/major/stderr"
check "refusal writes nothing" test ! -e "$WORK/major/repo"

# (b) --ack-qc unblocks and is recorded
run major --ack-qc "LABEL_EMPTY=c07 excluded from the cohort before the split"; rc=$?
check "--ack-qc unblocks (exit 0)" test "$rc" -eq 0
check "IMAGING_QC.md written" test -f "$WORK/major/repo/IMAGING_QC.md"
check "acknowledgement reason recorded" grep -q "Acknowledged: c07 excluded from the cohort before the split" "$WORK/major/repo/IMAGING_QC.md"
check "config.yaml points at the record" grep -q "^  record: IMAGING_QC.md" "$WORK/major/repo/config.yaml"
check "config.yaml counts the acknowledged Major" grep -q "^  major_acknowledged: 1" "$WORK/major/repo/config.yaml"
check "REPRODUCIBILITY.md points at the record" grep -q "Upstream imaging QC" "$WORK/major/repo/REPRODUCIBILITY.md"
check "acknowledged repo still passes training hygiene" python3 "$HYGIENE" --repo "$WORK/major/repo" --strict --quiet
check "malformed --ack-qc (no reason) exits 2" bash -c \
  "python3 '$SCAFFOLD' --manifest '$WORK/m.csv' --preprocessing-manifest '$WORK/major/preprocessing_manifest.json' --out '$WORK/major/r2' --quiet --ack-qc LABEL_EMPTY= >/dev/null 2>&1; test \$? -eq 2"
check "an ack for another code does not unblock (exit 1)" bash -c \
  "python3 '$SCAFFOLD' --manifest '$WORK/m.csv' --preprocessing-manifest '$WORK/major/preprocessing_manifest.json' --out '$WORK/major/r3' --quiet --ack-qc 'LABEL_MISSING=x' >/dev/null 2>&1; test \$? -eq 1"

# (c) Minor / Flag carried forward, not blocking
mk_project minor
profile_report "$WORK/minor/qc/dataset_profile.json" "$MINOR"
cat > "$WORK/minor/qc/normalizer_domain.json" <<'JSON'
{"detector": "check_normalizer_domain", "claims": [{"verdict": "NORMALIZER_SPLIT_DIVERGENCE", "severity": "Flag", "split": "ext", "detail": "3 of 9 case(s) bottom out near air"}], "summary": {}}
JSON
run minor; rc=$?
check "Minor + Flag do not block (exit 0)" test "$rc" -eq 0
check "Minor carried forward into IMAGING_QC.md" grep -q "INTENSITY_SCALE_INCONSISTENT\*\* (Minor" "$WORK/minor/repo/IMAGING_QC.md"
check "Flag carried forward into IMAGING_QC.md" grep -q "NORMALIZER_SPLIT_DIVERGENCE\*\* (Flag" "$WORK/minor/repo/IMAGING_QC.md"
check "carried-forward warning echoed on stderr" grep -q "CARRIED FORWARD: INTENSITY_SCALE_INCONSISTENT" "$WORK/minor/stderr"
check "config.yaml counts 2 carried-forward claims" grep -q "^  carried_forward: 2" "$WORK/minor/repo/config.yaml"
check "the gate with no report is NOT ASSESSED" grep -q "check_preprocessing_leakage\`: NOT ASSESSED" "$WORK/minor/repo/IMAGING_QC.md"

# (d) manifest given, no QC report anywhere -> explicit NOT ASSESSED
mkdir -p "$WORK/none/inner"; printf '%s\n' "$PM" > "$WORK/none/inner/preprocessing_manifest.json"
python3 "$SCAFFOLD" --manifest "$WORK/m.csv" --preprocessing-manifest "$WORK/none/inner/preprocessing_manifest.json" \
    --out "$WORK/none/repo" --quiet >/dev/null 2>"$WORK/none/stderr"; rc=$?
check "no QC report: scaffold proceeds (exit 0)" test "$rc" -eq 0
check "no QC report: stderr says so" grep -q "no imaging-data QC report found" "$WORK/none/stderr"
check "no QC report: every gate NOT ASSESSED" python3 -c "
t=open('$WORK/none/repo/IMAGING_QC.md').read()
for d in ('check_dataset_profile','check_preprocessing_leakage','check_normalizer_domain'):
    assert '\`'+d+'\`: NOT ASSESSED' in t, d"
check "no QC report: config.yaml lists them" grep -q "^  not_assessed: \[check_dataset_profile, check_preprocessing_leakage, check_normalizer_domain\]" "$WORK/none/repo/config.yaml"

# (e) a leakage report about a DIFFERENT manifest is skipped (demo 05 keeps a naive one beside it);
#     the sibling layout manifests/ + qc/ is found through <manifest dir>/../qc/
mkdir -p "$WORK/sib/manifests" "$WORK/sib/qc"; printf '%s\n' "$PM" > "$WORK/sib/manifests/preprocessing_manifest.json"
cat > "$WORK/sib/qc/leak_naive.json" <<'JSON'
{"detector": "check_preprocessing_leakage", "manifest": "manifests/preprocessing_manifest_naive.json", "claims": [{"verdict": "PREPROCESS_BEFORE_SPLIT", "severity": "Major", "detail": "x", "where": "t"}], "summary": {}}
JSON
cat > "$WORK/sib/qc/leak.json" <<'JSON'
{"detector": "check_preprocessing_leakage", "manifest": "manifests/preprocessing_manifest.json", "claims": [], "summary": {}}
JSON
python3 "$SCAFFOLD" --manifest "$WORK/m.csv" --preprocessing-manifest "$WORK/sib/manifests/preprocessing_manifest.json" \
    --out "$WORK/sib/repo" --quiet >/dev/null 2>&1; rc=$?
check "other-manifest leakage report does not block (exit 0)" test "$rc" -eq 0
check "other-manifest report listed as skipped" grep -q "skipped .*leak_naive.json" "$WORK/sib/repo/IMAGING_QC.md"
check "matching leakage report read via ../qc" grep -q "check_preprocessing_leakage\` — .*leak.json" "$WORK/sib/repo/IMAGING_QC.md"

# (f) --imaging-qc explicit file / directory; bad input exits 2
python3 "$SCAFFOLD" --manifest "$WORK/m.csv" --imaging-qc "$WORK/major/qc/dataset_profile.json" --out "$WORK/f1" --quiet >/dev/null 2>&1
check "--imaging-qc file alone (no manifest) still blocks on Major (exit 1)" test "$?" -eq 1
python3 "$SCAFFOLD" --manifest "$WORK/m.csv" --imaging-qc "$WORK/minor/qc" --out "$WORK/f2" --quiet >/dev/null 2>&1
check "--imaging-qc directory with Minor only scaffolds (exit 0)" test "$?" -eq 0
check "--imaging-qc directory: record written" test -f "$WORK/f2/IMAGING_QC.md"
check "--imaging-qc missing path exits 2" bash -c \
  "python3 '$SCAFFOLD' --manifest '$WORK/m.csv' --imaging-qc '$WORK/nope.json' --out '$WORK/f3' --quiet >/dev/null 2>&1; test \$? -eq 2"
printf '{"claims": []}\n' > "$WORK/notqc.json"
check "--imaging-qc on a non-imaging-data JSON exits 2" bash -c \
  "python3 '$SCAFFOLD' --manifest '$WORK/m.csv' --imaging-qc '$WORK/notqc.json' --out '$WORK/f4' --quiet >/dev/null 2>&1; test \$? -eq 2"

# (g) no manifest, no --imaging-qc: no QC artefact at all (the output main emitted)
python3 "$SCAFFOLD" --manifest "$WORK/m.csv" --out "$WORK/plain" --seed 42 --quiet >/dev/null 2>&1
check "plain scaffold: no IMAGING_QC.md" test ! -e "$WORK/plain/IMAGING_QC.md"
check "plain scaffold: config.yaml has no imaging_qc block" bash -c "! grep -q imaging_qc '$WORK/plain/config.yaml'"
check "plain scaffold: REPRODUCIBILITY.md unchanged" bash -c "! grep -q 'Upstream imaging QC' '$WORK/plain/REPRODUCIBILITY.md'"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
