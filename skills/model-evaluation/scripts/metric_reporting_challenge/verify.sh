#!/usr/bin/env bash
# Deterministic verifier for the metric-reporting challenge (model-evaluation).
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

echo "PASS: metric-reporting gate flags Dice-only/pixel-accuracy, accuracy-only, and detection without an IoU criterion; clears task-correct reports (including a line-wrapped IoU criterion)."
