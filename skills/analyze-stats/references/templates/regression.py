"""
Template: Regression Analysis (Logistic + Linear)
Performs logistic regression (binary outcome) or multiple linear regression (continuous outcome).
Generates OR/coefficient tables, model diagnostics, and publication-ready figures.

Usage:
    Modify the CONFIGURATION section below, then run:
        python regression.py

Input:  CSV with outcome and predictor variables
Output: coefficient/OR table CSV, diagnostic plots PDF/PNG, summary text
"""

# === REPRODUCIBILITY HEADER ===
import sys
import os
import datetime
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
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    print(f"statsmodels: {sm.__version__}")
except ImportError:
    print("Error: statsmodels not installed. Install with: pip install statsmodels")
    sys.exit(1)

try:
    from sklearn.metrics import roc_auc_score, brier_score_loss
    import sklearn
    print(f"sklearn: {sklearn.__version__}")
except ImportError:
    print("Warning: scikit-learn not installed. Some metrics unavailable.")

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

    # Regression type: "logistic" or "linear"
    "regression_type": "logistic",

    # Variables
    "outcome": "event",
    "predictors": ["age", "sex", "bmi", "smoking"],
    # Categorical predictors are entered as k-1 indicator (dummy) columns against a
    # reference level, whatever their dtype -- a nominal variable coded 1/2/3 is not
    # a linear term. List every categorical predictor here, numeric-coded or not.
    "categorical_vars": ["sex", "smoking"],
    # Reference level per categorical variable, e.g. {"smoking": "never"}.
    # Unlisted variables use their most frequent level; the choice is printed.
    "reference_levels": {},

    # Options
    # Crude (unadjusted) estimates for the table. They are descriptive only: do not
    # choose adjustment covariates by univariable P value (see regression.md).
    "run_univariable": True,
    "vif_threshold": 5.0,
    "epv_minimum": 10,
    # Bootstrap refits for the optimism-corrected C-statistic and calibration slope
    # (logistic only; Harrell/Steyerberg). Set to 0 to skip.
    "n_bootstrap_optimism": 200,
}


# === HELPER FUNCTIONS ===

def encode_predictors(df, predictors, categorical_vars, reference_levels):
    """Build the design matrix: continuous predictors as-is, categorical predictors
    as k-1 indicator columns against a stated reference level.

    Call this on complete cases only. Encoding before dropping missing rows is how
    a missing category turns into a numeric level (pandas codes NaN as -1).

    Returns (X without constant, {predictor: [design columns]}).
    """
    blocks, term_columns = [], {}
    for var in predictors:
        if var in categorical_vars:
            counts = df[var].value_counts()
            ref = reference_levels.get(var, counts.index[0])
            if ref not in counts.index:
                raise ValueError(f"Reference level {ref!r} for '{var}' not found; "
                                 f"levels are {list(counts.index)}")
            levels = [lv for lv in sorted(counts.index, key=str) if lv != ref]
            cols = {f"{var}: {lv} vs {ref}": (df[var] == lv).astype(float) for lv in levels}
            print(f"  {var}: reference = {ref!r}; levels {[str(lv) for lv in levels]}")
            blocks.append(pd.DataFrame(cols, index=df.index))
            term_columns[var] = list(cols)
        else:
            blocks.append(df[[var]].astype(float))
            term_columns[var] = [var]
    return pd.concat(blocks, axis=1), term_columns


def calculate_vif(X):
    """VIF for each column of X (no constant column in X).

    The constant is added here on purpose: variance_inflation_factor regresses each
    column on the other columns of the matrix it is given and does not add an
    intercept, so without one the VIF of any variable with a non-zero mean is
    inflated (two independent predictors, age and BMI, came out at ~19).
    """
    Xc = sm.add_constant(X, has_constant="add")
    vif_data = pd.DataFrame({
        "Variable": X.columns,
        "VIF": [variance_inflation_factor(Xc.values, i) for i in range(1, Xc.shape[1])],
    })
    return vif_data


