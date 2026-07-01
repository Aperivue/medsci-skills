#!/usr/bin/env python3
"""Render the four highest-yield clinical figures as tested, deterministic generators.

This is the *render* layer for the canonical figure anatomies described in prose under
``references/exemplar_plots/`` (km_curve / roc_pr / calibration_plot / decision_curve).
It turns those anatomy models into RUNNABLE code so a regression in a publication figure
is caught by a test, not by a reviewer — the gap that left make-figures with no
deterministic render check for any data plot.

Separation of concerns (do not duplicate the analysis SoT):
  - ``/analyze-stats`` *computes* the estimates (KM via lifelines, AUC, calibration
    slope/intercept, net benefit). Those numbers are the single source of truth.
  - this module *renders* already-computed inputs into the canonical anatomy, and
    asserts the load-bearing elements are present. It never recomputes a statistic and
    never invents a number.

Each renderer returns a matplotlib ``Figure`` so a verifier can introspect the actual
artists (lines, texts, collections) rather than pixel-diffing a PNG. ``assert_structure``
encodes the load-bearing-element invariants for each figure type.

Matplotlib (Agg, headless) + numpy only — no seaborn, no network, no RNG at import.
CLI:  render_core_figures.py --inputs fixture/synthetic_inputs.json --out-dir OUT
      (renders all four PNGs, runs every structural assertion; exit 1 on any failure).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless, deterministic
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402


# --------------------------------------------------------------------------- KM
def km_curve(groups: list[dict], max_follow_up: float, *, title: str = "") -> plt.Figure:
    """Kaplan–Meier step curve(s) with a number-at-risk table and censor marks.

    groups: [{name, time:[...], surv:[0..1], censor_times:[...],
              at_risk:{time:[...], n:[...]}}]  — already-computed step coordinates.
    The x-axis is clipped to ``max_follow_up`` so the curve is never extrapolated past
    observed follow-up (a recurrent KM error the exemplar anatomy warns against).
    """
    fig, (ax, ax_risk) = plt.subplots(
        2, 1, figsize=(6.4, 5.2), gridspec_kw={"height_ratios": [4, 1]}
    )
    for g in groups:
        t = np.asarray(g["time"], float)
        s = np.asarray(g["surv"], float)
        line, = ax.step(t, s, where="post", label=g["name"])
        # censor tick marks on the step curve
        for ct in g.get("censor_times", []):
            idx = np.searchsorted(t, ct, side="right") - 1
            idx = max(0, min(idx, len(s) - 1))
            ax.plot([ct], [s[idx]], marker="|", markersize=8, color=line.get_color())
    ax.set_xlim(0, max_follow_up)          # no extrapolation past follow-up
    ax.set_ylim(0, 1.02)
    ax.set_ylabel("Survival probability")
    ax.set_title(title or "Kaplan–Meier survival")
    ax.legend(loc="lower left", frameon=False)

    # number-at-risk table on the lower axes
    ax_risk.axis("off")
    ax_risk.set_xlim(0, max_follow_up)
    ax_risk.text(0, len(groups) + 0.5, "No. at risk", fontsize=9, fontweight="bold",
                 transform=ax_risk.get_yaxis_transform())
    for row, g in enumerate(groups):
        risk = g["at_risk"]
        y = len(groups) - row - 0.5
        for tt, nn in zip(risk["time"], risk["n"]):
            ax_risk.text(tt, y, str(int(nn)), ha="center", va="center", fontsize=8)
        ax_risk.text(0, y, g["name"], ha="right", va="center", fontsize=8,
                     transform=ax_risk.get_yaxis_transform())
    ax_risk.set_xlabel("Time (months)")
    fig.tight_layout()
    fig._mf_kind = "km"  # tag for assert_structure
    fig._mf_max_follow_up = max_follow_up
    return fig


# -------------------------------------------------------------------------- ROC
def roc_curve(fpr, tpr, auc: float, *, operating_point: dict | None = None,
              title: str = "") -> plt.Figure:
    """ROC curve with the chance diagonal, an AUC annotation, and an operating point."""
    fpr = np.asarray(fpr, float)
    tpr = np.asarray(tpr, float)
    fig, ax = plt.subplots(figsize=(5.2, 5.0))
    ax.plot(fpr, tpr, label=f"Model (AUC = {auc:.3f})")
    ax.plot([0, 1], [0, 1], linestyle="--", color="0.5", label="Chance")  # diagonal
    if operating_point:
        ax.scatter([operating_point["fpr"]], [operating_point["tpr"]],
                   color="crimson", zorder=5, s=40,
                   label=operating_point.get("label", "Operating point"))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("1 − specificity (false-positive rate)")
    ax.set_ylabel("Sensitivity (true-positive rate)")
    ax.set_title(title or "Receiver operating characteristic")
    ax.text(0.55, 0.10, f"AUC = {auc:.3f}", fontsize=11,
            bbox=dict(boxstyle="round", fc="white", ec="0.7"))
    ax.legend(loc="lower right", frameon=False)
    fig.tight_layout()
    fig._mf_kind = "roc"
    return fig


# ------------------------------------------------------------------ calibration
def calibration_plot(pred_mean, obs_freq, *, slope: float, intercept: float,
                     ci_low=None, ci_high=None, title: str = "") -> plt.Figure:
    """Calibration plot: binned observed-vs-predicted, the y=x identity line, and the
    fitted calibration slope/intercept annotation (the load-bearing calibration metrics)."""
    pred_mean = np.asarray(pred_mean, float)
    obs_freq = np.asarray(obs_freq, float)
    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    ax.plot([0, 1], [0, 1], linestyle="--", color="0.5", label="Ideal (y = x)")  # identity
    if ci_low is not None and ci_high is not None:
        yerr = np.vstack([obs_freq - np.asarray(ci_low, float),
                          np.asarray(ci_high, float) - obs_freq])
        ax.errorbar(pred_mean, obs_freq, yerr=yerr, fmt="o", capsize=3, label="Observed")
    else:
        ax.plot(pred_mean, obs_freq, marker="o", label="Observed")
    # fitted calibration line
    xs = np.linspace(0, 1, 50)
    ax.plot(xs, intercept + slope * xs, color="crimson", label="Calibration fit")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Predicted probability")
    ax.set_ylabel("Observed frequency")
    ax.set_title(title or "Calibration")
    ax.text(0.05, 0.88, f"slope = {slope:.2f}\nintercept = {intercept:.2f}", fontsize=10,
            bbox=dict(boxstyle="round", fc="white", ec="0.7"))
    ax.legend(loc="lower right", frameon=False)
    fig.tight_layout()
    fig._mf_kind = "calibration"
    return fig


# --------------------------------------------------------------- decision curve
def decision_curve(thresholds, net_benefit_model, prevalence: float, *,
                   model_label: str = "Model", title: str = "") -> plt.Figure:
    """Decision-curve (net-benefit) plot with the treat-all and treat-none reference
    strategies — the two references without which a DCA is uninterpretable."""
    pt = np.asarray(thresholds, float)
    nb_model = np.asarray(net_benefit_model, float)
    # treat-all net benefit = prev - (1-prev) * pt/(1-pt); treat-none = 0
    with np.errstate(divide="ignore", invalid="ignore"):
        nb_all = prevalence - (1 - prevalence) * pt / (1 - pt)
    fig, ax = plt.subplots(figsize=(6.0, 4.8))
    ax.plot(pt, nb_model, label=model_label, color="crimson")
    ax.plot(pt, nb_all, label="Treat all", color="0.4", linestyle="-.")
    ax.plot(pt, np.zeros_like(pt), label="Treat none", color="0.0", linestyle=":")
    ax.set_xlim(pt.min(), pt.max())
    lo = float(min(0.0, np.nanmin(nb_model)))
    ax.set_ylim(lo - 0.02, float(np.nanmax(nb_model)) + 0.05)
    ax.set_xlabel("Threshold probability")
    ax.set_ylabel("Net benefit")
    ax.set_title(title or "Decision-curve analysis")
    ax.legend(loc="upper right", frameon=False)
    fig.tight_layout()
    fig._mf_kind = "dca"
    return fig


# ------------------------------------------------------------------- forest
def forest_plot(studies: list[dict], pooled: dict, *, null_value: float = 1.0,
                effect_label: str = "Effect (95% CI)", title: str = "",
                log_x: bool = True) -> plt.Figure:
    """Meta-analysis forest plot from already-computed per-study estimates.

    studies: [{name, est, lo, hi, weight?}] — each study's point estimate + CI.
    pooled:  {est, lo, hi, label}          — the pooled estimate + CI + model name.
    Draws a weight-scaled marker + CI whisker per study, the null reference line, and a
    pooled diamond; the pooled row is always last. For a ratio measure keep log_x=True and
    null_value=1.0; for a mean difference pass log_x=False, null_value=0.0."""
    n = len(studies)
    fig, ax = plt.subplots(figsize=(6.6, 0.5 * n + 2.0))
    ys = list(range(n, 0, -1))  # top study at the highest y
    weights = np.asarray([s.get("weight", 1.0) for s in studies], float)
    wnorm = weights / weights.max() if weights.max() > 0 else np.ones(n)
    for y, s, w in zip(ys, studies, wnorm):
        ax.plot([s["lo"], s["hi"]], [y, y], color="0.3")             # CI whisker
        ax.scatter([s["est"]], [y], s=30 + 120 * w, marker="s",
                   color="steelblue", zorder=4)                       # weight-scaled box
    ax.axvline(null_value, linestyle="--", color="0.5")               # null reference
    # pooled diamond on a row below the studies
    yd = 0
    d = pooled
    ax.add_patch(Polygon([[d["lo"], yd], [d["est"], yd + 0.35],
                          [d["hi"], yd], [d["est"], yd - 0.35]],
                         closed=True, facecolor="crimson", edgecolor="black", zorder=5))
    labels = [s["name"] for s in studies] + [pooled.get("label", "Pooled")]
    ax.set_yticks(ys + [yd])
    ax.set_yticklabels(labels)
    ax.set_ylim(-1, n + 1)
    if log_x:
        ax.set_xscale("log")
    ax.set_xlabel(effect_label)
    ax.set_title(title or "Meta-analysis forest plot")
    fig.tight_layout()
    fig._mf_kind = "forest"
    fig._mf_n_studies = n
    fig._mf_null = null_value
    return fig


# -------------------------------------------------------------- Bland–Altman
def bland_altman(mean_vals, diff_vals, *, bias: float, sd_diff: float,
                 title: str = "") -> plt.Figure:
    """Bland–Altman agreement plot: difference vs mean, with the bias line and the
    95% limits of agreement (bias ± 1.96·SD) — the load-bearing agreement elements."""
    mean_vals = np.asarray(mean_vals, float)
    diff_vals = np.asarray(diff_vals, float)
    loa_hi, loa_lo = bias + 1.96 * sd_diff, bias - 1.96 * sd_diff
    fig, ax = plt.subplots(figsize=(6.0, 5.0))
    ax.scatter(mean_vals, diff_vals, s=25, color="steelblue", alpha=0.8)
    ax.axhline(bias, color="crimson", label=f"Bias {bias:.2f}")
    ax.axhline(loa_hi, linestyle="--", color="0.4", label=f"+1.96 SD {loa_hi:.2f}")
    ax.axhline(loa_lo, linestyle="--", color="0.4", label=f"−1.96 SD {loa_lo:.2f}")
    ax.set_xlabel("Mean of the two measurements")
    ax.set_ylabel("Difference between measurements")
    ax.set_title(title or "Bland–Altman agreement")
    ax.legend(loc="upper right", frameon=False)
    fig.tight_layout()
    fig._mf_kind = "bland_altman"
    fig._mf_loa = (loa_lo, loa_hi)
    return fig


# ---------------------------------------------------------- confusion matrix
def confusion_matrix(matrix, labels, *, title: str = "") -> plt.Figure:
    """Confusion matrix from an already-computed count grid. Rows = actual, cols =
    predicted; every cell is annotated with its count (for a 2×2, TN/FP/FN/TP)."""
    m = np.asarray(matrix, float)
    k = m.shape[0]
    if m.shape[0] != m.shape[1] or k != len(labels):
        raise AssertionError("confusion matrix must be square and match the label count")
    fig, ax = plt.subplots(figsize=(1.4 * k + 2, 1.4 * k + 2))
    ax.imshow(m, cmap="Blues")
    thresh = m.max() / 2.0 if m.max() else 0.5
    for i in range(k):
        for j in range(k):
            ax.text(j, i, str(int(m[i, j])), ha="center", va="center",
                    color="white" if m[i, j] > thresh else "black")
    ax.set_xticks(range(k)); ax.set_xticklabels(labels)
    ax.set_yticks(range(k)); ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title or "Confusion matrix")
    fig.tight_layout()
    fig._mf_kind = "confusion"
    fig._mf_k = k
    return fig


# ----------------------------------------------------- structural invariants
def assert_structure(fig: plt.Figure) -> list[str]:
    """Assert the load-bearing elements for the figure's kind. Returns the list of
    checks that PASSED; raises AssertionError on the first violated invariant."""
    kind = getattr(fig, "_mf_kind", None)
    passed: list[str] = []

    def has_text(ax, needle: str) -> bool:
        n = needle.lower()
        return any(n in t.get_text().lower() for t in ax.texts) \
            or (ax.get_legend() and any(n in t.get_text().lower()
                                        for t in ax.get_legend().get_texts()))

    if kind == "km":
        ax, ax_risk = fig.axes[0], fig.axes[1]
        steps = [ln for ln in ax.lines if len(ln.get_xdata()) > 2]
        assert steps, "KM: no step curve drawn"
        passed.append("KM step curve present")
        # no extrapolation past follow-up
        muf = getattr(fig, "_mf_max_follow_up")
        assert abs(ax.get_xlim()[1] - muf) < 1e-9, "KM: x-axis extends past follow-up"
        passed.append("KM x-axis clipped to follow-up (no extrapolation)")
        # monotonic non-increasing survival on each step curve
        for ln in steps:
            y = np.asarray(ln.get_ydata(), float)
            assert np.all(np.diff(y) <= 1e-9), "KM: survival curve is not non-increasing"
        passed.append("KM survival monotonic non-increasing")
        assert any(t.get_text().lower().startswith("no. at risk") or "at risk"
                   in t.get_text().lower() for t in ax_risk.texts), \
            "KM: number-at-risk table missing"
        passed.append("KM number-at-risk table present")
        assert "survival" in ax.get_ylabel().lower(), "KM: y-label not survival"
        passed.append("KM survival y-label")

    elif kind == "roc":
        ax = fig.axes[0]
        diag = [ln for ln in ax.lines
                if len(ln.get_xdata()) == 2
                and np.allclose(ln.get_xdata(), [0, 1])
                and np.allclose(ln.get_ydata(), [0, 1])]
        assert diag, "ROC: chance diagonal (0,0)-(1,1) missing"
        passed.append("ROC chance diagonal present")
        assert has_text(ax, "auc"), "ROC: AUC annotation missing"
        passed.append("ROC AUC annotation present")
        assert ax.collections, "ROC: operating-point marker missing"
        passed.append("ROC operating point present")
        assert "sensitiv" in ax.get_ylabel().lower(), "ROC: y-label not sensitivity"
        passed.append("ROC sensitivity y-label")

    elif kind == "calibration":
        ax = fig.axes[0]
        identity = [ln for ln in ax.lines
                    if len(ln.get_xdata()) == 2
                    and np.allclose(ln.get_xdata(), [0, 1])
                    and np.allclose(ln.get_ydata(), [0, 1])]
        assert identity, "Calibration: identity y=x line missing"
        passed.append("Calibration identity line present")
        assert has_text(ax, "slope") and has_text(ax, "intercept"), \
            "Calibration: slope/intercept annotation missing"
        passed.append("Calibration slope+intercept annotation present")
        assert "predicted" in ax.get_xlabel().lower(), "Calibration: x not predicted"
        assert "observed" in ax.get_ylabel().lower(), "Calibration: y not observed"
        passed.append("Calibration predicted-vs-observed axes")

    elif kind == "dca":
        ax = fig.axes[0]
        assert len(ax.lines) >= 3, "DCA: fewer than 3 strategies (model/all/none) drawn"
        passed.append("DCA has model + treat-all + treat-none")
        treat_none = [ln for ln in ax.lines if np.allclose(ln.get_ydata(), 0.0)]
        assert treat_none, "DCA: treat-none (net benefit = 0) reference missing"
        passed.append("DCA treat-none reference present")
        assert "net benefit" in ax.get_ylabel().lower(), "DCA: y-label not net benefit"
        passed.append("DCA net-benefit y-label")
        assert has_text(ax, "treat all") and has_text(ax, "treat none"), \
            "DCA: treat-all / treat-none not labelled"
        passed.append("DCA reference strategies labelled")

    elif kind == "forest":
        ax = fig.axes[0]
        n = getattr(fig, "_mf_n_studies")
        # one horizontal CI whisker (2-point line, equal y) per study
        whiskers = [ln for ln in ax.lines
                    if len(ln.get_xdata()) == 2 and np.allclose(np.diff(ln.get_ydata()), 0.0)]
        assert len(whiskers) >= n, "forest: missing per-study CI whiskers"
        passed.append(f"forest per-study CI rows present ({n})")
        null = getattr(fig, "_mf_null")
        assert any(len(ln.get_xdata()) == 2 and np.allclose(ln.get_xdata(), [null, null])
                   for ln in ax.lines), "forest: null reference line missing"
        passed.append("forest null reference line present")
        assert any(isinstance(p, Polygon) and len(p.get_xy()) >= 4 for p in ax.patches), \
            "forest: pooled diamond missing"
        passed.append("forest pooled diamond present")
        assert len(ax.get_yticklabels()) >= n + 1, "forest: study/pooled row labels missing"
        passed.append("forest study + pooled row labels present")

    elif kind == "bland_altman":
        ax = fig.axes[0]
        assert ax.collections, "Bland–Altman: scatter of differences missing"
        passed.append("Bland–Altman difference scatter present")
        hlines = [ln for ln in ax.lines if np.allclose(np.diff(ln.get_ydata()), 0.0)]
        assert len(hlines) >= 3, "Bland–Altman: need bias + two limits-of-agreement lines"
        passed.append("Bland–Altman bias + 2 LoA lines present")
        loa_lo, loa_hi = getattr(fig, "_mf_loa")
        yvals = [float(ln.get_ydata()[0]) for ln in hlines]
        assert any(abs(y - loa_hi) < 1e-6 for y in yvals) and any(abs(y - loa_lo) < 1e-6 for y in yvals), \
            "Bland–Altman: LoA lines not at bias ± 1.96·SD"
        passed.append("Bland–Altman LoA at bias ± 1.96·SD")
        assert "difference" in ax.get_ylabel().lower() and "mean" in ax.get_xlabel().lower(), \
            "Bland–Altman: axes not difference-vs-mean"
        passed.append("Bland–Altman difference-vs-mean axes")

    elif kind == "confusion":
        ax = fig.axes[0]
        k = getattr(fig, "_mf_k")
        assert ax.images, "confusion: matrix image missing"
        passed.append("confusion matrix image present")
        cells = [t for t in ax.texts if t.get_text().strip().lstrip("-").isdigit()]
        assert len(cells) >= k * k, f"confusion: expected {k * k} annotated cells"
        passed.append(f"confusion all {k}×{k} cells annotated")
        assert "predicted" in ax.get_xlabel().lower() and "actual" in ax.get_ylabel().lower(), \
            "confusion: axes not Predicted/Actual"
        passed.append("confusion Predicted/Actual axes")

    else:
        raise AssertionError(f"unknown figure kind: {kind!r}")
    return passed


# ----------------------------------------------------------------- driver
def render_all(inputs: dict, out_dir: Path) -> dict:
    """Render each figure kind present in ``inputs``, save PNGs, and assert structure.
    Returns {kind: [passed checks]}. Raises on any structural violation."""
    out_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, list[str]] = {}
    builders = {
        "km": lambda d: km_curve(d["groups"], d["max_follow_up"], title=d.get("title", "")),
        "roc": lambda d: roc_curve(d["fpr"], d["tpr"], d["auc"],
                                   operating_point=d.get("operating_point")),
        "calibration": lambda d: calibration_plot(
            d["pred_mean"], d["obs_freq"], slope=d["slope"], intercept=d["intercept"],
            ci_low=d.get("ci_low"), ci_high=d.get("ci_high")),
        "dca": lambda d: decision_curve(d["thresholds"], d["net_benefit_model"],
                                        d["prevalence"]),
        "forest": lambda d: forest_plot(d["studies"], d["pooled"],
                                        null_value=d.get("null_value", 1.0),
                                        effect_label=d.get("effect_label", "Effect (95% CI)"),
                                        log_x=d.get("log_x", True)),
        "bland_altman": lambda d: bland_altman(d["mean_vals"], d["diff_vals"],
                                               bias=d["bias"], sd_diff=d["sd_diff"]),
        "confusion": lambda d: confusion_matrix(d["matrix"], d["labels"]),
    }
    for kind, build in builders.items():
        if kind not in inputs:
            continue
        fig = build(inputs[kind])
        results[kind] = assert_structure(fig)
        fig.savefig(out_dir / f"{kind}.png", dpi=120)
        png = out_dir / f"{kind}.png"
        assert png.exists() and png.stat().st_size > 2000, f"{kind}: PNG not written"
        plt.close(fig)
    return results


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Render + structurally verify core clinical figures.")
    ap.add_argument("--inputs", required=True, help="JSON with km/roc/calibration/dca inputs")
    ap.add_argument("--out-dir", required=True, help="directory for rendered PNGs")
    args = ap.parse_args(argv)
    inputs = json.loads(Path(args.inputs).read_text(encoding="utf-8"))
    try:
        results = render_all(inputs, Path(args.out_dir))
    except AssertionError as e:
        print(f"RENDER-FAIL: {e}", file=sys.stderr)
        return 1
    for kind, checks in results.items():
        print(f"OK [{kind}] {len(checks)} structural invariants: {'; '.join(checks)}")
    print(f"PASS: {len(results)} figure(s) rendered + structurally verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
