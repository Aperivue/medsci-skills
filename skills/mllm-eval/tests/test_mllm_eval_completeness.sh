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

# --- F2 (wrong-sense keywords): an everyday sense of a keyword must not clear a Major check.
#     Each case is a plan complete on every other axis plus one wrong-sense sentence. ---
BASE="We evaluate on MIMIC-CXR with BLEU and RadGraph-F1. A blinded reader study is performed. Hallucination rate is measured by atomic facts. The prompt, temperature 0 and 3 runs are reported."
REF="The reference standard is set by two radiologists."
CAN="Contamination was probed with a canary."
sense(){ # label verdict text...   -> exactly that verdict, exit 1
  local l="$1" v="$2"; shift 2
  printf '%s\n' "$@" > "$TMP/sense.md"
  python3 "$DET" --plan "$TMP/sense.md" --task report_generation --out "$OUT" --strict --quiet >/dev/null 2>&1
  check "SENSE: $l exits 1" test "$?" -eq 1
  check "SENSE: $l -> only $v" python3 -c "import json;d=json.load(open('$OUT'));assert [c['verdict'] for c in d['claims']]==['$v'],d['claims']"
}
sense "'original clinical reports (reference reports)'" REFERENCE_STANDARD_MISSING "$BASE" "$CAN" \
  "Generated reports are compared with the original clinical reports (reference reports)."
sense "'Ground truth is the single original report'" REFERENCE_STANDARD_MISSING "$BASE" "$CAN" \
  "Ground truth is the single original report."
sense "'held-out test split of MIMIC-CXR' (public)" CONTAMINATION_UNADDRESSED "$BASE" "$REF" \
  "We use the held-out test split of MIMIC-CXR."
sense "'patient-level split prevented data leakage'" CONTAMINATION_UNADDRESSED "$BASE" "$REF" \
  "A patient-level split prevented data leakage."
sense "'patient-level split prevented test-set leakage'" CONTAMINATION_UNADDRESSED "$BASE" "$REF" \
  "A patient-level split prevented test-set leakage."
sense "'to avoid test set leakage'" CONTAMINATION_UNADDRESSED "$BASE" "$REF" \
  "Studies were split by patient to avoid test set leakage."
sense "'green arrows' is not the GREEN metric" NGRAM_ONLY \
  "We evaluate on MIMIC-CXR with BLEU. Findings are shown with green arrows. A blinded reader study is performed. Hallucination rate is measured by atomic facts." \
  "$REF" "$CAN" "The prompt, temperature 0 and 3 runs are reported."
sense "'Unsupported image formats were excluded'" FAITHFULNESS_MISSING \
  "We evaluate on MIMIC-CXR with BLEU and RadGraph-F1. Unsupported image formats were excluded. A blinded reader study is performed." \
  "$REF" "$CAN" "The prompt, temperature 0 and 3 runs are reported."
printf '%s\n' "We evaluate on MIMIC-CXR with BLEU and RadGraph-F1. Hallucination rate via atomic facts. A blinded reader study is performed." \
  "$REF" "$CAN" "Random sampling of 200 studies; the prompt is given; bootstrap 95% CIs." > "$TMP/sense.md"
python3 "$DET" --plan "$TMP/sense.md" --task report_generation --out "$OUT" --quiet >/dev/null 2>&1
check "SENSE: 'random sampling' / 'bootstrap CIs' are not decoding / multi-run" detail PROMPT_PROVENANCE_MISSING "temperature/seed, multi-run variance"
# negative controls: the expert-backed / private / pretraining / metric senses still clear.
ctl(){ # label text...   -> exit 0, no claims
  local l="$1"; shift
  printf '%s\n' "$@" > "$TMP/ctl.md"
  python3 "$DET" --plan "$TMP/ctl.md" --task report_generation --out "$OUT" --strict --quiet >/dev/null 2>&1
  check "SENSE control: $l exits 0" test "$?" -eq 0
  check "SENSE control: $l has no claims" python3 -c "import json;d=json.load(open('$OUT'));assert d['claims']==[],d['claims']"
}
ctl "'ground truth annotated by radiologists'" "$BASE" "$CAN" "Ground truth labels were annotated by two board-certified radiologists."
ctl "'reference reports rewritten by radiologists'" "$BASE" "$CAN" "Reference reports were rewritten by three thoracic radiologists."
ctl "'held-out internal test set'" "$BASE" "$REF" "Evaluation uses a held-out internal test set from our hospital."
ctl "'data leakage into the pretraining corpus'" "$BASE" "$REF" "We checked for data leakage of the benchmark into the pretraining corpus."
ctl "'benchmark leakage' (benchmark seen in training)" "$BASE" "$REF" "We assessed benchmark leakage for MIMIC-CXR."
ctl "GREEN score / unsupported findings / nucleus sampling / variance" \
  "We evaluate on MIMIC-CXR with BLEU and the GREEN score. A blinded reader study is performed. Unsupported findings per report are counted." \
  "$REF" "$CAN" "The prompt, nucleus sampling settings and variance across runs are reported."

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"; exit "$fail"
