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
  manifest mode only (an empty declaration is certain; prose absence is not):
    CLASSIFICATION_METRIC_MISSING (Major)  classification with no discrimination / threshold
                                  metric declared (accuracy, AUROC, AUPRC, sensitivity,
                                  specificity, PPV, NPV); Minor when only an "other:" metric is.
    SEGMENTATION_METRIC_MISSING (Major)  segmentation / interactive with no overlap metric
                                  (Dice / IoU) declared; Minor when only an "other:" metric is.
  all tasks:
    CI_MISSING           (Minor)  no confidence interval / uncertainty mentioned for
                                  the headline metric.

INPUTS
  --manifest  metrics_manifest.json: the reported metrics DECLARED as structured fields
              (preferred; template in templates/metrics_manifest.json, schema in
              references/metrics_manifest_schema.md). Each value must come from the
              field's allow-list or be "other:<description>"; anything else, a wrong
              type or an unknown key exits 2 and names the field. The verdicts above fire
              on what is declared (the keyword lists above are prose mode's; the manifest
              values are in the schema). The gate checks the declaration, not the numbers.
  --report    metrics report / results markdown (prose mode). Prose mode tests keyword
              presence with a short negation window, and says so. With --manifest,
              --report is not read.
  --task      segmentation | classification | detection | interactive | generative
              (required in prose mode; in manifest mode it must match "task" if given).

OUTPUT
  A table (stdout) and, with --out, a JSON artifact:
    {report|manifest, mode, task, claims[{verdict, severity, detail, where}], summary}
  Manifest mode adds "basis": "declared" and UNLISTED_METHOD (Minor) for each
  "other:<description>" value. The final line says only what was checked: "OK" when no
  claim fired, "No Major issue (N Minor ...)" when only Minors did; manifest mode marks
  both "(as declared)".

Stdlib-only. Exit codes: 0 clean (or report-only), 1 Major claim(s) (with --strict),
2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

