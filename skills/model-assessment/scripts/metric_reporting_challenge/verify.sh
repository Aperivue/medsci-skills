#!/usr/bin/env bash
# Deterministic verifier for the metric-reporting challenge (model-assessment).
# Network-free, stdlib-only. The gate flags a task-metric mismatch and clears a
# task-correct report. Exit 0 = all expectations hold.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_metric_reporting.py"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

want() {  # report task expected_verdict
  python3 "$DET" --report "$HERE/fixture/$1" --task "$2" --out "$TMP/o.json" --quiet >/dev/null 2>&1 || true
  python3 - "$TMP/o.json" "$3" <<'PY' || exit 1
import json, sys
d = json.load(open(sys.argv[1]))
assert any(c["verdict"] == sys.argv[2] for c in d["claims"]), f"{sys.argv[2]} not flagged"
PY
}
clean() {  # report task
  python3 "$DET" --report "$HERE/fixture/$1" --task "$2" --strict --quiet >/dev/null 2>&1 \
    || { echo "FAIL: $1 should pass --strict (no Major)" >&2; exit 1; }
}

want seg_bad.md segmentation NO_BOUNDARY_METRIC
want seg_bad.md segmentation PIXEL_ACCURACY_SEG
clean seg_good.md segmentation
want clf_bad.md classification ACCURACY_ONLY
clean clf_good.md classification
# Detection branch: a stated IoU match criterion is required; a hard-wrapped criterion
# (IoU and its threshold on different physical lines) must still be detected — det_good_wrapped
# locks the iou_crit proximity window against newline-induced false fires.
want det_no_iou.md detection DETECTION_METRIC_MISSING
clean det_good_wrapped.md detection
# Interactive / promptable segmentation: a static-Dice-only report must be flagged for the
# missing interaction axis (and, being segmentation, for the missing boundary metric); a report
# with the interaction axis, convergence split, per-case time, and a boundary metric must clear.
want interactive_bad.md interactive INTERACTIVE_NO_INTERACTION_COUNT
want interactive_bad.md interactive NO_BOUNDARY_METRIC
clean interactive_good.md interactive
# Generative / synthesis: image-quality similarity without a downstream-task evaluation is a Major
# (similarity is not clinical utility); a report that adds the downstream task clears. Multiclass
# classification with AUROC/accuracy but no aggregation scheme stated is flagged.
want generative_bad.md generative GENERATIVE_NO_DOWNSTREAM
clean generative_good.md generative
want multiclass_bad.md classification MULTICLASS_NO_AVERAGING

# Manifest mode: the same task-metric mismatches declared as fields; an off-list value exits 2.
mwant() {  # manifest expected_verdict
  python3 "$DET" --manifest "$HERE/fixture/$1" --out "$TMP/m.json" --quiet >/dev/null 2>&1 || true
  python3 - "$TMP/m.json" "$2" <<'PY' || exit 1
import json, sys
d = json.load(open(sys.argv[1]))
assert any(c["verdict"] == sys.argv[2] for c in d["claims"]), f"{sys.argv[2]} not flagged"
PY
}
mwant manifest_seg_bad.json PIXEL_ACCURACY_SEG
mwant manifest_seg_bad.json NO_BOUNDARY_METRIC
mwant manifest_det_no_match.json DETECTION_METRIC_MISSING
mwant manifest_clf_bad.json ACCURACY_ONLY
python3 "$DET" --manifest "$HERE/fixture/manifest_seg_good.json" --strict --quiet >/dev/null 2>&1 \
  || { echo "FAIL: manifest_seg_good should pass --strict" >&2; exit 1; }
printf '{"task": "segmentation", "metrics": ["dice", "boundary_f1"]}' > "$TMP/off.json"
set +e; python3 "$DET" --manifest "$TMP/off.json" --quiet >/dev/null 2>&1; rc=$?; set -e
[ "$rc" -eq 2 ] || { echo "FAIL: an off-list metric should exit 2 (got $rc)" >&2; exit 1; }

echo "PASS: metric-reporting gate flags Dice-only/pixel-accuracy, accuracy-only, detection without an IoU criterion, interactive segmentation reported as one-shot, generative similarity without a downstream task, and multiclass without an aggregation scheme; clears task-correct reports."
