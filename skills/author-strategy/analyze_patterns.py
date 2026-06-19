#!/usr/bin/env python3
"""
Analyze publication patterns from a PubMed CSV and generate visualizations + strategy report.

Usage:
    python analyze_patterns.py /path/to/publications.csv [--output-dir /path/to/report/]
"""

import argparse
from collections import Counter
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

matplotlib.rcParams["font.family"] = "Apple SD Gothic Neo"
matplotlib.rcParams["axes.unicode_minus"] = False

COLORS = {
    "GBD": "#e74c3c",
    "NHIS/Claims": "#3498db",
    "SR/MA": "#2ecc71",
    "Cross-national": "#9b59b6",
    "AI/ML": "#f39c12",
    "National survey": "#1abc9c",
    "Biobank": "#e67e22",
    "Clinical trial": "#34495e",
    "Letter/Commentary": "#95a5a6",
    "Case report": "#bdc3c7",
    "Other": "#7f8c8d",
}


def load_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    return df


def plot_yearly_stacked(df: pd.DataFrame, report_dir: Path, author_name: str):
    fig, ax = plt.subplots(figsize=(14, 7))
    min_year = max(int(df["year"].min()), df["year"].max() - 8) if len(df) > 50 else int(df["year"].min())
    df_yr = df[df["year"] >= min_year].copy()
    pivot = df_yr.groupby(["year", "study_type"]).size().unstack(fill_value=0)
    col_order = pivot.sum().sort_values(ascending=False).index
    pivot = pivot[col_order]
    colors = [COLORS.get(c, "#cccccc") for c in pivot.columns]
    pivot.plot(kind="bar", stacked=True, ax=ax, color=colors, width=0.8)
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Publications", fontsize=12)
    ax.set_title(f"{author_name}: Yearly Publication Count by Study Type (N={len(df)})", fontsize=14, fontweight="bold")
    ax.legend(title="Study Type", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=9)
    plt.tight_layout()
    fig.savefig(report_dir / "01_yearly_stacked.png", dpi=150, bbox_inches="tight")
    plt.close()


def plot_study_type_pie(df: pd.DataFrame, report_dir: Path):
    fig, ax = plt.subplots(figsize=(10, 8))
    counts = df["study_type"].value_counts()
    colors = [COLORS.get(c, "#cccccc") for c in counts.index]
    ax.pie(counts, labels=counts.index, autopct="%1.1f%%", colors=colors, pctdistance=0.85, startangle=90)
    ax.set_title(f"Study Type Distribution (N={len(df)})", fontsize=14, fontweight="bold")
    plt.tight_layout()
    fig.savefig(report_dir / "02_study_type_pie.png", dpi=150, bbox_inches="tight")
    plt.close()


def plot_author_position(df: pd.DataFrame, report_dir: Path):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    # Positional heuristic only (not leadership metadata): first / middle / last / unknown.
    pos_order = ["first", "middle", "last", "unknown"]
    pos_counts = df["author_position"].value_counts().reindex(pos_order, fill_value=0)
    colors_pos = ["#e74c3c", "#95a5a6", "#2ecc71", "#bdc3c7"]
    bars = axes[0].bar(pos_counts.index, pos_counts.values, color=colors_pos)
    axes[0].set_title("Author Position Overall", fontsize=12, fontweight="bold")
    axes[0].set_ylabel("Count")
    for bar, val in zip(bars, pos_counts.values):
        axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                     f"{val}\n({val / len(df) * 100:.1f}%)", ha="center", fontsize=9)

    key_types = [t for t in ["GBD", "NHIS/Claims", "SR/MA", "Cross-national", "National survey"]
                 if t in df["study_type"].values]
    if key_types:
        pos_by_type = df[df["study_type"].isin(key_types)].groupby(
            ["study_type", "author_position"]).size().unstack(fill_value=0)
        pos_by_type = pos_by_type.reindex(columns=pos_order, fill_value=0)
        pos_by_type.plot(kind="bar", ax=axes[1], color=colors_pos, width=0.8)
        axes[1].set_title("Author Position by Study Type", fontsize=12, fontweight="bold")
        axes[1].set_ylabel("Count")
        axes[1].legend(title="Position", fontsize=8)
        axes[1].tick_params(axis="x", rotation=0)

    plt.tight_layout()
    fig.savefig(report_dir / "03_author_position.png", dpi=150, bbox_inches="tight")
    plt.close()


