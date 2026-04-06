"""
survival_analysis.py — Publication-ready Survival Analysis
===========================================================
Kaplan-Meier curves, log-rank test, Cox proportional hazards model.

Input CSV columns:
    time        : float — Time to event or censoring (in days/months/years)
    event       : int   — Event indicator (1 = event occurred, 0 = censored)
    group       : str   — Group variable for KM comparison (optional)
    [covariates]: float/int — Covariates for Cox model

Outputs:
    - KM plot with at-risk table (PNG/PDF, 300 DPI)
    - Cox model results table (CSV)
    - Console: complete results summary

Usage:
    python survival_analysis.py --input data.csv \
        --time time_months --event event \
        --group treatment_group \
        --covariates age sex bmi comorbidity \
        --time-unit "Months" \
        --output survival_analysis

Dependencies:
    pip install lifelines pandas numpy matplotlib scipy
"""

import argparse
import sys
import warnings
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats

try:
    from lifelines import KaplanMeierFitter, CoxPHFitter
    from lifelines.statistics import logrank_test, multivariate_logrank_test
    from lifelines.utils import restricted_mean_survival_time
    LIFELINES_AVAILABLE = True
except ImportError:
    LIFELINES_AVAILABLE = False
    print("ERROR: lifelines not installed. Install with: pip install lifelines")
    sys.exit(1)

# ── Reproducibility ───────────────────────────────────────────────────────────
SCRIPT_VERSION = "1.0.0"
SEED = 42
np.random.seed(SEED)
print(f"survival_analysis.py v{SCRIPT_VERSION} | {datetime.now().strftime('%Y-%m-%d')}")

# ── Style ─────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 9,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
})

WONG_COLORS = ["#0072B2", "#D55E00", "#009E73", "#E69F00", "#CC79A7", "#56B4E9"]
LINE_STYLES = ["-", "--", "-.", ":", (0, (3, 1, 1, 1))]


def load_data(filepath, time_col, event_col):
    df = pd.read_csv(filepath)
    for col in [time_col, event_col]:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in {filepath}")
    df = df.dropna(subset=[time_col, event_col])
    return df


