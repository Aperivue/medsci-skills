#!/usr/bin/env python3
"""Task-correct metric-reporting gate for a medical-imaging model (model-assessment).

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
    AUPRC_MISSING        (Minor)  AUROC named but no AUPRC (the PPV-side view; report it
                                  with the test-set prevalence, its no-skill value).
    MULTICLASS_NO_AVERAGING (Minor)  a multiclass claim with AUROC/accuracy but no stated
                                  aggregation scheme (one-vs-rest / macro / micro / pairwise /
                                  Obuchowski), per Park et al. (Radiol Med 2024).
  detection:
    DETECTION_METRIC_MISSING (Major)  no FROC / mAP / sensitivity-per-false-positive,
                                      or no IoU match criterion stated.
  interactive (promptable segmentation — SAM2 / MedSAM2 / nnInteractive; also runs the
  segmentation checks above, since interactive segmentation is still segmentation):
    INTERACTIVE_NO_INTERACTION_COUNT (Major)  no interaction axis (number of clicks /
                                      interactions-to-threshold / Dice-vs-interactions).
    INTERACTIVE_NO_CONVERGENCE (Minor)  no initial-prompt vs converged/peak Dice split.
    INTERACTIVE_NO_TIME        (Minor)  no per-case interaction / inference time.
  generative (image synthesis / generation — Park et al., Radiol Med 2024):
    GENERATIVE_NO_DOWNSTREAM (Major)  image-quality similarity (SSIM / PSNR / SNR / CNR)
                                  reported without a downstream-task evaluation — similarity
                                  is not clinical utility (quality and task efficacy can diverge).
    GENERATIVE_NO_SIMILARITY (Minor)  a synthesis claim with no image-quality metric named.
  all tasks:
    CI_MISSING           (Minor)  no confidence interval / uncertainty mentioned for
                                  the headline metric.

INPUTS
  --report  metrics report / results markdown (required).
  --task    segmentation | classification | detection | interactive | generative (required).

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

# words that mark 'MSD' as the Medical Segmentation Decathlon dataset, not a distance
_MSD_DATASET = (r"(?:19|20)\d\d\b|task|challenge|data\b|dataset|data set|decathlon|benchmark|"
                r"release|collection|cohort|cases?\b|images?\b|scans?\b|volumes?\b|subset|split|"
                r"held[- ]?out|training\b|test\b|validation\b")

P = {
    "dice_iou": r"\b(dice|dsc|jaccard|iou|intersection over union)\b",
    # named boundary metrics only: the bare word 'boundary' ("boundary error was not
    # assessed") names no metric and must not satisfy the Dice+boundary pairing
    # 'MSD' also names the Medical Segmentation Decathlon ("the MSD liver task", "MSD Task09",
    # "the MSD 2018 release", "Medical Segmentation Decathlon (MSD)"). The bare abbreviation
    # counts as mean surface distance unless such a dataset context surrounds it, so a results
    # table ("| MSD (mm) |", "| MSD | 1.2 mm |") and prose ("MSD decreased to 1.2 mm") still count.
    "boundary": r"\b(hd95|hd 95|hausdorff|assd|\basd\b|\bmasd\b|"
                r"(?<!decathlon \()msd(?!\s*\)?[\s-]*(?:" + _MSD_DATASET + r"|[a-z]+[\s-]+(?:"
                + _MSD_DATASET + r")))|nsd|"
                r"normali[sz]ed surface dice|normali[sz]ed surface|surface dice similarity|"
                r"surface dsc|surface dice|surface distance|mean (?:surface|boundary) distance|"
                r"boundary[- ]?(?:iou|f1|f-?score))\b",
    "pixel_acc": r"\b(pixel[- ]?accuracy|voxel[- ]?accuracy|pixel-?wise accuracy)\b",
    "accuracy": r"\b(accuracy)\b",
    # 'diagnostic accuracy' / 'accuracy study' are study-type phrases, not the accuracy metric
    "accuracy_phrase": r"\b(diagnostic(?: test)? accuracy|accuracy study|accuracy studies)\b",
    "auroc": r"\b(auroc|auc[- ]?roc|\bauc\b|c[- ]?statistic|area under the (?:roc|receiver))\b",
    "auprc": r"\b(auprc|au[- ]?prc|average precision|precision[- ]?recall|pr[- ]?auc)\b",
    "sens": r"\b(sensitivit\w+|recall|true[- ]?positive rate|tpr)\b",
    "spec": r"\b(specificit\w+|true[- ]?negative rate|tnr)\b",
    # mAP is matched case-sensitively (or with an @/IoU suffix): a lower-case 'map' is a
    # saliency / heat / probability map, not mean average precision.
    "detection": r"\b(froc|(?-i:mAP)(?:@?\d+)?\b|map\s*@|mean average precision|"
                 r"sensitivity per (?:false positive|fp)|"
                 r"competition performance metric|cpm)\b",
    "iou_crit": r"\b(?:iou|intersection over union|overlap)\b[^.]{0,40}"
                r"(?:threshold|criterion|>=|≥|>|\bof\b|above|exceed|\d\.\d)"
                r"|match(?:ing)? criterion"
                r"|(?:cent(?:er|re|roid)|distance)[- ]?based"
                r"|hit (?:rule|criterion)|within (?:the )?lesion",
    "ci": r"confidence interval|credible interval|\b95\s*%?\s*ci|\bcis?\b|±|\+/-|\bsd\b|"
          r"standard deviation|bootstrap|interquartile|\biqr\b",
    # interactive / promptable segmentation (SAM2 / MedSAM2 / nnInteractive). The
    # interaction axis: number of clicks (NoC), interactions/clicks-to-threshold, or a
    # Dice-vs-interactions trajectory — the metric a static Dice cannot express.
    "interactions": r"\b(number of clicks|#\s?clicks|clicks?[- ]?to[- ]?(?:threshold|target)|"
                    r"\bnoc\b|noc@\d+|interaction[- ]?(?:count|budget)|"
                    r"interactions?[- ]?to[- ]?(?:threshold|target)|"
                    r"number of (?:interactions|prompts|corrections|edits)|"
                    r"corrective (?:click|interaction)|"
                    r"dice[- ]?(?:vs|versus|per|over|against)[- ]?(?:click|interaction|prompt)|"
                    r"clicks required)\b",
    # separation of the initial prompt from the converged / peak operating point
    "convergence": r"\b(initial[- ]?(?:dice|prompt|click|mask|prediction)|"
                   r"first[- ]?(?:click|prompt) dice|converged? dice|convergence|peak dice|"
                   r"plateau|saturat\w+|dice after \d+|"
                   r"after (?:the )?(?:first|final|last|\d+) (?:click|prompt|interaction))\b",
    # per-case interaction / inference efficiency. Matches named time terms AND a bare
    # number-plus-time-unit ("179±114 seconds", "120-200 ms"), since real interactive papers
    # report timing that way rather than always writing "inference time" (dogfood: nnInteractive).
    "interaction_time": r"\b(interaction time|time per (?:case|click|interaction|prompt)|"
                        r"per[- ]?case (?:time|latency)|(?:inference|annotation|completion|"
                        r"segmentation|processing|response) (?:time|latency|speed)|"
                        r"seconds per (?:case|click|interaction)|runtime|wall[- ]?clock|"
                        r"time[- ]?to[- ]?(?:threshold|target)|"
                        r"\d+(?:\.\d+)?\s*(?:±|\+/-|–|-|to)?\s*\d*(?:\.\d+)?\s*"
                        r"(?:ms|msec|milliseconds?|seconds?|minutes?|hours?)\b)\b",
    # generative / synthesis image evaluation (Park et al., Radiol Med 2024): full-reference
    # pixel/intensity similarity, no-reference quality, and the downstream-task efficacy that
    # image similarity alone does not establish.
    "sim_full_ref": r"\b(mse|rmse|nrmse|\bmae\b|psnr|peak signal[- ]?to[- ]?noise|ssim|"
                    r"structural similarity|pixel[- ]?wise similarity|full[- ]?reference)\b",
    "snr_cnr": r"\b(snr|cnr|signal[- ]?to[- ]?noise|contrast[- ]?to[- ]?noise)\b",
    "downstream": r"\b(downstream[- ]?(?:task|clinical|evaluation|performance)|task[- ]?based|"
                  r"efficacy (?:in|on|for) (?:performing |executing |conducting )?(?:the )?"
                  r"(?:downstream |clinical )?task|"
                  r"(?:segmentation|detection|classification|diagnostic|lesion) "
                  r"(?:performance|sensitivity|accuracy|dice|auroc) "
                  r"(?:on|of|using|with|from) (?:the )?"
                  r"(?:synthes\w+|generat\w+|synthetic|reconstruct\w+|denoised)|"
                  r"trained on (?:the )?(?:synthes\w+|generat\w+|synthetic)|"
                  r"indirect(?:ly)? (?:evaluat|assess))\b",
    # multiclass classification aggregation scheme (Park et al., Radiol Med 2024)
    "multiclass": r"\b(multi[- ]?class|multi[- ]?categor\w+|three[- ]?class|"
                  r"(?:\d+|four|five|six|seven|eight|nine|ten)[- ]?class(?:es|\b))\b",
    "averaging": r"\b(one[- ]?vs[- ]?rest|one[- ]?versus[- ]?rest|\bovr\b|one[- ]?vs[- ]?one|\bovo\b|"
                 r"pairwise|macro[- ]?averag\w+|micro[- ]?averag\w+|weighted average|obuchowski|"
                 r"per[- ]?class (?:auroc|auc))\b",
}

# Negation BEFORE the token ('we do NOT report pixel accuracy ...').
NEG_BEFORE = re.compile(r"\b(not|never|without|neither|avoid\w*|do(?:es)?n't|did not|do not|"
                        r"instead of|rather than)\b", re.IGNORECASE)
# Negation AFTER the token tied to a result verb ('AUROC was not computed/reported').
NEG_AFTER = re.compile(
    r"\b(?:was|were|is|are|not)\s+not\s+\w+"
    r"|\bnot\s+(?:computed|reported|available|performed|calculated|presented|provided|assessed|"
    r"evaluated|measured)\b", re.IGNORECASE)
# A negation only disavows a token in its own clause: "pixel accuracy was not used; HD95 7.2 mm"
# reports HD95. A period inside a number ("7.2") is not a clause break.
CLAUSE_BREAK = re.compile(r"[.;:!?](?:\s|$)")
# A negation also reaches every item of a coordinated list of BOUNDARY metrics: "we did not
# compute the Hausdorff distance or HD95" disavows HD95. Only an explicit not-reporting verb
# governs the list ("did not compute/report/...", "were not reported/computed/..."); "without",
# "not surprisingly" or a comparison ("were not significantly different from") never does, and
# the gap between the list item and the negation must be list glue only: no value (digit), no
# second predicate, no relative clause, no contrast ("instead", "but").
_DISAVOW_VERB = (r"(?:report|comput|calculat|measur|assess|evaluat|us|provid|present|perform|"
                 r"estimat|includ)\w*")
LIST_NEG_BEFORE = re.compile(
    r"\b(?:did not|do not|does not|didn't|don't|doesn't|never)\s+(?:\w+\s+)?" + _DISAVOW_VERB
    + r"\b", re.IGNORECASE)
LIST_NEG_AFTER = re.compile(
    r"\b(?:was|were|is|are)\s+not\s+(?:computed|reported|available|performed|calculated|"
    r"presented|provided|assessed|evaluated|measured|used|estimated|obtained)\b", re.IGNORECASE)
LIST_GLUE_END = re.compile(r"(?:,|\b(?:or|nor|and)\b|/)\s*(?:the\s+)?$", re.IGNORECASE)
LIST_GLUE_START = re.compile(r"^\s*(?:,|\b(?:or|nor|and)\b|/)", re.IGNORECASE)
LIST_BREAKER = re.compile(
    r"\d|\b(?:instead|but|rather|whereas|while|however|only|except|although|yet|which|that|who|"
    r"was|were|is|are|be|been|had|has|have|we|it|they|"
    r"report\w*|use[ds]?|using|comput\w+|calculat\w+|measur\w+|assess\w*|evaluat\w+|"
    r"present\w*|provid\w+|perform\w*|show\w*|achiev\w+|obtain\w*|yield\w*|gave|give\w*)\b",
    re.IGNORECASE)
LIST_SPAN = 120
OWN_VALUE = re.compile(r"^\s*(?:\([^)]{0,20}\)\s*)?(?:=|:|of|was|were|is|reached|achieved)?\s*\d",
                       re.IGNORECASE)
AFFIRM_COPULA = re.compile(r"\b(?:was|were|is|are|reached|achieved|yielded)\b", re.IGNORECASE)


def has(text: str, key: str) -> bool:
    return re.search(P[key], text, re.IGNORECASE) is not None


def has_affirmative(text: str, key: str, list_negation: bool = False) -> bool:
    """has(), but a match disavowed by a nearby negation does not count — so 'we do not
    report pixel accuracy' or 'AUROC was not computed' is not treated as reporting it.
    With list_negation, an explicit not-reporting verb also reaches the other items of a
    coordinated list (used for boundary metrics only)."""
    pat = re.compile(P[key], re.IGNORECASE)
    for m in pat.finditer(text):
        before = CLAUSE_BREAK.split(text[max(0, m.start() - 28): m.start()])[-1]
        after = CLAUSE_BREAK.split(text[m.end(): m.end() + 24])[0]
        if NEG_BEFORE.search(before) or NEG_AFTER.search(after):
            continue
        if list_negation and _list_negated(text, m.start(), m.end()):
            continue
        return True
    return False


def _list_negated(text: str, start: int, end: int) -> bool:
    """True when the match is a later/earlier item of a list governed by a not-reporting verb."""
    clause_before = CLAUSE_BREAK.split(text[max(0, start - LIST_SPAN): start])[-1]
    clause_after = CLAUSE_BREAK.split(text[end: end + LIST_SPAN])[0]
    negs = list(LIST_NEG_BEFORE.finditer(clause_before))
    # "We did not use pixel accuracy, Dice and HD95 were reported": the item has its own
    # (affirmative) predicate or value after it, so the earlier negation does not reach it.
    own_predicate = (OWN_VALUE.search(clause_after) is not None
                     or (AFFIRM_COPULA.search(clause_after) is not None
                         and NEG_AFTER.search(clause_after) is None))
    if negs and not own_predicate:
        # "did not compute| the Hausdorff distance or |HD95": the remainder must be list items
        # ending in list glue
        gap = clause_before[negs[-1].end():]
        if LIST_GLUE_END.search(gap) and not LIST_BREAKER.search(gap):
            return True
    na = LIST_NEG_AFTER.search(clause_after)
    if na:
        # "HD95| and ASSD |were not computed": the gap must be list glue + items only
        gap = clause_after[:na.start()]
        if LIST_GLUE_START.search(gap) and not LIST_BREAKER.search(gap):
            return True
    return False


def analyze(report: str, task: str) -> dict:
    text = Path(report).read_text(encoding="utf-8")
    claims = []

    def add(v, s, d):
        claims.append({"verdict": v, "severity": s, "detail": d, "where": Path(report).name})

    if task in ("segmentation", "interactive"):
        # interactive/promptable segmentation is still segmentation: the overlap-plus-boundary
        # requirement applies to its per-structure quality regardless of the interaction axis.
        if has_affirmative(text, "pixel_acc"):
            add("PIXEL_ACCURACY_SEG", "Major",
                "pixel/voxel accuracy is reported for segmentation — misleading on imbalanced masks; "
                "report Dice/IoU with a boundary metric instead")
        if has(text, "dice_iou") and not has_affirmative(text, "boundary", list_negation=True):
            add("NO_BOUNDARY_METRIC", "Major",
                "Dice/IoU is reported without a boundary metric (HD95 / NSD / surface distance) — "
                "overlap alone is shape- and size-insensitive; pair it with a boundary metric, "
                "per structure")
    if task == "interactive":
        # A promptable / interactive method's contribution is the accuracy-vs-interaction
        # trajectory and its efficiency, not a single operating point; a static Dice omits
        # exactly what makes it interactive (Metrics Reloaded does not cover this regime).
        if not has(text, "interactions"):
            add("INTERACTIVE_NO_INTERACTION_COUNT", "Major",
                "an interactive/promptable segmentation report does not quantify the interaction "
                "axis (number of clicks / interactions-to-threshold / Dice-vs-interactions) — a "
                "single Dice evaluates a promptable method as if it were one-shot")
        if not has(text, "convergence"):
            add("INTERACTIVE_NO_CONVERGENCE", "Minor",
                "no separation of the initial prompt from the converged/peak Dice — the interactive "
                "contribution is the improvement across interactions, not one operating point")
        if not has(text, "interaction_time"):
            add("INTERACTIVE_NO_TIME", "Minor",
                "no per-case interaction/inference time — efficiency is a primary interactive claim "
                "(a high-Dice method needing many slow interactions may not be clinically usable)")
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
                "AUROC is reported without AUPRC — add AUPRC for the PPV-side view, reported with the "
                "test-set prevalence (its no-skill value): AUPRC moves with prevalence, so a value from "
                "an enriched test set does not carry over to deployment")
        if has(text, "multiclass") and (accuracy_metric or auroc_reported) and not has(text, "averaging"):
            add("MULTICLASS_NO_AVERAGING", "Minor",
                "a multiclass classification reports AUROC/accuracy without stating the aggregation "
                "scheme (one-vs-rest, macro/micro averaging, pairwise, or the prevalence-weighted "
                "Obuchowski index) — the aggregate is ambiguous and prevalence-sensitive without it")
    elif task == "detection":
        if not has(text, "detection"):
            add("DETECTION_METRIC_MISSING", "Major",
                "no detection metric (FROC / mAP / sensitivity-per-false-positive) is reported — "
                "patient-level accuracy is not a detection metric")
        elif not has(text, "iou_crit"):
            add("DETECTION_METRIC_MISSING", "Major",
                "a detection metric is reported but the IoU match criterion is not stated — mAP/FROC "
                "are undefined without the match threshold")
    elif task == "generative":
        # image synthesis / generation (Park et al., Radiol Med 2024): full-reference similarity
        # (MSE/RMSE/PSNR/SSIM) or, without a reference, no-reference quality (SNR/CNR) — but image
        # quality and downstream-task efficacy need not align, so a clinical-utility claim needs a
        # downstream-task evaluation, not similarity alone.
        has_sim = has(text, "sim_full_ref") or has(text, "snr_cnr")
        if has_sim and not has(text, "downstream"):
            add("GENERATIVE_NO_DOWNSTREAM", "Major",
                "image-quality similarity (SSIM / PSNR / SNR / CNR) is reported for a generative / "
                "synthesis model without a downstream-task evaluation — pixel/intensity similarity does "
                "not establish clinical utility (quality and task efficacy need not align, e.g. an "
                "AI-denoised CT with higher CNR but lower lesion sensitivity); evaluate a downstream "
                "task (segmentation / detection / classification) on the synthesized images")
        if not has_sim:
            add("GENERATIVE_NO_SIMILARITY", "Minor",
                "a generative / synthesis evaluation names no image-quality metric — report "
                "full-reference similarity (MSE / RMSE / PSNR / SSIM) or, when no reference exists, "
                "no-reference quality (SNR / CNR, standardized visual scores)")

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
    ap = argparse.ArgumentParser(description="Task-correct metric-reporting gate (model-assessment).")
    ap.add_argument("--report", required=True, help="metrics report / results markdown")
    ap.add_argument("--task", required=True,
                    choices=["segmentation", "classification", "detection", "interactive", "generative"])
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
        print(" Metric Reporting (model-assessment)")
        print("=" * 41)
        print(render(result))
        print()
        s = result["summary"]
        print(f"MAJOR candidate: {s['n_major']} metric-reporting issue(s)." if s["n_major"]
              else "OK: task-correct metrics with uncertainty reported.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_metric_reporting", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
