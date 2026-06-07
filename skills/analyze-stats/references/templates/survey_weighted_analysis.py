"""
Template: Survey-Weighted Analysis for National Health Surveys
Supports KNHANES, NHANES, KCHS and similar complex survey data.
Produces weighted descriptives, wOR tables, and subgroup analyses.

NOTE: For publication-quality survey analysis, R (survey package) is strongly
recommended. This Python template handles basic weighted analysis but cannot
fully account for strata/cluster in variance estimation. Use the companion
R code blocks in analysis_guides/survey_weighted.md for complex designs.

Usage:
    Modify the CONFIGURATION section below, then run:
        python survey_weighted_analysis.py

Input:  CSV with survey design variables (weight, strata, cluster) + analysis variables
Output: Weighted Table 1, wOR table, subgroup results
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

    # Survey design variables
    "weight": "wt_itvex",       # Sampling weight column
    "strata": "kstrata",        # Stratification variable (for R code generation)
    "cluster": "psu",           # Cluster/PSU variable (for R code generation)
    "dataset_name": "KNHANES",  # "KNHANES", "NHANES", "KCHS"

    # Analysis variables
    "outcome": "diabetes",           # Binary outcome (0/1)
    "exposure": "depression",        # Primary exposure (binary or categorical)
    "covariates_model1": ["age", "sex"],
    "covariates_model2": ["age", "sex", "income", "education",
                          "smoking", "alcohol", "bmi"],
    "categorical_vars": ["sex", "income", "education", "smoking"],

    # Subgroup stratification variables
    "subgroup_vars": ["sex", "age_group", "income", "obesity"],

    # Output
    "effect_measure": "wOR",  # "wOR" for logistic, "beta" for linear
}


# === HELPER FUNCTIONS ===

def weighted_mean(x, w):
    """Calculate weighted mean."""
    return np.average(x, weights=w)


def weighted_std(x, w):
    """Calculate weighted standard deviation."""
    wm = weighted_mean(x, w)
    return np.sqrt(np.average((x - wm) ** 2, weights=w))


def weighted_proportion(x, w, level=1):
    """Calculate weighted proportion for a binary/categorical variable."""
    mask = x == level
    return np.average(mask, weights=w)


def weighted_smd(x, treatment, weights, is_binary=False):
    """Calculate weighted standardized mean difference."""
    t_mask = treatment == 1
    c_mask = treatment == 0

    w1, w0 = weights[t_mask], weights[c_mask]
    x1, x0 = x[t_mask], x[c_mask]

    wm1 = np.average(x1, weights=w1)
    wm0 = np.average(x0, weights=w0)

    if is_binary:
        denom = np.sqrt((wm1 * (1 - wm1) + wm0 * (1 - wm0)) / 2)
    else:
        wv1 = np.average((x1 - wm1) ** 2, weights=w1)
        wv0 = np.average((x0 - wm0) ** 2, weights=w0)
        denom = np.sqrt((wv1 + wv0) / 2)

    return (wm1 - wm0) / denom if denom > 0 else 0.0


def weighted_table1(df, group_col, continuous_vars, categorical_vars, weight_col):
    """Generate weighted Table 1 with group comparison."""
    groups = sorted(df[group_col].unique())
    results = []

    for var in continuous_vars:
        row = {"Variable": var, "Type": "continuous"}
        for g in groups:
            mask = df[group_col] == g
            wm = weighted_mean(df.loc[mask, var].values, df.loc[mask, weight_col].values)
            ws = weighted_std(df.loc[mask, var].values, df.loc[mask, weight_col].values)
            row[f"Group_{g}"] = f"{wm:.1f} ({ws:.1f})"
        # Weighted SMD
        smd = weighted_smd(
            df[var].values, df[group_col].values,
            df[weight_col].values, is_binary=False
        )
        row["SMD"] = f"{abs(smd):.3f}"
        results.append(row)

    for var in categorical_vars:
        levels = sorted(df[var].unique())
        for level in levels:
            row = {"Variable": f"  {var} = {level}", "Type": "categorical"}
            binary = (df[var] == level).astype(int)
            for g in groups:
                mask = df[group_col] == g
                wp = weighted_proportion(binary[mask].values, df.loc[mask, weight_col].values)
                n = mask.sum()
                row[f"Group_{g}"] = f"{int(n * wp)} ({wp*100:.1f}%)"
            smd = weighted_smd(
                binary.values, df[group_col].values,
                df[weight_col].values, is_binary=True
            )
            row["SMD"] = f"{abs(smd):.3f}"
            results.append(row)

    return pd.DataFrame(results)


def weighted_logistic(df, outcome_col, exposure_col, covariates, weight_col):
    """Run weighted logistic regression and return wOR with 95% CI.

    NOTE: This uses frequency weights which approximate survey weights for
    point estimates but do NOT correctly estimate variance for complex designs.
    For publication, generate and run the R code from survey_weighted.md.
    """
    formula_vars = [exposure_col] + covariates
    X = pd.get_dummies(df[formula_vars], drop_first=True, dtype=float)
    X = sm.add_constant(X)
    y = df[outcome_col]
    w = df[weight_col]

    model = sm.GLM(y, X, family=sm.families.Binomial(), freq_weights=w)
    result = model.fit()

    # Extract exposure effect
    # Find the exposure column(s) in the dummy-encoded X
    exp_cols = [c for c in X.columns if c.startswith(exposure_col)]
    if not exp_cols:
        exp_cols = [exposure_col]

    output_rows = []
    for col in exp_cols:
        coef = result.params[col]
        se = result.bse[col]
        p = result.pvalues[col]
        wor = np.exp(coef)
        ci_lo = np.exp(coef - 1.96 * se)
        ci_hi = np.exp(coef + 1.96 * se)
        output_rows.append({
            "Variable": col,
            "wOR": wor,
            "CI_lower": ci_lo,
            "CI_upper": ci_hi,
            "P": p,
            "formatted": f"{wor:.2f} ({ci_lo:.2f}-{ci_hi:.2f})",
        })

    return result, pd.DataFrame(output_rows)


def generate_r_code(config):
    """Generate publication-ready R code for the same analysis."""
    dataset = config["dataset_name"]
    weight = config["weight"]
    strata = config["strata"]
    cluster = config["cluster"]
    outcome = config["outcome"]
    exposure = config["exposure"]
    covs_m1 = " + ".join(config["covariates_model1"])
    covs_m2 = " + ".join(config["covariates_model2"])
    subgroups = config["subgroup_vars"]

    r_code = f"""# === R Code: Survey-Weighted Analysis ({dataset}) ===