def plot_journal_tier_heatmap(df: pd.DataFrame, report_dir: Path):
    fig, ax = plt.subplots(figsize=(12, 8))
    pivot = df.groupby(["study_type", "journal_tier"]).size().unstack(fill_value=0)
    tier_order = ["Lancet family", "Nature family", "NEJM/BMJ/JAMA", "IF>=10", "Other"]
    pivot = pivot.reindex(columns=[c for c in tier_order if c in pivot.columns], fill_value=0)
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
    sns.heatmap(pivot, annot=True, fmt="d", cmap="YlOrRd", ax=ax, linewidths=0.5)
    ax.set_title("Study Type x Journal Tier (count)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    fig.savefig(report_dir / "04_journal_tier_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close()


def plot_topic_distribution(df: pd.DataFrame, report_dir: Path):
    fig, ax = plt.subplots(figsize=(10, 7))
    topic_counts = df["topic"].value_counts()
    colors_topic = sns.color_palette("husl", len(topic_counts))
    bars = ax.barh(topic_counts.index[::-1], topic_counts.values[::-1], color=colors_topic[::-1])
    ax.set_xlabel("Publications")
    ax.set_title(f"Topic Distribution (N={len(df)})", fontsize=14, fontweight="bold")
    for bar, val in zip(bars, topic_counts.values[::-1]):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"{val} ({val / len(df) * 100:.1f}%)", va="center", fontsize=9)
    plt.tight_layout()
    fig.savefig(report_dir / "05_topic_distribution.png", dpi=150, bbox_inches="tight")
    plt.close()


def plot_growth_curve(df: pd.DataFrame, report_dir: Path):
    fig, ax = plt.subplots(figsize=(12, 6))
    min_year = max(int(df["year"].min()), df["year"].max() - 10)
    df_yr = df[df["year"] >= min_year].copy()
    yearly = df_yr.groupby("year").size().sort_index()
    cumulative = yearly.cumsum()
    ax.plot(cumulative.index, cumulative.values, "o-", color="#e74c3c", linewidth=2, markersize=8)
    ax2 = ax.twinx()
    ax2.bar(yearly.index, yearly.values, alpha=0.3, color="#3498db")
    ax.set_xlabel("Year")
    ax.set_ylabel("Cumulative", color="#e74c3c")
    ax2.set_ylabel("Yearly", color="#3498db")
    ax.set_title("Publication Growth Curve", fontsize=14, fontweight="bold")
    for y in cumulative.index:
        ax.annotate(f"{cumulative[y]}", (y, cumulative[y]),
                    textcoords="offset points", xytext=(0, 10), ha="center", fontsize=9)
    plt.tight_layout()
    fig.savefig(report_dir / "06_growth_curve.png", dpi=150, bbox_inches="tight")
    plt.close()


def plot_strategy_roi(df: pd.DataFrame, report_dir: Path):
    fig, ax = plt.subplots(figsize=(12, 8))
    data = []
    for st in df["study_type"].value_counts().index:
        subset = df[df["study_type"] == st]
        n = len(subset)
        high_tier = subset["journal_tier"].isin(
            ["Lancet family", "Nature family", "NEJM/BMJ/JAMA", "IF>=10"]).mean() * 100
        first_last = subset["author_position"].isin(["first", "last"]).mean() * 100
        data.append({"type": st, "count": n, "high_tier_pct": high_tier, "first_last_pct": first_last})
    plot_df = pd.DataFrame(data)
    ax.scatter(
        plot_df["high_tier_pct"], plot_df["first_last_pct"],
        s=plot_df["count"] * 3,
        c=[COLORS.get(t, "#cccccc") for t in plot_df["type"]],
        alpha=0.7, edgecolors="black", linewidths=0.5
    )
    for _, row in plot_df.iterrows():
        ax.annotate(f'{row["type"]}\n(n={row["count"]})',
                    (row["high_tier_pct"], row["first_last_pct"]),
                    fontsize=8, ha="center", va="bottom")
    ax.set_xlabel("% High-Tier Journal (IF>=10)", fontsize=12)
    ax.set_ylabel("% First or Last Author (positional)", fontsize=12)
    ax.set_title("Strategy ROI: Journal Quality vs Author Position vs Volume", fontsize=14, fontweight="bold")
    ax.axhline(y=50, color="gray", linestyle="--", alpha=0.3)
    ax.axvline(x=20, color="gray", linestyle="--", alpha=0.3)
    plt.tight_layout()
    fig.savefig(report_dir / "07_strategy_roi.png", dpi=150, bbox_inches="tight")
    plt.close()


