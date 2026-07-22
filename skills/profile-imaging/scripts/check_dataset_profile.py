#!/usr/bin/env python3
"""Dataset-profile gate for a medical-imaging dataset (profile-imaging).

Before a single model trains, a dataset carries facts that decide the study: how
heterogeneous the acquisition is, how rare the target is, whether the labels are
intact, and whether the split you intend to call a *test set* actually has ground
truth. Those facts are cheap to compute and expensive to discover late — a "test
set" with no labels is found after the training run; a 0.4 %-foreground target is
found when accuracy reads 99.6 % and means nothing.

This gate reads the **dataset profile** emitted by `profile_imaging_dataset.py`
(one record per case: grid, spacing, orientation, label values, foreground
fraction) together with the researcher's **declared plan** (do we resample?
reorient? which loss? which metrics?), and decides each finding by rule and by
set arithmetic over the case records — never from prose, and never by opening an
image. It is stdlib-only: the profile is JSON, so the gate runs anywhere.

CHECKS (verdicts):
  MAJOR
  1. LABEL_SHAPE_MISMATCH     label grid differs from its image grid — the pair cannot
                              be used as supervision as-is.
  2. LABEL_EMPTY              a case declared labelled whose label has zero foreground.
  3. LABEL_VALUE_UNEXPECTED   label values outside the declared label set (a stray index
                              silently becomes a class, or a class is missing).
  4. TEST_SET_UNLABELLED      a split declared as test/held-out whose cases carry no
                              labels. It cannot produce Dice, HD95, or any metric; the
                              held-out set has to come from somewhere else.
  5. ACCURACY_UNDER_IMBALANCE the plan reports accuracy while the target occupies a tiny
                              fraction of the volume — predicting background everywhere
                              scores near-perfect. (Pairs with model-evaluation's
                              ACCURACY_ONLY, which catches the same error downstream.)

  MINOR (flags — each is a decision to declare, not necessarily a defect)
  6. SPACING_HETEROGENEOUS    spacing spans >= --spacing-ratio on some axis and the plan
                              declares no resampling.
  7. ORIENTATION_MIXED        more than one orientation code and no reorientation declared.
  8. INTENSITY_SCALE_INCONSISTENT  cases disagree on whether the intensity domain looks
                              like CT Hounsfield units — mixed modality, or a rescale
                              slope/intercept not applied to part of the cohort.
  9. EXTREME_IMBALANCE        median foreground fraction below --imbalance-frac and the
                              plan declares no Dice-family (region/overlap) loss.
 10. LABEL_MISSING            cases in a labelled split with no label file.

THRESHOLDS
  --spacing-ratio (default 2.0) and --imbalance-frac (default 0.01) are **screening
  defaults, not published cut-points**. 2x through-plane spacing changes what a
  fixed-size patch sees; 1 % foreground is where plain accuracy stops carrying
  information. Both are adjustable, and both are reported in the output so a reader
  knows what was applied.

PROFILE (JSON — emitted by profile_imaging_dataset.py)
  {
    "dataset": "...",
    "declared_labels": {"0": "background", "1": "spleen"},
    "plan": {"resample": true, "reorient": false, "loss": "dice_ce",
             "metrics": ["dice", "hd95"]},
    "splits": [{"name": "train", "labelled": true}, {"name": "test", "labelled": false}],
    "cases": [{"case": "...", "split": "train", "shape": [512,512,90],
               "spacing_mm": [0.79,0.79,5.0], "orientation": "RAS",
               "label_values": [0,1], "foreground_fraction": 0.0039,
               "intensity": {"p01": -1024.0, "p99": 329.0}, "flags": []}]
  }

INPUTS
  --profile   dataset profile JSON (required).

OUTPUT
  A findings table (stdout) and, with --out, a JSON artifact.
  Exit 1 under --strict when any Major finding exists.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median

TEST_SPLIT_NAMES = {"test", "holdout", "hold_out", "held_out", "heldout", "external", "eval"}
DICE_FAMILY = ("dice", "tversky", "focal_tversky", "jaccard", "iou", "generalized_dice", "gdl", "lovasz")
ACCURACY_TERMS = ("accuracy", "acc", "pixel_accuracy", "voxel_accuracy")
# A CT case is expected to bottom out near air (-1000 HU). Anything whose 1st percentile
# sits far above that is not on the HU scale.
CT_AIR_P01_MAX = -500.0


def _norm(s) -> str:
    return str(s).strip().lower()


def _plan(profile: dict) -> dict:
    p = profile.get("plan") or {}
    return {
        "resample": bool(p.get("resample")),
        "reorient": bool(p.get("reorient")),
        "loss": _norm(p.get("loss") or ""),
        "metrics": [_norm(m) for m in (p.get("metrics") or [])],
    }


def _labelled_splits(profile: dict) -> dict[str, bool]:
    out: dict[str, bool] = {}
    for s in profile.get("splits") or []:
        out[_norm(s.get("name"))] = bool(s.get("labelled", True))
    return out


def analyze(profile_path: str, spacing_ratio: float, imbalance_frac: float) -> dict:
    profile = json.loads(Path(profile_path).read_text(encoding="utf-8"))
    cases = profile.get("cases") or []
    plan = _plan(profile)
    labelled = _labelled_splits(profile)
    declared = {int(k) for k in (profile.get("declared_labels") or {}).keys()} or None

    claims: list[dict] = []

    def claim(verdict: str, severity: str, detail: str, cases_hit: list[str] | None = None) -> None:
        claims.append({"verdict": verdict, "severity": severity, "detail": detail,
                       "cases": sorted(cases_hit or [])[:12], "n_cases": len(cases_hit or [])})

    # ---- per-case integrity -------------------------------------------------
    shape_mismatch, empty, unexpected, missing = [], [], [], []
    for c in cases:
        split = _norm(c.get("split"))
        is_lab = labelled.get(split, True)
        flags = set(c.get("flags") or [])
        if "LABEL_SHAPE_MISMATCH" in flags:
            shape_mismatch.append(c["case"])
        if is_lab and ("LABEL_MISSING" in flags or c.get("label_values") is None):
            missing.append(c["case"])
            continue
        if c.get("label_values") is None:
            continue
        if is_lab and c.get("foreground_fraction") == 0:
            empty.append(c["case"])
        if declared is not None:
            stray = set(int(v) for v in c["label_values"]) - declared
            if stray:
                unexpected.append(c["case"])

    if shape_mismatch:
        claim("LABEL_SHAPE_MISMATCH", "Major",
              "label grid differs from the image grid; the pair is not usable supervision as-is",
              shape_mismatch)
    if empty:
        claim("LABEL_EMPTY", "Major",
              "case is in a labelled split but its label contains no foreground voxel", empty)
    if unexpected:
        claim("LABEL_VALUE_UNEXPECTED", "Major",
              f"label values outside the declared set {sorted(declared or [])}", unexpected)
    if missing:
        claim("LABEL_MISSING", "Minor",
              "case sits in a split declared labelled but has no label file", missing)

    # ---- an unlabelled test set --------------------------------------------
    for name, is_lab in labelled.items():
        if name in TEST_SPLIT_NAMES and not is_lab:
            n = sum(1 for c in cases if _norm(c.get("split")) == name)
            claim("TEST_SET_UNLABELLED", "Major",
                  f"split '{name}' ({n} case(s)) has no ground truth — it cannot yield Dice, "
                  "HD95, or any held-out metric; carve the held-out set from labelled data",
                  [])

    # ---- acquisition heterogeneity -----------------------------------------
    spacings = [c["spacing_mm"] for c in cases if c.get("spacing_mm")]
    ratios = []
    if spacings:
        for i, ax in enumerate("xyz"):
            vals = [s[i] for s in spacings if len(s) > i and s[i] > 0]
            if vals:
                ratios.append((ax, max(vals) / min(vals), min(vals), max(vals)))
        worst = max(ratios, key=lambda r: r[1]) if ratios else None
        if worst and worst[1] >= spacing_ratio and not plan["resample"]:
            claim("SPACING_HETEROGENEOUS", "Minor",
                  f"{worst[0]}-spacing spans {worst[2]:.3g}-{worst[3]:.3g} mm ({worst[1]:.1f}x) "
                  "and the plan declares no resampling", [])

    orients = sorted({c.get("orientation") for c in cases if c.get("orientation")})
    if len(orients) > 1 and not plan["reorient"]:
        claim("ORIENTATION_MIXED", "Minor",
              f"{len(orients)} orientation codes present ({', '.join(orients)}) and no "
              "reorientation declared", [])

    p01s = [c["intensity"]["p01"] for c in cases
            if isinstance(c.get("intensity"), dict) and c["intensity"].get("p01") is not None]
    if p01s:
        ct_like = [v for v in p01s if v <= CT_AIR_P01_MAX]
        if ct_like and len(ct_like) != len(p01s):
            claim("INTENSITY_SCALE_INCONSISTENT", "Minor",
                  f"{len(ct_like)}/{len(p01s)} cases bottom out near air (<= {CT_AIR_P01_MAX:g}) "
                  "and the rest do not — mixed modality, or a rescale not applied to part of "
                  "the cohort", [])

    # ---- class imbalance ----------------------------------------------------
    fgs = [c["foreground_fraction"] for c in cases if c.get("foreground_fraction") is not None]
    med_fg = median(fgs) if fgs else None
    if med_fg is not None and med_fg < imbalance_frac:
        if not any(t in plan["loss"] for t in DICE_FAMILY):
            claim("EXTREME_IMBALANCE", "Minor",
                  f"median foreground fraction {med_fg:.4%} is below {imbalance_frac:.2%} and the "
                  "plan declares no Dice-family loss", [])
        if any(m in ACCURACY_TERMS for m in plan["metrics"]):
            claim("ACCURACY_UNDER_IMBALANCE", "Major",
                  f"the plan reports accuracy at median foreground {med_fg:.4%} — predicting "
                  "background everywhere would score ~{:.2%}".format(1 - med_fg), [])

    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "profile": profile_path,
        "dataset": profile.get("dataset"),
        "n_cases": len(cases),
        "splits": {k: ("labelled" if v else "unlabelled") for k, v in labelled.items()},
        "plan": plan,
        "thresholds": {"spacing_ratio": spacing_ratio, "imbalance_frac": imbalance_frac},
        "median_foreground_fraction": med_fg,
        "claims": claims,
        "summary": {"n_claims": len(claims), "n_major": n_major,
                    "n_flag": len(claims) - n_major},
    }


def render(result: dict) -> str:
    if not result["claims"]:
        return "  (no findings)"
    lines = []
    for c in result["claims"]:
        head = f"  [{c['severity']:<5}] {c['verdict']}: {c['detail']}"
        lines.append(head)
        if c["cases"]:
            shown = ", ".join(c["cases"])
            more = f" (+{c['n_cases'] - len(c['cases'])} more)" if c["n_cases"] > len(c["cases"]) else ""
            lines.append(f"           cases: {shown}{more}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Dataset-profile gate for medical imaging.")
    ap.add_argument("--profile", required=True, help="dataset profile JSON")
    ap.add_argument("--spacing-ratio", type=float, default=2.0,
                    help="max/min spacing ratio that trips SPACING_HETEROGENEOUS (default 2.0)")
    ap.add_argument("--imbalance-frac", type=float, default=0.01,
                    help="median foreground fraction below which imbalance is flagged (default 0.01)")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.profile, args.spacing_ratio, args.imbalance_frac)

    if not args.quiet:
        print("=" * 41)
        print("  Dataset-Profile Gate (profile-imaging)")
        print("=" * 41)
        fg = result["median_foreground_fraction"]
        fg_s = f"{fg:.4%}" if fg is not None else "n/a"
        print(f"  cases={result['n_cases']}  splits={result['splits']}  median_fg={fg_s}")
        print(f"  thresholds: spacing_ratio={result['thresholds']['spacing_ratio']}  "
              f"imbalance_frac={result['thresholds']['imbalance_frac']}")
        print(render(result))
        print()
        s = result["summary"]
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} dataset defect(s) that block training as planned.")
        elif s["n_flag"]:
            print(f"MINOR flag: {s['n_flag']} dataset decision(s) to declare (see table).")
        else:
            print("OK: dataset profile is intact and the declared plan matches what the data looks like.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(
            json.dumps({"detector": "check_dataset_profile", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
