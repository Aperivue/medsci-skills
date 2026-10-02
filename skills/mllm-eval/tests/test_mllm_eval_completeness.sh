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

# --- Negation is bounded to the concept's own phrase (review counterexamples). An unrelated
#     negation earlier in the same sentence, a relative clause, a negated property or a negated
#     result must NOT cancel an affirmative mention: a plan covering every axis stays clean. ---
cat > "$TMP/scope_repro.md" <<'MD'
We evaluate on MIMIC-CXR with BLEU and RadGraph-F1. Studies without prior imaging were adjudicated by two radiologists to form the reference standard. A blinded reader study is performed. Reports with no acute findings were also checked for hallucinations by atomic-fact decomposition. Because the training data are not public, contamination was probed with a canary. The prompt, temperature 0 and 3 runs are reported.
MD
python3 "$DET" --plan "$TMP/scope_repro.md" --task report_generation --out "$OUT" --strict --quiet >/dev/null 2>&1
check "SCOPE control: unrelated negation earlier in the sentence does not cancel (exit 0)" test "$?" -eq 0
check "SCOPE control: no REFERENCE_STANDARD_MISSING ('Studies without prior imaging were adjudicated')" no REFERENCE_STANDARD_MISSING
check "SCOPE control: no FAITHFULNESS_MISSING ('Reports with no acute findings ... hallucinations')" no FAITHFULNESS_MISSING
check "SCOPE control: no CONTAMINATION_UNADDRESSED ('data are not public, contamination was probed')" no CONTAMINATION_UNADDRESSED
BASE="We evaluate on MIMIC-CXR with BLEU and RadGraph-F1. The reference standard is adjudicated by two radiologists. A blinded reader study is performed. Contamination was probed with a canary. The prompt, temperature 0 and 3 runs are reported."
printf '%s\n' "$BASE" "Faithfulness, which was not part of prior work, is assessed via atomic facts." > "$TMP/scope_rel.md"
python3 "$DET" --plan "$TMP/scope_rel.md" --task report_generation --out "$OUT" --strict --quiet >/dev/null 2>&1
check "SCOPE control: relative clause 'which was not part of prior work' does not cancel (exit 0)" test "$?" -eq 0
check "SCOPE control: relative clause -> no FAITHFULNESS_MISSING" no FAITHFULNESS_MISSING
printf '%s\n' "We evaluate on MIMIC-CXR with BLEU and RadGraph-F1. Expert review is not blinded. A blinded reader study is performed; the reader study did not include trainees. Contamination was probed with a canary. Hallucination rate was not significantly different between models. No more than 5 runs were needed; the prompt and temperature 0 are reported." > "$TMP/scope_prop.md"
python3 "$DET" --plan "$TMP/scope_prop.md" --task report_generation --out "$OUT" --strict --quiet >/dev/null 2>&1
check "SCOPE control: negated property / negated result / 'no more than' do not cancel (exit 0)" test "$?" -eq 0
check "SCOPE control: no PROMPT_PROVENANCE_MISSING ('No more than 5 runs')" no PROMPT_PROVENANCE_MISSING
# --- Negations without an auxiliary verb (label, table cell, "none", "out of scope") withdraw the axis. ---
for form in "Hallucination: not assessed." "| Hallucination | not evaluated |" "Hallucination assessment: none." "Hallucination evaluation is out of scope."; do
  printf '%s\n\n%s\n' "$BASE" "$form" > "$TMP/label_neg.md"
  python3 "$DET" --plan "$TMP/label_neg.md" --task report_generation --out "$OUT" --strict --quiet >/dev/null 2>&1
  check "LABEL-NEG: '$form' exits 1" test "$?" -eq 1
  check "LABEL-NEG: '$form' -> FAITHFULNESS_MISSING" has FAITHFULNESS_MISSING
done
printf '%s\n' "$BASE" "Hallucination: none detected by atomic-fact checking." > "$TMP/label_ctl.md"
python3 "$DET" --plan "$TMP/label_ctl.md" --task report_generation --out "$OUT" --strict --quiet >/dev/null 2>&1
check "LABEL-NEG control: 'Hallucination: none detected' is a result (exit 0)" test "$?" -eq 0

