#!/usr/bin/env bash
# Regression test for the metric-reporting gate (model-evaluation). Synthetic, PII-free.
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
# negation: 'AUROC was not computed' -> the real ACCURACY_ONLY, no spurious AUPRC_MISSING
printf 'Classification accuracy 0.92; AUROC was not computed.\n' > "$W/aur.md"
python3 "$DET" --report "$W/aur.md" --task classification --out "$OUT" --quiet >/dev/null 2>&1
check "negation: 'AUROC was not computed' -> ACCURACY_ONLY" has ACCURACY_ONLY
check "negation: no spurious AUPRC_MISSING" no AUPRC_MISSING

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"; exit "$fail"
