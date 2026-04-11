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
from scipy import stats

np.random.seed(42)
print(f"Date: {datetime.date.today()}")
print(f"Python: {sys.version}")
print(f"numpy: {np.__version__}, pandas: {pd.__version__}, scipy: {stats.scipy.__version__}")

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
    "categorical_vars": ["sex", "smoking"],

    # Options
    "run_univariable": True,  # Run univariable analysis before multivariable
    "vif_threshold": 5.0,
    "epv_minimum": 10,
}


# === HELPER FUNCTIONS ===

def calculate_vif(X):
    """Calculate VIF for each predictor."""
    vif_data = pd.DataFrame()
    vif_data["Variable"] = X.columns
    vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
    return vif_data


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


def hosmer_lemeshow_test(y_true, y_pred, n_groups=10):
    """Hosmer-Lemeshow goodness-of-fit test."""
    data = pd.DataFrame({"y": y_true, "p": y_pred})
    data["group"] = pd.qcut(data["p"], n_groups, duplicates="drop")
    grouped = data.groupby("group").agg(
        obs=("y", "sum"),
        exp=("p", "sum"),
        n=("y", "count"),
        mean_p=("p", "mean")
    )
    chi2 = ((grouped["obs"] - grouped["exp"]) ** 2 /
            (grouped["exp"] * (1 - grouped["mean_p"]))).sum()
    df = len(grouped) - 2
    p_value = 1 - stats.chi2.cdf(chi2, df)
    return chi2, df, p_value


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
    n_events = y.sum()
    n_total = len(y)
    epv = n_events / len(predictors)

    print(f"\n{'='*60}")
    print(f"LOGISTIC REGRESSION")
    print(f"{'='*60}")
    print(f"Outcome: {outcome}")
    print(f"N = {n_total}, Events = {n_events} ({100*n_events/n_total:.1f}%)")
    print(f"Predictors: {len(predictors)}")
    print(f"EPV = {epv:.1f} (minimum recommended: {config['epv_minimum']})")
    if epv < config["epv_minimum"]:
        print(f"⚠ WARNING: EPV < {config['epv_minimum']}. Model may be unstable. "
              "Consider reducing predictors or using penalized regression.")

    # --- Univariable analysis ---
    if config["run_univariable"]:
        print(f"\n--- Univariable Analysis ---")
        uni_results = []
        for var in predictors:
            X_uni = sm.add_constant(df[[var]])
            try:
                model_uni = sm.Logit(y, X_uni).fit(disp=0)
                or_val = np.exp(model_uni.params[var])
                ci = np.exp(model_uni.conf_int().loc[var])
                p_val = model_uni.pvalues[var]
                uni_results.append({
                    "Variable": var,
                    "Uni_OR": or_val,
                    "Uni_CI_lower": ci[0],
                    "Uni_CI_upper": ci[1],
                    "Uni_P": p_val,
                    "Uni_OR_CI": f"{or_val:.2f} ({ci[0]:.2f}-{ci[1]:.2f})"
                })
            except Exception as e:
                print(f"  {var}: failed ({e})")
                uni_results.append({"Variable": var, "Uni_OR": np.nan})
        uni_df = pd.DataFrame(uni_results)
        print(uni_df[["Variable", "Uni_OR_CI", "Uni_P"]].to_string(index=False))

    # --- Multivariable analysis ---
    print(f"\n--- Multivariable Analysis ---")
    X = sm.add_constant(df[predictors])
    model = sm.Logit(y, X).fit(disp=0)
    print(model.summary2())

    # OR table
    var_names = ["const"] + predictors
    multi_table = logistic_or_table(model, var_names)

    # VIF (exclude intercept)
    vif_df = calculate_vif(df[predictors])
    print(f"\n--- VIF ---")
    print(vif_df.to_string(index=False))
    high_vif = vif_df[vif_df["VIF"] > config["vif_threshold"]]
    if len(high_vif) > 0:
        print(f"⚠ WARNING: Variables with VIF > {config['vif_threshold']}: "
              f"{', '.join(high_vif['Variable'])}")

    # C-statistic
    y_pred = model.predict(X)
    c_stat = roc_auc_score(y, y_pred)
    # Bootstrap CI for C-statistic
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
    print(f"\nC-statistic (AUC) = {c_stat:.3f} (95% CI: {c_ci[0]:.3f}-{c_ci[1]:.3f})")

    # Hosmer-Lemeshow
    hl_chi2, hl_df, hl_p = hosmer_lemeshow_test(y, y_pred)
    print(f"Hosmer-Lemeshow: chi2 = {hl_chi2:.2f}, df = {hl_df}, P = {hl_p:.3f}")

    # Brier score
    brier = brier_score_loss(y, y_pred)
    print(f"Brier score = {brier:.4f}")

    # Merge univariable + multivariable
    if config["run_univariable"]:
        combined = uni_df.merge(multi_table[multi_table["Variable"] != "const"],
                                on="Variable", how="outer")
        combined.to_csv(os.path.join(output_dir, "logistic_regression_table.csv"), index=False)
    else:
        multi_table.to_csv(os.path.join(output_dir, "logistic_regression_table.csv"), index=False)

    # Forest plot
    plot_forest_or(multi_table, output_dir)

    # Results text
    print(f"\n--- Manuscript Text ---")
    print(f"The logistic regression model demonstrated a C-statistic of {c_stat:.3f} "
          f"(95% CI, {c_ci[0]:.3f}-{c_ci[1]:.3f}) and adequate calibration "
          f"(Hosmer-Lemeshow P = {hl_p:.2f}).")

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
    X = sm.add_constant(df[predictors])
    model = sm.OLS(y, X).fit()
    print(model.summary2())

    # Coefficient table
    var_names = ["const"] + predictors
    coef_table = linear_coef_table(model, var_names)
    coef_table["R_squared"] = ""
    coef_table.loc[0, "R_squared"] = f"R²={model.rsquared:.3f}, Adj.R²={model.rsquared_adj:.3f}"
    coef_table.to_csv(os.path.join(output_dir, "linear_regression_table.csv"), index=False)
    print(f"\nR² = {model.rsquared:.3f}")
    print(f"Adjusted R² = {model.rsquared_adj:.3f}")

    # VIF
    vif_df = calculate_vif(df[predictors])
    print(f"\n--- VIF ---")
    print(vif_df.to_string(index=False))
    high_vif = vif_df[vif_df["VIF"] > config["vif_threshold"]]
    if len(high_vif) > 0:
        print(f"⚠ WARNING: Variables with VIF > {config['vif_threshold']}: "
              f"{', '.join(high_vif['Variable'])}")

    # Diagnostic plots
    plot_diagnostic_4panel(model, outcome, output_dir)

    # Normality of residuals
    if n_total < 50:
        stat, p = stats.shapiro(model.resid)
        print(f"\nShapiro-Wilk test on residuals: W = {stat:.4f}, P = {p:.3f}")
    else:
        stat, p = stats.kstest(model.resid, "norm",
                               args=(model.resid.mean(), model.resid.std()))
        print(f"\nKolmogorov-Smirnov test on residuals: D = {stat:.4f}, P = {p:.3f}")

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

    # Encode categorical variables if needed
    for cat_var in CONFIG.get("categorical_vars", []):
        if cat_var in df.columns and df[cat_var].dtype == "object":
            df[cat_var] = pd.Categorical(df[cat_var]).codes

    # Drop rows with missing values in analysis variables
    analysis_vars = [CONFIG["outcome"]] + CONFIG["predictors"]
    n_before = len(df)
    df_complete = df[analysis_vars].dropna()
    n_after = len(df_complete)
    if n_before != n_after:
        print(f"Missing data: {n_before - n_after} rows excluded ({100*(n_before-n_after)/n_before:.1f}%)")
        if (n_before - n_after) / n_before > 0.05:
            print("⚠ Consider multiple imputation (> 5% missing). "
                  "See analysis_guides/missing_data.md")

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
