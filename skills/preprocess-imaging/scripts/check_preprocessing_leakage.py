#!/usr/bin/env python3
"""Data-stage preprocessing-leakage gate for a medical-imaging pipeline (preprocess-imaging).

`model-validation`'s split-leakage gate proves the train/val/test *split* is
patient-disjoint. But leakage also enters one stage earlier — in **preprocessing** —
and the split table cannot see it. The three classic data-stage leaks
(Kapoor & Narayanan, Patterns 2023; Varoquaux & Cheplygina, npj Digit Med 2022;
CLAIM 2024 data-partition/preprocessing items) are:

  1. fitting a dataset-level normalisation / scaler on data that is NOT the training
     split (the test intensity distribution leaks into training);
  2. running any data-fitted transform BEFORE the split exists (there is no train/test
     distinction yet, so the fit is inherently cross-partition);
  3. the same patient's slices landing in more than one split (slice-level overlap that
     a per-image manifest hides).

This gate reads a declarative **preprocessing manifest** (JSON — the artifact this
skill emits, or one the researcher writes) and decides each of these by rule and by
set arithmetic on the patient IDs, not from prose. A *per-image* / *per-sample*
transform (each image normalised by its own statistics) is leakage-free and never
fires; only a *dataset-fitted* transform can leak.

CHECKS (verdicts):
  1. PREPROCESS_BEFORE_SPLIT  (Major)  a data-fitted transform runs before the split
                                       (stage=before_split) — the fit spans partitions.
  2. NORMALIZATION_LEAKAGE    (Major)  a data-fitted transform is fit on a non-train
                                       scope (all/full/dataset/test/both) after the split.
  3. PATIENT_CROSS_SPLIT      (Major)  a patient_id whose units appear in >= 2 splits.
  4. AUGMENTATION_ON_EVAL     (Minor)  an augmentation is applied to val/test (train-time
                                       augmentation folded into evaluation / undisclosed TTA).
  5. UNSPECIFIED_FIT_SCOPE    (Minor)  a data-fitted transform declares no fit_scope — the
                                       leak cannot be ruled out; declare train-only.
  6. MISSING_SEED             (Minor)  no split_seed — the split cannot be regenerated.

A data-fitted transform is one whose `type` is a fitted operation (normalization,
standardize, scaler, min-max, clip_percentile, histogram_match, pca, whitening,
feature_selection, …) AND whose `fit_scope` is not per-sample/none. A fixed transform
(fixed HU window, resample to a fixed spacing) is not data-fitted and never leaks.

MANIFEST (JSON)
  {
    "split_seed": 42,
    "transforms": [
      {"name": "...", "type": "standardize", "fit_scope": "train", "stage": "after_split"},
      {"name": "...", "type": "augmentation", "stage": "after_split", "applies_to": ["train"]}
    ],
    "split_assignment": [
      {"patient_id": "P001", "unit_id": "P001_s1", "split": "train"}, ...
    ]
  }
  fit_scope   : train / training / train_val / dev  -> OK; all / full / dataset / test /
                both / combined -> leak; sample / per_image / instance / none -> not data-fitted.
  stage       : before_split / after_split (synonyms: pre-split / post-split).
  split       : train/val/test synonyms collapse (training/validation/holdout/…).

INPUTS
  --manifest  preprocessing manifest JSON (required).

OUTPUT
  A reconciliation table (stdout) and, with --out, a JSON artifact:
    {manifest, n_transforms, n_units, n_patients, partitions{name:count}, seed,
     claims[{verdict, severity, detail, where}], summary}
  PREPROCESS_BEFORE_SPLIT / NORMALIZATION_LEAKAGE / PATIENT_CROSS_SPLIT are Major.

Stdlib-only (json / argparse / pathlib). Exit codes: 0 clean (or report-only),
1 Major claim(s) found (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Transform types whose parameters are FIT from data (so their fit scope matters).
FIT_BASED_TYPES = {
    "normalization", "normalize", "normalisation", "standardize", "standardise",
    "standardization", "zscore", "z-score", "z_score", "scaler", "scaling",
    "minmax", "min-max", "min_max", "clip_percentile", "percentile_clip",
    "percentile_clipping", "histogram_match", "histogram_matching",
    "histogram_equalization", "histogram_equalisation", "pca", "whitening",
    "feature_selection", "intensity_normalization", "intensity_normalisation",
    "nyul", "zca",
}
# fit_scope values that make a transform NOT data-fitted (per-sample or fixed).
SAMPLE_SCOPES = {
    "sample", "per_sample", "per-sample", "per_image", "per-image", "perimage",
    "instance", "per_instance", "none", "fixed", "self",
}
# fit_scope values that leak (fit touches non-training data).
NON_TRAIN_SCOPES = {
    "all", "full", "dataset", "entire", "everything", "combined", "both",
    "test", "testing", "holdout", "hold-out", "trainvaltest", "train_val_test",
    "train+test", "all_data", "whole",
}
TRAIN_OK_SCOPES = {
    "train", "training", "train_val", "trainval", "train+val", "development",
    "dev", "fold_train", "train_only",
}
BEFORE_STAGES = {"before_split", "before-split", "pre_split", "pre-split", "before", "pre"}
SPLIT_SYNONYM = {
    "train": "train", "training": "train",
    "val": "val", "validation": "val", "valid": "val", "dev": "val",
    "test": "test", "testing": "test", "holdout": "test", "hold-out": "test",
    "eval": "test", "evaluation": "test",
}
EVAL_SPLITS = {"val", "test"}


def _norm(s) -> str:
    return str(s).strip().lower() if s is not None else ""


def _is_fit_based(t: dict) -> bool:
    typ = _norm(t.get("type"))
    scope = _norm(t.get("fit_scope"))
    if typ not in FIT_BASED_TYPES:
        return False
    if scope in SAMPLE_SCOPES:
        return False
    return True


def check(manifest: dict) -> list[dict]:
    claims: list[dict] = []
    transforms = manifest.get("transforms") or []

    for t in transforms:
        name = t.get("name") or t.get("type") or "(unnamed)"
        typ = _norm(t.get("type"))
        scope = _norm(t.get("fit_scope"))
        stage = _norm(t.get("stage"))

        if _is_fit_based(t):
            if stage in BEFORE_STAGES:
                claims.append({
                    "verdict": "PREPROCESS_BEFORE_SPLIT", "severity": "Major",
                    "detail": (f"data-fitted transform '{name}' ({typ}) runs before the split "
                               f"(stage=before_split); the fit spans train and test"),
                    "where": name,
                })
            elif scope in NON_TRAIN_SCOPES:
                claims.append({
                    "verdict": "NORMALIZATION_LEAKAGE", "severity": "Major",
                    "detail": (f"data-fitted transform '{name}' ({typ}) is fit on a non-train "
                               f"scope ('{scope}'); test-set statistics leak into training"),
                    "where": name,
                })
            elif scope not in TRAIN_OK_SCOPES:
                # data-fitted, after split, but fit_scope undeclared/unknown -> ambiguous
                claims.append({
                    "verdict": "UNSPECIFIED_FIT_SCOPE", "severity": "Minor",
                    "detail": (f"data-fitted transform '{name}' ({typ}) declares no train-only "
                               f"fit_scope ('{scope or 'missing'}'); declare fit_scope=train so "
                               f"leakage can be ruled out"),
                    "where": name,
                })

        if typ in ("augmentation", "augment", "aug"):
            applies = [_norm(x) for x in (t.get("applies_to") or [])]
            applies = {SPLIT_SYNONYM.get(a, a) for a in applies}
            leaked = sorted(applies & EVAL_SPLITS)
            if leaked:
                claims.append({
                    "verdict": "AUGMENTATION_ON_EVAL", "severity": "Minor",
                    "detail": (f"augmentation '{name}' is applied to {'/'.join(leaked)}; "
                               f"train-time augmentation on an evaluation split folds "
                               f"undisclosed test-time augmentation into the reported metric"),
                    "where": name,
                })

    # Patient-level cross-split (set arithmetic).
    rows = manifest.get("split_assignment") or []
    pat_to_splits: dict[str, set] = {}
    for r in rows:
        pid = r.get("patient_id") or r.get("subject_id") or r.get("patient") or r.get("id")
        sp = SPLIT_SYNONYM.get(_norm(r.get("split")), _norm(r.get("split")))
        if pid is None or not sp:
            continue
        pat_to_splits.setdefault(str(pid), set()).add(sp)
    offenders = sorted(p for p, s in pat_to_splits.items() if len(s) >= 2)
    if offenders:
        ex = offenders[0]
        claims.append({
            "verdict": "PATIENT_CROSS_SPLIT", "severity": "Major",
            "detail": (f"{len(offenders)} of {len(pat_to_splits)} patients have units in "
                       f">= 2 splits (e.g. '{ex}' in {'/'.join(sorted(pat_to_splits[ex]))}); "
                       f"the same patient in train and test inflates every metric. "
                       f"Offenders: {', '.join(offenders)}"),
            "where": ex,
        })

    # Reproducibility.
    if manifest.get("split_seed") is None and rows:
        claims.append({
            "verdict": "MISSING_SEED", "severity": "Minor",
            "detail": "no split_seed recorded; the split cannot be regenerated or re-verified",
            "where": "split_seed",
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

    claims = check(manifest)
    rows = manifest.get("split_assignment") or []
    partitions: dict[str, int] = {}
    patients: set = set()
    for r in rows:
        sp = SPLIT_SYNONYM.get(_norm(r.get("split")), _norm(r.get("split")))
        if sp:
            partitions[sp] = partitions.get(sp, 0) + 1
        pid = r.get("patient_id") or r.get("subject_id") or r.get("patient") or r.get("id")
        if pid is not None:
            patients.add(str(pid))
    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "manifest": str(p),
        "n_transforms": len(manifest.get("transforms") or []),
        "n_units": len(rows),
        "n_patients": len(patients),
        "partitions": dict(sorted(partitions.items())),
        "seed": manifest.get("split_seed"),
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
        lines.append("| (none) | — | preprocessing manifest is leakage-safe |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Data-stage preprocessing-leakage gate.")
    ap.add_argument("--manifest", required=True, help="preprocessing manifest JSON")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.manifest)

    if not args.quiet:
        print("=" * 41)
        print(" Preprocessing-Leakage Gate (preprocess-imaging)")
        print("=" * 41)
        p = result
        print(f"  transforms={p['n_transforms']}  units={p['n_units']}  "
              f"patients={p['n_patients']}  partitions={p['partitions']}  seed={p['seed']}")
        print(render(result))
        print()
        s = result["summary"]
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} preprocessing-leakage issue(s).")
        elif s["n_flag"]:
            print(f"MINOR flag: {s['n_flag']} preprocessing hygiene issue(s) (see table).")
        else:
            print("OK: preprocessing manifest is leakage-safe.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_preprocessing_leakage", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