P = {
    "dice_iou": r"\b(dice|dsc|jaccard|iou|intersection over union)\b",
    # named boundary metrics only: the bare word 'boundary' ("boundary error was not
    # assessed") names no metric and must not satisfy the Dice+boundary pairing
    "boundary": r"\b(hd95|hd 95|hausdorff|assd|\basd\b|\bmasd\b|\bmsd\b|nsd|"
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
    "detection": r"\b(froc|map\b|mean average precision|sensitivity per (?:false positive|fp)|"
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


def has(text: str, key: str) -> bool:
    return re.search(P[key], text, re.IGNORECASE) is not None


def has_affirmative(text: str, key: str) -> bool:
    """has(), but a match disavowed by a nearby negation does not count — so 'we do not
    report pixel accuracy' or 'AUROC was not computed' is not treated as reporting it."""
    pat = re.compile(P[key], re.IGNORECASE)
    for m in pat.finditer(text):
        before = CLAUSE_BREAK.split(text[max(0, m.start() - 28): m.start()])[-1]
        after = CLAUSE_BREAK.split(text[m.end(): m.end() + 24])[0]
        if NEG_BEFORE.search(before) or NEG_AFTER.search(after):
            continue
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
        if has(text, "dice_iou") and not has_affirmative(text, "boundary"):
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
    return {"report": report, "mode": "prose", "task": task, "claims": claims,
            "summary": {"n_claims": len(claims), "n_major": n_major,
                        "verdict": "MAJOR_CANDIDATE" if n_major else "OK"}}


# --------------------------------------------------------------------------- manifest mode
# Allow-lists (compared after _key(): lower case, '-' and spaces -> '_'). Every value is a
# metric or scheme named in references/metric_guide.md or metric_selection_grounding.md.
TASKS = {"segmentation", "classification", "detection", "interactive", "generative"}
OVERLAP = {"dice", "iou"}
BOUNDARY = {"hd95", "hausdorff", "nsd", "surface_distance"}
DETECTION_M = {"froc", "map"}
SIMILARITY = {"mse", "rmse", "mae", "psnr", "ssim", "snr", "cnr"}
METRICS = (OVERLAP | BOUNDARY | DETECTION_M | SIMILARITY |
           {"pixel_accuracy", "accuracy", "auroc", "auprc", "sensitivity", "specificity",
            "ppv", "npv", "brier", "calibration_slope", "calibration_intercept", "ece",
            "noc", "likert_visual_score"})
# a classification report needs at least one of these (discrimination or threshold metrics)
CLF_HEADLINE = {"accuracy", "auroc", "auprc", "sensitivity", "specificity", "ppv", "npv"}
AVERAGING = {"one_vs_rest", "macro", "micro", "pairwise", "obuchowski"}
MATCH = {"iou_threshold", "centroid_threshold", "mask_threshold"}
INTERACTION = {"dice_vs_interactions", "interactions_to_threshold"}
DOWNSTREAM = {"segmentation", "detection", "classification", "quantitative_measurement"}
ALIASES = {"jaccard": "iou", "dsc": "dice", "hd": "hausdorff", "auc": "auroc", "roc_auc": "auroc",
           "pr_auc": "auprc", "mean_average_precision": "map",
           "assd": "surface_distance", "masd": "surface_distance", "surface_dice": "nsd",
           "normalised_surface_dice": "nsd", "normalized_surface_dice": "nsd",
           "sensitivity_per_false_positive": "froc", "sensitivity_per_fp": "froc",
           "recall": "sensitivity", "precision": "ppv", "normalised_surface_distance": "nsd",
           "normalized_surface_distance": "nsd", "one_vs_one": "pairwise"}

TOP_KEYS = {"task", "metrics", "ci_reported", "classification", "detection", "interactive",
            "generative", "notes"}
SUB_KEYS = {
    "classification": {"n_classes", "averaging"},
    "detection": {"match_criterion", "threshold"},
    "interactive": {"interaction_axis", "initial_vs_converged", "per_case_time"},
    "generative": {"downstream_task"},
}

OTHER = re.compile(r"^\s*other\s*:(.*)$", re.IGNORECASE | re.DOTALL)


class ManifestError(ValueError):
    pass


def _reject_constant(name: str):
    raise ManifestError(f"{name} is not a valid JSON number")


def _finite_float(text: str) -> float:
    v = float(text)
    if not math.isfinite(v):
        raise ManifestError(f"{text[:40]} is not a finite number")
    return v


def _short(v) -> str:
    r = repr(v)
    return r if len(r) <= 80 else r[:77] + "..."


def _key(v: str) -> str:
    k = re.sub(r"[\s\-]+", "_", v.strip().lower())
    return ALIASES.get(k, k)


def _enum(value, allowed: set, where: str, unlisted: list) -> str:
    """One allow-listed value, "none", or "other:<description>"; anything else is an error."""
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{where}: expected a non-empty string, got {_short(value)}")
    k = _key(value)
    if k == "none" or k in allowed:
        return k
    om = OTHER.match(value)
    if om:
        if not om.group(1).strip():
            raise ManifestError(f"{where}: 'other:' needs a description")
        if _key(om.group(1)) == "none":
            return "none"
        unlisted.append((where, value.strip()))
        return "other"
    raise ManifestError(f"{where}: {_short(value)} is not one of {sorted(allowed | {'none'})} "
                        f"(use \"other:<description>\" for one not listed)")


def _enum_list(value, allowed: set, where: str, unlisted: list) -> list:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        raise ManifestError(f"{where}: expected a list of strings, got {type(value).__name__}")
    out = [_enum(v, allowed, f"{where}[{i}]", unlisted) for i, v in enumerate(value)]
    if "none" in out and len(out) > 1:
        raise ManifestError(f"{where}: 'none' cannot be combined with other values")
    return list(dict.fromkeys(v for v in out if v != "none"))


def _obj(m: dict, key: str) -> dict:
    v = m.get(key)
    if v is None:
        return {}
    if not isinstance(v, dict):
        raise ManifestError(f"{key}: expected an object, got {type(v).__name__}")
    extra = set(v) - SUB_KEYS[key]
    if extra:
        raise ManifestError(f"{key}: unknown key(s) {sorted(extra)}; allowed {sorted(SUB_KEYS[key])}")
    return v


def _bool(v, where: str):
    if v is not None and not isinstance(v, bool):
        raise ManifestError(f"{where}: expected true/false, got {_short(v)}")
    return v


def _int(v, where: str, minimum: int):
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, int) or v < minimum:
        raise ManifestError(f"{where}: expected an integer >= {minimum}, got {_short(v)}")
    return v


