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
detail(){ python3 -c "import json;d=json.load(open('$OUT'));assert any(c['verdict']=='$1' and '$2' in c['detail'] for c in d['claims']),'$1'"; }
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

# --- F1 (negation): a plan that names every axis only to say it was NOT done must not clear.
#     Each concept appears, but negated ("no", "did not", "was not assessed", "are not reported"). ---
cat > "$TMP/negated.md" <<'MD'
We did not use an adjudicated reference standard; no expert review. BLEU-4 and ROUGE-L only; no
RadGraph or CheXbert. Hallucination was not assessed. No contamination check on MIMIC-CXR. No reader
study. The prompt, temperature and number of runs are not reported.
MD
python3 "$DET" --plan "$TMP/negated.md" --task report_generation --out "$OUT" --strict --quiet >/dev/null 2>&1
check "NEG: fully negated plan exits 1" test "$?" -eq 1
check "NEG: NGRAM_ONLY ('no RadGraph or CheXbert')" has NGRAM_ONLY
check "NEG: REFERENCE_STANDARD_MISSING ('did not use an adjudicated')" has REFERENCE_STANDARD_MISSING
check "NEG: FAITHFULNESS_MISSING ('was not assessed')" has FAITHFULNESS_MISSING
check "NEG: CONTAMINATION_UNADDRESSED ('No contamination check')" has CONTAMINATION_UNADDRESSED
check "NEG: READER_STUDY_MISSING ('No reader study')" has READER_STUDY_MISSING
# negative control: affirmative plan using result-negations ("no hallucinations were detected",
# "no evidence of contamination", "was not detected"), "not only", and "no X but Y" must stay clean.
cat > "$TMP/neg_control.md" <<'MD'
We evaluate on SLAKE. The reference standard is set by two radiologists, adjudicated by a third.
We report not only BLEU but also RadGraph-F1 and the GREEN score. Hallucination rate is measured via
atomic facts; no hallucinations were detected in 90% of reports. No evidence of contamination was found
by a canary probe; contamination was not detected. A blinded reader study is performed. We disclose the
prompt, temperature 0 and report mean +/- SD across 3 runs. We use no BLEU-only claim but RadGraph-F1.
MD
python3 "$DET" --plan "$TMP/neg_control.md" --task report_generation --out "$OUT" --strict --quiet >/dev/null 2>&1
check "NEG control: affirmative plan with result-negations passes (exit 0)" test "$?" -eq 0
check "NEG control: no PROMPT_PROVENANCE_MISSING" no PROMPT_PROVENANCE_MISSING

# --- F2 (wrong-sense keywords): everyday senses must not clear a Major check. ---
cat > "$TMP/wrongsense1.md" <<'MD'
Generated reports for MIMIC-CXR are scored with BLEU-4 and ROUGE-L against the original clinical
reports (reference reports). Findings are shown with green arrows. Unsupported claims are discussed as a
limitation. We use the held-out test split of MIMIC-CXR. Experts gave Likert ratings.
MD
python3 "$DET" --plan "$TMP/wrongsense1.md" --task report_generation --out "$OUT" --strict --quiet >/dev/null 2>&1
check "SENSE: wrong-sense plan 1 exits 1" test "$?" -eq 1
check "SENSE: NGRAM_ONLY ('green arrows' is not GREEN)" has NGRAM_ONLY
check "SENSE: REFERENCE_STANDARD_MISSING ('reference reports' = original reports)" has REFERENCE_STANDARD_MISSING
check "SENSE: FAITHFULNESS_MISSING ('unsupported claims' discussed)" has FAITHFULNESS_MISSING
check "SENSE: CONTAMINATION_UNADDRESSED (held-out split of a PUBLIC benchmark)" has CONTAMINATION_UNADDRESSED
cat > "$TMP/wrongsense2.md" <<'MD'
Reports are scored with BLEU against MIMIC-CXR. Ground truth is the single original report. Factuality
is discussed. Random sampling of 200 studies; the prompt is in the appendix; bootstrap 95% CIs.
Patient-level data leakage was prevented. Hallucinations are measured as a rate. Human evaluation planned.
MD
python3 "$DET" --plan "$TMP/wrongsense2.md" --task report_generation --out "$OUT" --strict --quiet >/dev/null 2>&1
check "SENSE: wrong-sense plan 2 exits 1" test "$?" -eq 1
check "SENSE: NGRAM_ONLY ('Factuality is discussed' is not a metric)" has NGRAM_ONLY
check "SENSE: REFERENCE_STANDARD_MISSING ('ground truth' = one original report)" has REFERENCE_STANDARD_MISSING
check "SENSE: CONTAMINATION_UNADDRESSED ('patient-level data leakage' is a split issue)" has CONTAMINATION_UNADDRESSED
check "SENSE: 'random sampling'/'bootstrap' do not satisfy decoding/multi-run" detail PROMPT_PROVENANCE_MISSING "temperature/seed, multi-run variance"
# negative control: the sense-specific phrasings still clear.
cat > "$TMP/sense_control.md" <<'MD'
We evaluate on MIMIC-CXR and an internal held-out set. The reference standard is radiologist consensus.
Quality uses the GREEN score and a factuality metric alongside BLEU. Faithfulness is assessed via atomic
facts. Benchmark leakage into pretraining is probed with a canary. A blinded reader study is performed.
The prompt, nucleus sampling settings and seed are disclosed; results are reported across runs.
MD
python3 "$DET" --plan "$TMP/sense_control.md" --task report_generation --out "$OUT" --strict --quiet >/dev/null 2>&1
check "SENSE control: sense-specific complete plan passes (exit 0)" test "$?" -eq 0
check "SENSE control: no PROMPT_PROVENANCE_MISSING" no PROMPT_PROVENANCE_MISSING

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"; exit "$fail"
