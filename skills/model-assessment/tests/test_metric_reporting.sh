#!/usr/bin/env bash
# Regression test for the metric-reporting gate (model-assessment). Synthetic, PII-free.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DET="$HERE/../scripts/check_metric_reporting.py"
F="$HERE/../scripts/metric_reporting_challenge/fixture"
OUT="$(mktemp -t mr_XXXX).json"; trap 'rm -f "$OUT"' EXIT
fail=0
check(){ local l="$1"; shift; if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$l"; else printf '  FAIL  %s\n' "$l"; fail=$((fail+1)); fi; }
has(){ python3 -c "import json;d=json.load(open('$OUT'));assert any(c['verdict']=='$1' for c in d['claims']),'$1'"; }
no(){ python3 -c "import json;d=json.load(open('$OUT'));assert not any(c['verdict']=='$1' for c in d['claims']),'$1'"; }
[[ -f "$DET" ]] || { echo "ENV-ERR" >&2; exit 2; }

python3 "$DET" --report "$F/seg_bad.md" --task segmentation --out "$OUT" --strict --quiet >/dev/null 2>&1
check "seg_bad exits 1" test "$?" -eq 1
check "NO_BOUNDARY_METRIC" has NO_BOUNDARY_METRIC
check "PIXEL_ACCURACY_SEG" has PIXEL_ACCURACY_SEG
python3 "$DET" --report "$F/seg_good.md" --task segmentation --out "$OUT" --strict --quiet >/dev/null 2>&1
check "seg_good exits 0" test "$?" -eq 0
check "seg_good no NO_BOUNDARY_METRIC" no NO_BOUNDARY_METRIC
python3 "$DET" --report "$F/clf_bad.md" --task classification --out "$OUT" --strict --quiet >/dev/null 2>&1
check "clf_bad exits 1 (ACCURACY_ONLY)" test "$?" -eq 1
check "ACCURACY_ONLY" has ACCURACY_ONLY
python3 "$DET" --report "$F/clf_good.md" --task classification --out "$OUT" --strict --quiet >/dev/null 2>&1
check "clf_good exits 0" test "$?" -eq 0
check "clf_good no CI_MISSING (CIs present)" no CI_MISSING

# --- false-positive robustness (folded from adversarial review): good reports must pass ---
W="$(mktemp -d)"; trap 'rm -rf "$W"; rm -f "$OUT"' EXIT
ok0() { python3 "$DET" --report "$1" --task "$2" --strict --quiet >/dev/null 2>&1; }
printf 'Detection: FROC; a hit required IoU with the lesion >= 0.3, with 95%% CI.\n' > "$W/det1.md"
check "FP: detection 'IoU ... >= 0.3' passes" ok0 "$W/det1.md" detection
printf 'mAP with overlap >= 0.5 as the match criterion, 95%% CI.\n' > "$W/det2.md"
check "FP: detection 'overlap >= 0.5' passes" ok0 "$W/det2.md" detection
printf 'Dice 0.81 and Surface DSC 0.92, with 95%% CIs.\n' > "$W/sdsc.md"
check "FP: segmentation 'Surface DSC' passes" ok0 "$W/sdsc.md" segmentation
printf 'We do NOT report pixel accuracy; instead Dice, HD95, ASSD with 95%% CIs.\n' > "$W/neg.md"
check "FP: 'do NOT report pixel accuracy' passes" ok0 "$W/neg.md" segmentation
printf 'This diagnostic accuracy study reports sensitivity 0.83 and specificity 0.90 (95%% CI).\n' > "$W/dx.md"
check "FP: 'diagnostic accuracy' study phrase + sens/spec passes" ok0 "$W/dx.md" classification
# boundary metric must be NAMED and affirmed: the bare word 'boundary' or a disavowed HD95 does
# not pair with Dice (Metrics Reloaded); a negation in an earlier clause does not disavow it.
printf 'Test-set Dice was 0.86 (95%% CI 0.83-0.88). Boundary error was not assessed.\n' > "$W/bword.md"
python3 "$DET" --report "$W/bword.md" --task segmentation --out "$OUT" --quiet >/dev/null 2>&1
check "bare word 'boundary' does not count as a boundary metric" has NO_BOUNDARY_METRIC
printf 'Dice 0.86 (95%% CI 0.83-0.88); HD95 was not computed.\n' > "$W/bneg.md"
python3 "$DET" --report "$W/bneg.md" --task segmentation --out "$OUT" --quiet >/dev/null 2>&1
check "'HD95 was not computed' -> NO_BOUNDARY_METRIC" has NO_BOUNDARY_METRIC
printf 'Pixel accuracy was not used; Dice 0.81 and HD95 7.2 mm (95%% CI 6.1-8.3).\n' > "$W/bclause.md"
check "FP: negation in an earlier clause leaves HD95 affirmed" ok0 "$W/bclause.md" segmentation
printf 'Dice 0.81 and Boundary IoU 0.62, with 95%% CIs.\n' > "$W/biou.md"
check "FP: 'Boundary IoU' is a boundary metric" ok0 "$W/biou.md" segmentation
# negation: 'AUROC was not computed' -> the real ACCURACY_ONLY, no spurious AUPRC_MISSING
printf 'Classification accuracy 0.92; AUROC was not computed.\n' > "$W/aur.md"
python3 "$DET" --report "$W/aur.md" --task classification --out "$OUT" --quiet >/dev/null 2>&1
check "negation: 'AUROC was not computed' -> ACCURACY_ONLY" has ACCURACY_ONLY
check "negation: no spurious AUPRC_MISSING" no AUPRC_MISSING

# --- interactive / promptable segmentation ---
python3 "$DET" --report "$F/interactive_bad.md" --task interactive --out "$OUT" --strict --quiet >/dev/null 2>&1
check "interactive_bad exits 1" test "$?" -eq 1
check "INTERACTIVE_NO_INTERACTION_COUNT" has INTERACTIVE_NO_INTERACTION_COUNT
check "interactive_bad also flags NO_BOUNDARY_METRIC (still segmentation)" has NO_BOUNDARY_METRIC
check "interactive_bad flags INTERACTIVE_NO_TIME" has INTERACTIVE_NO_TIME
python3 "$DET" --report "$F/interactive_good.md" --task interactive --out "$OUT" --strict --quiet >/dev/null 2>&1
check "interactive_good exits 0" test "$?" -eq 0
check "interactive_good no INTERACTIVE_NO_INTERACTION_COUNT" no INTERACTIVE_NO_INTERACTION_COUNT
check "interactive_good no INTERACTIVE_NO_CONVERGENCE" no INTERACTIVE_NO_CONVERGENCE
check "interactive_good no NO_BOUNDARY_METRIC" no NO_BOUNDARY_METRIC
# FP guard: a static (non-interactive) segmentation report is NOT run under --task interactive,
# and a full interactive report must not spuriously fire the interaction verdicts.
printf 'Interactive tumor segmentation: Dice rose from an initial-click Dice 0.55 to a peak Dice 0.90 (95%% CI 0.88-0.92); HD95 5.1 mm; median 3 clicks to threshold; interaction time 30 s/case.\n' > "$W/int_ok.md"
check "FP: full interactive one-liner passes --strict" ok0 "$W/int_ok.md" interactive
# dogfood regression (nnInteractive, arXiv 2503.08373): timing written as "N seconds" / "N ms"
# — not the literal phrase "inference time" — must still satisfy the interaction-time check.
printf 'Interactive segmentation: number of clicks to threshold, converged Dice, HD95 6 mm; per case 179±114 seconds and 120-200 ms per structure.\n' > "$W/int_time.md"
python3 "$DET" --report "$W/int_time.md" --task interactive --out "$OUT" --quiet >/dev/null 2>&1
check "dogfood: 'N seconds' / 'N ms' timing -> no INTERACTIVE_NO_TIME" no INTERACTIVE_NO_TIME

# --- generative / synthesis ---
python3 "$DET" --report "$F/generative_bad.md" --task generative --out "$OUT" --strict --quiet >/dev/null 2>&1
check "generative_bad exits 1 (no downstream)" test "$?" -eq 1
check "GENERATIVE_NO_DOWNSTREAM" has GENERATIVE_NO_DOWNSTREAM
python3 "$DET" --report "$F/generative_good.md" --task generative --out "$OUT" --strict --quiet >/dev/null 2>&1
check "generative_good exits 0 (downstream task present)" test "$?" -eq 0
check "generative_good no GENERATIVE_NO_DOWNSTREAM" no GENERATIVE_NO_DOWNSTREAM
# FP guard: a synthesis report that names no similarity metric is flagged NO_SIMILARITY, not DOWNSTREAM
printf 'We generated synthetic MRI and evaluated a downstream tumor-segmentation Dice of 0.88 on the synthesized images (95%% CI 0.85-0.90).\n' > "$W/gen_down_only.md"
python3 "$DET" --report "$W/gen_down_only.md" --task generative --out "$OUT" --quiet >/dev/null 2>&1
check "generative downstream-only -> GENERATIVE_NO_SIMILARITY not DOWNSTREAM" has GENERATIVE_NO_SIMILARITY
check "generative downstream-only -> no GENERATIVE_NO_DOWNSTREAM" no GENERATIVE_NO_DOWNSTREAM

# --- multiclass classification ---
python3 "$DET" --report "$F/multiclass_bad.md" --task classification --out "$OUT" --quiet >/dev/null 2>&1
check "MULTICLASS_NO_AVERAGING" has MULTICLASS_NO_AVERAGING
# FP guard: a multiclass report that states its aggregation scheme must NOT fire the verdict
printf 'Three-class classification: one-vs-rest macro-averaged AUROC 0.90 and AUPRC 0.71 (95%% CI).\n' > "$W/mc_ok.md"
python3 "$DET" --report "$W/mc_ok.md" --task classification --out "$OUT" --quiet >/dev/null 2>&1
check "FP: multiclass with one-vs-rest macro-average -> no MULTICLASS_NO_AVERAGING" no MULTICLASS_NO_AVERAGING

# --- F3: false clearances of NO_BOUNDARY_METRIC / ACCURACY_ONLY ---
# the Medical Segmentation Decathlon name 'MSD' is not mean surface distance
printf 'We trained on the MSD liver task. Mean Dice was 0.91 (95%% CI 0.89-0.93).\n' > "$W/msd_ds.md"
python3 "$DET" --report "$W/msd_ds.md" --task segmentation --out "$OUT" --quiet >/dev/null 2>&1
check "F3: 'MSD liver task' (dataset) -> NO_BOUNDARY_METRIC" has NO_BOUNDARY_METRIC
printf 'Dice 0.91 (95%% CI 0.89-0.93) and MSD 1.2 mm on the MSD liver task.\n' > "$W/msd_val.md"
check "F3 control: 'MSD 1.2 mm' is a boundary metric (passes --strict)" ok0 "$W/msd_val.md" segmentation
# a negation reaches every item of a coordinated list
printf 'Dice was 0.91 (95%% CI 0.89-0.93). We did not compute the Hausdorff distance or HD95.\n' > "$W/neglist.md"
python3 "$DET" --report "$W/neglist.md" --task segmentation --out "$OUT" --quiet >/dev/null 2>&1
check "F3: 'did not compute the Hausdorff distance or HD95' -> NO_BOUNDARY_METRIC" has NO_BOUNDARY_METRIC
printf 'We did not use pixel accuracy, Dice and HD95 were reported (95%% CI).\n' > "$W/neg_own.md"
check "F3 control: negation does not reach an item with its own predicate" ok0 "$W/neg_own.md" segmentation
# a negated sensitivity/specificity pair is not a threshold-pair report
printf 'Accuracy was 92%% (95%% CI 90-94). Sensitivity and specificity were not reported.\n' > "$W/acc_negpair.md"
python3 "$DET" --report "$W/acc_negpair.md" --task classification --out "$OUT" --quiet >/dev/null 2>&1
check "F3: negated sens/spec -> ACCURACY_ONLY" has ACCURACY_ONLY
printf 'Accuracy 92%%, sensitivity and specificity were 0.9 and 0.8 (95%% CI).\n' > "$W/acc_pair.md"
check "F3 control: reported sens/spec pair clears ACCURACY_ONLY" ok0 "$W/acc_pair.md" classification

# --- F4: false clearances of DETECTION_METRIC_MISSING ---
printf 'Lesion-level sensitivity was 0.88 (95%% CI 0.84-0.91). Figure 3 shows a saliency map; a prediction counted as a hit when its overlap of the lesion was any.\n' > "$W/det_map.md"
python3 "$DET" --report "$W/det_map.md" --task detection --out "$OUT" --quiet >/dev/null 2>&1
check "F4: 'saliency map' is not mAP -> DETECTION_METRIC_MISSING" has DETECTION_METRIC_MISSING
printf 'Patient-level sensitivity was 0.88. FROC analysis was not performed. IoU threshold 0.5.\n' > "$W/det_negfroc.md"
python3 "$DET" --report "$W/det_negfroc.md" --task detection --out "$OUT" --quiet >/dev/null 2>&1
check "F4: 'FROC analysis was not performed' -> DETECTION_METRIC_MISSING" has DETECTION_METRIC_MISSING
printf 'mAP@0.5 was 0.71 (95%% CI 0.65-0.77) with IoU threshold 0.5.\n' > "$W/det_map_ok.md"
check "F4 control: 'mAP@0.5' with IoU threshold passes --strict" ok0 "$W/det_map_ok.md" detection

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"; exit "$fail"
