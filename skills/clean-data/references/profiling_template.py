#!/usr/bin/env python3
"""
Data Profiling Template for Clinical Research Datasets
======================================================

Generates a structured profile of a CSV or Excel dataset.
Outputs a summary table to the console and saves it as CSV.

Usage:
    python profiling_template.py <file_path> [--output <output_dir>]

Requirements:
    - pandas
    - numpy
    - matplotlib, seaborn (optional, for plots)

This script does NOT modify the input data. It is read-only.
"""

import argparse
import os
import sys
import random
from pathlib import Path

import numpy as np
import pandas as pd

# Reproducibility
np.random.seed(42)
random.seed(42)


# ---------------------------------------------------------------------------
# 1. Data Loading
# ---------------------------------------------------------------------------

def load_data(file_path: str) -> pd.DataFrame:
    """Auto-detect CSV vs Excel and load into a DataFrame."""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext in (".csv", ".tsv"):
        sep = "\t" if ext == ".tsv" else ","
        df = pd.read_csv(path, sep=sep, low_memory=False)
    elif ext in (".xls", ".xlsx", ".xlsm"):
        df = pd.read_excel(path, engine="openpyxl")
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use CSV, TSV, or Excel.")

    print(f"Loaded {len(df)} rows x {len(df.columns)} columns from {path.name}")
    return df


# ---------------------------------------------------------------------------
# 2. Variable Summary
# ---------------------------------------------------------------------------

def build_variable_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Build a per-variable summary with type, missingness, and descriptive stats."""
    records = []

    for col in df.columns:
        series = df[col]
        n_missing = int(series.isna().sum())
        pct_missing = round(100 * n_missing / len(df), 2) if len(df) > 0 else 0.0
        n_unique = int(series.nunique(dropna=True))
        inferred_type = _infer_variable_type(series)

        rec = {
            "variable": col,
            "dtype": str(series.dtype),
            "inferred_type": inferred_type,
            "n_total": len(df),
            "n_missing": n_missing,
            "pct_missing": pct_missing,
            "n_unique": n_unique,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "sd": None,
        }

        # Numeric descriptive statistics
        if inferred_type == "numeric":
            numeric = pd.to_numeric(series, errors="coerce")
            rec["min"] = round(float(numeric.min()), 4) if numeric.notna().any() else None
            rec["max"] = round(float(numeric.max()), 4) if numeric.notna().any() else None
            rec["mean"] = round(float(numeric.mean()), 4) if numeric.notna().any() else None
            rec["median"] = round(float(numeric.median()), 4) if numeric.notna().any() else None
            rec["sd"] = round(float(numeric.std()), 4) if numeric.notna().any() else None

        records.append(rec)

    summary = pd.DataFrame(records)
    return summary


def _infer_variable_type(series: pd.Series) -> str:
    """Heuristic type inference: numeric, categorical, datetime, or text."""
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    # Try to parse as numeric (catches numeric-stored-as-string)
    coerced = pd.to_numeric(series.dropna(), errors="coerce")
    if coerced.notna().sum() > 0.8 * series.dropna().shape[0]:
        return "numeric"

    # Try to parse as datetime
    try:
        parsed = pd.to_datetime(series.dropna(), infer_datetime_format=True, errors="coerce")
        if parsed.notna().sum() > 0.8 * series.dropna().shape[0]:
            return "datetime"
    except Exception:
        pass

    # Categorical vs free text heuristic
    n_unique = series.nunique(dropna=True)
    n_rows = len(series.dropna())
    if n_rows > 0 and n_unique / n_rows < 0.05:
        return "categorical"
    if n_unique <= 20:
        return "categorical"

    return "text"


# ---------------------------------------------------------------------------
# 3. Flag Detection
# ---------------------------------------------------------------------------

def flag_missing(summary: pd.DataFrame, threshold: float = 5.0) -> pd.DataFrame:
    """Flag variables with missing percentage above the threshold."""
    flagged = summary[summary["pct_missing"] > threshold].copy()
    flagged["issue"] = "Missing > " + str(threshold) + "%"
    flagged["severity"] = flagged["pct_missing"].apply(
        lambda x: "High" if x > 30 else ("Medium" if x > 10 else "Low")
    )
    return flagged[["variable", "issue", "n_missing", "pct_missing", "severity"]]


def flag_outliers_iqr(df: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    """Flag numeric variables with outliers using the IQR method."""
    results = []
    numeric_vars = summary[summary["inferred_type"] == "numeric"]["variable"].tolist()

    for col in numeric_vars:
        numeric = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(numeric) < 10:
            continue
        q1 = numeric.quantile(0.25)
        q3 = numeric.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = numeric[(numeric < lower) | (numeric > upper)]
        if len(outliers) > 0:
            results.append({
                "variable": col,
                "issue": f"Outlier (IQR): {len(outliers)} values outside [{lower:.2f}, {upper:.2f}]",
                "count": len(outliers),
                "severity": "Medium",
            })

    return pd.DataFrame(results) if results else pd.DataFrame(
        columns=["variable", "issue", "count", "severity"]
    )


# ---------------------------------------------------------------------------
# 4. Distribution Plots (optional)
# ---------------------------------------------------------------------------

def plot_distributions(df: pd.DataFrame, summary: pd.DataFrame, output_dir: str):
    """Generate histograms for numeric and bar charts for categorical variables."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError:
        print("[INFO] matplotlib/seaborn not installed. Skipping distribution plots.")
        return

    plot_dir = os.path.join(output_dir, "profile_plots")
    os.makedirs(plot_dir, exist_ok=True)

    # Numeric histograms
    numeric_vars = summary[summary["inferred_type"] == "numeric"]["variable"].tolist()
    for col in numeric_vars[:20]:  # Limit to first 20 to avoid excessive plots
        fig, ax = plt.subplots(figsize=(6, 4))
        numeric = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(numeric) == 0:
            plt.close(fig)
            continue
        ax.hist(numeric, bins=30, edgecolor="black", alpha=0.7)
        ax.set_title(f"Distribution: {col}")
        ax.set_xlabel(col)
        ax.set_ylabel("Frequency")
        fig.tight_layout()
        fig.savefig(os.path.join(plot_dir, f"hist_{col}.png"), dpi=100)
        plt.close(fig)

    # Categorical bar charts
    cat_vars = summary[summary["inferred_type"] == "categorical"]["variable"].tolist()
    for col in cat_vars[:20]:
        fig, ax = plt.subplots(figsize=(6, 4))
        counts = df[col].value_counts().head(15)
        counts.plot(kind="barh", ax=ax, color="steelblue", edgecolor="black")
        ax.set_title(f"Categories: {col}")
        ax.set_xlabel("Count")
        fig.tight_layout()
        fig.savefig(os.path.join(plot_dir, f"bar_{col}.png"), dpi=100)
        plt.close(fig)

    print(f"[INFO] Distribution plots saved to {plot_dir}/")


