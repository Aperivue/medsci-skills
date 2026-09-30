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
import scipy
from scipy import stats

np.random.seed(42)
print(f"Date: {datetime.date.today()}")
print(f"Python: {sys.version}")
print(f"numpy: {np.__version__}, pandas: {pd.__version__}, scipy: {scipy.__version__}")

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
    # Entered as k-1 indicator columns (reference = most frequent level) whatever
    # their dtype; list numeric-coded nominal covariates here too.
    "categorical_covariates": ["sex"],

    # PS method: "matching", "iptw", "siptw", "overlap"
    "ps_method": "matching",

    # Matching options (greedy nearest neighbour on the logit PS, without
    # replacement, largest PS matched first -- the MatchIt defaults)
    "caliper_sd_multiplier": 0.2,   # caliper = 0.2 * SD(logit PS)
    "matching_ratio": 1,            # controls per treated unit (1 = 1:1, 3 = 1:3)

    # Balance threshold
    "smd_threshold": 0.10,

    # IPTW options
    "stabilized_weights": True,
    "weight_truncation": 10.0,      # truncate weights > this value
}


# === HELPER FUNCTIONS ===

def encode_covariates(df, covariates, categorical_covs):
    """Continuous covariates as-is; categorical ones as k-1 indicator columns
    (reference = most frequent level). Call on complete cases only: encoding
    before dropping missing rows turns a missing category into a level."""
    blocks, binary_cols = [], []
    for var in covariates:
        if var in categorical_covs:
            counts = df[var].value_counts()
            ref = counts.index[0]
            levels = [lv for lv in sorted(counts.index, key=str) if lv != ref]
            cols = {f"{var}={lv}": (df[var] == lv).astype(float) for lv in levels}
            print(f"  {var}: reference = {ref!r}")
            blocks.append(pd.DataFrame(cols, index=df.index))
            binary_cols += list(cols)
        else:
            blocks.append(df[[var]].astype(float))
    return pd.concat(blocks, axis=1), binary_cols


def estimate_ps(X, treatment):
    """Propensity scores from an (unpenalised) logistic regression."""
    fit = sm.GLM(np.asarray(treatment), sm.add_constant(X.values),
                 family=sm.families.Binomial()).fit()
    return np.asarray(fit.fittedvalues)


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
    """Generate balance table with SMD before/after adjustment.

    `covariates` are design-matrix columns; `categorical_covs` lists the ones
    that are 0/1 indicators."""
    treated = (df[treatment_col] == 1).values
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
    """Greedy 1:ratio nearest-neighbour matching on the logit PS, without
    replacement, within a caliper of caliper_sd_mult * SD(logit PS).

    Treated units are processed from the largest PS down; for ratio > 1 the
    matching runs in rounds (every treated unit gets its 1st control before any
    gets its 2nd). Each treated unit takes the nearest AVAILABLE control -- a
    used nearest neighbour does not drop the unit if another control lies
    within the caliper.

    df must have a 0..n-1 RangeIndex aligned with `ps`. Returns the matched
    rows with `subclass` (matched set) and `match_weight` (treated 1; each
    control 1/m for a set with m controls, rescaled to sum to the number of
    matched controls).
    """
    logit_ps = np.log(ps / (1 - ps))
    caliper = caliper_sd_mult * np.std(logit_ps, ddof=1)
    treat = df[treatment_col].values

    t_idx = np.flatnonzero(treat == 1)
    c_idx = np.flatnonzero(treat == 0)
    order = t_idx[np.argsort(-ps[t_idx], kind="stable")]
    c_sorted = c_idx[np.argsort(logit_ps[c_idx], kind="stable")]
    c_vals = logit_ps[c_sorted]
    used = np.zeros(len(c_sorted), dtype=bool)
    matches = {i: [] for i in order}

    for rnd in range(ratio):
        for i in order:
            if len(matches[i]) < rnd:        # found nothing in an earlier round
                continue
            x = logit_ps[i]
            pos = np.searchsorted(c_vals, x)
            left, right = pos - 1, pos
            while left >= 0 and used[left]:
                left -= 1
            while right < len(c_vals) and used[right]:
                right += 1
            cands = []
            if left >= 0:
                cands.append((x - c_vals[left], left))
            if right < len(c_vals):
                cands.append((c_vals[right] - x, right))
            if not cands:
                continue
            dist, j = min(cands)
            if dist <= caliper:
                used[j] = True
                matches[i].append(c_sorted[j])

    rows, subclass, weight = [], [], []
    for s_id, (i, ctrls) in enumerate((i, c) for i, c in matches.items() if c):
        rows += [i] + ctrls
        subclass += [s_id] * (1 + len(ctrls))
        weight += [1.0] + [1.0 / len(ctrls)] * len(ctrls)
    matched = df.loc[rows].copy()
    matched["subclass"] = subclass
    matched["match_weight"] = weight
    is_c = matched[treatment_col].values == 0
    matched.loc[is_c, "match_weight"] *= is_c.sum() / matched.loc[is_c, "match_weight"].sum()

    n_matched_t = sum(1 for c in matches.values() if c)
    n_full = sum(1 for c in matches.values() if len(c) == ratio)
    print(f"\nPS Matching Results (greedy NN, largest PS first, without replacement):")
    print(f"  Caliper: {caliper:.4f} (= {caliper_sd_mult} x SD(logit PS))")
    print(f"  Ratio 1:{ratio} -- treated with {ratio} control(s): {n_full}; "
          f"with fewer: {n_matched_t - n_full}")
    print(f"  Matched treated: {n_matched_t} / {len(t_idx)}; "
          f"matched controls: {int(used.sum())} / {len(c_idx)}")
    n_unmatched = len(t_idx) - n_matched_t
    if n_unmatched:
        print(f"  ⚠ {n_unmatched} treated unit(s) had no control within the caliper and are "
              "excluded: the estimand is the effect in the MATCHED treated, not the ATT "
              "of all treated. Report this number.")
    return matched


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


