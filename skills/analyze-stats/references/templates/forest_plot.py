"""
forest_plot.py — Publication-ready Forest Plot for Meta-analysis
================================================================
Generates a forest plot from a CSV file of study-level effect sizes.

Input CSV columns (required):
    study_label     : str  — Study author + year (e.g., "Kim 2022")
    effect_size     : float — Effect estimate (OR, RR, HR, MD, SMD, AUC)
    ci_lower        : float — Lower bound of 95% CI
    ci_upper        : float — Upper bound of 95% CI

Input CSV columns (optional):
    n_total         : int   — Total sample size (shown in table)
    weight          : float — Study weight % (determines box size)
    subgroup        : str   — Subgroup label (adds subgroup header rows)
    events_treat    : int   — Events in treatment/index group
    events_control  : int   — Events in control/comparator group

Pooled estimate (required as separate dict or CSV row with label="Pooled"):
    pooled_effect   : float
    pooled_ci_lower : float
    pooled_ci_upper : float
    i_squared       : float — I² heterogeneity (%)
    tau_squared     : float — τ² between-study variance
    q_p_value       : float — Cochran Q test p-value

Usage:
    python forest_plot.py --input studies.csv --pooled 0.82 0.65 1.04 \
        --i2 45.3 --tau2 0.021 --q-p 0.08 \
        --effect-label "OR" --null-value 1.0 \
        --output forest_plot --favor-left "Favors Treatment" --favor-right "Favors Control"

Outputs:
    forest_plot.pdf  — Vector format (submission quality)
    forest_plot.png  — Raster 300 DPI (web/preview)
"""

import argparse
import sys
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D
from datetime import datetime

# ── Reproducibility ───────────────────────────────────────────────────────────
SCRIPT_VERSION = "1.0.0"
SEED = 42
np.random.seed(SEED)

# ── Wong (2011) colorblind-safe colors ────────────────────────────────────────
COLORS = {
    "study_ci": "#333333",      # dark gray for CI lines
    "study_box": "#0072B2",     # blue for individual study boxes
    "pooled_diamond": "#D55E00",# vermillion for pooled diamond
    "subgroup_header": "#E8E8E8",
    "grid": "#DDDDDD",
    "null_line": "#888888",
}

# ── Figure style ──────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 9,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "figure.dpi": 150,
})


