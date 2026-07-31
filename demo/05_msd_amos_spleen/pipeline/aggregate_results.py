#!/usr/bin/env python3
"""Aggregate the per-case segmentation results into the pre-specified across-cohort summary.

Consumes the per-case CSVs written by evaluate_segmentation.py (results/per_case_<arm>.csv) and
produces the analysis EVALUATION_PLAN.md pre-specifies:

  §2  median Dice and median HD95 per arm, each with a bootstrap 95% CI over cases
      (10,000 resamples, seed recorded). Accuracy is never computed.
  §7  pre-specified subgroups, the SAME fixed cut-points applied to every arm (no data-driven,
      per-arm tertiles — a cut-point must be single-source and identical across cohorts, or the
      subgroups are not comparable):
        - spleen volume (gt_ml): small <100, normal 100-250, enlarged >250 mL
          (the plan's stated normal range ~100-250 mL; splenomegaly = enlarged)
        - slice thickness (spacing_z): thin <=2.0, mid 2.0-5.0, thick >=5.0 mm
        - modality: the arm itself (rung2 CT vs rung3 MRI), by construction
  §4  target-free cases (gt_empty=1) are NOT scored as Dice; a prediction on a target-free case
      (a hallucinated organ) is reported on its own line, never folded into a silent zero.

Across-cohort: rung1 (internal) is the reference; each external arm's Delta-from-internal (the
honest drop) is reported. This is the table behind make-figures external_validation_comparison.

Runs on the per-case CSVs that exist NOW (rung1 only) and re-runs unchanged once rung2/rung3 land.
Deterministic: numpy default_rng(SEED). numpy + stdlib only.
"""
from __future__ import annotations

import argparse
import csv
import glob
import os
import sys

import numpy as np

SEED = 20260725
N_BOOT = 10_000

# Fixed, recorded cut-points (identical across all arms — see module docstring).
VOL_EDGES = [100.0, 250.0]          # mL: small | normal | enlarged
VOL_LABELS = ["small (<100 mL)", "normal (100-250 mL)", "enlarged (>250 mL)"]
THK_EDGES = [2.0, 5.0]              # mm: thin | mid | thick
THK_LABELS = ["thin (<=2 mm)", "mid (2-5 mm)", "thick (>=5 mm)"]

# Arm ordering + display; rung1 is the internal reference.
ARM_ORDER = ["rung1_msd_heldout", "rung2_amos_ct", "rung3_amos_mri"]
ARM_LABEL = {
    "rung1_msd_heldout": "rung1 MSD held-out (internal)",
    "rung2_amos_ct": "rung2 AMOS CT (external)",
    "rung3_amos_mri": "rung3 AMOS MRI (modality shift)",
}


def _bin(value: float, edges: list[float], labels: list[str]) -> str:
    idx = 0
    for e in edges:
        if value >= e:
            idx += 1
    return labels[idx]


def load_rows(results_dir: str) -> dict[str, list[dict]]:
    arms: dict[str, list[dict]] = {}
    for path in sorted(glob.glob(os.path.join(results_dir, "per_case_*.csv"))):
        with open(path) as f:
            rows = list(csv.DictReader(f))
        if not rows:
            continue
        arm = rows[0]["arm"]
        arms[arm] = rows
    return arms


def _floats(rows: list[dict], key: str) -> np.ndarray:
    """Scored values only: blank means the metric was not computed (e.g. empty GT)."""
    out = []
    for r in rows:
        v = r.get(key, "")
        if v not in ("", "nan", "NaN", None):
            out.append(float(v))
    return np.asarray(out, dtype=float)


