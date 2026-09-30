"""
Template: Survey-Weighted Analysis for National Health Surveys
Supports KNHANES, NHANES, KCHS and similar complex survey data.
Produces weighted descriptives, wOR tables, and subgroup analyses.

Variance is design-based: Taylor linearization (Binder 1983) with strata and
PSUs, the same estimator as R survey::svyglm, and CIs/P values use the design
degrees of freedom (#PSU - #strata - #parameters + 1), as confint(svyglm) does.
Subgroups and complete-case restrictions are DOMAIN analyses on the full design
(rows outside the domain contribute zero scores but keep their PSU), which is
what subset(design, ...) does in R -- the data frame is never row-filtered
before the variance is computed. The script also writes survey_analysis.R so
the numbers can be cross-checked in R.

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

    # Survey design variables (all three are used for the variance)
    "weight": "wt_itvex",       # Sampling weight column (the one matching the
                                # smallest subsample your variables come from)
    "strata": "kstrata",        # Stratification variable
    "cluster": "psu",           # PSU variable (nested within strata)
    "dataset_name": "KNHANES",  # "KNHANES", "NHANES", "KCHS"

    # Analysis variables
    "outcome": "diabetes",           # Binary outcome (0/1)
    "exposure": "depression",        # Primary exposure (binary or categorical)
    "covariates_model1": ["age", "sex"],
    "covariates_model2": ["age", "sex", "income", "education",
                          "smoking", "alcohol", "bmi"],
    # Entered as k-1 indicators whatever their dtype (a 1-4 income code is not linear)
    "categorical_vars": ["sex", "income", "education", "smoking"],
    "reference_levels": {},     # e.g. {"income": 1}; default = lowest level (printed)

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
                n_level = int(binary[mask].sum())   # unweighted count; % is weighted
                row[f"Group_{g}"] = f"{n_level} ({wp*100:.1f}%)"
            smd = weighted_smd(
                binary.values, df[group_col].values,
                df[weight_col].values, is_binary=True
            )
            row["SMD"] = f"{abs(smd):.3f}"
            results.append(row)

    return pd.DataFrame(results)


def encode(df, variables, categorical_vars, reference_levels):
    """Design matrix columns for `variables`; categorical ones as k-1 indicators."""
    blocks, columns = [], {}
    for var in variables:
        if var in categorical_vars:
            levels = sorted(df[var].dropna().unique(), key=lambda v: (str(type(v)), v))
            ref = reference_levels.get(var, levels[0])
            cols = {f"{var}={lv}": (df[var] == lv).astype(float) for lv in levels if lv != ref}
            blocks.append(pd.DataFrame(cols, index=df.index))
            columns[var] = list(cols)
        else:
            blocks.append(df[[var]].astype(float))
            columns[var] = [var]
    return pd.concat(blocks, axis=1), columns


def design_vcov(scores, strata, psu):
    """Linearization variance of a total: sum over strata of
    n_h/(n_h-1) * sum_i (z_hi - zbar_h)(z_hi - zbar_h)', z_hi = PSU score totals.
    `scores` covers EVERY row of the design (zeros outside the analysis domain)."""
    z = pd.DataFrame(scores)
    z["_h"], z["_c"] = strata, psu
    totals = z.groupby(["_h", "_c"], sort=False).sum()
    p = scores.shape[1]
    V = np.zeros((p, p))
    for h, g in totals.groupby(level="_h", sort=False):
        n_h = len(g)
        if n_h < 2:
            raise ValueError(f"Stratum {h!r} has a single PSU; collapse it with a "
                             "neighbouring stratum (or see survey.lonely.psu in R).")
        d = g.values - g.values.mean(axis=0)
        V += n_h / (n_h - 1) * d.T @ d
    return V


def svy_logistic(df, design, outcome_col, exposure_col, covariates, domain,
                 categorical_vars, reference_levels):
    """Design-based weighted logistic regression on a domain of the full design.

    df/design cover every row of the survey file; `domain` is a boolean mask
    (subgroup AND complete cases). Returns (table of exposure rows, design df).
    """
    X_all, columns = encode(df, [exposure_col] + covariates, categorical_vars,
                            reference_levels)
    X_all = sm.add_constant(X_all)
    dom = np.asarray(domain)
    X, y = X_all[dom].values, df.loc[dom, outcome_col].astype(float).values
    w = design["w"].values[dom]
    w = w / w.mean()   # scaling cancels in the variance; keeps the IRLS well-conditioned

    fit = sm.GLM(y, X, family=sm.families.Binomial(), var_weights=w).fit()
    mu = np.asarray(fit.mu)
    A_inv = np.linalg.inv(X.T @ (X * (w * mu * (1 - mu))[:, None]))
    scores = np.zeros((len(df), X.shape[1]))
    scores[dom] = (X * (w * (y - mu))[:, None]) @ A_inv
    V = design_vcov(scores, design["h"], design["c"])

    # design df as in survey::degf on the subgroup domain, minus the parameters
    in_group = np.asarray(design["group_domain"])
    degf = (design["c"][in_group].nunique() - design["h"][in_group].nunique())
    df_resid = degf + 1 - X.shape[1]
    tq = stats.t.ppf(0.975, df_resid)

    names = list(X_all.columns)
    rows = []
    for col in columns[exposure_col]:
        k = names.index(col)
        coef, se = fit.params[k], np.sqrt(V[k, k])
        p = 2 * stats.t.sf(abs(coef / se), df_resid)
        lo, hi = np.exp(coef - tq * se), np.exp(coef + tq * se)
        rows.append({
            "Variable": col,
            "wOR": np.exp(coef),
            "CI_lower": lo,
            "CI_upper": hi,
            "P": p,
            "design_df": df_resid,
            "n_unweighted": int(dom.sum()),
            "formatted": f"{np.exp(coef):.2f} ({lo:.2f}-{hi:.2f})",
        })
    return pd.DataFrame(rows)


def generate_r_code(config):
    """Generate publication-ready R code for the same analysis."""
    dataset = config["dataset_name"]
    weight = config["weight"]
    strata = config["strata"]
    cluster = config["cluster"]
    outcome = config["outcome"]
    exposure = config["exposure"]
    refs = config.get("reference_levels", {})

    def term(v):
        if v not in config["categorical_vars"]:
            return v
        if v in refs:
            return f'relevel(factor({v}), ref = "{refs[v]}")'
        return f"factor({v})"

    exposure_name = exposure
    exposure = term(exposure)
    covs_m1 = " + ".join(term(v) for v in config["covariates_model1"])
    covs_m2 = " + ".join(term(v) for v in config["covariates_model2"])
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
# Analysis domain = complete cases on every Model 2 variable, so both models use the
# same sample (a domain of the full design, not a row filter)
cc_vars <- c({', '.join(f'"{v}"' for v in [config['outcome'], config['exposure']] + config['covariates_model2'])})
design <- subset(design, complete.cases(df[, cc_vars]))

# Step 2: Weighted Table 1
tab1 <- svyCreateTableOne(
  vars = c({', '.join([f'"{v}"' for v in config['covariates_model2']])}),
  strata = "{exposure_name}",
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
for (level in sort(unique(na.omit(df${sg})))) {{
  sub_design <- subset(design, {sg} == level)
  sub_model <- svyglm(
    {outcome} ~ {exposure} + {' + '.join([term(v) for v in config['covariates_model2'] if v != sg])},
    design = sub_design,
    family = quasibinomial()
  )
  cat("\\n{sg} =", level, "\\n")
  est <- exp(cbind(wOR = coef(sub_model), confint(sub_model)))
  print(est[grepl("{exposure_name}", rownames(est)), , drop = FALSE])
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

    for col in (weight_col, config["strata"], config["cluster"]):
        if col not in df.columns:
            print(f"ERROR: design column '{col}' not found in data.")
            print(f"Available columns: {list(df.columns)}")
            sys.exit(1)

    # Rows without design information cannot be placed in the design at all
    design_ok = df[[weight_col, config["strata"], config["cluster"]]].notna().all(axis=1)
    if (~design_ok).any():
        print(f"Dropped {int((~design_ok).sum())} rows with missing weight/strata/PSU.")
    df = df[design_ok].reset_index(drop=True)

    outcome_col = config["outcome"]
    exposure_col = config["exposure"]
    cat_vars = config["categorical_vars"]   # list the exposure here if it is categorical
    refs = config.get("reference_levels", {})

    # PSU ids are nested within strata (nest=TRUE)
    design = {
        "w": df[weight_col].astype(float),
        "h": df[config["strata"]].astype(str),
        "c": df[config["strata"]].astype(str) + "|" + df[config["cluster"]].astype(str),
        "group_domain": pd.Series(True, index=df.index),
    }

    # Complete cases are a DOMAIN of the full design, not a row filter
    analysis_vars = [outcome_col, exposure_col] + config["covariates_model2"]
    complete = df[analysis_vars].notna().all(axis=1)
    print(f"Unweighted N (complete cases): {int(complete.sum()):,} of {len(df):,}")
    print(f"Weighted N (population estimate): {df.loc[complete, weight_col].sum():,.0f}")
    print(f"Design: {design['h'].nunique()} strata, {design['c'].nunique()} PSUs, "
          f"design df = {design['c'].nunique() - design['h'].nunique()}")

    print(f"\n{'='*60}")
    print(f"SURVEY-WEIGHTED ANALYSIS (design-based, Taylor linearization)")
    print(f"{'='*60}")

    # --- Weighted Table 1 (point estimates; unweighted n, weighted %) ---
    print(f"\n--- Weighted Table 1 ---")
    continuous_vars = [v for v in config["covariates_model2"]
                       if v not in config["categorical_vars"]]
    categorical_vars = [v for v in config["covariates_model2"]
                        if v in config["categorical_vars"]]

    tab1 = weighted_table1(
        df[complete], exposure_col, continuous_vars, categorical_vars, weight_col
    )
    print(tab1.to_string(index=False))
    tab1.to_csv(os.path.join(output_dir, "weighted_table1.csv"), index=False)
    print("Saved: weighted_table1.csv")

    fmt_p = lambda x: f"{x:.3f}" if x >= 0.001 else "<0.001"

    # --- Model 1: Minimal adjustment ---
    print(f"\n--- Model 1: Adjusted for {', '.join(config['covariates_model1'])} ---")
    wor1 = svy_logistic(df, design, outcome_col, exposure_col,
                        config["covariates_model1"], complete, cat_vars, refs)
    print(wor1[["Variable", "formatted", "P", "design_df"]].to_string(index=False))

    # --- Model 2: Full adjustment ---
    print(f"\n--- Model 2: Adjusted for {', '.join(config['covariates_model2'])} ---")
    wor2 = svy_logistic(df, design, outcome_col, exposure_col,
                        config["covariates_model2"], complete, cat_vars, refs)
    print(wor2[["Variable", "formatted", "P", "design_df"]].to_string(index=False))

    # Combine wOR results
    wor_combined = pd.DataFrame({
        "Exposure": wor1["Variable"],
        "Model1_wOR": wor1["formatted"],
        "Model1_P": wor1["P"].map(fmt_p),
        "Model2_wOR": wor2["formatted"],
        "Model2_P": wor2["P"].map(fmt_p),
        "n_unweighted": wor2["n_unweighted"],
        "design_df": wor2["design_df"],
    })
    wor_combined.to_csv(os.path.join(output_dir, "wor_results.csv"), index=False)
    print("\nSaved: wor_results.csv")

    # --- Subgroup analyses: domains of the full design ---
    print(f"\n--- Subgroup Analyses (domain estimation) ---")
    subgroup_results = []

    for sg_var in config["subgroup_vars"]:
        if sg_var not in df.columns:
            print(f"  Skipping {sg_var} (not in data)")
            continue

        covs_no_sg = [v for v in config["covariates_model2"] if v != sg_var]
        for level in sorted(df[sg_var].dropna().unique()):
            in_group = df[sg_var] == level
            domain = complete & in_group
            if domain.sum() < 30:
                continue
            sg_design = dict(design, group_domain=in_group)
            try:
                wor_sg = svy_logistic(df, sg_design, outcome_col, exposure_col,
                                      covs_no_sg, domain, cat_vars, refs)
                for _, row in wor_sg.iterrows():
                    subgroup_results.append({
                        "Subgroup": sg_var,
                        "Level": level,
                        "Exposure": row["Variable"],
                        "n_unweighted": row["n_unweighted"],
                        "wOR": row["formatted"],
                        "P": fmt_p(row["P"]),
                        "design_df": row["design_df"],
                    })
            except Exception as e:
                print(f"  {sg_var}={level}: analysis failed ({e})")

    if subgroup_results:
        sg_df = pd.DataFrame(subgroup_results)
        print(sg_df.to_string(index=False))
        sg_df.to_csv(os.path.join(output_dir, "subgroup_results.csv"), index=False)
        print("Saved: subgroup_results.csv")
        print("  A difference between subgroups needs an interaction test on the full "
              "design, not a comparison of subgroup P values.")

    # --- Generate R code ---
    print(f"\n--- R Code (for publication-quality analysis) ---")
    r_code = generate_r_code(config)
    r_path = os.path.join(output_dir, "survey_analysis.R")
    with open(r_path, "w") as f:
        f.write(r_code)
    print(f"Saved: {r_path}  (cross-check: it reproduces the estimates above)")

    # --- Summary ---
    print(f"\n{'='*60}")
    print("Survey-weighted analysis complete.")
    print(f"  Table 1: weighted_table1.csv")
    print(f"  wOR results: wor_results.csv")
    if subgroup_results:
        print(f"  Subgroup results: subgroup_results.csv")
    print(f"  R code: survey_analysis.R")


if __name__ == "__main__":
    main()
