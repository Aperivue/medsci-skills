"""
Template: Table 1 — Baseline Demographics
Generates a publication-ready demographics table from tabular data.

Usage:
    Modify the CONFIGURATION section below, then run:
        python table1_demographics.py

Input:  CSV or Excel file with one row per subject
Output: table1_demographics.csv, table1_demographics.md (console), summary text
"""

# === REPRODUCIBILITY HEADER ===
import sys
import datetime
import numpy as np
import pandas as pd
from scipy import stats

np.random.seed(42)
print(f"Date: {datetime.date.today()}")
print(f"Python: {sys.version}")
print(f"numpy: {np.__version__}, pandas: {pd.__version__}, scipy: {stats.scipy.__version__}")
print()

# === CONFIGURATION (modify for your study) ===
INPUT_FILE = "data.csv"           # Path to input data
OUTPUT_DIR = "."                  # Output directory
GROUP_COL = None                  # Column name for group comparison (None = no comparison)
CONTINUOUS_VARS = []              # List of continuous variable column names
CATEGORICAL_VARS = []            # List of categorical variable column names
VAR_LABELS = {}                   # Optional display labels: {"col_name": "Display Name (unit)"}
DECIMAL_PLACES = 1                # Decimal places for continuous variables
# ==============================================


def load_data(filepath: str) -> pd.DataFrame:
    """Load CSV or Excel file."""
    if filepath.endswith((".xlsx", ".xls")):
        return pd.read_excel(filepath)
    return pd.read_csv(filepath)


def test_normality(series: pd.Series, alpha: float = 0.05) -> tuple:
    """Test normality using Shapiro-Wilk (n<50) or Kolmogorov-Smirnov (n>=50)."""
    clean = series.dropna()
    if len(clean) < 3:
        return False, np.nan
    if len(clean) < 50:
        stat, p = stats.shapiro(clean)
    else:
        stat, p = stats.kstest(clean, "norm", args=(clean.mean(), clean.std()))
    return p >= alpha, p


def format_continuous(series: pd.Series, is_normal: bool, dp: int = 1) -> str:
    """Format continuous variable as mean +/- SD or median (IQR)."""
    clean = series.dropna()
    if is_normal:
        return f"{clean.mean():.{dp}f} +/- {clean.std():.{dp}f}"
    else:
        q1, median, q3 = clean.quantile([0.25, 0.5, 0.75])
        return f"{median:.{dp}f} ({q1:.{dp}f}-{q3:.{dp}f})"


def format_categorical(series: pd.Series) -> dict:
    """Format categorical variable as n (%)."""
    counts = series.value_counts(dropna=False)
    total = len(series)
    result = {}
    for cat, n in counts.items():
        pct = 100.0 * n / total if total > 0 else 0.0
        label = str(cat) if pd.notna(cat) else "Missing"
        result[label] = f"{n} ({pct:.1f}%)"
    return result


def compare_continuous(groups: list, is_normal: bool) -> tuple:
    """Compare continuous variable between groups."""
    clean_groups = [g.dropna() for g in groups]
    if len(clean_groups) == 2:
        if is_normal:
            stat, p = stats.ttest_ind(*clean_groups)
            return "t-test", p
        else:
            stat, p = stats.mannwhitneyu(*clean_groups, alternative="two-sided")
            return "Mann-Whitney U", p
    else:
        if is_normal:
            stat, p = stats.f_oneway(*clean_groups)
            return "ANOVA", p
        else:
            stat, p = stats.kruskal(*clean_groups)
            return "Kruskal-Wallis", p


def compare_categorical(contingency: pd.DataFrame) -> tuple:
    """Compare categorical variable between groups using chi-square or Fisher's exact."""
    table = contingency.values
    # Use Fisher's exact test for 2x2 tables with any expected count < 5
    if table.shape == (2, 2):
        expected = stats.chi2_contingency(table, correction=False)[3]
        if (expected < 5).any():
            odds_ratio, p = stats.fisher_exact(table)
            return "Fisher's exact", p
    # Otherwise chi-square (with Yates' correction for 2x2)
    chi2, p, dof, expected = stats.chi2_contingency(table)
    if (expected < 5).any():
        print(f"  Warning: expected counts < 5 in some cells; consider collapsing categories.")
    return "Chi-square", p


def format_p(p: float) -> str:
    """Format p-value per reporting rules."""
    if pd.isna(p):
        return ""
    if p < 0.001:
        return "<0.001"
    return f"{p:.3f}"


