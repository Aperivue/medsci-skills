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

# --- detection metric controls: every spelling of mean average precision counts,
# also next to a saliency map and after an image-like word (clean on main) ---
for m in "mAP 0.71" "MAP of 0.71" "map@0.5 0.71" "mAP50-95 0.52" "mean average precision 0.71"; do
  printf 'Detection: %s (95%% CI 0.65-0.77), IoU threshold 0.5. Figure 3 shows a saliency map.\n' "$m" > "$W/det_ap.md"
  check "control: '$m' + saliency map passes --strict" ok0 "$W/det_ap.md" detection
done
for m in "The instance segmentation mAP was 0.42" "The confidence mAP was 0.42" \
         "At high density mAP was 0.42" "With attention mAP was 0.42"; do
  printf '%s (95%% CI 0.38-0.46) at an IoU threshold of 0.5.\n' "$m" > "$W/det_ap2.md"
  check "control: '$m' passes --strict" ok0 "$W/det_ap2.md" detection
done
for m in 'The instance segmentation\nmAP was 0.42' 'The mAP\nwas 0.42'; do
  printf "$m"' (95%% CI 0.38-0.46) at an IoU threshold of 0.5.\n' > "$W/det_ap3.md"
  check "control: wrapped '$m' passes --strict" ok0 "$W/det_ap3.md" detection
done

# --- manifest mode: declared metrics instead of prose keywords -----------------------------
mrun(){ python3 "$DET" --manifest "$1" --out "$OUT" --strict --quiet >/dev/null 2>&1; }
mrun "$F/manifest_seg_bad.json"
check "manifest seg_bad exits 1" test "$?" -eq 1
check "  PIXEL_ACCURACY_SEG" has PIXEL_ACCURACY_SEG
check "  NO_BOUNDARY_METRIC" has NO_BOUNDARY_METRIC
check "  mode=manifest" python3 -c "import json;assert json.load(open('$OUT'))['mode']=='manifest'"
mrun "$F/manifest_seg_good.json"
check "manifest seg_good exits 0" test "$?" -eq 0
mrun "$F/manifest_det_no_match.json"
check "manifest detection without match criterion exits 1" test "$?" -eq 1
check "  DETECTION_METRIC_MISSING" has DETECTION_METRIC_MISSING
mrun "$F/manifest_clf_bad.json"
check "manifest accuracy + sensitivity only -> ACCURACY_ONLY" has ACCURACY_ONLY