# --- Negation scope is the concept's own noun phrase, whatever the verb (round-2 review
#     counterexamples). A negator separated from the concept by a lexical verb ("underwent",
#     "received", "required"), a modal ("will undergo", "can receive"), a preposition ("edited
#     before", "examples in the prompt"), a relative clause or a list does NOT cancel it. ---
cat > "$TMP/scope_verb.md" <<'MD'
We evaluate on MIMIC-CXR with BLEU and RadGraph-F1. Studies without IV contrast underwent expert review by two radiologists. A blinded reader study is performed. Reports were not edited before hallucination assessment. Contamination was probed with a canary. The prompt, temperature 0 and 3 runs are reported.
MD
python3 "$DET" --plan "$TMP/scope_verb.md" --task report_generation --out "$OUT" --strict --quiet >/dev/null 2>&1
check "SCOPE-VERB control: 'without IV contrast underwent expert review' / 'not edited before hallucination' (exit 0)" test "$?" -eq 0
check "SCOPE-VERB control: no REFERENCE_STANDARD_MISSING" no REFERENCE_STANDARD_MISSING
check "SCOPE-VERB control: no FAITHFULNESS_MISSING" no FAITHFULNESS_MISSING
# Generated controls: each axis is named exactly once, right after an unrelated negation that
# sits behind a modal, a lexical verb, a relative clause, a preposition or a list.
cat > "$TMP/scope_gen1.md" <<'MD'
We evaluate on MIMIC-CXR with BLEU and RadGraph-F1. Studies without contrast will undergo expert review.
Reports lacking findings must undergo hallucination audit. Readers did not know the model identity
during the blinded reader study. Without access to the weights we still probe contamination with a
canary. We use no few-shot examples in the prompt; temperature 0 and 3 runs are reported.
MD
cat > "$TMP/scope_gen2.md" <<'MD'
We evaluate on MIMIC-CXR with BLEU and RadGraph-F1. Patients who had no prior CT underwent expert review.
For No Finding studies hallucination is assessed via atomic facts. We do not claim deployment; a blinded
reader study is performed. Models were not fine-tuned, so contamination is probed with a canary. The
prompt, temperature 0 and 3 runs are reported.
MD
cat > "$TMP/scope_gen3.md" <<'MD'
We evaluate on MIMIC-CXR with BLEU and RadGraph-F1.
- No-finding studies: reference standard adjudicated by two radiologists.
- Exclusions: no prior imaging, no implants; negative studies with no pathology underwent hallucination audit.
- Cases with no follow-up can receive a blinded reader study.
- Because the training data are not public, contamination was probed with a canary.
- The prompt, temperature 0 and 3 runs are reported.
MD
for g in scope_gen1 scope_gen2 scope_gen3; do
  python3 "$DET" --plan "$TMP/$g.md" --task report_generation --out "$OUT" --strict --quiet >/dev/null 2>&1
  check "SCOPE-GEN control: $g (unrelated negation behind a verb / clause / list) exits 0" test "$?" -eq 0
  check "SCOPE-GEN control: $g has no claims" python3 -c "import json;d=json.load(open('$OUT'));assert d['claims']==[],d['claims']"
done
# --- More withdrawal forms: a determiner negator, a negated do-verb, a dash or parenthesis label,
#     "beyond our scope", "was skipped". Each withdraws its axis from an otherwise complete plan. ---
BASE_ALL="We evaluate on MIMIC-CXR with BLEU and RadGraph-F1."
for pair in \
  "FAITHFULNESS_MISSING|The study lacks any formal hallucination evaluation." \
  "FAITHFULNESS_MISSING|We did not evaluate hallucination." \
  "FAITHFULNESS_MISSING|Faithfulness is beyond our scope." \
  "FAITHFULNESS_MISSING|Hallucination evaluation was skipped." \
  "REFERENCE_STANDARD_MISSING|Expert review — not performed." \
  "REFERENCE_STANDARD_MISSING|We do not have an expert reference standard." \
  "CONTAMINATION_UNADDRESSED|Contamination (not assessed)." \
  "READER_STUDY_MISSING|We did not perform any kind of formal blinded reader study." \
  "REFERENCE_STANDARD_MISSING|The reference standard and expert review were not performed."; do
  v="${pair%%|*}"; form="$(printf '%b' "${pair#*|}")"
  {
    printf '%s\n' "$BASE_ALL"
    [[ "$v" == REFERENCE_STANDARD_MISSING ]] || printf '%s\n' "The reference standard is adjudicated by two radiologists."
    [[ "$v" == READER_STUDY_MISSING ]] || printf '%s\n' "A blinded reader study is performed."
    [[ "$v" == FAITHFULNESS_MISSING ]] || printf '%s\n' "Hallucination is assessed via atomic facts."
    [[ "$v" == CONTAMINATION_UNADDRESSED ]] || printf '%s\n' "Contamination was probed with a canary."
    printf '%s\n' "The prompt, temperature 0 and 3 runs are reported." "$form"
  } > "$TMP/withdraw.md"
  python3 "$DET" --plan "$TMP/withdraw.md" --task report_generation --out "$OUT" --quiet >/dev/null 2>&1
  check "WITHDRAW: '$form' -> $v" has "$v"
  check "WITHDRAW: '$form' -> only $v" python3 -c "import json;d=json.load(open('$OUT'));assert [c['verdict'] for c in d['claims']]==['$v'],d['claims']"
done

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"; exit "$fail"