def siptw_weights(ps, treatment, truncation=10.0):
    """Calculate Stabilized Inverse Probability of Treatment Weights (SIPTW).

    SIPTW maintains the sample size of the entire cohort and allows for
    appropriate estimation of the variance of the main effect. Increasingly
    used in emulated target trial frameworks (Yon DK group pattern).

    Weights:
        Treated:   P(T=1) / PS
        Control:   P(T=0) / (1 - PS)

    This is equivalent to stabilized IPTW but explicitly named SIPTW in some
    literature to distinguish from unstabilized IPTW.
    """
    p_treat = treatment.mean()
    w = np.where(treatment == 1, p_treat / ps, (1 - p_treat) / (1 - ps))

    # Truncation
    n_truncated = (w > truncation).sum()
    if n_truncated > 0:
        print(f"  Truncated {n_truncated} weights > {truncation}")
        w = np.clip(w, None, truncation)

    # Effective sample size
    ess_treated = (w[treatment == 1].sum()) ** 2 / (w[treatment == 1] ** 2).sum()
    ess_control = (w[treatment == 0].sum()) ** 2 / (w[treatment == 0] ** 2).sum()

    print(f"\nSIPTW Weights Summary:")
    print(f"  Mean: {w.mean():.2f}, SD: {w.std():.2f}")
    print(f"  Min: {w.min():.2f}, Max: {w.max():.2f}")
    print(f"  Effective sample size (treated): {ess_treated:.0f} / {(treatment == 1).sum()}")
    print(f"  Effective sample size (control): {ess_control:.0f} / {(treatment == 0).sum()}")

    return w


def overlap_weights(ps, treatment):
    """Calculate overlap weights (ATO)."""
    w = np.where(treatment == 1, 1 - ps, ps)

    print(f"\nOverlap Weights Summary:")
    print(f"  Mean: {w.mean():.3f}, SD: {w.std():.3f}")
    print(f"  Min: {w.min():.3f}, Max: {w.max():.3f}")

    return w


def weighted_outcome_analysis(df, treatment_col, outcome_col, outcome_type, weights,
                              cluster=None):
    """Treatment effect from a weighted regression of the outcome on treatment.

    Weights enter as var_weights (not freq_weights: they are not case counts),
    and the SE is sandwich-robust (HC0) -- or cluster-robust by matched set when
    `cluster` is given. Model-based SEs from a weighted fit are wrong: the
    unstabilised-IPTW CI covered the true null effect in 77% of simulated
    studies (Austin 2016, doi:10.1002/sim.7084). The robust SE ignores the
    estimation of the PS, which is conservative for the ATE; bootstrap the
    whole pipeline if precision is load-bearing.
    """
    X = sm.add_constant(df[[treatment_col]].astype(float))
    y = df[outcome_col].astype(float)
    w = np.asarray(weights, dtype=float)
    fit_kw = ({"cov_type": "cluster", "cov_kwds": {"groups": np.asarray(cluster)}}
              if cluster is not None else {"cov_type": "HC0"})
    se_label = "cluster-robust by matched set" if cluster is not None else "robust (HC0)"

    families = [("mean difference", sm.families.Gaussian(), False)]
    if outcome_type == "binary":
        families = [("OR", sm.families.Binomial(), True),
                    ("risk difference", sm.families.Gaussian(), False)]

    print(f"\n--- Weighted Outcome Analysis ({se_label} SE) ---")
    results = {}
    for label, family, exponentiate in families:
        with warnings.catch_warnings():
            # statsmodels warns that robust covariances are "not fully supported"
            # with var_weights; HC0 and cluster SEs here match R sandwich::vcovHC
            # / vcovCL on the same weighted fits to 6 decimals.
            warnings.filterwarnings("ignore", message="cov_type not fully supported")
            res = sm.GLM(y, X, family=family, var_weights=w).fit(**fit_kw)
        coef = res.params[treatment_col]
        lo, hi = res.conf_int().loc[treatment_col]
        p_val = res.pvalues[treatment_col]
        if exponentiate:
            coef, lo, hi = np.exp(coef), np.exp(lo), np.exp(hi)
        print(f"Treatment effect ({label}): {coef:.3f} (95% CI: {lo:.3f} to {hi:.3f}), "
              f"P = {p_val:.3f}")
        results[label] = (coef, lo, hi, p_val)
    return results