mj(){ printf '%s' "$1" > "$W/m.json"; mrun "$W/m.json"; }
# the prose Known limits, declared: negated boundary metric, negated FROC, saliency map, Decathlon
mj '{"task":"segmentation","metrics":["dice"],"ci_reported":true}'
check "Dice with no boundary metric declared -> NO_BOUNDARY_METRIC" has NO_BOUNDARY_METRIC
mj '{"task":"detection","metrics":["sensitivity"],"detection":{"match_criterion":"iou_threshold"},"ci_reported":true}'
check "detection with no FROC/mAP declared -> DETECTION_METRIC_MISSING" has DETECTION_METRIC_MISSING
mj '{"task":"detection","metrics":["map"],"detection":{"match_criterion":"IoU threshold","threshold":0.5},"ci_reported":true}'
check "mAP + IoU threshold -> exit 0" test "$?" -eq 0
mj '{"task":"classification","metrics":["accuracy","sensitivity","specificity"],"ci_reported":true}'
check "accuracy + sensitivity + specificity -> no ACCURACY_ONLY" no ACCURACY_ONLY
mj '{"task":"classification","metrics":["AUC","accuracy"],"ci_reported":true}'
check "'AUC' folds to auroc -> AUPRC_MISSING (Minor)" has AUPRC_MISSING
mj '{"task":"classification","metrics":["auroc","auprc"],"classification":{"n_classes":3},"ci_reported":true}'
check "3 classes without averaging -> MULTICLASS_NO_AVERAGING" has MULTICLASS_NO_AVERAGING
mj '{"task":"classification","metrics":["auroc","auprc"],"classification":{"n_classes":3,"averaging":["one-vs-rest","macro"]},"ci_reported":true}'
check "3 classes with one-vs-rest macro -> clean" no MULTICLASS_NO_AVERAGING
mj '{"task":"interactive","metrics":["dice","nsd"],"ci_reported":true}'
check "interactive without interaction axis -> exit 1" test "$?" -eq 1
check "  INTERACTIVE_NO_INTERACTION_COUNT" has INTERACTIVE_NO_INTERACTION_COUNT
check "  INTERACTIVE_NO_TIME" has INTERACTIVE_NO_TIME
mj '{"task":"interactive","metrics":["dice","hd95","noc"],"interactive":{"interaction_axis":"interactions_to_threshold","initial_vs_converged":true,"per_case_time":true},"ci_reported":true}'
check "interactive complete -> exit 0" test "$?" -eq 0
mj '{"task":"generative","metrics":["psnr","ssim"],"ci_reported":true}'
check "generative similarity only -> GENERATIVE_NO_DOWNSTREAM" has GENERATIVE_NO_DOWNSTREAM
mj '{"task":"generative","metrics":["psnr","ssim"],"generative":{"downstream_task":"segmentation"},"ci_reported":true}'
check "generative with downstream task -> exit 0" test "$?" -eq 0
mj '{"task":"segmentation","metrics":["dice","hd95"]}'
check "ci_reported missing -> CI_MISSING (Minor)" has CI_MISSING
mj '{"task":"interactive","metrics":["dice","hd95","noc"],"interactive":{"initial_vs_converged":true,"per_case_time":true},"ci_reported":true}'
check "metric noc counts as the interaction axis (exit 0)" test "$?" -eq 0
mj '{"task":"detection","metrics":["average_precision"],"detection":{"match_criterion":"iou_threshold"},"ci_reported":true}'
check "'average_precision' is not folded (ambiguous) -> exit 2" test "$?" -eq 2
mj '{"task":"segmentation","metrics":["dice","ASSD"],"ci_reported":true}'
check "ASSD folds to surface_distance (boundary)" test "$?" -eq 0
mj '{"task":"detection","metrics":["sensitivity per false positive"],"detection":{"match_criterion":"iou_threshold"},"ci_reported":true}'
check "sensitivity per false positive folds to froc" test "$?" -eq 0
mj '{"task":"segmentation","metrics":["dice","hd95"],"ci_reported":true,"notes":1e400}'
check "non-finite number anywhere exits 2" test "$?" -eq 2
cp "$HERE/../templates/metrics_manifest.json" "$W/tpl.json"
python3 - "$W/tpl.json" <<'PY'
import json, sys
m = json.load(open(sys.argv[1])); m["task"] = "detection"; m["metrics"] = ["froc"]; m["ci_reported"] = True
json.dump(m, open(sys.argv[1], "w"))
PY
mrun "$W/tpl.json"
check "template defaults do not switch off the detection match check" has DETECTION_METRIC_MISSING
printf '\xef\xbb\xbf{"task":"segmentation","metrics":["dice","hd95"],"ci_reported":true}' > "$W/bom.json"; mrun "$W/bom.json"
check "UTF-8 BOM is read" test "$?" -eq 0
# other: escape hatch
mj '{"task":"segmentation","metrics":["dice","other: ASSD"],"ci_reported":true}'
check "other: metric is recorded but does not satisfy the boundary check" has NO_BOUNDARY_METRIC
check "  UNLISTED_METHOD reported" has UNLISTED_METHOD
mj '{"task":"detection","metrics":["froc"],"detection":{"match_criterion":"other: within 5 mm of the lesion centre"},"ci_reported":true}'
check "other: match criterion covers the field (exit 0)" test "$?" -eq 0
# input errors exit 2 and never 1
mj '{"task":"segmentation","metrics":["dice","boundary_f1"]}'
check "off-list metric exits 2" test "$?" -eq 2
mj '{"task":"segmentation","metrics":"dice","ci_reported":"yes"}'
check "non-boolean ci_reported exits 2" test "$?" -eq 2
mj '{"task":"segmentation","metrix":["dice"]}'
check "misspelled top-level key exits 2" test "$?" -eq 2
mj '{"task":"segmentation","detection":{"iou":0.5}}'
check "unknown sub-key exits 2" test "$?" -eq 2
mj '{"task":"other: registration","metrics":["dice"]}'
check "task other: exits 2" test "$?" -eq 2
mj '{"task":"classification","classification":{"n_classes":1}}'
check "n_classes < 2 exits 2" test "$?" -eq 2
mj '{"task":"detection","metrics":["froc"],"detection":{"match_criterion":"iou_threshold","threshold":Infinity}}'
check "Infinity exits 2" test "$?" -eq 2
mj '{"task":"segmentation","metrics":["none","dice"]}'
check "'none' mixed with a metric exits 2" test "$?" -eq 2
python3 -c "print('{\"notes\":'+'['*100000+']'*100000+'}')" > "$W/deep.json"
python3 "$DET" --manifest "$W/deep.json" --task segmentation --quiet >/dev/null 2>&1
check "deeply nested JSON exits 2" test "$?" -eq 2
python3 -c "print('{\"task\":\"classification\",\"classification\":{\"n_classes\":'+'9'*5000+'}}')" > "$W/big.json"
python3 "$DET" --manifest "$W/big.json" --quiet >/dev/null 2>&1
check "5000-digit integer exits 2" test "$?" -eq 2
python3 -c "print('{\"task\":\"detection\",\"metrics\":[\"froc\"],\"detection\":{\"match_criterion\":\"iou_threshold\",\"threshold\":1'+'0'*400+'},\"ci_reported\":true}')" > "$W/hugeint.json"
python3 "$DET" --manifest "$W/hugeint.json" --quiet >/dev/null 2>&1
check "400-digit integer threshold does not crash (exit 0)" test "$?" -eq 0
mj '{"metrics":["dice","hd95"],"ci_reported":true}'
check "manifest without task and no --task exits 2" test "$?" -eq 2
python3 "$DET" --manifest "$W/m.json" --task segmentation --quiet >/dev/null 2>&1
check "  ... --task supplies it" test "$?" -eq 0
python3 "$DET" --manifest "$F/manifest_seg_good.json" --task detection --quiet >/dev/null 2>&1
check "--task contradicting the manifest exits 2" test "$?" -eq 2
python3 "$DET" --manifest "$F/manifest_seg_good.json" --report "$F/seg_bad.md" --strict --quiet >/dev/null 2>&1
check "--manifest wins over --report" test "$?" -eq 0
python3 "$DET" --manifest "" --report "$F/seg_good.md" --task segmentation --quiet >/dev/null 2>&1
check "--manifest '' exits 2" test "$?" -eq 2
python3 "$DET" --quiet >/dev/null 2>&1
check "no input exits 2" test "$?" -eq 2
python3 "$DET" --report "$F/seg_good.md" --quiet >/dev/null 2>&1
check "--report without --task exits 2" test "$?" -eq 2
python3 "$DET" --report "$F/seg_good.md" --task segmentation --out "$OUT" > "$W/prose.txt" 2>&1
check "prose mode prints the PROSE_MODE notice" grep -q '^PROSE_MODE:' "$W/prose.txt"
check "prose mode JSON mode=prose" python3 -c "import json;assert json.load(open('$OUT'))['mode']=='prose'"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"; exit "$fail"