def optimism_corrected_logistic(X, y, n_boot, seed=42):
    """Bootstrap optimism correction (Harrell 1996; Steyerberg 2001) for the
    C-statistic and the calibration slope of a logistic model.

    Each bootstrap sample refits the model; optimism = performance of the refit on
    its own bootstrap sample minus its performance on the original data.
    """
    rng = np.random.default_rng(seed)
    y = np.asarray(y); Xv = np.asarray(X, dtype=float); n = len(y)

    def slope(y_, lp_):
        return sm.GLM(y_, sm.add_constant(lp_), family=sm.families.Binomial()).fit().params[1]

    opt_c, opt_s = [], []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        yb = y[idx]
        if yb.min() == yb.max():
            continue
        try:
            fit = sm.Logit(yb, Xv[idx]).fit(disp=0)
        except Exception:
            continue
        lp_boot, lp_orig = Xv[idx] @ fit.params, Xv @ fit.params
        opt_c.append(roc_auc_score(yb, lp_boot) - roc_auc_score(y, lp_orig))
        opt_s.append(slope(yb, lp_boot) - slope(y, lp_orig))
    return float(np.mean(opt_c)), float(np.mean(opt_s)), len(opt_c)


def logistic_or_table(model, var_names):
    """Generate OR table from logistic regression results."""
    or_vals = np.exp(model.params)
    ci = np.exp(model.conf_int())
    table = pd.DataFrame({
        "Variable": var_names,
        "OR": or_vals,
        "CI_lower": ci[0],
        "CI_upper": ci[1],
        "P_value": model.pvalues
    })
    table["OR_CI"] = table.apply(
        lambda r: f"{r['OR']:.2f} ({r['CI_lower']:.2f}-{r['CI_upper']:.2f})", axis=1
    )
    return table


def linear_coef_table(model, var_names):
    """Generate coefficient table from linear regression results."""
    ci = model.conf_int()
    table = pd.DataFrame({
        "Variable": var_names,
        "Coefficient": model.params,
        "CI_lower": ci[0],
        "CI_upper": ci[1],
        "P_value": model.pvalues
    })
    table["Coef_CI"] = table.apply(
        lambda r: f"{r['Coefficient']:.3f} ({r['CI_lower']:.3f} to {r['CI_upper']:.3f})", axis=1
    )
    return table


