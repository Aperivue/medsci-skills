"""
likert_summary.py — Publication-ready Likert Scale Survey Analysis
===================================================================
Analyzes Likert-scale survey data for medical education research papers.

Input:
    CSV with respondent rows and item columns.
    Likert responses should be numeric (1–5 or 1–7).
    Optional group column for subgroup comparisons.

Outputs:
    - Console: formatted descriptive statistics and test results
    - CSV: summary tables (table1_likert.csv)
    - PNG/PDF: diverging stacked bar chart (300 DPI)

Usage:
    python likert_summary.py --input survey_data.csv \
        --items Q1 Q2 Q3 Q4 Q5 \
        --labels "Strongly Disagree" "Disagree" "Neutral" "Agree" "Strongly Agree" \
        --group group_column \
        --scale 5 \
        --output likert_analysis

Dependencies:
    pip install pandas numpy matplotlib scipy pingouin
"""

import argparse
import sys
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats

try:
    import pingouin as pg
    PINGOUIN_AVAILABLE = True
except ImportError:
    PINGOUIN_AVAILABLE = False
    warnings.warn("pingouin not installed. Cronbach's alpha will be skipped. "
                  "Install with: pip install pingouin")

# ── Reproducibility ───────────────────────────────────────────────────────────
SCRIPT_VERSION = "1.0.0"
SEED = 42
np.random.seed(SEED)
print(f"Script: likert_summary.py v{SCRIPT_VERSION} | Date: {datetime.now().strftime('%Y-%m-%d')}")

# ── Style ─────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 9,
    "figure.dpi": 150,
})

# Diverging palette: negative → neutral → positive (colorblind-safe)
DIVERGE_COLORS_5 = ["#D55E00", "#E69F00", "#CCCCCC", "#56B4E9", "#0072B2"]
DIVERGE_COLORS_7 = ["#D55E00", "#E69F00", "#F0E442", "#CCCCCC",
                     "#56B4E9", "#009E73", "#0072B2"]


