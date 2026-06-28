#!/usr/bin/env python3
"""Task-correct metric-reporting gate for a medical-imaging model (model-evaluation).

A conservative presence linter for a metrics report / results section: it flags when
the reported metric set does not match the task and prevalence, per Metrics Reloaded
(Maier-Hein & Reinke et al., Nat Methods 2024) and CLAIM 2024. It checks which metrics
are named (and whether confidence intervals are mentioned); it does not recompute a
number. Fires only when a required metric is clearly absent or a forbidden one is the
headline.

CHECKS (verdicts; which apply depends on --task):
  segmentation:
    NO_BOUNDARY_METRIC   (Major)  Dice/IoU named but no boundary metric (HD95 / HD /
                                  ASSD / NSD / surface distance).
    PIXEL_ACCURACY_SEG   (Major)  pixel/voxel accuracy reported for segmentation
                                  (misleading on imbalanced masks).
  classification:
    ACCURACY_ONLY        (Major)  accuracy named but no AUROC (threshold-independent
                                  discrimination).
    AUPRC_MISSING        (Minor)  AUROC named but no AUPRC (the minority-class metric
                                  under imbalance).
  detection:
    DETECTION_METRIC_MISSING (Major)  no FROC / mAP / sensitivity-per-false-positive,
                                      or no IoU match criterion stated.
  all tasks:
    CI_MISSING           (Minor)  no confidence interval / uncertainty mentioned for
                                  the headline metric.

INPUTS
  --report  metrics report / results markdown (required).
  --task    segmentation | classification | detection (required).

OUTPUT
  A table (stdout) and, with --out, a JSON artifact:
    {report, task, claims[{verdict, severity, detail, where}], summary}

Stdlib-only. Exit codes: 0 clean (or report-only), 1 Major claim(s) (with --strict),
2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

P = {
    "dice_iou": r"\b(dice|dsc|jaccard|iou|intersection over union)\b",
    "boundary": r"\b(hd95|hd 95|hausdorff|assd|\basd\b|\bmasd\b|\bmsd\b|nsd|"
                r"normali[sz]ed surface dice|normali[sz]ed surface|surface dice similarity|"
                r"surface dsc|surface dice|surface distance|mean (?:surface|boundary) distance|"
                r"boundary)\b",
    "pixel_acc": r"\b(pixel[- ]?accuracy|voxel[- ]?accuracy|pixel-?wise accuracy)\b",
    "accuracy": r"\b(accuracy)\b",
    # 'diagnostic accuracy' / 'accuracy study' are study-type phrases, not the accuracy metric
    "accuracy_phrase": r"\b(diagnostic(?: test)? accuracy|accuracy study|accuracy studies)\b",
    "auroc": r"\b(auroc|auc[- ]?roc|\bauc\b|c[- ]?statistic|area under the (?:roc|receiver))\b",
    "auprc": r"\b(auprc|au[- ]?prc|average precision|precision[- ]?recall|pr[- ]?auc)\b",
    "sens": r"\b(sensitivit\w+|recall|true[- ]?positive rate|tpr)\b",
    "spec": r"\b(specificit\w+|true[- ]?negative rate|tnr)\b",
    "detection": r"\b(froc|map\b|mean average precision|sensitivity per (?:false positive|fp)|"
                 r"competition performance metric|cpm)\b",
    "iou_crit": r"\b(?:iou|intersection over union|overlap)\b[^.\n]{0,40}"
                r"(?:threshold|criterion|>=|≥|>|\bof\b|above|exceed|\d\.\d)"
                r"|match(?:ing)? criterion"
                r"|(?:cent(?:er|re|roid)|distance)[- ]?based"
                r"|hit (?:rule|criterion)|within (?:the )?lesion",
    "ci": r"confidence interval|credible interval|\b95\s*%?\s*ci|\bcis?\b|±|\+/-|\bsd\b|"
          r"standard deviation|bootstrap|interquartile|\biqr\b",
}

# Negation BEFORE the token ('we do NOT report pixel accuracy ...').
NEG_BEFORE = re.compile(r"\b(not|never|without|neither|avoid\w*|do(?:es)?n't|did not|do not|"
                        r"instead of|rather than)\b", re.IGNORECASE)
# Negation AFTER the token tied to a result verb ('AUROC was not computed/reported').
NEG_AFTER = re.compile(
    r"\b(?:was|were|is|are|not)\s+not\s+\w+"
    r"|\bnot\s+(?:computed|reported|available|performed|calculated|presented|provided|assessed|"
    r"evaluated|measured)\b", re.IGNORECASE)


def has(text: str, key: str) -> bool:
    return re.search(P[key], text, re.IGNORECASE) is not None


def has_affirmative(text: str, key: str) -> bool:
    """has(), but a match disavowed by a nearby negation does not count — so 'we do not
    report pixel accuracy' or 'AUROC was not computed' is not treated as reporting it."""
    pat = re.compile(P[key], re.IGNORECASE)
    for m in pat.finditer(text):
        before = text[max(0, m.start() - 28): m.start()]
        after = text[m.end(): m.end() + 24]
        if NEG_BEFORE.search(before) or NEG_AFTER.search(after):
            continue
        return True
    return False