def plot_diagnostic_4panel(model, outcome_name, output_dir):
    """Generate 4-panel diagnostic plot for linear regression."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    fitted = model.fittedvalues
    residuals = model.resid
    std_resid = model.get_influence().resid_studentized_internal
    leverage = model.get_influence().hat_matrix_diag
    cooks_d = model.get_influence().cooks_distance[0]

    # 1. Residuals vs Fitted
    axes[0, 0].scatter(fitted, residuals, alpha=0.5, s=20)
    axes[0, 0].axhline(y=0, color="red", linestyle="--")
    axes[0, 0].set_xlabel("Fitted values")
    axes[0, 0].set_ylabel("Residuals")
    axes[0, 0].set_title("Residuals vs Fitted")

    # 2. Q-Q plot
    stats.probplot(std_resid, plot=axes[0, 1])
    axes[0, 1].set_title("Normal Q-Q")

    # 3. Scale-Location
    axes[1, 0].scatter(fitted, np.sqrt(np.abs(std_resid)), alpha=0.5, s=20)
    axes[1, 0].set_xlabel("Fitted values")
    axes[1, 0].set_ylabel("√|Standardized residuals|")
    axes[1, 0].set_title("Scale-Location")

    # 4. Residuals vs Leverage
    axes[1, 1].scatter(leverage, std_resid, alpha=0.5, s=20)
    axes[1, 1].axhline(y=0, color="red", linestyle="--")
    # Cook's distance contours
    n = len(fitted)
    threshold = 4 / n
    high_cook = cooks_d > threshold
    if high_cook.any():
        axes[1, 1].scatter(leverage[high_cook], std_resid[high_cook],
                           color="red", s=40, zorder=5, label=f"Cook's D > {threshold:.3f}")
        axes[1, 1].legend()
    axes[1, 1].set_xlabel("Leverage")
    axes[1, 1].set_ylabel("Standardized residuals")
    axes[1, 1].set_title("Residuals vs Leverage")

    plt.suptitle(f"Diagnostic Plots: {outcome_name}", fontsize=14, y=1.02)
    plt.tight_layout()

    for ext in ["pdf", "png"]:
        fig.savefig(os.path.join(output_dir, f"diagnostic_plots.{ext}"),
                    dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: diagnostic_plots.pdf/.png")

    # Report influential observations
    n_influential = high_cook.sum()
    if n_influential > 0:
        print(f"\nWarning: {n_influential} observation(s) with Cook's D > {threshold:.3f}")


def plot_forest_or(or_table, output_dir, title="Multivariable Logistic Regression"):
    """Forest plot for odds ratios."""
    # Exclude intercept
    plot_data = or_table[or_table["Variable"] != "const"].copy()
    plot_data = plot_data.iloc[::-1]  # reverse for top-down display

    fig, ax = plt.subplots(figsize=(8, max(3, len(plot_data) * 0.6)))

    y_pos = range(len(plot_data))
    ax.errorbar(
        plot_data["OR"], y_pos,
        xerr=[plot_data["OR"] - plot_data["CI_lower"],
              plot_data["CI_upper"] - plot_data["OR"]],
        fmt="o", color="navy", capsize=4, markersize=6
    )
    ax.axvline(x=1, color="red", linestyle="--", alpha=0.7)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(plot_data["Variable"])
    ax.set_xlabel("Odds Ratio (95% CI)")
    ax.set_title(title)
    ax.set_xscale("log")

    plt.tight_layout()
    for ext in ["pdf", "png"]:
        fig.savefig(os.path.join(output_dir, f"forest_plot_or.{ext}"),
                    dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: forest_plot_or.pdf/.png")


# === MAIN ANALYSIS ===

def run_logistic(df, config):
    """Run logistic regression analysis."""
    outcome = config["outcome"]
    predictors = config["predictors"]
    output_dir = config["output_dir"]

    y = df[outcome]
    n_events = int(y.sum())
    n_total = len(y)
    X_raw, term_columns = encode_predictors(
        df, predictors, config.get("categorical_vars", []),
        config.get("reference_levels", {}))
    n_params = X_raw.shape[1]
    # EPV counts model parameters (each dummy column is one), and the limiting
    # outcome class
    epv = min(n_events, n_total - n_events) / n_params

    print(f"\n{'='*60}")
    print(f"LOGISTIC REGRESSION")
    print(f"{'='*60}")
    print(f"Outcome: {outcome}")
    print(f"N = {n_total}, Events = {n_events} ({100*n_events/n_total:.1f}%)")
    print(f"Predictors: {len(predictors)} ({n_params} model parameters)")
    print(f"EPV = {epv:.1f} per parameter (minimum recommended: {config['epv_minimum']})")
    if epv < config["epv_minimum"]:
        print(f"⚠ WARNING: EPV < {config['epv_minimum']}. Model may be unstable. "
              "Consider reducing predictors or using penalized regression.")
    print("  For a prediction model, justify N with the Riley et al. criteria "
          "(pmsampsize), not EPV alone.")

    # --- Univariable (crude) analysis: descriptive, not a selection step ---
    if config["run_univariable"]:
        print(f"\n--- Univariable (crude) Analysis ---")
        uni_results = []
        for var in predictors:
            cols = term_columns[var]
            X_uni = sm.add_constant(X_raw[cols])
            try:
                model_uni = sm.Logit(y, X_uni).fit(disp=0)
                for col in cols:
                    or_val = np.exp(model_uni.params[col])
                    ci = np.exp(model_uni.conf_int().loc[col])
                    uni_results.append({
                        "Variable": col,
                        "Uni_OR": or_val,
                        "Uni_CI_lower": ci[0],
                        "Uni_CI_upper": ci[1],
                        "Uni_P": model_uni.pvalues[col],
                        "Uni_OR_CI": f"{or_val:.2f} ({ci[0]:.2f}-{ci[1]:.2f})"
                    })
            except Exception as e:
                print(f"  {var}: failed ({e})")
                uni_results.extend({"Variable": col, "Uni_OR": np.nan} for col in cols)
        uni_df = pd.DataFrame(uni_results)
        print(uni_df[["Variable", "Uni_OR_CI", "Uni_P"]].to_string(index=False))

    # --- Multivariable analysis ---
    print(f"\n--- Multivariable Analysis ---")
    X = sm.add_constant(X_raw)
    model = sm.Logit(y, X).fit(disp=0)
    print(model.summary2())

    # OR table
    multi_table = logistic_or_table(model, list(model.params.index))

    # VIF (exclude intercept)
    vif_df = calculate_vif(X_raw)
    print(f"\n--- VIF ---")
    print(vif_df.to_string(index=False))
    high_vif = vif_df[vif_df["VIF"] > config["vif_threshold"]]
    if len(high_vif) > 0:
        print(f"⚠ NOTE: VIF > {config['vif_threshold']}: {', '.join(high_vif['Variable'])}. "
              "Inspect these; collinearity among adjustment covariates does not bias the "
              "exposure estimate, so do not drop a confounder on VIF alone. Dummy columns "
              "of one variable are collinear with each other by design (use GVIF).")

    # Discrimination and calibration. Everything computed on the data the model was
    # fitted to is APPARENT (optimistic); the bootstrap refit gives the corrected value.
    y_pred = model.predict(X)
    c_stat = roc_auc_score(y, y_pred)
    n_boot = 1000
    c_boots = []
    for i in range(n_boot):
        rng = np.random.RandomState(i)
        idx = rng.choice(len(y), len(y), replace=True)
        try:
            c_boots.append(roc_auc_score(y.iloc[idx], y_pred.iloc[idx]))
        except ValueError:
            continue
    c_ci = np.percentile(c_boots, [2.5, 97.5])
    print(f"\nApparent C-statistic (AUC) = {c_stat:.3f} (95% CI: {c_ci[0]:.3f}-{c_ci[1]:.3f}; "
          "development data, not optimism-corrected)")

    b_opt = config.get("n_bootstrap_optimism", 0)
    c_corr = slope_corr = None
    if b_opt:
        opt_c, opt_s, b_used = optimism_corrected_logistic(X, y, b_opt)
        c_corr = c_stat - opt_c
        slope_corr = 1.0 - opt_s  # apparent slope of an ML logistic fit is 1 by construction
        print(f"Optimism-corrected C-statistic = {c_corr:.3f} "
              f"(bootstrap, {b_used} refits; optimism {opt_c:.3f})")
        print(f"Optimism-corrected calibration slope = {slope_corr:.3f} "
              f"(apparent slope is 1.00 by construction)")
    print("Calibration: report the corrected slope, calibration-in-the-large and a "
          "flexible calibration curve (analysis_guides/calibration.md). "
          "Hosmer-Lemeshow is not reported (TRIPOD E&E; Van Calster 2016).")

    # Brier score
    brier = brier_score_loss(y, y_pred)
    print(f"Apparent Brier score = {brier:.4f}")

    # Merge univariable + multivariable
    if config["run_univariable"]:
        combined = uni_df.merge(multi_table[multi_table["Variable"] != "const"],
                                on="Variable", how="outer")
        combined.to_csv(os.path.join(output_dir, "logistic_regression_table.csv"), index=False)
    else:
        multi_table.to_csv(os.path.join(output_dir, "logistic_regression_table.csv"), index=False)

    # Forest plot
    plot_forest_or(multi_table, output_dir)

    # Results text: numbers only; the reader judges adequacy from them
    print(f"\n--- Manuscript Text ---")
    text = (f"The apparent C-statistic of the logistic regression model was {c_stat:.3f} "
            f"(95% CI, {c_ci[0]:.3f}-{c_ci[1]:.3f})")
    if c_corr is not None:
        text += (f"; after bootstrap optimism correction ({b_opt} resamples) the "
                 f"C-statistic was {c_corr:.3f} and the calibration slope {slope_corr:.3f}")
    print(text + ".")

    return model


def run_linear(df, config):
    """Run multiple linear regression analysis."""
    outcome = config["outcome"]
    predictors = config["predictors"]
    output_dir = config["output_dir"]

    y = df[outcome]
    n_total = len(y)

    print(f"\n{'='*60}")
    print(f"MULTIPLE LINEAR REGRESSION")
    print(f"{'='*60}")
    print(f"Outcome: {outcome}")
    print(f"N = {n_total}")
    print(f"Predictors: {len(predictors)}")
    print(f"N per predictor: {n_total / len(predictors):.0f} (recommended >= 10-20)")

    # --- Model fitting ---
    X_raw, _ = encode_predictors(df, predictors, config.get("categorical_vars", []),
                                 config.get("reference_levels", {}))
    X = sm.add_constant(X_raw)
    model = sm.OLS(y, X).fit()
    print(model.summary2())

    # Coefficient table
    coef_table = linear_coef_table(model, list(model.params.index))
    coef_table["R_squared"] = ""
    coef_table.loc[0, "R_squared"] = f"R²={model.rsquared:.3f}, Adj.R²={model.rsquared_adj:.3f}"
    coef_table.to_csv(os.path.join(output_dir, "linear_regression_table.csv"), index=False)
    print(f"\nR² = {model.rsquared:.3f}")
    print(f"Adjusted R² = {model.rsquared_adj:.3f}")

    # VIF
    vif_df = calculate_vif(X_raw)
    print(f"\n--- VIF ---")
    print(vif_df.to_string(index=False))
    high_vif = vif_df[vif_df["VIF"] > config["vif_threshold"]]
    if len(high_vif) > 0:
        print(f"⚠ NOTE: VIF > {config['vif_threshold']}: {', '.join(high_vif['Variable'])}. "
              "Inspect these; do not drop a confounder on VIF alone.")

    # Diagnostic plots
    plot_diagnostic_4panel(model, outcome, output_dir)

    # Residual normality is judged from the Normal Q-Q panel. A normality test is not
    # used to pick the model: it rejects trivially at large n and misses departures at
    # small n (the KS test with estimated mean/SD is also miscalibrated).
    print(f"\nResidual skewness = {stats.skew(model.resid):.2f} "
          "(inspect the Normal Q-Q panel in diagnostic_plots)")

    # Results text
    print(f"\n--- Manuscript Text ---")
    print(f"Multiple linear regression was performed with {outcome} as the dependent variable. "
          f"The model explained {model.rsquared_adj*100:.1f}% of the variance "
          f"(adjusted R² = {model.rsquared_adj:.2f}).")

    return model


# === ENTRY POINT ===

if __name__ == "__main__":
    # Load data
    df = pd.read_csv(CONFIG["data_path"])
    print(f"Data loaded: {df.shape[0]} rows x {df.shape[1]} columns")

    # Drop rows with missing values in analysis variables FIRST; categorical
    # predictors are dummy-coded afterwards, inside the model functions
    analysis_vars = [CONFIG["outcome"]] + CONFIG["predictors"]
    n_before = len(df)
    df_complete = df[analysis_vars].dropna()
    n_after = len(df_complete)
    if n_before != n_after:
        print(f"Missing data: {n_before - n_after} rows excluded "
              f"({100*(n_before-n_after)/n_before:.1f}%); complete-case analysis.")
        print("  Whether complete-case analysis is adequate depends on which variables "
              "are missing and why, not on the percentage. See "
              "analysis_guides/missing_data.md")

    # Run appropriate regression
    if CONFIG["regression_type"] == "logistic":
        model = run_logistic(df_complete, CONFIG)
    elif CONFIG["regression_type"] == "linear":
        model = run_linear(df_complete, CONFIG)
    else:
        print(f"Error: Unknown regression type '{CONFIG['regression_type']}'")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("Analysis complete.")
