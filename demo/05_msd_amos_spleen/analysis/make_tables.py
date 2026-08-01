#!/usr/bin/env python3
"""Publication tables for Demo 5, derived from the per-case artifacts only.

Every cell traces to `../results/per_case_<arm>.csv` (one row per case, written by
`pipeline/evaluate_segmentation.py`) or to `../results/normalizer_evidence_<arm>.json`
(written by `pipeline/normalizer_modality_evidence.py`). Nothing is typed in by hand, and
nothing is re-derived from prose. Emits:

  tables/table1_cohort_characteristics.csv   who is in each arm, and how the images differ
  tables/table2_performance.csv              the headline metrics with bootstrap CIs
  tables/table3_subgroups.csv                the pre-specified subgroups, same cut-points every arm
  tables/table4_normalisation_evidence.csv   what the trained plan's normaliser does to each arm
  tables/key_scalars.csv                     the numbers the manuscript quotes inline

Bootstrap settings are the ones fixed in EVALUATION_PLAN.md and used by
`pipeline/aggregate_results.py`: 10,000 resamples, seed 20260725. The two scripts therefore
report identical medians and intervals; `reproduce.sh` checks that they do.

Cases whose reference contains no target are excluded from the metric distributions (Dice is
0/0 there) and counted on their own line instead — the rule was fixed before any prediction
existed, and the denominators in Table 2 are the visible consequence.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys

import numpy as np

SEED = 20260725
N_BOOT = 10_000

ARM_ORDER = ["rung1_msd_heldout", "rung2_amos_ct", "rung3_amos_mri",
             "rung3b_amos_mri_rescaled"]
ARM_LABEL = {
    "rung1_msd_heldout": "rung1 MSD held-out (internal)",
    "rung2_amos_ct": "rung2 AMOS CT (external)",
    "rung3_amos_mri": "rung3 AMOS MRI (modality shift)",
    "rung3b_amos_mri_rescaled": "rung3b AMOS MRI rescaled (counterfactual)",
}
# Cut-points are half-open on the LEFT of each edge: `bin_of` increments on `value >= edge`, so a
# case sitting exactly on an edge falls into the UPPER stratum. The labels say so literally
# (`<100`, not `<=100`), because they did not at first: they read "thin (<=2 mm)" while 67 of the
# 300 external CT cases sit at exactly 2.00 mm and were being placed in "mid". The stratum
# memberships never changed; the labels were describing a different rule from the one in the code.
VOL_EDGES, VOL_LABELS = [100.0, 250.0], [
    "small (<100 mL)", "normal (100-250 mL)", "enlarged (>=250 mL)"]
THK_EDGES, THK_LABELS = [2.0, 5.0], [
    "thin (<2 mm)", "mid (2-5 mm)", "thick (>=5 mm)"]


def read_arms(results_dir: str) -> dict[str, list[dict]]:
    arms: dict[str, list[dict]] = {}
    for arm in ARM_ORDER:
        path = os.path.join(results_dir, f"per_case_{arm}.csv")
        if not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            arms[arm] = list(csv.DictReader(fh))
    if not arms:
        print(f"FATAL: no per_case_*.csv in {results_dir}", file=sys.stderr)
        raise SystemExit(2)
    return arms


def col(rows: list[dict], key: str, only_scored: bool = False) -> np.ndarray:
    out = []
    for r in rows:
        if only_scored and r.get("dice", "") in ("", "nan", None):
            continue
        v = r.get(key, "")
        if v not in ("", "nan", "NaN", None):
            out.append(float(v))
    return np.asarray(out, dtype=float)


def arm_rng(*key):
    """A generator seeded from SEED and a STABLE hash of the key, so an arm's interval does not
    depend on how many other arms were bootstrapped before it. One shared stream made the seed
    reproducible only for a fixed arm ORDER: adding an arm silently moved intervals already
    published. `hash()` is deliberately NOT used here -- Python randomises string hashing per
    process (PYTHONHASHSEED), so it would have made the "deterministic" claim false in the act of
    fixing determinism. blake2b is stable across processes, machines and versions."""
    parts = [SEED]
    for k in key:
        parts.append(int.from_bytes(hashlib.blake2b(str(k).encode(), digest_size=4).digest(), "big"))
    return np.random.default_rng(parts)


def boot_median_ci(x: np.ndarray, rng) -> tuple[float, float, float]:
    if x.size == 0:
        return (float("nan"),) * 3
    med = float(np.median(x))
    if x.size == 1:
        return (med, med, med)
    idx = rng.integers(0, x.size, size=(N_BOOT, x.size))
    b = np.median(x[idx], axis=1)
    lo, hi = np.percentile(b, [2.5, 97.5])
    return (med, float(lo), float(hi))


def boot_delta_ci(x: np.ndarray, ref: np.ndarray, key_a, key_b) -> tuple[float, float, float]:
    """95% interval for the difference in population medians between two INDEPENDENT arms.

    A bare difference of two separately-estimated medians is not an inferential quantity: the two
    marginal intervals say nothing about the uncertainty of their difference, and here the reference
    arm has n=9, which contributes most of it. Both arms are resampled independently (cases are
    patients, one row each) and the difference is taken inside each replicate."""
    if x.size == 0 or ref.size == 0:
        return (float("nan"),) * 3
    ra, rb = arm_rng(key_a, "delta"), arm_rng(key_b, "delta_ref")
    ia = ra.integers(0, x.size, size=(N_BOOT, x.size))
    ib = rb.integers(0, ref.size, size=(N_BOOT, ref.size))
    d = np.median(x[ia], axis=1) - np.median(ref[ib], axis=1)
    lo, hi = np.percentile(d, [2.5, 97.5])
    return (float(np.median(x) - np.median(ref)), float(lo), float(hi))


def fmt_ci(t: tuple[float, float, float], nd: int = 4) -> str:
    m, lo, hi = t
    return "n/a" if m != m else f"{m:.{nd}f} [{lo:.{nd}f}-{hi:.{nd}f}]"


def iqr(x: np.ndarray, nd: int = 2) -> str:
    if x.size == 0:
        return "n/a"
    q1, med, q3 = np.percentile(x, [25, 50, 75])
    return f"{med:.{nd}f} ({q1:.{nd}f}-{q3:.{nd}f})"


def bin_of(v: float, edges, labels) -> str:
    i = 0
    for e in edges:
        if v >= e:
            i += 1
    return labels[i]


def write_csv(path: str, header: list[str], rows: list[list]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {path}  ({len(rows)} row(s))")


def main() -> int:
    ap = argparse.ArgumentParser(description="Demo 5 publication tables (derived, never typed).")
    ap.add_argument("--results-dir", default="../results")
    ap.add_argument("--out-dir", default="tables")
    a = ap.parse_args()

    arms = read_arms(a.results_dir)
    rng = np.random.default_rng(SEED)
    present = [x for x in ARM_ORDER if x in arms]

    # ---- Table 1: cohort characteristics -------------------------------------------------
    t1 = []
    for arm in present:
        rows = arms[arm]
        gt = col(rows, "gt_ml", only_scored=True)
        zs = col(rows, "spacing_z")
        inplane = col(rows, "spacing_x")
        t1.append([
            ARM_LABEL[arm], len(rows),
            sum(r["gt_empty"] == "1" for r in rows),
            iqr(gt, 1), f"{gt.min():.1f}-{gt.max():.1f}" if gt.size else "n/a",
            iqr(zs, 2), f"{zs.min():.2f}-{zs.max():.2f}" if zs.size else "n/a",
            f"{int((zs >= 5.0).sum())}/{zs.size}" if zs.size else "n/a",
            iqr(inplane, 3),
        ])
    write_csv(os.path.join(a.out_dir, "table1_cohort_characteristics.csv"),
              ["arm", "n_cases", "n_target_free",
               "spleen_volume_mL_median_IQR", "spleen_volume_mL_range",
               "slice_thickness_mm_median_IQR", "slice_thickness_mm_range",
               "n_thick_ge5mm", "in_plane_mm_median_IQR"], t1)

    # ---- Table 2: performance ------------------------------------------------------------
    ref_dice = None
    ref_vals = col(arms.get("rung1_msd_heldout", []), "dice")
    t2 = []
    for arm in present:
        rows = arms[arm]
        d = col(rows, "dice")
        h = col(rows, "hd95_mm")
        dice_ci = boot_median_ci(d, arm_rng(arm, 'dice'))
        if arm == "rung1_msd_heldout":
            ref_dice = dice_ci[0]
        if arm == "rung1_msd_heldout" or ref_dice is None:
            delta = ""
        else:
            dm, dlo, dhi = boot_delta_ci(d, ref_vals, arm, "rung1_msd_heldout")
            delta = f"{dm:+.4f} [{dlo:+.4f}-{dhi:+.4f}]"
        t2.append([
            ARM_LABEL[arm], len(rows), int(d.size),
            sum(r["gt_empty"] == "1" for r in rows),
            sum(r["pred_empty"] == "1" for r in rows),
            sum(r["gt_empty"] == "1" and r["pred_empty"] == "0" for r in rows),
            fmt_ci(dice_ci), f"{float(d.mean()):.4f}" if d.size else "n/a",
            f"{float(d.min()):.4f}" if d.size else "n/a",
            # HD95 has its OWN denominator and it is not n_scored: a non-empty reference with an
            # EMPTY prediction has a Dice of 0 but no predicted surface, so no HD95 exists for it.
            # Those are the worst cases in the arm, so an HD95 median quoted against n_scored is
            # optimistic by exactly the cases that failed hardest -- and the gap is widest on the
            # worst arm (rung 3: 40 of 59). The count is carried beside the value, never inferred.
            int(h.size), fmt_ci(boot_median_ci(h, arm_rng(arm, 'hd95')), 2), delta,
        ])
    write_csv(os.path.join(a.out_dir, "table2_performance.csv"),
              ["arm", "n_evaluated", "n_scored", "n_target_free", "n_empty_prediction",
               "n_false_positive_on_target_free", "dice_median_95CI", "dice_mean", "dice_min",
               "n_with_hd95", "hd95_mm_median_95CI", "delta_dice_vs_internal_95CI"], t2)

    # ---- Table 3: pre-specified subgroups ------------------------------------------------
    t3 = []
    for arm in present:
        rows = arms[arm]
        for axis, key, edges, labels in (
            ("spleen volume", "gt_ml", VOL_EDGES, VOL_LABELS),
            ("slice thickness", "spacing_z", THK_EDGES, THK_LABELS),
        ):
            buckets: dict[str, list[float]] = {lab: [] for lab in labels}
            for r in rows:
                if r.get("dice", "") in ("", "nan", None):
                    continue
                try:
                    buckets[bin_of(float(r[key]), edges, labels)].append(float(r["dice"]))
                except (KeyError, ValueError):
                    continue
            for lab in labels:
                arr = np.asarray(buckets[lab], dtype=float)
                t3.append([ARM_LABEL[arm], axis, lab, arr.size,
                           fmt_ci(boot_median_ci(arr, arm_rng(arm, key, lab)))])
    write_csv(os.path.join(a.out_dir, "table3_subgroups.csv"),
              ["arm", "subgroup_axis", "stratum", "n_scored", "dice_median_95CI"], t3)

    # ---- Table 4: normalisation evidence -------------------------------------------------
    t4 = []
    for arm in present:
        p = os.path.join(a.results_dir, f"normalizer_evidence_{arm}.json")
        if not os.path.exists(p):
            continue
        ev = json.load(open(p, encoding="utf-8"))
        c, n = ev["cohort"], ev["plan_normalisation"]
        t4.append([
            ARM_LABEL[arm], ev["n_cases"],
            "/".join(n["scheme"]) if isinstance(n["scheme"], list) else str(n["scheme"]),
            f"[{n['clip_lo']:.0f}, {n['clip_hi']:.0f}]",
            f"{n['mean']:.1f} / {n['std']:.1f}",
            f"{c['cases_with_any_negative_voxel']}/{ev['n_cases']}",
            f"{c['frac_above_clip_hi']['median']*100:.1f}% "
            f"({c['frac_above_clip_hi']['min']*100:.1f}-{c['frac_above_clip_hi']['max']*100:.1f})",
            f"{c['levels_surviving_clip']['median']:.0f} "
            f"({c['levels_surviving_clip']['min']:.0f}-{c['levels_surviving_clip']['max']:.0f})",
        ])
    if t4:
        write_csv(os.path.join(a.out_dir, "table4_normalisation_evidence.csv"),
                  ["arm", "n_cases", "normalisation_scheme_from_trained_plan", "clip_window_HU",
                   "zscore_mean_sd", "cases_with_any_negative_voxel",
                   "pct_voxels_above_clip_ceiling_median_range",
                   "intensity_levels_surviving_clip_median_range"], t4)

    # ---- key scalars the manuscript quotes inline ----------------------------------------
    ks = []
    for arm in present:
        rows = arms[arm]
        d = col(rows, "dice")
        m = boot_median_ci(d, arm_rng(arm, 'dice'))
        ks += [
            [f"{arm}_n_evaluated", len(rows)],
            [f"{arm}_n_scored", int(d.size)],
            [f"{arm}_dice_median", f"{m[0]:.4f}"],
            [f"{arm}_dice_ci_low", f"{m[1]:.4f}"],
            [f"{arm}_dice_ci_high", f"{m[2]:.4f}"],
            [f"{arm}_n_empty_prediction", sum(r["pred_empty"] == "1" for r in rows)],
        ]
    write_csv(os.path.join(a.out_dir, "key_scalars.csv"), ["key", "value"], ks)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