def analyze(report: str, task: str) -> dict:
    text = Path(report).read_text(encoding="utf-8")
    claims = []

    def add(v, s, d):
        claims.append({"verdict": v, "severity": s, "detail": d, "where": Path(report).name})

    if task == "segmentation":
        if has_affirmative(text, "pixel_acc"):
            add("PIXEL_ACCURACY_SEG", "Major",
                "pixel/voxel accuracy is reported for segmentation — misleading on imbalanced masks; "
                "report Dice/IoU with a boundary metric instead")
        if has(text, "dice_iou") and not has(text, "boundary"):
            add("NO_BOUNDARY_METRIC", "Major",
                "Dice/IoU is reported without a boundary metric (HD95 / NSD / surface distance) — "
                "overlap alone is shape- and size-insensitive; pair it with a boundary metric, "
                "per structure")
    elif task == "classification":
        # the accuracy METRIC, excluding the study-type phrase 'diagnostic accuracy'; a
        # sensitivity+specificity pair is a threshold-pair report, not accuracy-only
        acc_stripped = re.sub(P["accuracy_phrase"], " ", text, flags=re.IGNORECASE)
        accuracy_metric = re.search(P["accuracy"], acc_stripped, re.IGNORECASE) is not None
        threshold_pair = has(text, "sens") and has(text, "spec")
        auroc_reported = has_affirmative(text, "auroc")
        if accuracy_metric and not auroc_reported and not threshold_pair:
            add("ACCURACY_ONLY", "Major",
                "accuracy is reported without AUROC — accuracy is prevalence-dependent and misleading "
                "under imbalance; report threshold-independent discrimination (AUROC)")
        if auroc_reported and not has(text, "auprc"):
            add("AUPRC_MISSING", "Minor",
                "AUROC is reported without AUPRC — AUPRC tracks the minority class and is informative "
                "under imbalance")
    elif task == "detection":
        if not has(text, "detection"):
            add("DETECTION_METRIC_MISSING", "Major",
                "no detection metric (FROC / mAP / sensitivity-per-false-positive) is reported — "
                "patient-level accuracy is not a detection metric")
        elif not has(text, "iou_crit"):
            add("DETECTION_METRIC_MISSING", "Major",
                "a detection metric is reported but the IoU match criterion is not stated — mAP/FROC "
                "are undefined without the match threshold")

    if not has(text, "ci"):
        add("CI_MISSING", "Minor",
            "no confidence interval / uncertainty is reported for the headline metric")

    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {"report": report, "task": task, "claims": claims,
            "summary": {"n_claims": len(claims), "n_major": n_major,
                        "verdict": "MAJOR_CANDIDATE" if n_major else "OK"}}


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | task-correct metrics with uncertainty reported |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Task-correct metric-reporting gate (model-evaluation).")
    ap.add_argument("--report", required=True, help="metrics report / results markdown")
    ap.add_argument("--task", required=True, choices=["segmentation", "classification", "detection"])
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    if not Path(args.report).is_file():
        sys.stderr.write(f"ERROR: --report not found: {args.report}\n")
        return 2
    result = analyze(args.report, args.task)

    if not args.quiet:
        print("=" * 41)
        print(" Metric Reporting (model-evaluation)")
        print("=" * 41)
        print(render(result))
        print()
        s = result["summary"]
        print(f"MAJOR candidate: {s['n_major']} metric-reporting issue(s)." if s["n_major"]
              else "OK: task-correct metrics with uncertainty reported.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