def load_data(filepath: str) -> pd.DataFrame:
    """Load study data from CSV."""
    df = pd.read_csv(filepath)
    required = ["study_label", "effect_size", "ci_lower", "ci_upper"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df


def compute_box_size(weights: pd.Series, min_size=0.08, max_size=0.35) -> np.ndarray:
    """Scale box heights proportional to study weight."""
    if weights is None or weights.isna().all():
        return np.full(len(weights), (min_size + max_size) / 2)
    w = weights.fillna(weights.mean())
    w_norm = (w - w.min()) / (w.max() - w.min() + 1e-9)
    return min_size + w_norm * (max_size - min_size)


def make_forest_plot(
    df: pd.DataFrame,
    pooled_effect: float,
    pooled_ci_lower: float,
    pooled_ci_upper: float,
    i_squared: float,
    tau_squared: float,
    q_p_value: float,
    effect_label: str = "OR",
    null_value: float = 1.0,
    log_scale: bool = True,
    favor_left: str = "Favors Treatment",
    favor_right: str = "Favors Control",
    output_path: str = "forest_plot",
) -> None:
    """Generate and save the forest plot."""

    n_studies = len(df)
    has_subgroups = "subgroup" in df.columns and df["subgroup"].notna().any()
    has_weights = "weight" in df.columns

    # ── Layout calculations ───────────────────────────────────────────────────
    row_height = 0.45  # inches per row
    header_height = 1.2
    footer_height = 0.9
    n_rows = n_studies + (1 if has_subgroups else 0) + 2  # +subgroup headers + pooled + blank
    fig_height = max(4.5, header_height + n_rows * row_height + footer_height)
    fig_width = 7.0  # double column

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.set_axis_off()

    # ── Column positions (normalized 0–1 in figure space) ────────────────────
    col_label = 0.02
    col_n = 0.38
    col_events = 0.44
    col_weight = 0.51
    col_plot_left = 0.57
    col_plot_right = 0.87
    col_effect = 0.89

    # ── All effect values for x-axis range ───────────────────────────────────
    all_effects = list(df["effect_size"]) + [pooled_effect,
                                              pooled_ci_lower, pooled_ci_upper]
    if log_scale:
        all_log = [np.log(x) for x in all_effects if x > 0]
        x_min_log = min(all_log) - 0.5
        x_max_log = max(all_log) + 0.5
    else:
        x_min_log = min(all_effects) - abs(min(all_effects)) * 0.2
        x_max_log = max(all_effects) + abs(max(all_effects)) * 0.2

    def to_plot_x(value):
        """Map effect value to normalized plot x position."""
        if log_scale and value > 0:
            log_val = np.log(value)
        else:
            log_val = value
        frac = (log_val - x_min_log) / (x_max_log - x_min_log)
        return col_plot_left + frac * (col_plot_right - col_plot_left)

    # ── Headers ───────────────────────────────────────────────────────────────
    fig.text(col_label, 0.96, "Study", fontsize=9, fontweight="bold",
             transform=fig.transFigure, va="top")
    if "n_total" in df.columns:
        fig.text(col_n, 0.96, "N", fontsize=9, fontweight="bold",
                 transform=fig.transFigure, va="top", ha="center")
    if has_weights:
        fig.text(col_weight, 0.96, "Weight\n(%)", fontsize=8, fontweight="bold",
                 transform=fig.transFigure, va="top", ha="center")
    fig.text((col_plot_left + col_plot_right) / 2, 0.96,
             f"{effect_label} (95% CI)", fontsize=9, fontweight="bold",
             transform=fig.transFigure, va="top", ha="center")

    # ── Y positions for each row ───────────────────────────────────────────────
    y_start = 0.90
    y_step = row_height / fig_height
    box_sizes = compute_box_size(df.get("weight"))

    current_subgroup = None
    y = y_start

    rows = []
    if has_subgroups:
        for sg, group in df.groupby("subgroup", sort=False):
            rows.append(("subgroup_header", sg, None))
            for _, row in group.iterrows():
                rows.append(("study", row, None))
    else:
        for _, row in df.iterrows():
            rows.append(("study", row, None))

    rows.append(("blank", None, None))
    rows.append(("pooled", None, None))

    box_idx = 0
    for row_type, data, _ in rows:
        y -= y_step

        if row_type == "subgroup_header":
            fig.text(col_label, y, data, fontsize=9, fontweight="bold",
                     transform=fig.transFigure, va="center",
                     color="#333333", style="italic")

        elif row_type == "study":
            row = data
            # Study label
            fig.text(col_label, y, row["study_label"], fontsize=8,
                     transform=fig.transFigure, va="center")
            # N
            if "n_total" in row.index and pd.notna(row["n_total"]):
                fig.text(col_n, y, f"{int(row['n_total']):,}", fontsize=8,
                         transform=fig.transFigure, va="center", ha="center")
            # Weight
            if "weight" in row.index and pd.notna(row.get("weight")):
                fig.text(col_weight, y, f"{row['weight']:.1f}", fontsize=8,
                         transform=fig.transFigure, va="center", ha="center")
            # CI line
            x_lo = to_plot_x(row["ci_lower"])
            x_hi = to_plot_x(row["ci_upper"])
            x_mid = to_plot_x(row["effect_size"])
            bh = box_sizes[box_idx] * y_step

            # Draw CI line
            fig.add_artist(Line2D([x_lo, x_hi], [y, y],
                                   transform=fig.transFigure,
                                   color=COLORS["study_ci"], linewidth=0.8, zorder=2))
            # Draw study box
            rect = patches.FancyBboxPatch(
                (x_mid - bh * 0.5 * (fig_height / fig_width), y - bh * 0.5),
                bh * (fig_height / fig_width), bh,
                boxstyle="square,pad=0",
                transform=fig.transFigure,
                facecolor=COLORS["study_box"],
                edgecolor=COLORS["study_box"],
                zorder=3,
            )
            fig.add_artist(rect)

            # Effect value text
            val_str = f"{row['effect_size']:.2f} ({row['ci_lower']:.2f}–{row['ci_upper']:.2f})"
            fig.text(col_effect, y, val_str, fontsize=7.5,
                     transform=fig.transFigure, va="center")

            box_idx += 1

        elif row_type == "pooled":
            # Separator line
            y_sep = y + y_step * 0.3
            ax.axhline(y=0, xmin=col_label, xmax=0.98, color="#888888",
                        linewidth=0.5, transform=fig.transFigure, zorder=1)

            # Diamond
            x_lo = to_plot_x(pooled_ci_lower)
            x_hi = to_plot_x(pooled_ci_upper)
            x_mid = to_plot_x(pooled_effect)
            diamond_h = y_step * 0.4
            diamond = plt.Polygon(
                [[x_lo, y], [x_mid, y + diamond_h / 2],
                 [x_hi, y], [x_mid, y - diamond_h / 2]],
                transform=fig.transFigure,
                facecolor=COLORS["pooled_diamond"],
                edgecolor=COLORS["pooled_diamond"],
                zorder=4,
            )
            fig.add_artist(diamond)

            # Pooled estimate text
            val_str = f"{pooled_effect:.2f} ({pooled_ci_lower:.2f}–{pooled_ci_upper:.2f})"
            fig.text(col_label, y, "Pooled estimate", fontsize=8, fontweight="bold",
                     transform=fig.transFigure, va="center")
            fig.text(col_effect, y, val_str, fontsize=7.5, fontweight="bold",
                     transform=fig.transFigure, va="center")

    # ── Null line ─────────────────────────────────────────────────────────────
    x_null = to_plot_x(null_value)
    fig.add_artist(Line2D([x_null, x_null], [y - y_step, y_start + y_step],
                           transform=fig.transFigure,
                           color=COLORS["null_line"], linewidth=0.8,
                           linestyle="--", zorder=1))

    # ── X-axis ticks ─────────────────────────────────────────────────────────
    if log_scale:
        tick_values_raw = [0.25, 0.5, 1.0, 2.0, 4.0]
    else:
        span = x_max_log - x_min_log
        tick_values_raw = np.linspace(x_min_log, x_max_log, 5)

    y_axis = y - y_step * 1.2
    for tv in tick_values_raw:
        try:
            tx = to_plot_x(tv)
        except Exception:
            continue
        if col_plot_left <= tx <= col_plot_right:
            fig.text(tx, y_axis, f"{tv}", fontsize=7.5,
                     transform=fig.transFigure, va="top", ha="center")
            fig.add_artist(Line2D([tx, tx], [y_axis + 0.01, y - y_step * 0.8],
                                   transform=fig.transFigure,
                                   color="#888888", linewidth=0.5))

    # ── Favor labels ─────────────────────────────────────────────────────────
    y_favor = y_axis - 0.025
    fig.text((col_plot_left + x_null) / 2, y_favor, f"← {favor_left}",
             fontsize=7.5, transform=fig.transFigure, va="top", ha="center",
             color="#555555")
    fig.text((x_null + col_plot_right) / 2, y_favor, f"{favor_right} →",
             fontsize=7.5, transform=fig.transFigure, va="top", ha="center",
             color="#555555")

    # ── Heterogeneity footer ──────────────────────────────────────────────────
    y_footer = y_favor - 0.035
    het_str = (
        f"Heterogeneity: I² = {i_squared:.1f}%, τ² = {tau_squared:.3f}, "
        f"Q-test P = {q_p_value:.3f}  |  "
        f"N studies = {n_studies}"
    )
    fig.text(col_label, y_footer, het_str, fontsize=7.5,
             transform=fig.transFigure, va="top", color="#444444")

    # ── Reproducibility footer ────────────────────────────────────────────────
    rep_str = (
        f"Generated: {datetime.now().strftime('%Y-%m-%d')} | "
        f"Script v{SCRIPT_VERSION} | seed={SEED}"
    )
    fig.text(0.99, 0.01, rep_str, fontsize=6, transform=fig.transFigure,
             va="bottom", ha="right", color="#999999")

    # ── Save ──────────────────────────────────────────────────────────────────
    for ext in ["pdf", "png"]:
        outfile = f"{output_path}.{ext}"
        dpi = 300 if ext == "png" else None
        plt.savefig(outfile, dpi=dpi, bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        print(f"Saved: {outfile}")

    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Generate publication-ready forest plot")
    parser.add_argument("--input", required=True, help="Path to CSV file")
    parser.add_argument("--pooled", nargs=3, type=float, metavar=("EFFECT", "CI_LO", "CI_HI"),
                        required=True, help="Pooled effect size and 95% CI")
    parser.add_argument("--i2", type=float, default=0.0, help="I² (%)")
    parser.add_argument("--tau2", type=float, default=0.0, help="τ²")
    parser.add_argument("--q-p", type=float, default=1.0, dest="q_p",
                        help="Cochran Q p-value")
    parser.add_argument("--effect-label", default="OR", help="Label for effect measure")
    parser.add_argument("--null-value", type=float, default=1.0,
                        help="Null value (1.0 for OR/RR; 0 for MD)")
    parser.add_argument("--log-scale", action="store_true", default=True,
                        help="Use log scale for OR/RR (default: True)")
    parser.add_argument("--no-log-scale", action="store_false", dest="log_scale")
    parser.add_argument("--favor-left", default="Favors Treatment")
    parser.add_argument("--favor-right", default="Favors Control")
    parser.add_argument("--output", default="forest_plot", help="Output file path (no extension)")

    args = parser.parse_args()

    df = load_data(args.input)
    pooled_effect, pooled_ci_lo, pooled_ci_hi = args.pooled

    print(f"\n── Forest Plot Generation ──────────────────")
    print(f"Studies: {len(df)}")
    print(f"Pooled {args.effect_label}: {pooled_effect:.2f} "
          f"(95% CI: {pooled_ci_lo:.2f}–{pooled_ci_hi:.2f})")
    print(f"I² = {args.i2:.1f}%, τ² = {args.tau2:.3f}, Q P = {args.q_p:.3f}")

    make_forest_plot(
        df=df,
        pooled_effect=pooled_effect,
        pooled_ci_lower=pooled_ci_lo,
        pooled_ci_upper=pooled_ci_hi,
        i_squared=args.i2,
        tau_squared=args.tau2,
        q_p_value=args.q_p,
        effect_label=args.effect_label,
        null_value=args.null_value,
        log_scale=args.log_scale,
        favor_left=args.favor_left,
        favor_right=args.favor_right,
        output_path=args.output,
    )


# ── Example CSV format ────────────────────────────────────────────────────────
EXAMPLE_CSV = """study_label,effect_size,ci_lower,ci_upper,n_total,weight,subgroup
Kim 2019,0.72,0.51,1.02,234,12.4,Single-center
Park 2020,0.61,0.45,0.83,418,18.2,Single-center
Lee 2021,0.88,0.62,1.24,156,10.1,Single-center
Chen 2022,0.65,0.50,0.85,512,19.8,Multi-center
Wang 2022,0.71,0.53,0.95,345,15.6,Multi-center
Smith 2023,0.58,0.41,0.81,289,14.7,Multi-center
Jones 2023,0.77,0.55,1.08,198,9.2,Multi-center
"""

# ── Run example ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Demo mode: generate example
        import io
        print("Running in demo mode with example data...")
        df = pd.read_csv(io.StringIO(EXAMPLE_CSV))
        make_forest_plot(
            df=df,
            pooled_effect=0.70,
            pooled_ci_lower=0.59,
            pooled_ci_upper=0.83,
            i_squared=23.4,
            tau_squared=0.008,
            q_p_value=0.24,
            effect_label="OR",
            null_value=1.0,
            log_scale=True,
            favor_left="Favors Treatment",
            favor_right="Favors Control",
            output_path="forest_plot_demo",
        )
    else:
        main()