def km_analysis(df, time_col, event_col, group_col=None,
                time_unit="Months", output_path="survival"):
    """Kaplan-Meier analysis with at-risk table."""
    fig = plt.figure(figsize=(7.0, 5.0))

    if group_col and group_col in df.columns:
        groups = sorted(df[group_col].dropna().unique())
        n_groups = len(groups)
        gs = gridspec.GridSpec(2, 1, height_ratios=[3.5, 1.5], hspace=0.05)
    else:
        groups = None
        n_groups = 1
        gs = gridspec.GridSpec(2, 1, height_ratios=[3.5, 1.5], hspace=0.05)

    ax_km = fig.add_subplot(gs[0])
    ax_risk = fig.add_subplot(gs[1])

    fitters = {}

    if groups:
        for i, g in enumerate(groups):
            mask = df[group_col] == g
            d = df[mask]
            kmf = KaplanMeierFitter()
            kmf.fit(d[time_col], d[event_col], label=str(g))
            fitters[g] = kmf

            kmf.plot_survival_function(
                ax=ax_km,
                color=WONG_COLORS[i % len(WONG_COLORS)],
                linestyle=LINE_STYLES[i % len(LINE_STYLES)],
                linewidth=1.5,
                ci_show=True,
                ci_alpha=0.15,
            )

            # Median survival
            med = kmf.median_survival_time_
            print(f"  {g}: Median survival = {med:.1f} {time_unit}")

        # Log-rank test
        if n_groups == 2:
            g1, g2 = groups
            lr = logrank_test(
                df.loc[df[group_col] == g1, time_col],
                df.loc[df[group_col] == g2, time_col],
                df.loc[df[group_col] == g1, event_col],
                df.loc[df[group_col] == g2, event_col],
            )
            p_str = f"P {'< .001' if lr.p_value < 0.001 else f'= {lr.p_value:.3f}'}"
            ax_km.text(0.98, 0.5, f"Log-rank {p_str}",
                       transform=ax_km.transAxes, fontsize=8,
                       va="center", ha="right")
            print(f"\n  Log-rank test: χ² = {lr.test_statistic:.3f}, P = {lr.p_value:.4f}")
        else:
            mlr = multivariate_logrank_test(
                df[time_col], df[group_col], df[event_col]
            )
            p_str = f"P {'< .001' if mlr.p_value < 0.001 else f'= {mlr.p_value:.3f}'}"
            ax_km.text(0.98, 0.5, f"Log-rank {p_str}",
                       transform=ax_km.transAxes, fontsize=8,
                       va="center", ha="right")
    else:
        # Single-group KM
        kmf = KaplanMeierFitter()
        kmf.fit(df[time_col], df[event_col], label="All patients")
        fitters["All"] = kmf
        kmf.plot_survival_function(ax=ax_km, color=WONG_COLORS[0],
                                    linewidth=1.5, ci_show=True, ci_alpha=0.2)
        med = kmf.median_survival_time_
        print(f"  Median survival: {med:.1f} {time_unit}")

    # KM axis formatting
    ax_km.set_ylim(-0.02, 1.05)
    ax_km.set_xlim(left=0)
    ax_km.set_ylabel("Survival probability", fontsize=9)
    ax_km.set_xlabel("")
    ax_km.spines[["top", "right"]].set_visible(False)
    ax_km.legend(fontsize=8, frameon=False)
    ax_km.grid(axis="y", color="#EEEEEE", linewidth=0.5)

    # At-risk table
    ax_risk.set_axis_off()
    time_points = np.linspace(0, df[time_col].max() * 0.95, 6)
    row_offset = 1.0

    for i, (label, kmf) in enumerate(fitters.items()):
        at_risk = [kmf.event_table["at_risk"].iloc[
            max(0, (kmf.event_table.index <= t).sum() - 1)
        ] for t in time_points]
        ax_risk.text(-0.01, row_offset - i * 0.35, str(label),
                     transform=ax_risk.transAxes, fontsize=7.5,
                     va="top", ha="right",
                     color=WONG_COLORS[i % len(WONG_COLORS)])
        for j, (t, n) in enumerate(zip(time_points, at_risk)):
            ax_risk.text(j / (len(time_points) - 1), row_offset - i * 0.35,
                          str(int(n)), transform=ax_risk.transAxes,
                          fontsize=7.5, va="top", ha="center")

    ax_km.set_xticks(time_points)
    ax_km.set_xlabel(time_unit, fontsize=9)

    plt.suptitle("Kaplan-Meier Survival Curves", fontsize=10, y=1.01, fontweight="bold")
    plt.tight_layout()

    for ext in ["pdf", "png"]:
        outfile = f"{output_path}_km.{ext}"
        dpi = 300 if ext == "png" else None
        plt.savefig(outfile, dpi=dpi, bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        print(f"Saved: {outfile}")
    plt.close()


def cox_analysis(df, time_col, event_col, covariates, output_path="survival"):
    """Cox proportional hazards model."""
    model_df = df[[time_col, event_col] + covariates].dropna()
    print(f"\n── Cox PH Model (N = {len(model_df)}) ───────────────────────")

    cph = CoxPHFitter(penalizer=0.1)
    cph.fit(model_df, duration_col=time_col, event_col=event_col)
    cph.print_summary()

    # Check PH assumption
    print("\n── Proportional Hazards Assumption (Schoenfeld residuals) ───")
    try:
        cph.check_assumptions(model_df, p_value_threshold=0.05, show_plots=False)
    except Exception as e:
        print(f"  PH assumption check: {e}")

    # Save results table
    summary = cph.summary.copy()
    summary.columns = [c.replace(" ", "_") for c in summary.columns]
    outfile = f"{output_path}_cox_results.csv"
    summary.to_csv(outfile)
    print(f"\nSaved: {outfile}")

    # Concordance index
    print(f"\nConcordance index (C-statistic): {cph.concordance_index_:.3f}")

    return cph


def rmst_analysis(df, time_col, event_col, group_col, t_star, output_path="survival"):
    """Restricted Mean Survival Time analysis."""
    if group_col not in df.columns:
        return

    groups = df[group_col].dropna().unique()
    print(f"\n── Restricted Mean Survival Time (t* = {t_star}) ────────────")
    for g in groups:
        d = df[df[group_col] == g]
        kmf = KaplanMeierFitter()
        kmf.fit(d[time_col], d[event_col])
        rmst = restricted_mean_survival_time(kmf, t=t_star)
        print(f"  {g}: RMST = {rmst:.2f}")


def main():
    parser = argparse.ArgumentParser(description="Survival analysis")
    parser.add_argument("--input", required=True)
    parser.add_argument("--time", required=True, help="Time column name")
    parser.add_argument("--event", required=True, help="Event column name (1=event, 0=censored)")
    parser.add_argument("--group", default=None)
    parser.add_argument("--covariates", nargs="+", default=None)
    parser.add_argument("--time-unit", default="Months")
    parser.add_argument("--rmst-t", type=float, default=None,
                        help="t* for RMST (in same units as time)")
    parser.add_argument("--output", default="survival_analysis")

    args = parser.parse_args()

    df = load_data(args.input, args.time, args.event)
    print(f"\nN = {len(df)} | Events: {df[args.event].sum()} "
          f"({df[args.event].mean()*100:.1f}%)")

    print("\n── Kaplan-Meier Analysis ────────────────────")
    km_analysis(df, args.time, args.event, args.group,
                args.time_unit, args.output)

    if args.covariates:
        cox_analysis(df, args.time, args.event, args.covariates, args.output)

    if args.rmst_t and args.group:
        rmst_analysis(df, args.time, args.event, args.group,
                      args.rmst_t, args.output)

    print(f"\n── Session Info ─────────────────────────────")
    print(f"Python: {sys.version.split()[0]}")
    for pkg in ["lifelines", "pandas", "numpy", "scipy"]:
        try:
            import importlib
            m = importlib.import_module(pkg)
            print(f"  {pkg}: {m.__version__}")
        except Exception:
            pass


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: python survival_analysis.py --input data.csv "
              "--time time_months --event event --group treatment")
    else:
        main()