# === MAIN ANALYSIS ===

def main():
    config = CONFIG
    df = pd.read_csv(config["data_path"])
    output_dir = config["output_dir"]
    print(f"Data loaded: {df.shape[0]} rows x {df.shape[1]} columns")

    treatment_col = config["treatment"]
    outcome_col = config["outcome"]
    covariates = config["covariates"]

    # Drop missing FIRST (and re-index so row positions match the PS array),
    # then dummy-code categorical covariates
    analysis_vars = [treatment_col, outcome_col] + covariates
    n_before = len(df)
    df = df.dropna(subset=analysis_vars).reset_index(drop=True)
    n_after = len(df)
    if n_before != n_after:
        print(f"Excluded {n_before - n_after} rows with missing data ({100*(n_before-n_after)/n_before:.1f}%)")
    X_cov, binary_cols = encode_covariates(df, covariates,
                                           config.get("categorical_covariates", []))
    df = pd.concat([df, X_cov.drop(columns=[c for c in X_cov.columns if c in df.columns])],
                   axis=1)
    covariates = list(X_cov.columns)

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
    ps = estimate_ps(X_cov, treatment)
    df["ps"] = ps
    plot_ps_distribution(ps, treatment, output_dir)

    # Pre-adjustment balance
    print(f"\n--- Pre-adjustment Balance ---")
    bal_before = balance_table(df, treatment_col, covariates,
                               binary_cols)
    print(bal_before[["Variable", "SMD_before"]].to_string(index=False))
    n_imbalanced = (bal_before["SMD_before"] > config["smd_threshold"]).sum()
    print(f"Variables with SMD > {config['smd_threshold']}: {n_imbalanced}/{len(covariates)}")

    # Step 2: Apply PS method
    weights = None
    if config["ps_method"] == "matching":
        print(f"\n--- Step 2: PS Matching ---")
        df_matched = ps_matching(
            df, ps, treatment_col,
            caliper_sd_mult=config["caliper_sd_multiplier"],
            ratio=config["matching_ratio"]
        )
        # Balance after matching (match weights: 1/m per control in a 1:m set)
        bal_after = balance_table(df_matched, treatment_col, covariates, binary_cols,
                                  weights=df_matched["match_weight"].values)
        bal_combined = bal_before.copy()
        bal_combined["SMD_after"] = bal_after["SMD_after"].values

    elif config["ps_method"] == "iptw":
        print(f"\n--- Step 2: IPTW ---")
        weights = iptw_weights(ps, treatment,
                                stabilized=config["stabilized_weights"],
                                truncation=config["weight_truncation"])
        df["weights"] = weights
        bal_combined = balance_table(df, treatment_col, covariates,
                                     binary_cols,
                                     weights=weights)

    elif config["ps_method"] == "siptw":
        print(f"\n--- Step 2: SIPTW (Stabilized Inverse Probability of Treatment Weighting) ---")
        weights = siptw_weights(ps, treatment,
                                truncation=config["weight_truncation"])
        df["weights"] = weights
        bal_combined = balance_table(df, treatment_col, covariates,
                                     binary_cols,
                                     weights=weights)

    elif config["ps_method"] == "overlap":
        print(f"\n--- Step 2: Overlap Weighting ---")
        weights = overlap_weights(ps, treatment)
        df["weights"] = weights
        bal_combined = balance_table(df, treatment_col, covariates,
                                     binary_cols,
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
        # Effect in the matched sample: match weights, SE clustered on the matched set
        weighted_outcome_analysis(df_matched, treatment_col, outcome_col,
                                  config["outcome_type"], df_matched["match_weight"],
                                  cluster=df_matched["subclass"])
    else:
        # Weighted analysis for IPTW/OW
        weighted_outcome_analysis(df, treatment_col, outcome_col,
                                   config["outcome_type"], weights)

    print(f"\n{'='*60}")
    print("Propensity score analysis complete.")


if __name__ == "__main__":
    main()