def analyze_manifest(path: str, task_arg: str | None) -> dict:
    try:
        m = json.loads(Path(path).read_text(encoding="utf-8-sig"), parse_constant=_reject_constant,
                       parse_float=_finite_float)
    except (OSError, ValueError, RecursionError) as e:   # ValueError covers JSONDecodeError
        raise ManifestError(f"cannot read manifest: {e}")
    if not isinstance(m, dict):
        raise ManifestError("manifest must be a JSON object")
    extra = set(m) - TOP_KEYS
    if extra:
        raise ManifestError(f"unknown top-level key(s) {sorted(extra)}; allowed {sorted(TOP_KEYS)}")
    unlisted: list = []

    task = m.get("task")
    if task is None:
        if task_arg is None:
            raise ManifestError("task: missing (set it in the manifest or pass --task)")
        task = task_arg
    else:
        task = _enum(task, TASKS, "task", [])
        if task not in TASKS:
            raise ManifestError(f"task: must be one of {sorted(TASKS)}")
        if task_arg is not None and task_arg != task:
            raise ManifestError(f"task: manifest says {task!r} but --task is {task_arg!r}")

    metrics = set(_enum_list(m.get("metrics"), METRICS, "metrics", unlisted))
    ci = _bool(m.get("ci_reported"), "ci_reported")
    clf = _obj(m, "classification")
    n_classes = _int(clf.get("n_classes"), "classification.n_classes", 2)
    averaging = _enum_list(clf.get("averaging"), AVERAGING, "classification.averaging", unlisted)
    det = _obj(m, "detection")
    match = (_enum(det["match_criterion"], MATCH, "detection.match_criterion", unlisted)
             if det.get("match_criterion") is not None else None)
    thr = det.get("threshold")   # recorded, not gated
    if thr is not None and (isinstance(thr, bool) or not isinstance(thr, (int, float))
                            or (isinstance(thr, float) and not math.isfinite(thr)) or thr < 0):
        raise ManifestError(f"detection.threshold: expected a finite number >= 0, got {_short(thr)}")
    inter = _obj(m, "interactive")
    axis = _enum_list(inter.get("interaction_axis"), INTERACTION, "interactive.interaction_axis",
                      unlisted)
    conv = _bool(inter.get("initial_vs_converged"), "interactive.initial_vs_converged")
    ptime = _bool(inter.get("per_case_time"), "interactive.per_case_time")
    gen = _obj(m, "generative")
    downstream = _enum_list(gen.get("downstream_task"), DOWNSTREAM, "generative.downstream_task",
                            unlisted)

    claims = []

    def add(v, sev, d, where):
        claims.append({"verdict": v, "severity": sev, "detail": d, "where": where})

    # An "other:" metric might be the headline metric under another name, so its absence from
    # the allow-list is not certain: the headline-metric verdicts drop to Minor then.
    other_metric = any(w.startswith("metrics[") for w, _ in unlisted)

    def headline_missing(verdict, what):
        if other_metric:
            add(verdict, "Minor",
                f"no {what} declared on the allow-list; an \"other:\" metric is declared — confirm "
                "by eye that it is one", "metrics")
        else:
            add(verdict, "Major",
                f"no {what} declared — the task's headline metric is absent, so nothing below it "
                "can be checked", "metrics")

    if task in ("segmentation", "interactive"):
        if not metrics & OVERLAP:
            headline_missing("SEGMENTATION_METRIC_MISSING", "overlap metric (Dice / IoU)")
        if "pixel_accuracy" in metrics:
            add("PIXEL_ACCURACY_SEG", "Major",
                "pixel/voxel accuracy is declared for segmentation — misleading on imbalanced masks; "
                "report Dice/IoU with a boundary metric instead", "metrics")
        if metrics & OVERLAP and not metrics & BOUNDARY:
            add("NO_BOUNDARY_METRIC", "Major",
                "Dice/IoU is declared without a boundary metric (HD95 / NSD / surface distance) — "
                "overlap alone is shape- and size-insensitive; pair it with a boundary metric, "
                "per structure", "metrics")
    if task == "interactive":
        if not axis and "noc" not in metrics:   # NoC is the interactions-to-threshold metric
            add("INTERACTIVE_NO_INTERACTION_COUNT", "Major",
                "no interaction axis declared (Dice-vs-interactions, interactions-to-threshold or NoC) — "
                "a single Dice evaluates a promptable method as if it were one-shot",
                "interactive.interaction_axis")
        if conv is not True:
            add("INTERACTIVE_NO_CONVERGENCE", "Minor",
                "no initial-prompt vs converged/peak Dice split declared",
                "interactive.initial_vs_converged")
        if ptime is not True:
            add("INTERACTIVE_NO_TIME", "Minor",
                "no per-case interaction/inference time declared", "interactive.per_case_time")
    elif task == "classification":
        acc, auroc = "accuracy" in metrics, "auroc" in metrics
        if not metrics & CLF_HEADLINE:
            headline_missing("CLASSIFICATION_METRIC_MISSING",
                             "discrimination or threshold metric (AUROC / AUPRC / sensitivity + "
                             "specificity / PPV / NPV / accuracy)")
        if acc and not auroc and not {"sensitivity", "specificity"} <= metrics:
            add("ACCURACY_ONLY", "Major",
                "accuracy is declared without AUROC (or a sensitivity + specificity pair) — accuracy "
                "is prevalence-dependent and misleading under imbalance", "metrics")
        if auroc and "auprc" not in metrics:
            add("AUPRC_MISSING", "Minor",
                "AUROC is declared without AUPRC — add AUPRC with the test-set prevalence (its "
                "no-skill value)", "metrics")
        if n_classes is not None and n_classes > 2 and (acc or auroc) and not averaging:
            add("MULTICLASS_NO_AVERAGING", "Minor",
                f"a {n_classes}-class classification declares AUROC/accuracy without an aggregation "
                "scheme (one-vs-rest, macro/micro, pairwise, Obuchowski)", "classification.averaging")
    elif task == "detection":
        if not metrics & DETECTION_M:
            add("DETECTION_METRIC_MISSING", "Major",
                "no detection metric (FROC / mAP) declared — patient-level accuracy is not a "
                "detection metric", "metrics")
        elif match in (None, "none"):
            add("DETECTION_METRIC_MISSING", "Major",
                "a detection metric is declared but no match criterion (IoU / centroid / mask "
                "threshold) — FROC and mAP are undefined without it", "detection.match_criterion")
    elif task == "generative":
        has_sim = bool(metrics & SIMILARITY)
        if has_sim and not downstream:
            add("GENERATIVE_NO_DOWNSTREAM", "Major",
                "image-quality similarity is declared without a downstream-task evaluation — "
                "similarity does not establish clinical utility", "generative.downstream_task")
        if not has_sim:
            add("GENERATIVE_NO_SIMILARITY", "Minor",
                "no image-quality metric declared (MSE / RMSE / MAE / PSNR / SSIM, or SNR / CNR)",
                "metrics")

    if ci is not True:
        add("CI_MISSING", "Minor",
            "no confidence interval declared for the headline metric", "ci_reported")

    for where, value in unlisted:
        effect = ("is recorded but satisfies no metric check" if where.startswith("metrics[")
                  else "counts as covering this field")
        add("UNLISTED_METHOD", "Minor",
            f"{value!r} is not on the allow-list; it {effect} — confirm it by eye", where)

    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {"manifest": path, "mode": "manifest", "basis": "declared", "task": task, "claims": claims,
            "summary": {"n_claims": len(claims), "n_major": n_major,
                        "verdict": "MAJOR_CANDIDATE" if n_major else "OK"}}


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append(f"| (none) | — | no issue found by the {result['task']} checks |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Task-correct metric-reporting gate (model-assessment).")
    ap.add_argument("--manifest", help="metrics_manifest.json with the declared metrics (preferred)")
    ap.add_argument("--report", help="metrics report / results markdown (prose mode)")
    ap.add_argument("--task",
                    choices=["segmentation", "classification", "detection", "interactive", "generative"])
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    if args.manifest is not None:
        if not Path(args.manifest).is_file():
            sys.stderr.write(f"ERROR: --manifest not found: {args.manifest}\n")
            return 2
        if args.report is not None:
            sys.stderr.write("NOTE: --manifest given; --report is not read\n")
        try:
            result = analyze_manifest(args.manifest, args.task)
        except (ManifestError, ValueError, OverflowError, RecursionError) as e:
            # any unreadable manifest is an input error (exit 2), never a Major (exit 1)
            sys.stderr.write(f"ERROR: {args.manifest}: {e}\n")
            return 2
    elif args.report is not None:
        if args.task is None:
            sys.stderr.write("ERROR: --task is required with --report\n")
            return 2
        if not Path(args.report).is_file():
            sys.stderr.write(f"ERROR: --report not found: {args.report}\n")
            return 2
        result = analyze(args.report, args.task)
    else:
        sys.stderr.write("ERROR: pass --manifest (preferred) or --report\n")
        return 2

    if not args.quiet:
        print("=" * 41)
        print(" Metric Reporting (model-assessment)")
        print("=" * 41)
        print(render(result))
        print()
        if result["mode"] == "prose":
            print("PROSE_MODE: keyword presence with a short negation window; declare the metrics "
                  "in --manifest for a field-level check.")
        else:
            print("Manifest mode: checks what is declared, not the reported numbers.")
        s = result["summary"]
        basis = " (as declared)" if result["mode"] == "manifest" else ""
        n_minor = s["n_claims"] - s["n_major"]
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} metric-reporting issue(s).")
        elif n_minor:
            print(f"No Major issue{basis}: {n_minor} Minor (see table).")
        else:
            print(f"OK{basis}: no metric-reporting issue found by the {result['task']} checks.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_metric_reporting", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