def generate_report(df: pd.DataFrame, report_dir: Path, author_name: str):
    total = len(df)
    types = df["study_type"].value_counts()
    positions = df["author_position"].value_counts()
    high_tier = len(df[df["journal_tier"].isin(
        ["Lancet family", "Nature family", "NEJM/BMJ/JAMA", "IF>=10"])])
    first_last = len(df[df["author_position"].isin(["first", "last"])])

    # Top 3 study types
    top_types = types.head(3)
    type_rows = "\n".join(
        f"| {st} | {n} | {n / total * 100:.1f}% |"
        for st, n in top_types.items()
    )

    # Top 3 topics
    top_topics = df["topic"].value_counts().head(5)
    topic_rows = "\n".join(
        f"| {tp} | {n} | {n / total * 100:.1f}% |"
        for tp, n in top_topics.items()
    )

    # Year range
    years = df["year"].dropna().astype(int)
    year_range = f"{years.min()}-{years.max()}"
    recent_year = years.max()
    recent_count = len(df[df["year"] == recent_year])

    report = f"""# {author_name} — Publication Strategy Analysis

## Summary

| Metric | Value |
|--------|-------|
| Total PubMed publications | {total} |
| Year range | {year_range} |
| {recent_year} publications | {recent_count} |
| High-tier journals (Lancet/Nature/NEJM/BMJ/JAMA/IF>=10) | {high_tier} ({high_tier / total * 100:.1f}%) |
| First or last author (positional heuristic) | {first_last} ({first_last / total * 100:.1f}%) |

## Study Type Breakdown

| Type | Count | % |
|------|-------|---|
{type_rows}
| Other | {total - top_types.sum()} | {(total - top_types.sum()) / total * 100:.1f}% |

## Topic Clusters (Top 5)

| Topic | Count | % |
|-------|-------|---|
{topic_rows}

## Author Position (positional heuristic — not leadership metadata)

| Position | Count | % |
|----------|-------|---|
| First author | {positions.get("first", 0)} | {positions.get("first", 0) / total * 100:.1f}% |
| Last author | {positions.get("last", 0)} | {positions.get("last", 0) / total * 100:.1f}% |
| Middle | {positions.get("middle", 0)} | {positions.get("middle", 0) / total * 100:.1f}% |
| Unknown | {positions.get("unknown", 0)} | {positions.get("unknown", 0) / total * 100:.1f}% |

## Key Observations

1. **Primary strategy**: {types.index[0]} ({types.iloc[0]} papers, {types.iloc[0] / total * 100:.1f}%)
2. **Secondary strategy**: {types.index[1] if len(types) > 1 else "N/A"} ({types.iloc[1] if len(types) > 1 else 0} papers)
3. **High-tier placement rate**: {high_tier / total * 100:.1f}%
4. **First/last positional rate** (positional heuristic, not leadership): {first_last / total * 100:.1f}%

## Visualizations

- `01_yearly_stacked.png` — yearly publication count by study type
- `02_study_type_pie.png` — study type distribution
- `03_author_position.png` — author position overall and by study type
- `04_journal_tier_heatmap.png` — study type x journal tier
- `05_topic_distribution.png` — topic clusters
- `06_growth_curve.png` — cumulative publication growth
- `07_strategy_roi.png` — journal quality vs author position vs volume

---
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
Data source: PubMed, {total} records
"""

    with open(report_dir / "analysis_report.md", "w") as f:
        f.write(report)
    print(f"Saved: analysis_report.md")


def main():
    parser = argparse.ArgumentParser(description="Analyze author publication patterns")
    parser.add_argument("csv_path", help="Path to publications CSV")
    parser.add_argument("--output-dir", "-o", help="Output directory for report", default=None)
    parser.add_argument("--author-name", help="Author name for report title", default="Author")
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    report_dir = Path(args.output_dir) if args.output_dir else csv_path.parent / "report"
    report_dir.mkdir(parents=True, exist_ok=True)

    df = load_data(str(csv_path))
    print(f"Loaded {len(df)} records\n")

    plot_yearly_stacked(df, report_dir, args.author_name)
    print("Saved: 01_yearly_stacked.png")
    plot_study_type_pie(df, report_dir)
    print("Saved: 02_study_type_pie.png")
    plot_author_position(df, report_dir)
    print("Saved: 03_author_position.png")
    plot_journal_tier_heatmap(df, report_dir)
    print("Saved: 04_journal_tier_heatmap.png")
    plot_topic_distribution(df, report_dir)
    print("Saved: 05_topic_distribution.png")
    plot_growth_curve(df, report_dir)
    print("Saved: 06_growth_curve.png")
    plot_strategy_roi(df, report_dir)
    print("Saved: 07_strategy_roi.png")
    generate_report(df, report_dir, args.author_name)

    print(f"\nAll outputs in: {report_dir}")


if __name__ == "__main__":
    main()
