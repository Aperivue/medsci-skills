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
#   (g) without --preprocessing-manifest / --imaging-qc nothing about QC is emitted;
#   (h) run from inside manifests/ (relative spellings) ../qc is still searched;
#   (i) fail closed: odd-cased / missing / unknown severity blocks; summary.n_major above the
#       listed Majors blocks; unreadable QC files are reported and NOT ASSESSED;
#   (j) leakage-report matching: Windows separators, same-name-different-file, ambiguous -> read;
#   (k) --ack-qc: malformed code / duplicate code exit 2; newlines collapsed in the record.
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
printf '%s\n' "$PM" > "$WORK/sib/manifests/preprocessing_manifest_naive.json"   # the other file exists
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

# (h) B1: from inside manifests/, both relative spellings must still reach ../qc (a Major there blocks)
mkdir -p "$WORK/rel/manifests" "$WORK/rel/qc"; printf '%s\n' "$PM" > "$WORK/rel/manifests/preprocessing_manifest.json"
profile_report "$WORK/rel/qc/dataset_profile.json" "$MAJOR"
for spelling in preprocessing_manifest.json ./preprocessing_manifest.json; do
    check "run inside manifests/ as '$spelling': ../qc Major blocks (exit 1)" bash -c \
      "cd '$WORK/rel/manifests' && python3 '$SCAFFOLD' --manifest '$WORK/m.csv' --preprocessing-manifest '$spelling' --out '$WORK/rel/repo' --quiet >/dev/null 2>&1; test \$? -eq 1"
done
check "relative run wrote nothing" test ! -e "$WORK/rel/repo"

# (i) N1 + N2: fail closed on severity, on an inconsistent summary, on unreadable files
sev_case() {  # $1 label, $2 claims JSON, $3 extra report keys, $4 expected exit
    mk_project "$1"
    printf '{"detector": "check_dataset_profile", "claims": [%s]%s}\n' "$2" "$3" > "$WORK/$1/qc/dataset_profile.json"
    run "$1"; test "$?" -eq "$4"; }
check "severity 'major' (lower case) blocks"   sev_case s_lc '{"verdict": "LABEL_EMPTY", "severity": "major", "detail": "x"}' '' 1
check "severity 'MAJOR ' (trailing space) blocks" sev_case s_uc '{"verdict": "LABEL_EMPTY", "severity": "MAJOR ", "detail": "x"}' '' 1
check "missing severity blocks"                sev_case s_none '{"verdict": "LABEL_EMPTY", "detail": "x"}' '' 1
check "unknown severity 'Critical' blocks"     sev_case s_unk '{"verdict": "LABEL_EMPTY", "severity": "Critical", "detail": "x"}' '' 1
check "severity 'minor' / 'FLAG' do not block" sev_case s_min '{"verdict": "A_B", "severity": "minor", "detail": "x"}, {"verdict": "C_D", "severity": " FLAG", "detail": "y"}' '' 0
check "summary.n_major 2 with no claims blocks" sev_case s_sum '' ', "summary": {"n_major": 2}' 1
check "inconsistent summary named on stderr" grep -q QC_REPORT_INCONSISTENT "$WORK/s_sum/stderr"
check "detector given as a script name is recognised" sev_case s_det '{"verdict": "LABEL_EMPTY", "severity": "Major", "detail": "x"}' ', "detector": "scripts/check_dataset_profile.py"' 1
mk_project unread
printf '{"detector": "check_dataset_profile", "claims": [' > "$WORK/unread/qc/truncated.json"
printf '{"detector": "check_preprocessing_leakage", "claims": null}\n' > "$WORK/unread/qc/nullclaims.json"
printf '[1, 2]\n' > "$WORK/unread/qc/list.json"
printf '\xef\xbb\xbf{"detector": "check_normalizer_domain", "claims": [{"verdict": "NORMALIZER_SPLIT_DIVERGENCE", "severity": "Flag", "detail": "bom"}]}\n' > "$WORK/unread/qc/bom.json"
printf '{"tool": "something_else", "claims": []}\n' > "$WORK/unread/qc/unrelated.json"
run unread; rc=$?
check "unreadable files do not pass silently: stderr names each" bash -c \
  "grep -q 'UNREADABLE QC FILE: .*truncated.json' '$WORK/unread/stderr' && grep -q 'UNREADABLE QC FILE: .*nullclaims.json' '$WORK/unread/stderr' && grep -q 'UNREADABLE QC FILE: .*list.json' '$WORK/unread/stderr'"
check "unreadable files listed in IMAGING_QC.md as NOT ASSESSED" bash -c \
  "grep -q 'UNREADABLE .*truncated.json' '$WORK/unread/repo/IMAGING_QC.md' && grep -q 'nullclaims.json\`: NOT ASSESSED' '$WORK/unread/repo/IMAGING_QC.md'"
