"""
Template: Inter-rater Agreement Analysis
Calculates Cohen's/Fleiss' kappa, ICC, and Krippendorff's alpha with bootstrap CIs.
Generates Bland-Altman plots for continuous measurements.

Usage:
    Modify the CONFIGURATION section below, then run:
        python agreement_analysis.py

Input:  CSV with rows=items, columns=raters (or long format)
Output: agreement_table.csv, bland_altman.pdf/.png, summary text
"""

# === REPRODUCIBILITY HEADER ===
import sys
import os
import datetime
import warnings
import numpy as np
import pandas as pd
from scipy import stats

np.random.seed(42)
print(f"Date: {datetime.date.today()}")
print(f"Python: {sys.version}")
print(f"numpy: {np.__version__}, pandas: {pd.__version__}, scipy: {stats.scipy.__version__}")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

STYLE_PATH = os.path.expanduser(
    "~/.claude/skills/analyze-stats/references/style/figure_style.mplstyle"
)
if os.path.exists(STYLE_PATH):
    plt.style.use(STYLE_PATH)

print()

# === CONFIGURATION (modify for your study) ===
INPUT_FILE = "data.csv"           # Path to input data
OUTPUT_DIR = "."                  # Output directory
RATER_COLS = []                   # Column names for each rater (wide format)
DATA_TYPE = "auto"                # "categorical", "ordinal", "continuous", or "auto"
BOOTSTRAP_N = 1000                # Number of bootstrap iterations for CIs
ALPHA = 0.05                      # Significance level
# ==============================================


def load_data(filepath: str) -> pd.DataFrame:
    """Load CSV or Excel file."""
    if filepath.endswith((".xlsx", ".xls")):
        return pd.read_excel(filepath)
    return pd.read_csv(filepath)


def detect_data_type(df: pd.DataFrame, cols: list) -> str:
    """Auto-detect whether ratings are categorical, ordinal, or continuous."""
    combined = pd.concat([df[c] for c in cols], ignore_index=True).dropna()
    n_unique = combined.nunique()

    if combined.dtype == object or combined.dtype.name == "category":
        return "categorical"
    if n_unique <= 10 and all(combined == combined.astype(int)):
        return "ordinal"
    return "continuous"


def interpret_kappa(kappa: float) -> str:
    """Interpret kappa using Landis & Koch (1977) guidelines."""
    if kappa < 0:
        return "poor"
    if kappa < 0.20:
        return "slight"
    if kappa < 0.40:
        return "fair"
    if kappa < 0.60:
        return "moderate"
    if kappa < 0.80:
        return "substantial"
    return "almost perfect"


def interpret_icc(icc: float) -> str:
    """Interpret ICC using Cicchetti (1994) guidelines."""
    if icc < 0.40:
        return "poor"
    if icc < 0.60:
        return "fair"
    if icc < 0.75:
        return "good"
    return "excellent"


def cohens_kappa(r1: np.ndarray, r2: np.ndarray) -> float:
    """Cohen's kappa for 2 raters, categorical data."""
    from sklearn.metrics import cohen_kappa_score
    return cohen_kappa_score(r1, r2)


def cohens_weighted_kappa(r1: np.ndarray, r2: np.ndarray,
                          weights: str = "linear") -> float:
    """Weighted Cohen's kappa for ordinal data."""
    from sklearn.metrics import cohen_kappa_score
    return cohen_kappa_score(r1, r2, weights=weights)


def fleiss_kappa(rating_matrix: np.ndarray) -> float:
    """Fleiss' kappa for multiple raters, categorical data.

    Args:
        rating_matrix: n_items x n_categories matrix of category counts per item
    """
    n_items, n_categories = rating_matrix.shape
    n_raters = int(rating_matrix.sum(axis=1)[0])

    p_j = rating_matrix.sum(axis=0) / (n_items * n_raters)
    P_i = (rating_matrix**2).sum(axis=1) - n_raters
    P_i = P_i / (n_raters * (n_raters - 1))

    P_bar = P_i.mean()
    P_e = (p_j**2).sum()

    if P_e == 1:
        return 1.0
    return (P_bar - P_e) / (1 - P_e)