# Requires: survey, tableone
# install.packages(c("survey", "tableone"))

library(survey)
library(tableone)

df <- read.csv("{config['data_path']}")

# Step 1: Declare survey design
design <- svydesign(
  id = ~{cluster},
  strata = ~{strata},
  weights = ~{weight},
  data = df,
  nest = TRUE
)

# Step 2: Weighted Table 1
tab1 <- svyCreateTableOne(
  vars = c({', '.join([f'"{v}"' for v in config['covariates_model2']])}),
  strata = "{exposure}",
  data = design,
  test = TRUE,
  smd = TRUE
)
print(tab1, smd = TRUE)

# Step 3: Model 1 (age + sex)
model1 <- svyglm(
  {outcome} ~ {exposure} + {covs_m1},
  design = design,
  family = quasibinomial()
)
exp(cbind(wOR = coef(model1), confint(model1)))

# Step 4: Model 2 (full adjustment)
model2 <- svyglm(
  {outcome} ~ {exposure} + {covs_m2},
  design = design,
  family = quasibinomial()
)
exp(cbind(wOR = coef(model2), confint(model2)))

# Step 5: Subgroup analyses
"""
    for sg in subgroups:
        r_code += f"""
# Subgroup: {sg}
for (level in unique(df${sg})) {{
  sub_design <- subset(design, {sg} == level)
  sub_model <- svyglm(
    {outcome} ~ {exposure} + {' + '.join([v for v in config['covariates_model2'] if v != sg])},
    design = sub_design,
    family = quasibinomial()
  )
  cat("\\n{sg} =", level, "\\n")
  print(exp(cbind(wOR = coef(sub_model), confint(sub_model)))["{exposure}", ])
}}
"""
    return r_code


# === MAIN ANALYSIS ===

def main():
    config = CONFIG
    df = pd.read_csv(config["data_path"])
    output_dir = config["output_dir"]
    weight_col = config["weight"]

    print(f"Data loaded: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"Dataset: {config['dataset_name']}")
    print(f"Weight column: {weight_col}")

    # Check weight column exists
    if weight_col not in df.columns:
        print(f"ERROR: Weight column '{weight_col}' not found in data.")
        print(f"Available columns: {list(df.columns)}")
        sys.exit(1)

    # Drop missing
    analysis_vars = ([config["outcome"], config["exposure"], weight_col] +
                     config["covariates_model2"])
    n_before = len(df)
    df = df.dropna(subset=[v for v in analysis_vars if v in df.columns])
    n_after = len(df)
    if n_before != n_after:
        print(f"Excluded {n_before - n_after} rows with missing data "
              f"({100*(n_before-n_after)/n_before:.1f}%)")

    outcome_col = config["outcome"]
    exposure_col = config["exposure"]

    # Weighted sample size
    total_weight = df[weight_col].sum()
    print(f"Unweighted N: {len(df):,}")
    print(f"Weighted N: {total_weight:,.0f}")

    print(f"\n{'='*60}")
    print(f"SURVEY-WEIGHTED ANALYSIS")
    print(f"{'='*60}")

    # --- Weighted Table 1 ---
    print(f"\n--- Weighted Table 1 ---")
    continuous_vars = [v for v in config["covariates_model2"]
                       if v not in config["categorical_vars"]]
    categorical_vars = [v for v in config["covariates_model2"]
                        if v in config["categorical_vars"]]

    tab1 = weighted_table1(
        df, exposure_col, continuous_vars, categorical_vars, weight_col
    )
    print(tab1.to_string(index=False))
    tab1.to_csv(os.path.join(output_dir, "weighted_table1.csv"), index=False)
    print("Saved: weighted_table1.csv")

    # --- Model 1: Minimal adjustment ---
    print(f"\n--- Model 1: Adjusted for {', '.join(config['covariates_model1'])} ---")
    result1, wor1 = weighted_logistic(
        df, outcome_col, exposure_col,
        config["covariates_model1"], weight_col
    )
    print(wor1[["Variable", "formatted", "P"]].to_string(index=False))

    # --- Model 2: Full adjustment ---
    print(f"\n--- Model 2: Adjusted for {', '.join(config['covariates_model2'])} ---")
    result2, wor2 = weighted_logistic(
        df, outcome_col, exposure_col,
        config["covariates_model2"], weight_col
    )
    print(wor2[["Variable", "formatted", "P"]].to_string(index=False))

    # Combine wOR results
    wor_combined = pd.DataFrame({
        "Exposure": wor1["Variable"],
        "Model1_wOR": wor1["formatted"],
        "Model1_P": wor1["P"].map(lambda x: f"{x:.3f}" if x >= 0.001 else "<0.001"),
        "Model2_wOR": wor2["formatted"],
        "Model2_P": wor2["P"].map(lambda x: f"{x:.3f}" if x >= 0.001 else "<0.001"),
    })
    wor_combined.to_csv(os.path.join(output_dir, "wor_results.csv"), index=False)
    print("\nSaved: wor_results.csv")

    # --- Subgroup Analyses ---
    print(f"\n--- Subgroup Analyses ---")
    subgroup_results = []

    for sg_var in config["subgroup_vars"]:
        if sg_var not in df.columns:
            print(f"  Skipping {sg_var} (not in data)")
            continue

        covs_no_sg = [v for v in config["covariates_model2"] if v != sg_var]
        for level in sorted(df[sg_var].unique()):
            subset = df[df[sg_var] == level]
            if len(subset) < 30:
                continue
            try:
                _, wor_sg = weighted_logistic(
                    subset, outcome_col, exposure_col,
                    covs_no_sg, weight_col
                )
                for _, row in wor_sg.iterrows():
                    subgroup_results.append({
                        "Subgroup": sg_var,
                        "Level": level,
                        "wOR": row["formatted"],
                        "P": f"{row['P']:.3f}" if row["P"] >= 0.001 else "<0.001",
                    })
            except Exception as e:
                print(f"  {sg_var}={level}: analysis failed ({e})")

    if subgroup_results:
        sg_df = pd.DataFrame(subgroup_results)
        print(sg_df.to_string(index=False))
        sg_df.to_csv(os.path.join(output_dir, "subgroup_results.csv"), index=False)
        print("Saved: subgroup_results.csv")

    # --- Generate R code ---
    print(f"\n--- R Code (for publication-quality analysis) ---")
    r_code = generate_r_code(config)
    r_path = os.path.join(output_dir, "survey_analysis.R")
    with open(r_path, "w") as f:
        f.write(r_code)
    print(f"Saved: {r_path}")
    print("NOTE: Run the R code for correct variance estimation with strata/cluster.")

    # --- Summary ---
    print(f"\n{'='*60}")
    print("Survey-weighted analysis complete.")
    print(f"  Table 1: weighted_table1.csv")
    print(f"  wOR results: wor_results.csv")
    if subgroup_results:
        print(f"  Subgroup results: subgroup_results.csv")
    print(f"  R code: survey_analysis.R")
    print(f"\n⚠ Python results use frequency weights only.")
    print(f"  For publication, run survey_analysis.R with full design specification.")


if __name__ == "__main__":
    main()