def boot_median_ci(x: np.ndarray, rng: np.random.Generator) -> tuple[float, float, float]:
    if x.size == 0:
        return (float("nan"), float("nan"), float("nan"))
    med = float(np.median(x))
    if x.size == 1:
        return (med, med, med)
    idx = rng.integers(0, x.size, size=(N_BOOT, x.size))
    boot = np.median(x[idx], axis=1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return (med, float(lo), float(hi))


def _fmt(t: tuple[float, float, float]) -> str:
    m, lo, hi = t
    if m != m:  # nan
        return "n/a"
    return f"{m:.4f} [{lo:.4f}-{hi:.4f}]"


def summarise_arm(rows: list[dict], rng: np.random.Generator) -> dict:
    scored = [r for r in rows if r.get("dice", "") not in ("", "nan", None)]
    dice = _floats(rows, "dice")
    hd95 = _floats(rows, "hd95_mm")
    target_free = [r for r in rows if r.get("gt_empty", "0") == "1"]
    # a target-free case with a non-empty prediction = hallucinated organ (report separately)
    hallucinated = [r for r in target_free if r.get("pred_empty", "0") == "0"]
    return {
        "n_total": len(rows),
        "n_scored": len(scored),
        "n_target_free": len(target_free),
        "n_hallucinated_on_target_free": len(hallucinated),
        "hallucinated_cases": [r["case"] for r in hallucinated],
        "dice": boot_median_ci(dice, rng),
        "hd95": boot_median_ci(hd95, rng),
    }


def subgroup_table(rows: list[dict], key: str, edges, labels, rng) -> list[tuple[str, int, tuple]]:
    buckets: dict[str, list[float]] = {lab: [] for lab in labels}
    for r in rows:
        if r.get("dice", "") in ("", "nan", None):
            continue
        try:
            v = float(r[key])
        except (KeyError, ValueError):
            continue
        buckets[_bin(v, edges, labels)].append(float(r["dice"]))
    out = []
    for lab in labels:
        arr = np.asarray(buckets[lab], dtype=float)
        out.append((lab, arr.size, boot_median_ci(arr, rng)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default="results")
    ap.add_argument("--out", default="results/summary_across_cohorts.md")
    ap.add_argument("--figure", default="", help="optional PNG path (requires matplotlib)")
    a = ap.parse_args()

    arms = load_rows(a.results_dir)
    if not arms:
        print(f"FATAL: no per_case_*.csv in {a.results_dir}", file=sys.stderr)
        return 1

    rng = np.random.default_rng(SEED)
    present = [x for x in ARM_ORDER if x in arms] + [x for x in arms if x not in ARM_ORDER]
    summ = {arm: summarise_arm(arms[arm], rng) for arm in present}

    ref = summ.get("rung1_msd_heldout")
    L = []
    L.append("# Demo 5 - across-cohort segmentation results\n")
    L.append(f"Bootstrap: {N_BOOT} resamples, seed {SEED}. Metric CIs are median [2.5-97.5 pct].")
    L.append("Accuracy is not reported (target ~0.2-0.4% of volume). Dice/HD95 on scored cases only.\n")
    L.append("## Per-arm summary (Dice, HD95, Delta-Dice from internal)\n")
    L.append("| arm | n scored | Dice median [95% CI] | HD95 mm median [95% CI] | dDice vs internal |")
    L.append("|---|---:|---|---|---|")
    for arm in present:
        s = summ[arm]
        dd = ""
        if ref and arm != "rung1_msd_heldout" and s["dice"][0] == s["dice"][0] and ref["dice"][0] == ref["dice"][0]:
            dd = f"{s['dice'][0] - ref['dice'][0]:+.4f}"
        L.append(f"| {ARM_LABEL.get(arm, arm)} | {s['n_scored']} | {_fmt(s['dice'])} | {_fmt(s['hd95'])} | {dd} |")
    L.append("")

    # target-free / hallucination lines (§4)
    L.append("## Target-free cases (§4 - never a silent zero)\n")
    for arm in present:
        s = summ[arm]
        note = "none" if s["n_target_free"] == 0 else (
            f"{s['n_target_free']} target-free; "
            f"{s['n_hallucinated_on_target_free']} predicted a (false) organ "
            f"{s['hallucinated_cases'] or ''}")
        L.append(f"- {ARM_LABEL.get(arm, arm)}: {note}")
    L.append("")

    # subgroups (§7), same fixed cut-points every arm
    L.append("## Pre-specified subgroups (§7 - identical cut-points across arms)\n")
    L.append(f"Volume edges {VOL_EDGES} mL; slice-thickness edges {THK_EDGES} mm (fixed, recorded).\n")
    for arm in present:
        L.append(f"### {ARM_LABEL.get(arm, arm)}")
        for title, key, edges, labels in (
            ("Spleen volume (gt_ml)", "gt_ml", VOL_EDGES, VOL_LABELS),
            ("Slice thickness (spacing_z)", "spacing_z", THK_EDGES, THK_LABELS),
        ):
            L.append(f"- **{title}**")
            for lab, n, ci in subgroup_table(arms[arm], key, edges, labels, rng):
                L.append(f"    - {lab}: n={n}, Dice {_fmt(ci)}")
        L.append("")

    text = "\n".join(L)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w") as f:
        f.write(text)
    print(text)
    print(f"\nwrote {a.out}")

    if a.figure:
        try:
            _make_figure(present, summ, ref, a.figure)
            print(f"wrote {a.figure}")
        except Exception as e:  # figure is optional; never fail the analysis on it
            print(f"(figure skipped: {e})", file=sys.stderr)
    return 0


def _make_figure(present, summ, ref, path):
    """Across-cohort Dice with bootstrap CI (make-figures external_validation_comparison anatomy):
    internal as the reference row, each cohort a point + 95% CI, the honest drop read at a glance."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    arms = [x for x in present if summ[x]["dice"][0] == summ[x]["dice"][0]]
    y = list(range(len(arms)))[::-1]
    fig, ax = plt.subplots(figsize=(8.0, 0.85 * len(arms) + 1.9))
    for yi, arm in zip(y, arms):
        m, lo, hi = summ[arm]["dice"]
        ref_row = arm == "rung1_msd_heldout"
        ax.errorbar(m, yi, xerr=[[m - lo], [hi - m]], fmt="o", capsize=4,
                    color="#1B2A4E" if ref_row else "#B83E3A")
        ax.text(m, yi + 0.16, f"{m:.3f}", ha="center", va="bottom", fontsize=9)
    if ref and ref["dice"][0] == ref["dice"][0]:
        ax.axvline(ref["dice"][0], ls="--", lw=0.8, color="#1B2A4E", alpha=0.5)
    ax.set_yticks(y)
    ax.set_yticklabels([ARM_LABEL.get(a, a) for a in arms])
    # headroom so the topmost value label cannot collide with the title
    ax.set_ylim(-0.55, len(arms) - 1 + 0.75)
    ax.set_xlabel("Dice (median, bootstrap 95% CI over cases)")
    ax.set_title("Spleen segmentation across cohorts\n"
                 "internal reference and the honest drop", fontsize=11)
    lo_edge = min(summ[a]["dice"][1] for a in arms)
    ax.set_xlim(min(0.5, lo_edge) - 0.05, 1.02)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")


if __name__ == "__main__":
    raise SystemExit(main())