check "a UTF-8 BOM report is read (Flag carried forward)" grep -q "NORMALIZER_SPLIT_DIVERGENCE\*\* (Flag" "$WORK/unread/repo/IMAGING_QC.md"
check "unrelated JSON (no detector) is ignored" bash -c "! grep -q unrelated.json '$WORK/unread/repo/IMAGING_QC.md' '$WORK/unread/stderr'"
check "config.yaml counts the unreadable files" grep -q "^  unreadable: 3" "$WORK/unread/repo/config.yaml"

# (j) N3: leakage-report matching
leak_case() {  # $1 label, $2 recorded manifest path (JSON-escaped), $3 make the other file (yes/no)
    mkdir -p "$WORK/$1/manifests" "$WORK/$1/qc"; printf '%s\n' "$PM" > "$WORK/$1/manifests/preprocessing_manifest.json"
    [ "$3" = yes ] && printf '%s\n' "$PM" > "$WORK/$1/manifests/preprocessing_manifest_naive.json"
    printf '{"detector": "check_preprocessing_leakage", "manifest": "%s", "claims": [{"verdict": "PREPROCESS_BEFORE_SPLIT", "severity": "Major", "detail": "x"}]}\n' "$2" > "$WORK/$1/qc/leak.json"
    python3 "$SCAFFOLD" --manifest "$WORK/m.csv" --preprocessing-manifest "$WORK/$1/manifests/preprocessing_manifest.json" \
        --out "$WORK/$1/repo" --quiet >/dev/null 2>"$WORK/$1/stderr"; }
leak_case l_win 'manifests\\preprocessing_manifest_naive.json' yes
check "Windows-separated path to a different existing file is skipped (exit 0)" test "$?" -eq 0
check "skip reason shown in IMAGING_QC.md" grep -q "skipped .*leak.json.: audits .*preprocessing_manifest_naive.json, a different file" "$WORK/l_win/repo/IMAGING_QC.md"
leak_case l_amb 'elsewhere/preprocessing_manifest_naive.json' no
check "recorded path that does not resolve is read, not skipped (exit 1)" test "$?" -eq 1
leak_case l_same 'manifests/preprocessing_manifest.json' no
check "report about this manifest is applied (exit 1)" test "$?" -eq 1
mkdir -p "$WORK/l_twin/other"; leak_case l_twin 'other/preprocessing_manifest.json' no
printf '%s\n' "$PM" > "$WORK/l_twin/other/preprocessing_manifest.json"
python3 "$SCAFFOLD" --manifest "$WORK/m.csv" --preprocessing-manifest "$WORK/l_twin/manifests/preprocessing_manifest.json" \
    --out "$WORK/l_twin/repo" --quiet >/dev/null 2>&1
check "same file name, demonstrably different file: skipped (exit 0)" test "$?" -eq 0

# (k) N4 + N5: ack hygiene
ack_rc() { python3 "$SCAFFOLD" --manifest "$WORK/m.csv" --preprocessing-manifest "$WORK/major/preprocessing_manifest.json" \
    --out "$WORK/major/rk" --quiet "$@" >/dev/null 2>"$WORK/ack.err"; echo $?; }
check "lower-case ack code exits 2"                 test "$(ack_rc --ack-qc 'label_empty=x')" -eq 2
check "lower-case ack code: error says malformed"   grep -q "malformed CODE" "$WORK/ack.err"
check "duplicate ack for one code exits 2"          test "$(ack_rc --ack-qc 'LABEL_EMPTY=a' --ack-qc 'LABEL_EMPTY=b')" -eq 2
check "duplicate ack: error says duplicate"         grep -q "duplicate" "$WORK/ack.err"
rm -rf "$WORK/major/repo"
run major --ack-qc "LABEL_EMPTY=line one
## injected heading"
check "newline in ack reason collapsed to one line" grep -q "Acknowledged: line one ## injected heading" "$WORK/major/repo/IMAGING_QC.md"
check "no heading injected by the reason" bash -c "! grep -q '^## injected' '$WORK/major/repo/IMAGING_QC.md'"

# (l) N6: --imaging-qc replaces the search; an empty directory is recorded NOT ASSESSED
mkdir -p "$WORK/emptyqc"
python3 "$SCAFFOLD" --manifest "$WORK/m.csv" --preprocessing-manifest "$WORK/major/preprocessing_manifest.json" \
    --imaging-qc "$WORK/emptyqc" --out "$WORK/eq" --quiet >/dev/null 2>&1
check "--imaging-qc empty dir replaces the search (Major beside manifest not read; exit 0)" test "$?" -eq 0
check "--imaging-qc empty dir: gates NOT ASSESSED" grep -q "check_dataset_profile\`: NOT ASSESSED" "$WORK/eq/IMAGING_QC.md"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
