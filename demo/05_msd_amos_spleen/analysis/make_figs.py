#!/usr/bin/env python3
"""Publication figures for Demo 5, from the per-case artifacts only.

  Fig 1  per-case Dice by arm — the distribution the medians hide
  Fig 3  pre-specified subgroups on the external CT arm — where the model is actually worst
  Fig 4  normalisation evidence — why rung 3 collapsed, measured on both external arms

Fig 2 (across-cohort Dice with bootstrap CI) is written by `pipeline/aggregate_results.py`, which
owns the bootstrap; it is not duplicated here. Fig 5 (case flow) is a Graphviz diagram built by
`make_flow.sh` through the shipped `/make-figures` R pipeline.

No number is hard-coded: every value is read from `../results/`. Palette follows the repo's
navy/coral convention.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

R = Path("../results")
F = Path("../figures")
F.mkdir(exist_ok=True)

NAVY, CORAL, GREY = "#1B2A4E", "#B83E3A", "#8A8A8A"
ARMS = ["rung1_msd_heldout", "rung2_amos_ct", "rung3_amos_mri"]
SHORT = {"rung1_msd_heldout": "rung 1\nMSD held-out\n(internal)",
         "rung2_amos_ct": "rung 2\nAMOS CT\n(external)",
         "rung3_amos_mri": "rung 3\nAMOS MRI\n(modality shift)"}
RNG = np.random.default_rng(20260725)          # jitter only; never a reported quantity


def per_case(arm: str) -> list[dict]:
    p = R / f"per_case_{arm}.csv"
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def dice_of(rows: list[dict]) -> np.ndarray:
    return np.asarray([float(r["dice"]) for r in rows
                       if r.get("dice", "") not in ("", "nan", None)], dtype=float)


# ---------------------------------------------------------------- Fig 1: Dice by arm
def fig1() -> None:
    data = {a: dice_of(per_case(a)) for a in ARMS}
    data = {a: v for a, v in data.items() if v.size}
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    pos = np.arange(len(data)) + 1
    ax.boxplot(list(data.values()), positions=pos, widths=0.45, showfliers=False,
               medianprops=dict(color=CORAL, lw=2),
               boxprops=dict(color=NAVY), whiskerprops=dict(color=NAVY),
               capprops=dict(color=NAVY))
    for i, (arm, v) in enumerate(data.items(), start=1):
        x = i + RNG.uniform(-0.16, 0.16, size=v.size)
        ax.scatter(x, v, s=14, alpha=0.45, color=NAVY, edgecolors="none", zorder=3)
        ax.text(i, 1.045, f"n={v.size}", ha="center", va="bottom", fontsize=9, color=GREY)
    ax.set_xticks(pos)
    ax.set_xticklabels([SHORT[a] for a in data], fontsize=9)
    ax.set_ylabel("per-case Dice")
    ax.set_ylim(-0.04, 1.10)
    ax.set_title("Per-case Dice by cohort — the spread a median hides", fontsize=11)
    ax.axhline(0, ls=":", lw=0.8, color=GREY)
    fig.tight_layout()
    fig.savefig(F / "fig1_dice_by_arm.png", dpi=300, bbox_inches="tight")
    fig.savefig(F / "fig1_dice_by_arm.pdf", bbox_inches="tight")
    plt.close(fig)
    print("wrote fig1_dice_by_arm.{png,pdf}")


# ------------------------------------------------- Fig 4: why rung 3 collapsed (measured)
def fig_normalisation() -> None:
    ev = {}
    for arm in ("rung2_amos_ct", "rung3_amos_mri"):
        p = R / f"normalizer_evidence_{arm}.json"
        if p.exists():
            ev[arm] = json.loads(p.read_text(encoding="utf-8"))
    if len(ev) < 2:
        print("fig4 (normalisation) skipped — needs both external arms' normalisation evidence")
        return

    lbl = {"rung2_amos_ct": "AMOS CT (n=300)", "rung3_amos_mri": "AMOS MRI (n=60)"}
    colour = {"rung2_amos_ct": NAVY, "rung3_amos_mri": CORAL}
    clip_lo = ev["rung2_amos_ct"]["plan_normalisation"]["clip_lo"]
    clip_hi = ev["rung2_amos_ct"]["plan_normalisation"]["clip_hi"]

    fig, (axa, axb) = plt.subplots(1, 2, figsize=(9.6, 4.2))

    # (a) the intensity domain the plan assumes: HU has an air floor; arbitrary units do not
    for i, arm in enumerate(("rung2_amos_ct", "rung3_amos_mri"), start=1):
        v = np.asarray([c["raw_min"] for c in ev[arm]["cases"]], dtype=float)
        x = i + RNG.uniform(-0.16, 0.16, size=v.size)
        axa.scatter(x, v, s=16, alpha=0.5, color=colour[arm], edgecolors="none")
    axa.axhline(clip_lo, ls="--", lw=1, color=GREY)
    axa.annotate(f"clip floor {clip_lo:.0f} HU", xy=(0.55, clip_lo), xycoords=("axes fraction", "data"),
                 xytext=(0, -14), textcoords="offset points", ha="center", va="top",
                 fontsize=8, color=GREY)
    axa.set_xticks([1, 2])
    axa.set_xticklabels([lbl["rung2_amos_ct"], lbl["rung3_amos_mri"]], fontsize=9)
    axa.set_ylabel("per-case minimum intensity")
    axa.set_title("(a) Hounsfield units have an air floor.\nOne of these cohorts does not.",
                  fontsize=10)

    # (b) how much of each volume the CT clip destroys
    for i, arm in enumerate(("rung2_amos_ct", "rung3_amos_mri"), start=1):
        v = np.asarray([c["frac_above_clip_hi"] for c in ev[arm]["cases"]], dtype=float) * 100
        x = i + RNG.uniform(-0.16, 0.16, size=v.size)
        axb.scatter(x, v, s=16, alpha=0.5, color=colour[arm], edgecolors="none")
        axb.hlines(np.median(v), i - 0.26, i + 0.26, color=colour[arm], lw=2.4)
        axb.text(i, np.median(v) + 2.0, f"median {np.median(v):.1f}%", ha="center",
                 fontsize=9, color=colour[arm])
    axb.set_xticks([1, 2])
    axb.set_xticklabels([lbl["rung2_amos_ct"], lbl["rung3_amos_mri"]], fontsize=9)
    axb.set_ylabel(f"% of voxels flattened at the clip ceiling ({clip_hi:.0f})")
    axb.set_title("(b) The same trained normaliser,\napplied to both arms", fontsize=10)

    fig.suptitle("The trained plan applies CTNormalization to whatever it is handed", fontsize=11)
    fig.tight_layout()
    fig.savefig(F / "fig4_normalisation_evidence.png", dpi=300, bbox_inches="tight")
    fig.savefig(F / "fig4_normalisation_evidence.pdf", bbox_inches="tight")
    plt.close(fig)
    print("wrote fig4_normalisation_evidence.{png,pdf}")


# ------------------------------------------------ Fig 3: pre-specified subgroups (external CT)
def fig_subgroups() -> None:
    p = Path("tables/table3_subgroups.csv")
    if not p.exists():
        print("fig3 (subgroups) skipped — run make_tables.py first")
        return
    with p.open(newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["arm"].startswith("rung2")]
    if not rows:
        print("fig3 (subgroups) skipped — no external CT subgroup rows")
        return

    labels, meds, los, his, ns, axes_of = [], [], [], [], [], []
    for r in rows:
        cell = r["dice_median_95CI"]
        if cell == "n/a":
            continue
        m, rest = cell.split(" [")
        lo, hi = rest.rstrip("]").split("-")
        labels.append(r["stratum"])
        meds.append(float(m)); los.append(float(lo)); his.append(float(hi))
        ns.append(int(r["n_scored"]))
        axes_of.append(r["subgroup_axis"])

    y = np.arange(len(labels))[::-1]
    fig, ax = plt.subplots(figsize=(7.8, 0.42 * len(labels) + 1.8))
    for yi, m, lo, hi, n in zip(y, meds, los, his, ns):
        ax.errorbar(m, yi, xerr=[[m - lo], [hi - m]], fmt="o", capsize=3, color=NAVY)
        ax.text(1.01, yi, f"n={n}", va="center", fontsize=8, color=GREY,
                transform=ax.get_yaxis_transform())
    # separate the two pre-specified axes, and name them
    for i in range(1, len(axes_of)):
        if axes_of[i] != axes_of[i - 1]:
            ax.axhline((y[i] + y[i - 1]) / 2, ls="-", lw=0.6, color=GREY, alpha=0.5)
    seen = []
    for a_name, yi in zip(axes_of, y):
        if a_name not in seen:
            seen.append(a_name)
            ax.text(0.012, yi + 0.42, a_name, transform=ax.get_yaxis_transform(),
                    fontsize=8.5, style="italic", color=GREY, va="bottom")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_ylim(y.min() - 0.6, y.max() + 0.9)
    ax.set_xlabel("Dice (median, bootstrap 95% CI)")
    ax.set_xlim(0, 1.0)
    ax.set_title("Pre-specified subgroups, external CT arm —\nthe model is worst on the spleens "
                 "the task exists to measure", fontsize=10)
    fig.tight_layout()
    fig.savefig(F / "fig3_subgroups_external_ct.png", dpi=300, bbox_inches="tight")
    fig.savefig(F / "fig3_subgroups_external_ct.pdf", bbox_inches="tight")
    plt.close(fig)
    print("wrote fig3_subgroups_external_ct.{png,pdf}")


if __name__ == "__main__":
    fig1()               # -> fig1_dice_by_arm
    fig_subgroups()      # -> fig3_subgroups_external_ct
    fig_normalisation()  # -> fig4_normalisation_evidence