def build_table1(df: pd.DataFrame) -> pd.DataFrame:
    """Build the full Table 1 dataframe."""
    rows = []
    test_footnotes = set()

    if GROUP_COL and GROUP_COL in df.columns:
        groups = df[GROUP_COL].dropna().unique()
        groups = sorted(groups, key=str)
        group_dfs = {str(g): df[df[GROUP_COL] == g] for g in groups}
    else:
        groups = []
        group_dfs = {}

    n_row = {"Variable": "n"}
    if group_dfs:
        for g_name, g_df in group_dfs.items():
            n_row[g_name] = str(len(g_df))
    n_row["Overall"] = str(len(df))
    if group_dfs:
        n_row["p-value"] = ""
        n_row["Test"] = ""
    rows.append(n_row)

    # --- Continuous variables ---
    for var in CONTINUOUS_VARS:
        if var not in df.columns:
            print(f"Warning: '{var}' not found in data, skipping.")
            continue
        label = VAR_LABELS.get(var, var)
        is_normal, norm_p = test_normality(df[var])
        stat_type = "mean +/- SD" if is_normal else "median (IQR)"

        row = {"Variable": f"{label}, {stat_type}"}
        row["Overall"] = format_continuous(df[var], is_normal, DECIMAL_PLACES)

        if group_dfs:
            for g_name, g_df in group_dfs.items():
                row[g_name] = format_continuous(g_df[var], is_normal, DECIMAL_PLACES)
            grp_series = [g_df[var] for g_df in group_dfs.values()]
            test_name, p_val = compare_continuous(grp_series, is_normal)
            row["p-value"] = format_p(p_val)
            row["Test"] = test_name
            test_footnotes.add(test_name)

        rows.append(row)

    # --- Categorical variables ---
    for var in CATEGORICAL_VARS:
        if var not in df.columns:
            print(f"Warning: '{var}' not found in data, skipping.")
            continue
        label = VAR_LABELS.get(var, var)

        # Header row for this variable
        header_row = {"Variable": f"{label}, n (%)"}

        if group_dfs:
            contingency = pd.crosstab(df[var], df[GROUP_COL])
            test_name, p_val = compare_categorical(contingency)
            header_row["p-value"] = format_p(p_val)
            header_row["Test"] = test_name
            test_footnotes.add(test_name)
            for g_name in group_dfs:
                header_row[g_name] = ""
        header_row["Overall"] = ""
        rows.append(header_row)

        # Category rows
        all_cats = format_categorical(df[var])
        for cat_label, cat_val in all_cats.items():
            cat_row = {"Variable": f"  {cat_label}"}
            cat_row["Overall"] = cat_val
            if group_dfs:
                for g_name, g_df in group_dfs.items():
                    cat_counts = format_categorical(g_df[var])
                    cat_row[g_name] = cat_counts.get(cat_label, "0 (0.0%)")
                cat_row["p-value"] = ""
                cat_row["Test"] = ""
            rows.append(cat_row)

    # Build dataframe
    table_df = pd.DataFrame(rows)

    # Reorder columns
    col_order = ["Variable"]
    if group_dfs:
        col_order += [str(g) for g in sorted(groups, key=str)]
    col_order += ["Overall"]
    if group_dfs:
        col_order += ["p-value", "Test"]
    table_df = table_df[col_order]

    print("\n--- Test Methods Used ---")
    for t in sorted(test_footnotes):
        print(f"  - {t}")
    print()

    return table_df


def save_outputs(table_df: pd.DataFrame) -> None:
    """Save table as CSV and print markdown version."""
    import os
    csv_path = os.path.join(OUTPUT_DIR, "table1_demographics.csv")

    # Save CSV (without Test column for manuscript)
    export_df = table_df.drop(columns=["Test"], errors="ignore")
    export_df.to_csv(csv_path, index=False)
    print(f"Saved: {csv_path}")

    # Print markdown table
    print("\n--- Table 1. Baseline Characteristics ---\n")
    print(export_df.to_markdown(index=False))


def print_results_text(df: pd.DataFrame, table_df: pd.DataFrame) -> None:
    """Print copy-paste-ready text for Results section."""
    print("\n--- Results Text (copy-paste ready) ---\n")
    n_total = len(df)

    if GROUP_COL and GROUP_COL in df.columns:
        groups = df[GROUP_COL].dropna().unique()
        group_counts = df[GROUP_COL].value_counts()
        parts = [f"{g} (n = {group_counts[g]})" for g in sorted(groups, key=str)]
        print(f"A total of {n_total} subjects were included and divided into "
              f"{len(groups)} groups: {', '.join(parts)}. "
              f"Baseline characteristics are summarized in Table 1.")
    else:
        print(f"A total of {n_total} subjects were included. "
              f"Baseline characteristics are summarized in Table 1.")

    # Report missing data
    missing = df[CONTINUOUS_VARS + CATEGORICAL_VARS].isnull().sum()
    missing = missing[missing > 0]
    if len(missing) > 0:
        print(f"\nMissing data: ", end="")
        parts = [f"{VAR_LABELS.get(col, col)}: {n} ({100*n/len(df):.1f}%)"
                 for col, n in missing.items()]
        print("; ".join(parts) + ".")


# === MAIN ===
if __name__ == "__main__":
    print("=" * 60)
    print("Table 1: Baseline Demographics")
    print("=" * 60)

    df = load_data(INPUT_FILE)
    print(f"\nLoaded: {INPUT_FILE} ({df.shape[0]} rows, {df.shape[1]} columns)")

    # Auto-detect if CONTINUOUS_VARS and CATEGORICAL_VARS are empty
    if not CONTINUOUS_VARS and not CATEGORICAL_VARS:
        print("\nNo variables specified. Auto-detecting from data types...")
        for col in df.columns:
            if col == GROUP_COL:
                continue
            if pd.api.types.is_numeric_dtype(df[col]) and df[col].nunique() > 10:
                CONTINUOUS_VARS.append(col)
                print(f"  Continuous: {col}")
            elif df[col].nunique() <= 20:
                CATEGORICAL_VARS.append(col)
                print(f"  Categorical: {col}")

    table_df = build_table1(df)
    save_outputs(table_df)
    print_results_text(df, table_df)
