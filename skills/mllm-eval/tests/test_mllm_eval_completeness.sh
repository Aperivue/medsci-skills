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

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"; exit "$fail"