def load_data(filepath: str, item_cols: list) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    missing = [c for c in item_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Item columns not found in CSV: {missing}")
    return df


def descriptive_stats(df: pd.DataFrame, items: list, labels: list) -> pd.DataFrame:
    """Compute descriptive statistics for each Likert item."""
    rows = []
    for item in items:
        col = df[item].dropna()
        rows.append({
            "Item": item,
            "N": len(col),
            "Mean": round(col.mean(), 2),
            "Median": col.median(),
            "SD": round(col.std(), 2),
            "Q1": col.quantile(0.25),
            "Q3": col.quantile(0.75),
            "Min": col.min(),
            "Max": col.max(),
        })
    return pd.DataFrame(rows)


def frequency_table(df: pd.DataFrame, items: list, labels: list, scale: int) -> pd.DataFrame:
    """Compute frequency distribution for each item."""
    scale_values = list(range(1, scale + 1))
    item_labels = labels if labels else [str(v) for v in scale_values]

    rows = []
    for item in items:
        col = df[item].dropna()
        row = {"Item": item, "N": len(col)}
        for val, label in zip(scale_values, item_labels):
            count = (col == val).sum()
            pct = count / len(col) * 100
            row[f"{label} (n)"] = count
            row[f"{label} (%)"] = round(pct, 1)
        rows.append(row)
    return pd.DataFrame(rows)


def cronbach_alpha(df: pd.DataFrame, items: list) -> float:
    """Compute Cronbach's alpha for a set of items."""
    if not PINGOUIN_AVAILABLE:
        return None
    try:
        result = pg.cronbach_alpha(df[items].dropna())
        return round(result[0], 3)
    except Exception as e:
        print(f"  Warning: Could not compute Cronbach's alpha: {e}")
        return None


def compare_groups(df: pd.DataFrame, items: list, group_col: str) -> pd.DataFrame:
    """Mann-Whitney U test for group comparison on each item."""
    groups = df[group_col].dropna().unique()
    if len(groups) != 2:
        print(f"  Warning: Group comparison requires exactly 2 groups; found {len(groups)}")
        return pd.DataFrame()

    g1, g2 = groups
    rows = []
    for item in items:
        d1 = df.loc[df[group_col] == g1, item].dropna()
        d2 = df.loc[df[group_col] == g2, item].dropna()

        stat, p = stats.mannwhitneyu(d1, d2, alternative="two-sided")
        # Rank-biserial r (effect size)
        n1, n2 = len(d1), len(d2)
        r = 1 - (2 * stat) / (n1 * n2)

        rows.append({
            "Item": item,
            f"{g1} Median [IQR]": f"{d1.median():.1f} [{d1.quantile(0.25):.1f}–{d1.quantile(0.75):.1f}]",
            f"{g2} Median [IQR]": f"{d2.median():.1f} [{d2.quantile(0.25):.1f}–{d2.quantile(0.75):.1f}]",
            "U statistic": round(stat, 1),
            "P value": round(p, 3),
            "r (effect size)": round(r, 3),
            "Interpretation": "small" if abs(r) < 0.3 else ("medium" if abs(r) < 0.5 else "large"),
        })
    return pd.DataFrame(rows)


def prepost_comparison(df: pd.DataFrame, pre_items: list, post_items: list) -> pd.DataFrame:
    """Wilcoxon signed-rank test for pre-post comparison."""
    rows = []
    for pre, post in zip(pre_items, post_items):
        paired = df[[pre, post]].dropna()
        d_pre = paired[pre]
        d_post = paired[post]

        stat, p = stats.wilcoxon(d_pre, d_post, alternative="two-sided")
        n = len(paired)
        z = stats.norm.ppf(p / 2)  # approximation
        r = abs(z) / np.sqrt(n)

        rows.append({
            "Item": f"{pre} → {post}",
            "N (paired)": n,
            "Pre Median [IQR]": f"{d_pre.median():.1f} [{d_pre.quantile(0.25):.1f}–{d_pre.quantile(0.75):.1f}]",
            "Post Median [IQR]": f"{d_post.median():.1f} [{d_post.quantile(0.25):.1f}–{d_post.quantile(0.75):.1f}]",
            "W statistic": round(stat, 1),
            "P value": round(p, 3),
            "r (effect size)": round(r, 3),
        })
    return pd.DataFrame(rows)


def diverging_bar_chart(
    df: pd.DataFrame,
    items: list,
    labels: list,
    scale: int,
    group_col: str = None,
    output_path: str = "likert_chart",
    item_names: dict = None,
) -> None:
    """Generate diverging stacked bar chart."""
    colors = DIVERGE_COLORS_5 if scale == 5 else DIVERGE_COLORS_7
    scale_values = list(range(1, scale + 1))
    neutral_idx = scale // 2  # 0-indexed neutral position

    plot_df = df[items].copy()

    # Compute proportions for each item
    prop_data = []
    for item in items:
        col = plot_df[item].dropna()
        n = len(col)
        props = [(col == v).sum() / n for v in scale_values]
        prop_data.append(props)

    prop_arr = np.array(prop_data)  # shape: (n_items, scale)

    fig, ax = plt.subplots(figsize=(7.0, max(3.0, len(items) * 0.55 + 1.5)))

    y_pos = np.arange(len(items))
    height = 0.6

    # Diverging: negative on left, positive on right
    neg_props = prop_arr[:, :neutral_idx]     # columns before neutral
    neutral_prop = prop_arr[:, neutral_idx]   # neutral column
    pos_props = prop_arr[:, neutral_idx + 1:] # columns after neutral

    # Starting x for left bars (negative, goes left from center)
    left_start = -(neg_props.sum(axis=1) + neutral_prop / 2)

    # Draw negative bars (left to right, so right-most color first)
    x_left = left_start.copy()
    for i in range(neg_props.shape[1] - 1, -1, -1):
        ax.barh(y_pos, neg_props[:, i], left=x_left, height=height,
                color=colors[i], edgecolor="white", linewidth=0.5)
        x_left += neg_props[:, i]

    # Draw neutral bar
    x_neutral = -(neutral_prop / 2)
    ax.barh(y_pos, neutral_prop, left=x_neutral, height=height,
            color=colors[neutral_idx], edgecolor="white", linewidth=0.5)

    # Draw positive bars
    x_right = neutral_prop / 2
    for i, j in enumerate(range(neutral_idx + 1, scale)):
        ax.barh(y_pos, pos_props[:, i], left=x_right, height=height,
                color=colors[j], edgecolor="white", linewidth=0.5)
        x_right += pos_props[:, i]

    # Percentage labels on bars > 10%
    # (omitted for brevity — add if needed)

    # Axes formatting
    ax.axvline(0, color="black", linewidth=0.8, zorder=5)
    ax.set_yticks(y_pos)
    y_labels = [item_names.get(item, item) if item_names else item for item in items]
    ax.set_yticklabels(y_labels, fontsize=8)
    ax.set_xlabel("Proportion of respondents", fontsize=9)

    # X-axis: convert to percentage
    xticks = ax.get_xticks()
    ax.set_xticklabels([f"{abs(x)*100:.0f}%" for x in xticks], fontsize=8)

    # Legend
    legend_patches = [mpatches.Patch(color=colors[i], label=labels[i])
                      for i in range(scale)]
    ax.legend(handles=legend_patches, loc="lower center",
              bbox_to_anchor=(0.5, -0.25), ncol=scale, fontsize=7.5,
              frameon=False)

    ax.set_xlim(-1.0, 1.0)
    ax.grid(axis="x", color="#DDDDDD", linewidth=0.5)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()

    for ext in ["pdf", "png"]:
        outfile = f"{output_path}_diverging.{ext}"
        dpi = 300 if ext == "png" else None
        plt.savefig(outfile, dpi=dpi, bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        print(f"Saved: {outfile}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Likert scale analysis")
    parser.add_argument("--input", required=True)
    parser.add_argument("--items", nargs="+", required=True)
    parser.add_argument("--labels", nargs="+",
                        default=["Strongly Disagree", "Disagree", "Neutral",
                                  "Agree", "Strongly Agree"])
    parser.add_argument("--scale", type=int, default=5, choices=[5, 7])
    parser.add_argument("--group", default=None)
    parser.add_argument("--pre-items", nargs="+", default=None)
    parser.add_argument("--post-items", nargs="+", default=None)
    parser.add_argument("--output", default="likert_analysis")

    args = parser.parse_args()

    df = load_data(args.input, args.items)
    print(f"\nLoaded: {len(df)} respondents, {len(args.items)} items")

    # ── Descriptive statistics ────────────────────────────────────────────────
    print("\n── Descriptive Statistics ──────────────────")
    desc = descriptive_stats(df, args.items, args.labels)
    print(desc.to_string(index=False))

    # ── Frequency table ───────────────────────────────────────────────────────
    print("\n── Frequency Distribution ──────────────────")
    freq = frequency_table(df, args.items, args.labels, args.scale)
    print(freq.to_string(index=False))

    # ── Cronbach's alpha ──────────────────────────────────────────────────────
    if PINGOUIN_AVAILABLE:
        alpha = cronbach_alpha(df, args.items)
        if alpha is not None:
            print(f"\n── Cronbach's Alpha: {alpha}")
            interp = ("excellent" if alpha >= 0.9 else
                      "good" if alpha >= 0.8 else
                      "acceptable" if alpha >= 0.7 else
                      "questionable" if alpha >= 0.6 else "poor")
            print(f"   Interpretation: {interp}")

    # ── Group comparison ──────────────────────────────────────────────────────
    if args.group and args.group in df.columns:
        print(f"\n── Group Comparison ({args.group}) — Mann-Whitney U ──")
        grp = compare_groups(df, args.items, args.group)
        if not grp.empty:
            print(grp.to_string(index=False))
            grp.to_csv(f"{args.output}_group_comparison.csv", index=False)
            print(f"Saved: {args.output}_group_comparison.csv")

    # ── Pre-post comparison ───────────────────────────────────────────────────
    if args.pre_items and args.post_items:
        print("\n── Pre-Post Comparison — Wilcoxon Signed-Rank ──")
        pp = prepost_comparison(df, args.pre_items, args.post_items)
        print(pp.to_string(index=False))
        pp.to_csv(f"{args.output}_prepost.csv", index=False)
        print(f"Saved: {args.output}_prepost.csv")

    # ── Save tables ───────────────────────────────────────────────────────────
    desc.to_csv(f"{args.output}_descriptive.csv", index=False)
    freq.to_csv(f"{args.output}_frequency.csv", index=False)
    print(f"\nSaved: {args.output}_descriptive.csv")
    print(f"Saved: {args.output}_frequency.csv")

    # ── Diverging bar chart ───────────────────────────────────────────────────
    diverging_bar_chart(df, args.items, args.labels, args.scale,
                         output_path=args.output)

    print("\n── Session Info ─────────────────────────────")
    print(f"Python: {sys.version.split()[0]}")
    for pkg in ["pandas", "numpy", "scipy", "pingouin"]:
        try:
            import importlib
            m = importlib.import_module(pkg)
            print(f"  {pkg}: {m.__version__}")
        except Exception:
            print(f"  {pkg}: not installed")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("No arguments provided. Run with --help for usage.")
        print("\nExample:")
        print("  python likert_summary.py --input survey.csv "
              "--items Q1 Q2 Q3 Q4 Q5 --scale 5 --group specialty")
    else:
        main()
