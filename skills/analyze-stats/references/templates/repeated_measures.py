"""
Template: Repeated Measures / Mixed Models Analysis
Supports RM ANOVA, Linear Mixed Models (LMM), and GEE for longitudinal data.
Generates spaghetti plots, model summaries, and Time x Group interaction results.

Usage:
    Modify the CONFIGURATION section below, then run:
        python repeated_measures.py

Input:  CSV in wide or long format with repeated measurements
Output: model summary, spaghetti plot PDF/PNG, group mean trajectory plot
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
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    print(f"statsmodels: {sm.__version__}")
except ImportError:
    print("Error: statsmodels not installed. Install with: pip install statsmodels")
    sys.exit(1)

try:
    import pingouin as pg
    print(f"pingouin: {pg.__version__}")
except ImportError:
    print("Warning: pingouin not installed. RM ANOVA unavailable. Install: pip install pingouin")
    pg = None

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
    "data_format": "wide",  # "wide" or "long"

    # Variables (for wide format)
    "id_col": "subject_id",
    "group_col": "group",                # between-subject factor (optional, None if single group)
    "time_columns": ["t0", "t1", "t2", "t3"],  # column names for each time point
    "outcome_name": "score",             # name for the outcome in long format

    # Variables (for long format) -- used if data_format == "long"
    "time_col": "time",
    "outcome_col": "score",

    # Analysis method: "rm_anova", "lmm", "gee"
    "method": "lmm",

    # LMM options
    "random_effects": "intercept",  # "intercept" or "intercept_slope"

    # Covariates (optional, for LMM/GEE only)
    "covariates": [],
}


# === HELPER FUNCTIONS ===

def wide_to_long(df, id_col, group_col, time_columns, outcome_name):
    """Convert wide format to long format."""
    if group_col and group_col in df.columns:
        id_vars = [id_col, group_col]
    else:
        id_vars = [id_col]

    df_long = df.melt(
        id_vars=id_vars,
        value_vars=time_columns,
        var_name="time_label",
        value_name=outcome_name
    )

    # Create numeric time variable
    time_map = {col: i for i, col in enumerate(time_columns)}
    df_long["time"] = df_long["time_label"].map(time_map)

    return df_long


def plot_spaghetti(df_long, id_col, time_col, outcome_col, group_col, output_dir):
    """Generate spaghetti plot showing individual trajectories."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left: individual trajectories
    ax = axes[0]
    if group_col and group_col in df_long.columns:
        groups = df_long[group_col].unique()
        colors = plt.cm.tab10(np.linspace(0, 1, len(groups)))
        for grp, color in zip(groups, colors):
            grp_data = df_long[df_long[group_col] == grp]
            for subj_id in grp_data[id_col].unique():
                subj = grp_data[grp_data[id_col] == subj_id]
                ax.plot(subj[time_col], subj[outcome_col], alpha=0.2, color=color, linewidth=0.5)
            # Add group label
            ax.plot([], [], color=color, alpha=0.5, label=f"{grp}")
        ax.legend(title=group_col)
    else:
        for subj_id in df_long[id_col].unique():
            subj = df_long[df_long[id_col] == subj_id]
            ax.plot(subj[time_col], subj[outcome_col], alpha=0.15, color="steelblue", linewidth=0.5)

    ax.set_xlabel("Time")
    ax.set_ylabel(outcome_col)
    ax.set_title("Individual Trajectories")

    # Right: group means with error bars
    ax = axes[1]
    if group_col and group_col in df_long.columns:
        for grp, color in zip(groups, colors):
            grp_data = df_long[df_long[group_col] == grp]
            means = grp_data.groupby(time_col)[outcome_col].mean()
            sems = grp_data.groupby(time_col)[outcome_col].sem()
            ax.errorbar(means.index, means.values, yerr=1.96 * sems.values,
                        marker="o", capsize=4, label=f"{grp}", color=color)
        ax.legend(title=group_col)
    else:
        means = df_long.groupby(time_col)[outcome_col].mean()
        sems = df_long.groupby(time_col)[outcome_col].sem()
        ax.errorbar(means.index, means.values, yerr=1.96 * sems.values,
                    marker="o", capsize=4, color="steelblue")

    ax.set_xlabel("Time")
    ax.set_ylabel(f"{outcome_col} (mean ± 95% CI)")
    ax.set_title("Group Mean Trajectories")

    plt.tight_layout()
    for ext in ["pdf", "png"]:
        fig.savefig(os.path.join(output_dir, f"trajectories.{ext}"),
                    dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: trajectories.pdf/.png")


def run_rm_anova(df_long, id_col, time_col, outcome_col, group_col):
    """Run repeated measures ANOVA with Greenhouse-Geisser correction."""
    if pg is None:
        print("Error: pingouin package required for RM ANOVA. Install: pip install pingouin")
        return None

    print(f"\n{'='*60}")
    print("REPEATED MEASURES ANOVA")
    print(f"{'='*60}")

    # Missing data check
    n_subjects = df_long[id_col].nunique()
    n_timepoints = df_long[time_col].nunique()
    n_expected = n_subjects * n_timepoints
    n_actual = len(df_long.dropna(subset=[outcome_col]))
    n_missing = n_expected - n_actual
    if n_missing > 0:
        pct_missing = 100 * n_missing / n_expected
        print(f"⚠ Missing observations: {n_missing}/{n_expected} ({pct_missing:.1f}%)")
        if pct_missing > 5:
            print("⚠ > 5% missing. RM ANOVA uses complete cases only. Consider LMM instead.")
        # Drop incomplete subjects
        complete_subjects = df_long.groupby(id_col)[outcome_col].count()
        complete_ids = complete_subjects[complete_subjects == n_timepoints].index
        df_long = df_long[df_long[id_col].isin(complete_ids)]
        print(f"  Complete subjects: {len(complete_ids)}/{n_subjects}")

    if group_col and group_col in df_long.columns:
        # Mixed ANOVA (between + within)
        aov = pg.mixed_anova(
            data=df_long, dv=outcome_col, within=time_col,
            between=group_col, subject=id_col, correction=True
        )
    else:
        # One-way RM ANOVA
        aov = pg.rm_anova(
            data=df_long, dv=outcome_col, within=time_col,
            subject=id_col, correction=True
        )

    print(f"\nRM ANOVA Results:")
    print(aov.to_string())

    # Sphericity check (Mauchly's test) via pingouin
    spher = pg.sphericity(
        data=df_long, dv=outcome_col, within=time_col,
        subject=id_col
    )
    if isinstance(spher, tuple):
        spher_result, W, chi2, dof, pval = spher
    else:
        spher_result = spher
        pval = None

    print(f"\nMauchly's sphericity test: {'Passed' if spher_result else 'Violated'}")
    if pval is not None:
        print(f"  P = {pval:.3f}")
    if not spher_result:
        print("  → Greenhouse-Geisser correction applied (see eps column)")

    # Post-hoc pairwise comparisons
    if group_col and group_col in df_long.columns:
        print(f"\n--- Post-hoc: Time within each group ---")
        for grp in df_long[group_col].unique():
            grp_data = df_long[df_long[group_col] == grp]
            pw = pg.pairwise_tests(
                data=grp_data, dv=outcome_col, within=time_col,
                subject=id_col, padjust="bonf"
            )
            print(f"\nGroup: {grp}")
            print(pw[["Contrast", "A", "B", "T", "p-unc", "p-corr"]].to_string(index=False))

    return aov


def run_lmm(df_long, id_col, time_col, outcome_col, group_col, random_effects, covariates):
    """Run Linear Mixed Model."""
    print(f"\n{'='*60}")
    print("LINEAR MIXED MODEL")
    print(f"{'='*60}")

    # Build formula
    fixed_parts = [time_col]
    if group_col and group_col in df_long.columns:
        fixed_parts.append(group_col)
        fixed_parts.append(f"{time_col}:{group_col}")
    fixed_parts.extend(covariates)

    formula = f"{outcome_col} ~ " + " + ".join(fixed_parts)
    print(f"Formula: {formula}")

    # Random effects
    if random_effects == "intercept_slope":
        re_formula = f"~{time_col}"
        print(f"Random effects: intercept + slope")
    else:
        re_formula = "~1"
        print(f"Random effects: intercept only")

    # Fit model
    try:
        model = smf.mixedlm(formula, data=df_long, groups=df_long[id_col],
                             re_formula=re_formula)
        result = model.fit(reml=True)
        print(f"\n{result.summary()}")

        # Extract key results
        print(f"\n--- Fixed Effects ---")
        for name, coef in result.fe_params.items():
            ci = result.conf_int().loc[name]
            p = result.pvalues[name]
            print(f"  {name}: β = {coef:.3f} (95% CI: {ci[0]:.3f} to {ci[1]:.3f}), P = {p:.3f}")

        # Random effects variance
        print(f"\n--- Random Effects ---")
        print(f"  Group variance: {result.cov_re.iloc[0, 0]:.4f}")
        print(f"  Residual variance: {result.scale:.4f}")
        print(f"  ICC (approx): {result.cov_re.iloc[0, 0] / (result.cov_re.iloc[0, 0] + result.scale):.3f}")

        # Model fit
        print(f"\nAIC: {result.aic:.1f}")
        print(f"BIC: {result.bic:.1f}")
        print(f"Log-likelihood: {result.llf:.1f}")

        # Save results
        fe_table = pd.DataFrame({
            "Variable": result.fe_params.index,
            "Coefficient": result.fe_params.values,
            "CI_lower": result.conf_int()[0].values,
            "CI_upper": result.conf_int()[1].values,
            "P_value": result.pvalues.values
        })

        return result, fe_table

    except Exception as e:
        if random_effects == "intercept_slope":
            print(f"⚠ Model with random slope failed to converge: {e}")
            print("  Falling back to random intercept only...")
            return run_lmm(df_long, id_col, time_col, outcome_col,
                           group_col, "intercept", covariates)
        else:
            print(f"Error: LMM failed: {e}")
            return None, None


def run_gee(df_long, id_col, time_col, outcome_col, group_col, covariates):
    """Run Generalized Estimating Equations."""
    from statsmodels.genmod.generalized_estimating_equations import GEE
    from statsmodels.genmod.cov_struct import Exchangeable, Autoregressive

    print(f"\n{'='*60}")
    print("GEE (Generalized Estimating Equations)")
    print(f"{'='*60}")

    # Build formula
    fixed_parts = [time_col]
    if group_col and group_col in df_long.columns:
        fixed_parts.append(group_col)
        fixed_parts.append(f"{time_col}:{group_col}")
    fixed_parts.extend(covariates)

    formula = f"{outcome_col} ~ " + " + ".join(fixed_parts)
    print(f"Formula: {formula}")

    # Sort by id and time for proper correlation structure
    df_sorted = df_long.sort_values([id_col, time_col]).reset_index(drop=True)

    # Check cluster size
    n_clusters = df_sorted[id_col].nunique()
    print(f"Number of clusters (subjects): {n_clusters}")
    if n_clusters < 30:
        print("⚠ WARNING: GEE requires >= 30-40 clusters for reliable sandwich SE.")

    # Fit with exchangeable correlation
    try:
        model = GEE.from_formula(
            formula, groups=id_col, data=df_sorted,
            cov_struct=Exchangeable(), family=sm.families.Gaussian()
        )
        result = model.fit()
        print(f"\n{result.summary()}")

        print(f"\n--- Population-averaged Effects ---")
        for name in result.params.index:
            coef = result.params[name]
            ci = result.conf_int().loc[name]
            p = result.pvalues[name]
            print(f"  {name}: β = {coef:.3f} (95% CI: {ci[0]:.3f} to {ci[1]:.3f}), P = {p:.3f}")

        return result

    except Exception as e:
        print(f"Error: GEE failed: {e}")
        return None


# === MAIN ANALYSIS ===

def main():
    config = CONFIG
    output_dir = config["output_dir"]

    # Load data
    df = pd.read_csv(config["data_path"])
    print(f"Data loaded: {df.shape[0]} rows x {df.shape[1]} columns")

    id_col = config["id_col"]
    group_col = config.get("group_col")
    outcome_col = config.get("outcome_col", config.get("outcome_name", "score"))
    time_col = config.get("time_col", "time")

    # Convert to long format if needed
    if config["data_format"] == "wide":
        print("Converting wide → long format...")
        df_long = wide_to_long(
            df, id_col, group_col,
            config["time_columns"], config["outcome_name"]
        )
        outcome_col = config["outcome_name"]
        time_col = "time"
        print(f"Long format: {df_long.shape[0]} rows")
    else:
        df_long = df.copy()

    # Summary
    n_subjects = df_long[id_col].nunique()
    n_timepoints = df_long[time_col].nunique()
    print(f"\nSubjects: {n_subjects}")
    print(f"Time points: {n_timepoints}")
    if group_col and group_col in df_long.columns:
        print(f"Groups: {df_long[group_col].value_counts().to_dict()}")

    # Missing data report
    n_expected = n_subjects * n_timepoints
    n_observed = df_long[outcome_col].notna().sum()
    n_missing = n_expected - n_observed
    print(f"Observations: {n_observed}/{n_expected} ({100*n_missing/n_expected:.1f}% missing)")

    # Descriptive statistics per time point
    print(f"\n--- Descriptive Statistics by Time ---")
    desc = df_long.groupby(time_col)[outcome_col].agg(["count", "mean", "std"])
    print(desc.to_string())

    if group_col and group_col in df_long.columns:
        print(f"\n--- By Group and Time ---")
        desc_grp = df_long.groupby([group_col, time_col])[outcome_col].agg(["count", "mean", "std"])
        print(desc_grp.to_string())

    # Spaghetti plot
    plot_spaghetti(df_long, id_col, time_col, outcome_col, group_col, output_dir)

    # Run analysis
    method = config["method"]
    if method == "rm_anova":
        result = run_rm_anova(df_long, id_col, time_col, outcome_col, group_col)
    elif method == "lmm":
        result, fe_table = run_lmm(
            df_long, id_col, time_col, outcome_col, group_col,
            config["random_effects"], config.get("covariates", [])
        )
        if fe_table is not None:
            fe_table.to_csv(os.path.join(output_dir, "lmm_results.csv"), index=False)
            print(f"Saved: lmm_results.csv")
    elif method == "gee":
        result = run_gee(
            df_long, id_col, time_col, outcome_col, group_col,
            config.get("covariates", [])
        )
    else:
        print(f"Error: Unknown method '{method}'")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("Repeated measures analysis complete.")


if __name__ == "__main__":
    main()
