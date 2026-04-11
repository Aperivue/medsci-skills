"""
Template: Propensity Score Analysis
Supports PS matching, IPTW, and overlap weighting for observational studies.
Generates balance tables, Love plots, and weighted outcome analyses.

Usage:
    Modify the CONFIGURATION section below, then run:
        python propensity_score.py

Input:  CSV with treatment indicator, outcome, and covariate columns
Output: balance table CSV, Love plot PDF/PNG, PS distribution plot, outcome results
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

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.neighbors import NearestNeighbors
    import sklearn
    print(f"sklearn: {sklearn.__version__}")
except ImportError:
    print("Error: scikit-learn not installed. Install with: pip install scikit-learn")
    sys.exit(1)

try:
    import statsmodels.api as sm
    print(f"statsmodels: {sm.__version__}")
except ImportError:
    print("Error: statsmodels not installed. Install with: pip install statsmodels")
    sys.exit(1)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

STYLE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "style", "figure_style.mplstyle")
if os.path.exists(STYLE_PATH):
    plt.style.use(STYLE_PATH)


# === CONFIGURATION ===
CONFIG = {
    # Data
    "data_path": "data.csv",
    "output_dir": ".",

    # Variables
    "treatment": "treatment",       # Binary treatment indicator (0/1)
    "outcome": "outcome",           # Outcome variable
    "outcome_type": "continuous",    # "continuous" or "binary"
    "covariates": ["age", "sex", "bmi", "comorbidity_score"],
    "categorical_covariates": ["sex"],

    # PS method: "matching", "iptw", "overlap"
    "ps_method": "matching",

    # Matching options
    "caliper_sd_multiplier": 0.2,   # caliper = 0.2 * SD(logit PS)
    "matching_ratio": 1,            # 1:1 matching

    # Balance threshold
    "smd_threshold": 0.10,

    # IPTW options
    "stabilized_weights": True,
    "weight_truncation": 10.0,      # truncate weights > this value
}


# === HELPER FUNCTIONS ===

def estimate_ps(df, treatment_col, covariates):
    """Estimate propensity scores using logistic regression."""
    X = df[covariates].values
    y = df[treatment_col].values
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X, y)
    ps = model.predict_proba(X)[:, 1]
    return ps


def calculate_smd(x1, x0, is_binary=False):
    """Calculate standardized mean difference."""
    if is_binary:
        p1, p0 = x1.mean(), x0.mean()
        denom = np.sqrt((p1 * (1 - p1) + p0 * (1 - p0)) / 2)
        if denom == 0:
            return 0.0
        return (p1 - p0) / denom
    else:
        denom = np.sqrt((x1.var() + x0.var()) / 2)
        if denom == 0:
            return 0.0
        return (x1.mean() - x0.mean()) / denom


def balance_table(df, treatment_col, covariates, categorical_covs, weights=None):
    """Generate balance table with SMD before/after adjustment."""
    treated = df[treatment_col] == 1
    results = []

    for var in covariates:
        is_cat = var in categorical_covs
        x1 = df.loc[treated, var]
        x0 = df.loc[~treated, var]

        if weights is not None:
            w1 = weights[treated]
            w0 = weights[~treated]
            # Weighted means
            wm1 = np.average(x1, weights=w1)
            wm0 = np.average(x0, weights=w0)
            # Weighted SMD (approximate)
            if is_cat:
                denom = np.sqrt((wm1 * (1 - wm1) + wm0 * (1 - wm0)) / 2)
            else:
                wv1 = np.average((x1 - wm1) ** 2, weights=w1)
                wv0 = np.average((x0 - wm0) ** 2, weights=w0)
                denom = np.sqrt((wv1 + wv0) / 2)
            smd_adj = (wm1 - wm0) / denom if denom > 0 else 0.0
        else:
            smd_adj = None

        smd_raw = calculate_smd(x1, x0, is_binary=is_cat)

        row = {
            "Variable": var,
            "Treated_mean": x1.mean(),
            "Treated_sd": x1.std(),
            "Control_mean": x0.mean(),
            "Control_sd": x0.std(),
            "SMD_before": abs(smd_raw),
        }
        if smd_adj is not None:
            row["SMD_after"] = abs(smd_adj)
        results.append(row)

    return pd.DataFrame(results)


def plot_love(bal_df, smd_threshold, output_dir, title="Love Plot"):
    """Generate Love plot comparing SMD before and after adjustment."""
    fig, ax = plt.subplots(figsize=(8, max(3, len(bal_df) * 0.5)))

    y_pos = range(len(bal_df))
    ax.scatter(bal_df["SMD_before"], y_pos, marker="o", color="gray",
               s=60, label="Before", zorder=3)
    if "SMD_after" in bal_df.columns:
        ax.scatter(bal_df["SMD_after"], y_pos, marker="s", color="navy",
                   s=60, label="After", zorder=4)

    ax.axvline(x=smd_threshold, color="red", linestyle="--", alpha=0.7,
               label=f"Threshold ({smd_threshold})")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(bal_df["Variable"])
    ax.set_xlabel("Absolute Standardized Mean Difference")
    ax.set_title(title)
    ax.legend(loc="best")
    ax.set_xlim(left=0)

    plt.tight_layout()
    for ext in ["pdf", "png"]:
        fig.savefig(os.path.join(output_dir, f"love_plot.{ext}"),
                    dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: love_plot.pdf/.png")


def plot_ps_distribution(ps, treatment, output_dir):
    """Plot PS distribution by treatment group."""
    fig, ax = plt.subplots(figsize=(8, 5))

    ax.hist(ps[treatment == 1], bins=30, alpha=0.5, density=True,
            color="steelblue", label="Treated")
    ax.hist(ps[treatment == 0], bins=30, alpha=0.5, density=True,
            color="coral", label="Control")
    ax.set_xlabel("Propensity Score")
    ax.set_ylabel("Density")
    ax.set_title("Propensity Score Distribution")
    ax.legend()

    plt.tight_layout()
    for ext in ["pdf", "png"]:
        fig.savefig(os.path.join(output_dir, f"ps_distribution.{ext}"),
                    dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: ps_distribution.pdf/.png")


def ps_matching(df, ps, treatment_col, caliper_sd_mult=0.2, ratio=1):
    """Perform 1:N nearest-neighbor PS matching with caliper."""
    logit_ps = np.log(ps / (1 - ps))
    caliper = caliper_sd_mult * logit_ps.std()

    treated_idx = df.index[df[treatment_col] == 1].values
    control_idx = df.index[df[treatment_col] == 0].values

    treated_logit = logit_ps[treated_idx].reshape(-1, 1)
    control_logit = logit_ps[control_idx].reshape(-1, 1)

    nn = NearestNeighbors(n_neighbors=ratio, metric="euclidean")
    nn.fit(control_logit)
    distances, indices = nn.kneighbors(treated_logit)

    matched_treated = []
    matched_control = []
    used_controls = set()

    for i, (dist_arr, idx_arr) in enumerate(zip(distances, indices)):
        for d, j in zip(dist_arr, idx_arr):
            ctrl_orig_idx = control_idx[j]
            if d <= caliper and ctrl_orig_idx not in used_controls:
                matched_treated.append(treated_idx[i])
                matched_control.append(ctrl_orig_idx)
                used_controls.add(ctrl_orig_idx)
                break

    matched_indices = matched_treated + matched_control
    n_unmatched = len(treated_idx) - len(matched_treated)

    print(f"\nPS Matching Results:")
    print(f"  Caliper: {caliper:.4f} (= {caliper_sd_mult} x SD(logit PS))")
    print(f"  Matched pairs: {len(matched_treated)}")
    print(f"  Unmatched treated: {n_unmatched}")
    print(f"  Unmatched controls: {len(control_idx) - len(matched_control)}")

    return df.loc[matched_indices].copy(), matched_indices


def iptw_weights(ps, treatment, stabilized=True, truncation=10.0):
    """Calculate IPTW weights (ATE)."""
    if stabilized:
        p_treat = treatment.mean()
        w = np.where(treatment == 1, p_treat / ps, (1 - p_treat) / (1 - ps))
    else:
        w = np.where(treatment == 1, 1 / ps, 1 / (1 - ps))

    # Truncation
    n_truncated = (w > truncation).sum()
    if n_truncated > 0:
        print(f"  Truncated {n_truncated} weights > {truncation}")
        w = np.clip(w, None, truncation)

    print(f"\nIPTW Weights Summary:")
    print(f"  Mean: {w.mean():.2f}, SD: {w.std():.2f}")
    print(f"  Min: {w.min():.2f}, Max: {w.max():.2f}")
    print(f"  Stabilized: {stabilized}")

    return w


def overlap_weights(ps, treatment):
    """Calculate overlap weights (ATO)."""
    w = np.where(treatment == 1, 1 - ps, ps)

    print(f"\nOverlap Weights Summary:")
    print(f"  Mean: {w.mean():.3f}, SD: {w.std():.3f}")
    print(f"  Min: {w.min():.3f}, Max: {w.max():.3f}")

    return w


def weighted_outcome_analysis(df, treatment_col, outcome_col, outcome_type, weights):
    """Perform weighted outcome analysis."""
    import statsmodels.api as sm

    X = sm.add_constant(df[[treatment_col]])
    y = df[outcome_col]

    if outcome_type == "binary":
        model = sm.GLM(y, X, family=sm.families.Binomial(), freq_weights=weights)
    else:
        model = sm.WLS(y, X, weights=weights)

    result = model.fit()
    print(f"\n--- Weighted Outcome Analysis ---")
    print(result.summary2())

    # Extract treatment effect
    coef = result.params[treatment_col]
    ci = result.conf_int().loc[treatment_col]
    p_val = result.pvalues[treatment_col]

    if outcome_type == "binary":
        or_val = np.exp(coef)
        or_ci = np.exp(ci)
        print(f"\nTreatment effect (OR): {or_val:.2f} (95% CI: {or_ci[0]:.2f}-{or_ci[1]:.2f}), P = {p_val:.3f}")
    else:
        print(f"\nTreatment effect (β): {coef:.3f} (95% CI: {ci[0]:.3f}-{ci[1]:.3f}), P = {p_val:.3f}")

    return result


# === MAIN ANALYSIS ===

def main():
    config = CONFIG
    df = pd.read_csv(config["data_path"])
    output_dir = config["output_dir"]
    print(f"Data loaded: {df.shape[0]} rows x {df.shape[1]} columns")

    treatment_col = config["treatment"]
    outcome_col = config["outcome"]
    covariates = config["covariates"]

    # Encode categorical variables
    for cat_var in config.get("categorical_covariates", []):
        if cat_var in df.columns and df[cat_var].dtype == "object":
            df[cat_var] = pd.Categorical(df[cat_var]).codes

    # Drop missing
    analysis_vars = [treatment_col, outcome_col] + covariates
    n_before = len(df)
    df = df.dropna(subset=analysis_vars)
    n_after = len(df)
    if n_before != n_after:
        print(f"Excluded {n_before - n_after} rows with missing data ({100*(n_before-n_after)/n_before:.1f}%)")

    treatment = df[treatment_col].values
    n_treated = treatment.sum()
    n_control = len(treatment) - n_treated

    print(f"\n{'='*60}")
    print(f"PROPENSITY SCORE ANALYSIS")
    print(f"{'='*60}")
    print(f"Method: {config['ps_method'].upper()}")
    print(f"Treated: {n_treated}, Control: {n_control}")
    print(f"Covariates: {len(covariates)}")

    # Step 1: Estimate PS
    print(f"\n--- Step 1: PS Estimation ---")
    ps = estimate_ps(df, treatment_col, covariates)
    df["ps"] = ps
    plot_ps_distribution(ps, treatment, output_dir)

    # Pre-adjustment balance
    print(f"\n--- Pre-adjustment Balance ---")
    bal_before = balance_table(df, treatment_col, covariates,
                               config.get("categorical_covariates", []))
    print(bal_before[["Variable", "SMD_before"]].to_string(index=False))
    n_imbalanced = (bal_before["SMD_before"] > config["smd_threshold"]).sum()
    print(f"Variables with SMD > {config['smd_threshold']}: {n_imbalanced}/{len(covariates)}")

    # Step 2: Apply PS method
    weights = None
    if config["ps_method"] == "matching":
        print(f"\n--- Step 2: PS Matching ---")
        df_matched, _ = ps_matching(
            df, ps, treatment_col,
            caliper_sd_mult=config["caliper_sd_multiplier"],
            ratio=config["matching_ratio"]
        )
        # Balance after matching
        bal_after = balance_table(df_matched, treatment_col, covariates,
                                  config.get("categorical_covariates", []))
        bal_combined = bal_before.copy()
        bal_combined["SMD_after"] = bal_after["SMD_before"].values

    elif config["ps_method"] == "iptw":
        print(f"\n--- Step 2: IPTW ---")
        weights = iptw_weights(ps, treatment,
                                stabilized=config["stabilized_weights"],
                                truncation=config["weight_truncation"])
        df["weights"] = weights
        bal_combined = balance_table(df, treatment_col, covariates,
                                     config.get("categorical_covariates", []),
                                     weights=weights)

    elif config["ps_method"] == "overlap":
        print(f"\n--- Step 2: Overlap Weighting ---")
        weights = overlap_weights(ps, treatment)
        df["weights"] = weights
        bal_combined = balance_table(df, treatment_col, covariates,
                                     config.get("categorical_covariates", []),
                                     weights=weights)

    # Step 3: Balance assessment
    print(f"\n--- Step 3: Post-adjustment Balance ---")
    print(bal_combined[["Variable", "SMD_before", "SMD_after"]].to_string(index=False))
    n_imbalanced_after = (bal_combined["SMD_after"] > config["smd_threshold"]).sum()
    print(f"Variables with SMD > {config['smd_threshold']} after adjustment: "
          f"{n_imbalanced_after}/{len(covariates)}")

    if n_imbalanced_after > 0:
        print("⚠ WARNING: Some covariates remain imbalanced. "
              "Consider adding interaction terms to PS model or switching method.")

    # Love plot
    plot_love(bal_combined, config["smd_threshold"], output_dir)

    # Save balance table
    bal_combined.to_csv(os.path.join(output_dir, "balance_table.csv"), index=False)
    print(f"Saved: balance_table.csv")

    # Step 4: Outcome analysis
    print(f"\n--- Step 4: Outcome Analysis ---")
    if config["ps_method"] == "matching":
        # Simple comparison in matched data
        t_outcome = df_matched.loc[df_matched[treatment_col] == 1, outcome_col]
        c_outcome = df_matched.loc[df_matched[treatment_col] == 0, outcome_col]
        if config["outcome_type"] == "continuous":
            stat, p = stats.ttest_ind(t_outcome, c_outcome)
            diff = t_outcome.mean() - c_outcome.mean()
            print(f"Mean difference: {diff:.3f}")
            print(f"Treated: {t_outcome.mean():.3f} ± {t_outcome.std():.3f}")
            print(f"Control: {c_outcome.mean():.3f} ± {c_outcome.std():.3f}")
            print(f"t = {stat:.3f}, P = {p:.3f}")
        else:
            # For binary outcome in matched data
            tab = pd.crosstab(df_matched[treatment_col], df_matched[outcome_col])
            print(tab)
    else:
        # Weighted analysis for IPTW/OW
        weighted_outcome_analysis(df, treatment_col, outcome_col,
                                   config["outcome_type"], weights)

    print(f"\n{'='*60}")
    print("Propensity score analysis complete.")


if __name__ == "__main__":
    main()
