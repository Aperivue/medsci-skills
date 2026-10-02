#!/usr/bin/env python3
"""Explainability-report rigor gate for a medical-imaging model (model-assessment).

A saliency / Grad-CAM map is the most over-interpreted artifact in medical-imaging AI:
a colourful heat-map over the lesion is routinely presented as proof the model is
"looking at the right thing" — yet Adebayo et al. (NeurIPS 2018) showed many saliency
methods produce visually convincing maps that are *independent of the model's learned
weights and of the labels*, so they explain nothing. An explainability analysis is only
trustworthy when it (a) passes sanity checks (model- and data-randomisation), (b) reports
a *quantitative* localisation metric against ground truth rather than eyeballed examples,
(c) is computed over a cohort rather than a handful of cherry-picked cases, and (d) is
framed as attribution, not as validation of correctness or as causal evidence
(CLAIM 2024 / TRIPOD+AI interpretability items).

This gate reads a declarative **explainability-report manifest** (JSON — the artifact
this skill emits, or one the researcher writes) and decides each requirement by rule,
not from prose.

CHECKS (verdicts):
  1. SALIENCY_AS_VALIDATION  (Major)  the map is framed as validation / correctness / causal
                                      evidence (interpretation=validation/causal/proof). A
                                      saliency map is attribution, not proof the model is right.
  2. NO_SANITY_CHECK         (Major)  no sanity check declared. Adebayo et al. randomisation
                                      tests are the minimum bar; a map that survives neither is
                                      uninterpretable.
  3. NO_LOCALIZATION_METRIC  (Major)  a localisation / faithfulness claim with no quantitative
                                      metric (IoU / pointing game / Dice vs ground truth) — the
                                      map "hits the lesion" is asserted, never measured.
  4. INSUFFICIENT_SANITY     (Minor)  a sanity check is declared but not both the model- and
                                      the data-randomisation axis (Adebayo recommends both).
  5. CHERRY_PICKED_EXAMPLES  (Minor)  no cohort-level result — only illustrative examples, so
                                      the reader cannot tell how often the map behaves this way.
  6. MISSING_METHOD          (Minor)  no XAI method named — the analysis is not reproducible.

MANIFEST (JSON)
  {
    "method": "grad-cam",                 // grad-cam / gradcam++ / saliency / attention_rollout /
                                          // integrated_gradients / shap / ...
    "n_examples": 200,
    "cohort_level": true,                 // an aggregate result over the cohort (not just examples)
    "localization_metric": "iou",         // iou / pointing_game / dice / none
    "localization_value": 0.63,
    "sanity_checks": ["model_randomization", "data_randomization"],
    "interpretation": "localization"      // localization / faithfulness / attribution /
                                          // explanation / validation / causal
  }
  Values are enumerated (case and separators normalised). An unrecognised
  `interpretation` or `sanity_checks` entry is an input error (exit 2); a none-like
  sanity entry ("none", "not performed") counts as no sanity check.

INPUTS
  --manifest  explainability-report manifest JSON (required).

OUTPUT
  A reconciliation table (stdout) and, with --out, a JSON artifact:
    {manifest, method, n_examples, cohort_level, localization_metric, sanity_checks,
     interpretation, claims[{verdict, severity, detail, where}], summary}
  SALIENCY_AS_VALIDATION / NO_SANITY_CHECK / NO_LOCALIZATION_METRIC are Major.

Stdlib-only (json / argparse / pathlib). Exit codes: 0 clean (or report-only),
1 Major claim(s) found (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Enumerated vocabularies, keyed on _key() (lower-case, separators -> "_", British -s- -> -z-).
# A value outside the vocabulary is an input error (exit 2): free text such as "the map
# proves the model is correct" used to match no set and cleared the Major
# SALIENCY_AS_VALIDATION check.
VALIDATION_INTERP = {
    "validation", "validate", "validated", "causal", "causation", "causality",
    "proof", "proves", "correctness", "ground_truth", "verifies",
    "verification", "confirms",
}
LOCALIZATION_INTERP = {
    "localization", "faithfulness", "faithful", "correctness",
    "attention_correctness", "region",
}
DESCRIPTIVE_INTERP = {"attribution", "explanation", "descriptive", "exploratory",
                      "hypothesis_generating", "illustrative", "qualitative"}
KNOWN_INTERP = VALIDATION_INTERP | LOCALIZATION_INTERP | DESCRIPTIVE_INTERP
NO_METRIC_VALUES = {"", "none", "na", "n/a", "no", "false", "eyeball", "visual", "qualitative"}

# sanity_checks vocabulary. A none-like entry ("none", "not performed") declares NO check —
# it used to count as a declared check and downgraded the Major NO_SANITY_CHECK to a Minor.
# Each axis is matched exactly, not by substring ("metadata_check" is not data randomisation).
SANITY_NONE = {"", "none", "no", "na", "n_a", "false", "null", "nil", "not_performed",
               "not_done", "not_applicable", "not_assessed", "not_run", "skipped", "omitted"}
SANITY_MODEL = {"model_randomization", "model_parameter_randomization",
                "parameter_randomization", "weight_randomization",
                "cascading_randomization", "cascading_model_randomization",
                "independent_randomization", "independent_layer_randomization",
                "model_randomization_test", "model_parameter_randomization_test"}
SANITY_DATA = {"data_randomization", "label_randomization", "data_label_randomization",
               "label_permutation", "permuted_labels", "data_randomization_test",
               "label_randomization_test"}
# recognised checks that are neither Adebayo randomisation axis
SANITY_OTHER = {"roar", "remove_and_retrain", "deletion", "insertion", "deletion_curve",
                "insertion_curve", "infidelity", "sensitivity_n", "max_sensitivity",
                "input_invariance", "pixel_perturbation", "perturbation"}
KNOWN_SANITY = SANITY_MODEL | SANITY_DATA | SANITY_OTHER


def _norm(s) -> str:
    return str(s).strip().lower() if s is not None else ""


def _key(s) -> str:
    """Canonical vocabulary key: 'Model randomisation' -> 'model_randomization'."""
    k = re.sub(r"[^a-z0-9]+", "_", _norm(s)).strip("_")
    return k.replace("randomisation", "randomization").replace("localisation", "localization")


def _sanity_list(raw) -> list:
    if raw is None or raw is False:
        return []
    if isinstance(raw, list):
        return raw
    return [raw]


def validate(manifest: dict) -> list[str]:
    """Input errors that would otherwise make a check silently skip (-> exit 2)."""
    errors = []
    raw_interp = manifest.get("interpretation")
    if raw_interp is not None:
        if not isinstance(raw_interp, str) or _key(raw_interp) not in KNOWN_INTERP:
            errors.append(
                f"unrecognised interpretation {raw_interp!r}; use one of attribution / explanation / "
                f"localization / faithfulness (or validation / causal, which the gate flags) — free "
                f"text cannot be checked for a validation or causal framing")
    for s in _sanity_list(manifest.get("sanity_checks")):
        k = _key(s) if isinstance(s, str) else None
        if k is None or (k not in SANITY_NONE and k not in KNOWN_SANITY):
            errors.append(
                f"unrecognised sanity_checks entry {s!r}; use model_randomization / "
                f"data_randomization (Adebayo et al.), another named check (roar, deletion, "
                f"insertion, infidelity), or none")
    return errors


def check(manifest: dict) -> list[dict]:
    claims: list[dict] = []
    method = manifest.get("method")
    cohort = manifest.get("cohort_level")
    loc_metric = _norm(manifest.get("localization_metric"))
    # none-like entries ("none", "not performed") declare no check at all
    sanity = [s for s in _sanity_list(manifest.get("sanity_checks"))
              if _key(s) not in SANITY_NONE]
    interp = _key(manifest.get("interpretation") or "explanation")

    # 1. Saliency framed as validation / causal evidence.
    if interp in VALIDATION_INTERP:
        claims.append({
            "verdict": "SALIENCY_AS_VALIDATION", "severity": "Major",
            "detail": (f"the saliency map is framed as '{interp}'; a saliency/attribution map "
                       f"shows where signal is attributed, not that the model is correct or that "
                       f"the relationship is causal"),
            "where": "interpretation",
        })

    # 2. No sanity check at all.
    if not sanity:
        claims.append({
            "verdict": "NO_SANITY_CHECK", "severity": "Major",
            "detail": ("no sanity check declared; Adebayo et al. model- and data-randomisation "
                       "tests are the minimum bar for a trustworthy saliency analysis"),
            "where": "sanity_checks",
        })

    # 3. Localisation/faithfulness claim without a quantitative metric.
    loc_ok = bool(loc_metric) and loc_metric not in NO_METRIC_VALUES
    if interp in LOCALIZATION_INTERP and not loc_ok:
        claims.append({
            "verdict": "NO_LOCALIZATION_METRIC", "severity": "Major",
            "detail": (f"interpretation='{interp}' asserts the map localises the finding, but no "
                       f"quantitative localisation metric (IoU / pointing game / Dice vs ground "
                       f"truth) is reported ('{loc_metric or 'missing'}')"),
            "where": "localization_metric",
        })

    # 4. Sanity check present but not both randomisation axes.
    sset = {_key(s) for s in sanity}
    if sanity:
        has_model = bool(sset & SANITY_MODEL)
        has_data = bool(sset & SANITY_DATA)
        if not (has_model and has_data):
            if not has_model and not has_data:
                missing = "model- and data-randomisation tests are"
            elif has_model:
                missing = "data-randomisation test is"
            else:
                missing = "model-randomisation test is"
            claims.append({
                "verdict": "INSUFFICIENT_SANITY", "severity": "Minor",
                "detail": (f"sanity checks declared ({', '.join(sorted(sset))}) but the "
                           f"{missing} missing; Adebayo et al. recommend both axes"),
                "where": "sanity_checks",
            })

    # 5. No cohort-level result.
    if cohort is not True:
        claims.append({
            "verdict": "CHERRY_PICKED_EXAMPLES", "severity": "Minor",
            "detail": ("no cohort-level result declared (cohort_level != true); illustrative "
                       "examples alone cannot show how often the map behaves as claimed"),
            "where": "cohort_level",
        })

    # 6. No XAI method named.
    if not method:
        claims.append({
            "verdict": "MISSING_METHOD", "severity": "Minor",
            "detail": "no XAI method named; the explainability analysis is not reproducible",
            "where": "method",
        })

    return claims


def analyze(manifest_path: str) -> dict:
    p = Path(manifest_path)
    if not p.is_file():
        sys.stderr.write(f"ERROR: manifest not found: {manifest_path}\n")
        sys.exit(2)
    try:
        manifest = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError) as e:
        sys.stderr.write(f"ERROR: manifest is not valid JSON: {e}\n")
        sys.exit(2)
    if not isinstance(manifest, dict):
        sys.stderr.write("ERROR: manifest JSON must be an object\n")
        sys.exit(2)

    errors = validate(manifest)
    if errors:
        for e in errors:
            sys.stderr.write(f"ERROR: {e}\n")
        sys.exit(2)
    claims = check(manifest)
    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "manifest": str(p),
        "method": manifest.get("method"),
        "n_examples": manifest.get("n_examples"),
        "cohort_level": manifest.get("cohort_level"),
        "localization_metric": manifest.get("localization_metric"),
        "sanity_checks": manifest.get("sanity_checks") or [],
        "interpretation": manifest.get("interpretation"),
        "claims": claims,
        "summary": {
            "n_claims": len(claims),
            "n_major": n_major,
            "n_flag": len(claims) - n_major,
            "verdict": "MAJOR_CANDIDATE" if n_major else "OK",
        },
    }


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | explainability report meets the rigor bar |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Explainability-report rigor gate.")
    ap.add_argument("--manifest", required=True, help="explainability-report manifest JSON")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.manifest)

    if not args.quiet:
        print("=" * 41)
        print(" Explainability-Report Gate (model-assessment)")
        print("=" * 41)
        print(f"  method={result['method']}  n_examples={result['n_examples']}  "
              f"cohort_level={result['cohort_level']}  "
              f"localization_metric={result['localization_metric']}  "
              f"interpretation={result['interpretation']}")
        print(render(result))
        print()
        s = result["summary"]
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} explainability-rigor issue(s).")
        elif s["n_flag"]:
            print(f"MINOR flag: {s['n_flag']} explainability-rigor issue(s) (see table).")
        else:
            print("OK: explainability report meets the rigor bar.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_explainability_report", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