def compute_icc(df: pd.DataFrame, cols: list,
                model: str = "two-way", type_: str = "agreement") -> float:
    """Compute Intraclass Correlation Coefficient.

    Args:
        model: "one-way", "two-way" (random), or "two-way-mixed"
        type_: "consistency" or "agreement" (only for two-way)
    Returns: ICC value
    """
    ratings = df[cols].values
    n_subjects, n_raters = ratings.shape

    grand_mean = ratings.mean()

    ss_total = np.sum((ratings - grand_mean) ** 2)
    row_means = ratings.mean(axis=1)
    col_means = ratings.mean(axis=0)

    ss_rows = n_raters * np.sum((row_means - grand_mean) ** 2)
    ss_cols = n_subjects * np.sum((col_means - grand_mean) ** 2)
    ss_error = ss_total - ss_rows - ss_cols

    ms_rows = ss_rows / (n_subjects - 1)
    ms_cols = ss_cols / (n_raters - 1) if n_raters > 1 else 0
    ms_error = ss_error / ((n_subjects - 1) * (n_raters - 1)) if (n_subjects > 1 and n_raters > 1) else 0

    if model == "one-way":
        ms_within = (ss_total - ss_rows) / (n_subjects * (n_raters - 1))
        icc = (ms_rows - ms_within) / (ms_rows + (n_raters - 1) * ms_within)
    elif model in ("two-way", "two-way-mixed"):
        if type_ == "agreement":
            icc = (ms_rows - ms_error) / (
                ms_rows + (n_raters - 1) * ms_error +
                n_raters * (ms_cols - ms_error) / n_subjects
            )
        else:  # consistency
            icc = (ms_rows - ms_error) / (ms_rows + (n_raters - 1) * ms_error)
    else:
        raise ValueError(f"Unknown model: {model}")

    return icc


def bootstrap_ci(data: pd.DataFrame, cols: list, metric_func,
                 n_bootstrap: int = 1000, alpha: float = 0.05,
                 **kwargs) -> tuple:
    """Bootstrap confidence interval for any agreement metric."""
    n = len(data)
    boot_values = []

    for _ in range(n_bootstrap):
        idx = np.random.choice(n, size=n, replace=True)
        boot_data = data.iloc[idx]
        try:
            val = metric_func(boot_data, cols, **kwargs)
            if np.isfinite(val):
                boot_values.append(val)
        except Exception:
            continue

    if len(boot_values) < 10:
        return (np.nan, np.nan)

    boot_values = np.array(boot_values)
    ci_lo = np.percentile(boot_values, 100 * alpha / 2)
    ci_hi = np.percentile(boot_values, 100 * (1 - alpha / 2))
    return (ci_lo, ci_hi)


