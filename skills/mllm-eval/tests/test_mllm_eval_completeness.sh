#!/usr/bin/env bash
# Regression test for the MLLM-evaluation completeness gate (mllm-eval). Synthetic, PII-free.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DET="$HERE/../scripts/check_mllm_eval_completeness.py"
F="$HERE/../scripts/mllm_eval_completeness_challenge/fixture"
OUT="$(mktemp -t mec_XXXX).json"; trap 'rm -f "$OUT"' EXIT
fail=0
check(){ local l="$1"; shift; if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$l"; else printf '  FAIL  %s\n' "$l"; fail=$((fail+1)); fi; }
has(){ python3 -c "import json;d=json.load(open('$OUT'));assert any(c['verdict']=='$1' for c in d['claims']),'$1'"; }
no(){ python3 -c "import json;d=json.load(open('$OUT'));assert not any(c['verdict']=='$1' for c in d['claims']),'$1'"; }
[[ -f "$DET" ]] || { echo "ENV-ERR" >&2; exit 2; }

python3 "$DET" --plan "$F/plan_bad.md" --task report_generation --out "$OUT" --strict --quiet >/dev/null 2>&1
check "plan_bad exits 1" test "$?" -eq 1
check "NGRAM_ONLY" has NGRAM_ONLY
check "FAITHFULNESS_MISSING" has FAITHFULNESS_MISSING
check "REFERENCE_STANDARD_MISSING" has REFERENCE_STANDARD_MISSING
check "CONTAMINATION_UNADDRESSED" has CONTAMINATION_UNADDRESSED
python3 "$DET" --plan "$F/plan_good.md" --task report_generation --out "$OUT" --strict --quiet >/dev/null 2>&1
check "plan_good exits 0" test "$?" -eq 0
check "plan_good no NGRAM_ONLY" no NGRAM_ONLY
check "plan_good no FAITHFULNESS_MISSING" no FAITHFULNESS_MISSING

# vqa task: a bare VQA-RAD accuracy plan -> CONTAMINATION + FAITHFULNESS + ANSWER_MATCHING
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"; rm -f "$OUT"' EXIT
printf 'We report accuracy on VQA-RAD.\n' > "$TMP/vqa.md"
python3 "$DET" --plan "$TMP/vqa.md" --task vqa --out "$OUT" --strict --quiet >/dev/null 2>&1
check "vqa bare plan exits 1" test "$?" -eq 1
check "vqa FAITHFULNESS_MISSING" has FAITHFULNESS_MISSING
check "vqa CONTAMINATION_UNADDRESSED" has CONTAMINATION_UNADDRESSED
check "vqa ANSWER_MATCHING_MISSING" has ANSWER_MATCHING_MISSING

# --- false-positive robustness (folded from adversarial review): a complete plan stated in
#     non-canonical vocabulary must PASS (knowledge cutoff / gold standard / graded-on-scale /
#     groundedness / semantic match). ---
cat > "$TMP/good_vocab.md" <<'MD'
We evaluate the model on SLAKE. The reference is the original board-certified radiologists' reports
(the gold standard). Quality uses RadGraph-F1 and CheXbert-F1 with 95% CIs. Groundedness is assessed
(each statement supported vs unsupported by the image); a false-premise probe gives a hallucination rate.
Contamination is controlled against the model's knowledge cutoff versus the benchmark release. Three
radiologists graded outputs on an acceptability scale (masked). We disclose the prompt, temperature and
seed, and report mean +/- SD across 3 runs. Free-text answers were scored by clinician-adjudicated
semantic equivalence.
MD
python3 "$DET" --plan "$TMP/good_vocab.md" --task report_generation --out "$OUT" --strict --quiet >/dev/null 2>&1
check "FP: complete plan in non-canonical vocabulary passes (exit 0)" test "$?" -eq 0

# --- manifest mode: declared fields instead of prose keywords ----------------------------
python3 "$DET" --manifest "$F/manifest_bad.json" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "manifest_bad exits 1" test "$?" -eq 1
for v in NGRAM_ONLY FAITHFULNESS_MISSING REFERENCE_STANDARD_MISSING CONTAMINATION_UNADDRESSED; do
  check "manifest_bad $v" has "$v"
done
check "manifest_bad READER_STUDY_MISSING is Major (deployment claim)" python3 -c "import json;d=json.load(open('$OUT'));assert any(c['verdict']=='READER_STUDY_MISSING' and c['severity']=='Major' for c in d['claims'])"
python3 "$DET" --manifest "$F/manifest_good.json" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "manifest_good exits 0" test "$?" -eq 0
check "manifest_good mode=manifest" python3 -c "import json;assert json.load(open('$OUT'))['mode']=='manifest'"

# the prose Known limits, declared as fields: a reader study that was not done, faithfulness
# not assessed, a patient-split 'leakage' that is not a contamination control
mk(){ python3 - "$F/manifest_good.json" "$TMP/m.json" "$1" <<'PY'
import json, sys
m = json.load(open(sys.argv[1]))
exec(sys.argv[3])
json.dump(m, open(sys.argv[2], "w"))
PY
}
run(){ python3 "$DET" --manifest "$TMP/m.json" --out "$OUT" --strict --quiet >/dev/null 2>&1; }
mk 'm["reader_study"]={"performed": False}; m["claims"]["clinical_deployment"]=True'; run
check "reader study declared not performed + deployment -> exit 1" test "$?" -eq 1
check "  READER_STUDY_MISSING" has READER_STUDY_MISSING
mk 'm["faithfulness"]={"methods": "none"}'; run
check "faithfulness declared none -> FAITHFULNESS_MISSING" has FAITHFULNESS_MISSING
mk 'del m["contamination"]'; run
check "benchmark without contamination methods -> CONTAMINATION_UNADDRESSED" has CONTAMINATION_UNADDRESSED
mk 'm["benchmarks"]=[]; del m["contamination"]'; run
check "no benchmark -> no contamination check" no CONTAMINATION_UNADDRESSED

# allow-list: unknown values exit 2; other:<description> is accepted with a Minor note
mk 'm["metrics"]["clinical"]=["bertscore"]'; run
check "unlisted value without other: exits 2" test "$?" -eq 2
mk 'm["metrics"]["clinical"]=["other: BERTScore against radiologist reports"]'; run
check "other:<description> exits 0" test "$?" -eq 0
check "  UNLISTED_METHOD reported" has UNLISTED_METHOD
check "  other: counts as a clinical metric" no NGRAM_ONLY
mk 'm["metrics"]["clinical"]=["other:"]'; run
check "empty other: exits 2" test "$?" -eq 2
mk 'm["faithfulness"]={"methods": ["none", "atomic_fact_decomposition"]}'; run
check "'none' mixed with a method exits 2" test "$?" -eq 2
mk 'm["reader_study"]["performed"]="yes"'; run
check "non-boolean reader_study.performed exits 2" test "$?" -eq 2
mk 'm["faithfullness"]=m.pop("faithfulness")'; run
check "misspelled top-level key exits 2" test "$?" -eq 2
mk 'm["runs"]={"n": 0}'; run
check "runs.n = 0 exits 2" test "$?" -eq 2
mk 'm["Reference-Standard"]=1' ; run
check "unknown key with other spelling exits 2" test "$?" -eq 2
mk 'm["metrics"]["clinical"]=["RadGraph-F1", "CheXbert F1"]'; run
check "case and separators are normalised" test "$?" -eq 0
mk 'm["runs"]={"n": 1}'; run
check "fewer than 3 runs -> PROMPT_PROVENANCE_MISSING (Minor, exit 0)" test "$?" -eq 0
check "  PROMPT_PROVENANCE_MISSING" has PROMPT_PROVENANCE_MISSING
mk 'del m["task"]'; run
check "manifest without task and no --task exits 2" test "$?" -eq 2
python3 "$DET" --manifest "$TMP/m.json" --task vqa --out "$OUT" --quiet >/dev/null 2>&1
check "  ... --task supplies it" test "$?" -eq 0
check "  vqa with answer_matching none -> ANSWER_MATCHING_MISSING" has ANSWER_MATCHING_MISSING
python3 "$DET" --manifest "$F/manifest_good.json" --task vqa --quiet >/dev/null 2>&1
check "--task that contradicts the manifest exits 2" test "$?" -eq 2
printf '[1, 2]' > "$TMP/arr.json"
python3 "$DET" --manifest "$TMP/arr.json" --quiet >/dev/null 2>&1
check "non-object manifest exits 2" test "$?" -eq 2
printf '{"task": ' > "$TMP/broken.json"
python3 "$DET" --manifest "$TMP/broken.json" --quiet >/dev/null 2>&1
check "invalid JSON exits 2" test "$?" -eq 2

# reference standard: only an adjudicated expert reference clears it (SKILL.md Phase 2)
mk 'm["reference_standard"]={"type": "model-derived label"}'; run
check "model-derived label -> REFERENCE_STANDARD_MISSING" has REFERENCE_STANDARD_MISSING
# reader study must be blinded (evaluation_axes.md ME7)
mk 'm["reader_study"]={"performed": True, "blinded": False}; m["claims"]["clinical_deployment"]=True'; run
check "unblinded reader study + deployment -> exit 1" test "$?" -eq 1
mk 'm["reader_study"]={"performed": True}'; run
check "reader study without declared blinding -> READER_STUDY_MISSING" has READER_STUDY_MISSING
# task cannot be other:, benchmarks may be a string or "none"
mk 'm["task"]="other: report summarisation"'; run
check "task other: exits 2" test "$?" -eq 2
mk 'm["benchmarks"]="none"; del m["contamination"]'; run
check "benchmarks 'none' -> no contamination check" no CONTAMINATION_UNADDRESSED
mk 'm["benchmarks"]="MIMIC-CXR"; del m["contamination"]'; run
check "benchmarks as one string -> CONTAMINATION_UNADDRESSED" has CONTAMINATION_UNADDRESSED
mk 'm["answer_matching"]={"method": "Normalized"}; m["task"]="vqa"'; run
check "US spelling 'normalized' is accepted" no ANSWER_MATCHING_MISSING
mk 'm["metrics"]["clinical"]=["Other : BERTScore"]'; run
check "'Other : x' is read as other:" has UNLISTED_METHOD
printf '{"task": "vqa", "decoding": {"temperature": Infinity}}' > "$TMP/inf.json"
python3 "$DET" --manifest "$TMP/inf.json" --quiet >/dev/null 2>&1
check "Infinity exits 2" test "$?" -eq 2
python3 -c "print('{\"notes\":'+'['*100000+']'*100000+'}')" > "$TMP/deep.json"
python3 "$DET" --manifest "$TMP/deep.json" --task vqa --quiet >/dev/null 2>&1
check "deeply nested JSON exits 2" test "$?" -eq 2
python3 "$DET" --manifest "" --plan "$F/plan_good.md" --task vqa --quiet >/dev/null 2>&1
check "--manifest '' exits 2 (not prose mode)" test "$?" -eq 2

python3 -c "print('{\"task\":\"vqa\",\"runs\":{\"n\":'+'9'*5000+'}}')" > "$TMP/big.json"
python3 "$DET" --manifest "$TMP/big.json" --quiet >/dev/null 2>&1
check "5000-digit integer exits 2" test "$?" -eq 2
printf '{"task": "vqa", "decoding": {"temperature": 1e999}}' > "$TMP/huge.json"
python3 "$DET" --manifest "$TMP/huge.json" --quiet >/dev/null 2>&1
check "temperature 1e999 (inf) exits 2" test "$?" -eq 2
mk 'm["metrics"]["clinical"]="none"; m["metrics"]["lexical"]=["ROUGE-L"]'; run
check "ROUGE-L is read as rouge (NGRAM_ONLY)" has NGRAM_ONLY
mk 'm["faithfulness"]={"methods": "other: none"}'; run
check "'other: none' is read as none" has FAITHFULNESS_MISSING

python3 -c "print('{\"task\":\"vqa\",\"decoding\":{\"temperature\":1'+'0'*400+'}}')" > "$TMP/hugeint.json"
python3 "$DET" --manifest "$TMP/hugeint.json" --quiet >/dev/null 2>&1
check "400-digit integer temperature does not crash (exit 0, finite)" test "$?" -eq 0

# with --manifest the prose plan is not read; with neither, or --plan without --task, exit 2
python3 "$DET" --manifest "$F/manifest_good.json" --plan "$F/plan_bad.md" --strict --quiet >/dev/null 2>&1
check "--manifest wins over --plan" test "$?" -eq 0
python3 "$DET" --quiet >/dev/null 2>&1
check "no input exits 2" test "$?" -eq 2
python3 "$DET" --plan "$F/plan_good.md" --quiet >/dev/null 2>&1
check "--plan without --task exits 2" test "$?" -eq 2

# prose mode says what it is
python3 "$DET" --plan "$F/plan_good.md" --task report_generation --out "$OUT" > "$TMP/prose.txt" 2>&1
check "prose mode prints the PROSE_MODE notice" grep -q '^PROSE_MODE:' "$TMP/prose.txt"
check "prose mode JSON mode=prose" python3 -c "import json;assert json.load(open('$OUT'))['mode']=='prose'"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"; exit "$fail"