# ---------------------------------------------------------------------------
# 5. Report Output
# ---------------------------------------------------------------------------

def print_summary(summary: pd.DataFrame):
    """Print a formatted summary table to the console."""
    display_cols = [
        "variable", "inferred_type", "n_missing", "pct_missing",
        "n_unique", "min", "max", "mean", "median", "sd"
    ]
    print("\n" + "=" * 80)
    print("VARIABLE SUMMARY")
    print("=" * 80)
    print(summary[display_cols].to_string(index=False))
    print("=" * 80)


def save_outputs(summary: pd.DataFrame, flags_missing: pd.DataFrame,
                 flags_outlier: pd.DataFrame, output_dir: str):
    """Save profiling results as CSV files."""
    os.makedirs(output_dir, exist_ok=True)

    summary_path = os.path.join(output_dir, "variable_summary.csv")
    summary.to_csv(summary_path, index=False)
    print(f"[SAVED] Variable summary -> {summary_path}")

    if len(flags_missing) > 0:
        missing_path = os.path.join(output_dir, "flags_missing.csv")
        flags_missing.to_csv(missing_path, index=False)
        print(f"[SAVED] Missing flags -> {missing_path}")

    if len(flags_outlier) > 0:
        outlier_path = os.path.join(output_dir, "flags_outliers.csv")
        flags_outlier.to_csv(outlier_path, index=False)
        print(f"[SAVED] Outlier flags -> {outlier_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Profile a clinical research dataset.")
    parser.add_argument("file_path", help="Path to CSV or Excel file")
    parser.add_argument("--output", default="./data_profile",
                        help="Output directory for profiling results (default: ./data_profile)")
    parser.add_argument("--no-plots", action="store_true",
                        help="Skip distribution plots")
    args = parser.parse_args()

    # Load
    df = load_data(args.file_path)

    # Profile
    summary = build_variable_summary(df)
    print_summary(summary)

    # Flag
    flags_missing = flag_missing(summary, threshold=5.0)
    flags_outlier = flag_outliers_iqr(df, summary)

    if len(flags_missing) > 0:
        print("\n[FLAGS] Variables with >5% missing:")
        print(flags_missing.to_string(index=False))

    if len(flags_outlier) > 0:
        print("\n[FLAGS] Variables with IQR outliers:")
        print(flags_outlier.to_string(index=False))

    # Save
    save_outputs(summary, flags_missing, flags_outlier, args.output)

    # Plot (optional)
    if not args.no_plots:
        plot_distributions(df, summary, args.output)

    print("\n[DONE] Profiling complete. Review outputs before proceeding to cleaning.")


if __name__ == "__main__":
    main()