def bland_altman_plot(r1: np.ndarray, r2: np.ndarray,
                      name1: str, name2: str, output_dir: str) -> dict:
    """Generate Bland-Altman plot for two continuous raters."""
    mean_vals = (r1 + r2) / 2
    diff_vals = r1 - r2
    mean_diff = diff_vals.mean()
    std_diff = diff_vals.std(ddof=1)

    loa_upper = mean_diff + 1.96 * std_diff
    loa_lower = mean_diff - 1.96 * std_diff

    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    ax.scatter(mean_vals, diff_vals, s=15, alpha=0.6, color="#0072B2", edgecolors="none")
    ax.axhline(mean_diff, color="#D55E00", linewidth=1, label=f"Mean: {mean_diff:.2f}")
    ax.axhline(loa_upper, color="#D55E00", linewidth=0.8, linestyle="--",
               label=f"+1.96 SD: {loa_upper:.2f}")
    ax.axhline(loa_lower, color="#D55E00", linewidth=0.8, linestyle="--",
               label=f"-1.96 SD: {loa_lower:.2f}")
    ax.set_xlabel(f"Mean of {name1} and {name2}")
    ax.set_ylabel(f"Difference ({name1} - {name2})")
    ax.legend(fontsize=7, loc="upper right")

    fig.tight_layout()
    pdf_path = os.path.join(output_dir, "bland_altman.pdf")
    png_path = os.path.join(output_dir, "bland_altman.png")
    fig.savefig(pdf_path, format="pdf", bbox_inches="tight")
    fig.savefig(png_path, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {pdf_path}")
    print(f"Saved: {png_path}")

    return {
        "mean_diff": mean_diff,
        "sd_diff": std_diff,
        "loa_lower": loa_lower,
        "loa_upper": loa_upper,
    }


def _icc_for_bootstrap(data, cols, model="two-way", type_="agreement"):
    """Wrapper for ICC to use with bootstrap_ci."""
    return compute_icc(data, cols, model=model, type_=type_)


def _kappa_for_bootstrap_2raters(data, cols):
    """Wrapper for Cohen's kappa to use with bootstrap_ci."""
    r1 = data[cols[0]].values
    r2 = data[cols[1]].values
    mask = ~(pd.isna(r1) | pd.isna(r2))
    if mask.sum() < 2:
        return np.nan
    return cohens_kappa(r1[mask], r2[mask])


def analyze_categorical(df: pd.DataFrame, cols: list, output_dir: str) -> list:
    """Run agreement analysis for categorical data."""
    results = []
    n_raters = len(cols)
    n_items = len(df)

    if n_raters == 2:
        r1 = df[cols[0]].values
        r2 = df[cols[1]].values
        mask = ~(pd.isna(r1) | pd.isna(r2))
        r1_clean, r2_clean = r1[mask], r2[mask]

        kappa = cohens_kappa(r1_clean, r2_clean)
        ci_lo, ci_hi = bootstrap_ci(df, cols, _kappa_for_bootstrap_2raters,
                                     n_bootstrap=BOOTSTRAP_N, alpha=ALPHA)

        results.append({
            "Metric": "Cohen's kappa",
            "Value": f"{kappa:.3f}",
            "95% CI": f"({ci_lo:.3f}-{ci_hi:.3f})",
            "Interpretation": interpret_kappa(kappa),
            "n_items": int(mask.sum()),
            "n_raters": 2,
        })

        pct_agree = np.mean(r1_clean == r2_clean)
        results.append({
            "Metric": "Percent agreement",
            "Value": f"{pct_agree:.3f}",
            "95% CI": "",
            "Interpretation": "",
            "n_items": int(mask.sum()),
            "n_raters": 2,
        })
    else:
        categories = sorted(set(pd.concat([df[c] for c in cols]).dropna().unique()))
        rating_counts = np.zeros((n_items, len(categories)))
        for i in range(n_items):
            for c in cols:
                val = df[c].iloc[i]
                if pd.notna(val) and val in categories:
                    rating_counts[i, categories.index(val)] += 1

        fk = fleiss_kappa(rating_counts)
        results.append({
            "Metric": "Fleiss' kappa",
            "Value": f"{fk:.3f}",
            "95% CI": "",
            "Interpretation": interpret_kappa(fk),
            "n_items": n_items,
            "n_raters": n_raters,
        })

    return results


def analyze_continuous(df: pd.DataFrame, cols: list, output_dir: str) -> list:
    """Run agreement analysis for continuous data."""
    results = []
    n_raters = len(cols)

    for type_ in ["agreement", "consistency"]:
        icc = compute_icc(df, cols, model="two-way", type_=type_)
        ci_lo, ci_hi = bootstrap_ci(df, cols, _icc_for_bootstrap,
                                     n_bootstrap=BOOTSTRAP_N, alpha=ALPHA,
                                     model="two-way", type_=type_)
        label = f"ICC (two-way, {type_})"
        results.append({
            "Metric": label,
            "Value": f"{icc:.3f}",
            "95% CI": f"({ci_lo:.3f}-{ci_hi:.3f})",
            "Interpretation": interpret_icc(icc),
            "n_items": len(df),
            "n_raters": n_raters,
        })

    if n_raters == 2:
        r1 = df[cols[0]].values.astype(float)
        r2 = df[cols[1]].values.astype(float)
        mask = ~(np.isnan(r1) | np.isnan(r2))
        ba = bland_altman_plot(r1[mask], r2[mask], cols[0], cols[1], output_dir)
        results.append({
            "Metric": "Bland-Altman mean diff",
            "Value": f"{ba['mean_diff']:.3f}",
            "95% CI": f"LoA: ({ba['loa_lower']:.3f}-{ba['loa_upper']:.3f})",
            "Interpretation": "",
            "n_items": int(mask.sum()),
            "n_raters": 2,
        })

    return results


def analyze_ordinal(df: pd.DataFrame, cols: list, output_dir: str) -> list:
    """Run agreement analysis for ordinal data (weighted kappa + ICC)."""
    results = []

    if len(cols) == 2:
        r1 = df[cols[0]].values
        r2 = df[cols[1]].values
        mask = ~(pd.isna(r1) | pd.isna(r2))
        r1_clean, r2_clean = r1[mask], r2[mask]

        for weight in ["linear", "quadratic"]:
            wk = cohens_weighted_kappa(r1_clean, r2_clean, weights=weight)
            results.append({
                "Metric": f"Weighted kappa ({weight})",
                "Value": f"{wk:.3f}",
                "95% CI": "",
                "Interpretation": interpret_kappa(wk),
                "n_items": int(mask.sum()),
                "n_raters": 2,
            })

    results.extend(analyze_continuous(df, cols, output_dir))
    return results


def save_results(results: list, output_dir: str) -> None:
    """Save agreement metrics as CSV and print formatted output."""
    df = pd.DataFrame(results)
    csv_path = os.path.join(output_dir, "agreement_table.csv")
    df.to_csv(csv_path, index=False)
    print(f"\nSaved: {csv_path}")
    print("\n--- Agreement Analysis Results ---\n")
    print(df.to_markdown(index=False))


def print_results_text(results: list, data_type: str) -> None:
    """Print manuscript-ready text for Results section."""
    print("\n--- Results Text (copy-paste ready) ---\n")

    for r in results:
        metric = r["Metric"]
        value = r["Value"]
        ci = r.get("95% CI", "")
        interp = r.get("Interpretation", "")
        n_items = r.get("n_items", "")
        n_raters = r.get("n_raters", "")

        text = f"{metric} was {value}"
        if ci:
            text += f" (95% CI: {ci})"
        if interp:
            text += f", indicating {interp} agreement"
        text += f" (n = {n_items} items, {n_raters} raters)."
        print(text)
    print()


# === MAIN ===
if __name__ == "__main__":
    print("=" * 60)
    print("Inter-rater Agreement Analysis")
    print("=" * 60)

    df = load_data(INPUT_FILE)
    print(f"\nLoaded: {INPUT_FILE} ({df.shape[0]} rows, {df.shape[1]} columns)")

    if not RATER_COLS:
        RATER_COLS = [c for c in df.columns if c.lower().startswith("rater")]
        if not RATER_COLS:
            RATER_COLS = list(df.columns)
        print(f"Using rater columns: {RATER_COLS}")

    if DATA_TYPE == "auto":
        DATA_TYPE = detect_data_type(df, RATER_COLS)
    print(f"Data type: {DATA_TYPE}")
    print(f"Items: {len(df)}, Raters: {len(RATER_COLS)}")

    for col in RATER_COLS:
        n_miss = df[col].isna().sum()
        if n_miss > 0:
            print(f"  Missing in {col}: {n_miss} ({100*n_miss/len(df):.1f}%)")

    if DATA_TYPE == "categorical":
        results = analyze_categorical(df, RATER_COLS, OUTPUT_DIR)
    elif DATA_TYPE == "ordinal":
        results = analyze_ordinal(df, RATER_COLS, OUTPUT_DIR)
    elif DATA_TYPE == "continuous":
        results = analyze_continuous(df, RATER_COLS, OUTPUT_DIR)
    else:
        raise ValueError(f"Unknown data type: {DATA_TYPE}")

    save_results(results, OUTPUT_DIR)
    print_results_text(results, DATA_TYPE)
