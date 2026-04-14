"""
MedSci Skills Demo 3: NHANES Obesity & Diabetes
E2E Pipeline Step 1 — analyze-stats

Research question: Association between obesity (BMI) and diabetes (HbA1c >= 6.5%)
in US adults using NHANES 2017-2018, accounting for survey weights.

Pipeline: Table 1 -> weighted prevalence -> logistic regression ->
          subgroup analysis -> figures

Usage: python3 analyze.py
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
print(f"Python: {sys.version.split()[0]}")
import scipy
print(f"numpy: {np.__version__}, pandas: {pd.__version__}, scipy: {scipy.__version__}")

import statsmodels.api as sm
from statsmodels.stats.proportion import proportion_confint
import statsmodels
print(f"statsmodels: {statsmodels.__version__}")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

print()

# === LOAD DATA ===
df = pd.read_csv("data/nhanes_2017_2018.csv")
print(f"Loaded: {df.shape[0]} participants, {df.shape[1]} columns")

# ============================================================
# PART A: TABLE 1 — BASELINE DEMOGRAPHICS
# ============================================================
print("\n" + "=" * 60)
print("PART A: Table 1 — Baseline Characteristics by BMI Category")
print("=" * 60)

GROUP_COL = "bmi_category"
groups = ["Normal", "Overweight", "Obese"]
df_main = df[df["bmi_category"].isin(groups)].copy()
print(f"Analysis sample (excluding underweight): {len(df_main)}")

group_dfs = {g: df_main[df_main[GROUP_COL] == g] for g in groups}


def format_p(p):
    if pd.isna(p):
        return ""
    if p < 0.001:
        return "<0.001"
    return f"{p:.3f}"


def wilson_ci(count, nobs, alpha=0.05):
    lo, hi = proportion_confint(count, nobs, alpha=alpha, method="wilson")
    return lo, hi


rows = []

# N row
n_row = {"Variable": "n"}
for g in groups:
    n_row[g] = str(len(group_dfs[g]))
n_row["Overall"] = str(len(df_main))
n_row["p-value"] = ""
rows.append(n_row)

# Age
row = {"Variable": "Age (years), mean +/- SD"}
row["Overall"] = f"{df_main['age'].mean():.1f} +/- {df_main['age'].std():.1f}"
for g in groups:
    gdf = group_dfs[g]
    row[g] = f"{gdf['age'].mean():.1f} +/- {gdf['age'].std():.1f}"
_, p = stats.f_oneway(*[group_dfs[g]["age"].dropna() for g in groups])
row["p-value"] = format_p(p)
rows.append(row)

# Gender
row = {"Variable": "Female, n (%)"}
row["Overall"] = f"{(df_main['gender']=='Female').sum()} ({100*(df_main['gender']=='Female').mean():.1f}%)"
for g in groups:
    gdf = group_dfs[g]
    n_f = (gdf["gender"] == "Female").sum()
    row[g] = f"{n_f} ({100*n_f/len(gdf):.1f}%)"
contingency = pd.crosstab(df_main["gender"], df_main[GROUP_COL])
_, p, _, _ = stats.chi2_contingency(contingency)
row["p-value"] = format_p(p)
rows.append(row)

# Race/ethnicity
row = {"Variable": "Race/ethnicity, n (%)"}
row["Overall"] = ""
for g in groups:
    row[g] = ""
contingency = pd.crosstab(df_main["race_ethnicity"], df_main[GROUP_COL])
_, p, _, _ = stats.chi2_contingency(contingency)
row["p-value"] = format_p(p)
rows.append(row)
for race in ["Non-Hispanic White", "Non-Hispanic Black", "Non-Hispanic Asian",
             "Mexican American", "Other Hispanic", "Other/Multi-Racial"]:
    cat_row = {"Variable": f"  {race}"}
    mask = df_main["race_ethnicity"] == race
    cat_row["Overall"] = f"{mask.sum()} ({100*mask.mean():.1f}%)"
    for g in groups:
        gdf = group_dfs[g]
        n_cat = (gdf["race_ethnicity"] == race).sum()
        cat_row[g] = f"{n_cat} ({100*n_cat/len(gdf):.1f}%)"
    cat_row["p-value"] = ""
    rows.append(cat_row)

# BMI
row = {"Variable": "BMI (kg/m2), mean +/- SD"}
row["Overall"] = f"{df_main['bmi'].mean():.1f} +/- {df_main['bmi'].std():.1f}"
for g in groups:
    gdf = group_dfs[g]
    row[g] = f"{gdf['bmi'].mean():.1f} +/- {gdf['bmi'].std():.1f}"
_, p = stats.f_oneway(*[group_dfs[g]["bmi"].dropna() for g in groups])
row["p-value"] = format_p(p)
rows.append(row)

# HbA1c
row = {"Variable": "HbA1c (%), mean +/- SD"}
row["Overall"] = f"{df_main['hba1c'].mean():.2f} +/- {df_main['hba1c'].std():.2f}"
for g in groups:
    gdf = group_dfs[g]
    row[g] = f"{gdf['hba1c'].mean():.2f} +/- {gdf['hba1c'].std():.2f}"
_, p = stats.f_oneway(*[group_dfs[g]["hba1c"].dropna() for g in groups])
row["p-value"] = format_p(p)
rows.append(row)

# Diabetes prevalence
row = {"Variable": "Diabetes (HbA1c >= 6.5%), n (%)"}
row["Overall"] = f"{df_main['diabetes'].sum()} ({100*df_main['diabetes'].mean():.1f}%)"
for g in groups:
    gdf = group_dfs[g]
    row[g] = f"{gdf['diabetes'].sum()} ({100*gdf['diabetes'].mean():.1f}%)"
contingency = pd.crosstab(df_main["diabetes"], df_main[GROUP_COL])
_, p, _, _ = stats.chi2_contingency(contingency)
row["p-value"] = format_p(p)
rows.append(row)

# Glycemic status
row = {"Variable": "Glycemic status, n (%)"}
row["Overall"] = ""
for g in groups:
    row[g] = ""
contingency = pd.crosstab(df_main["glycemic_status"], df_main[GROUP_COL])
_, p, _, _ = stats.chi2_contingency(contingency)
row["p-value"] = format_p(p)
rows.append(row)
for status in ["Normal", "Prediabetes", "Diabetes"]:
    cat_row = {"Variable": f"  {status}"}
    mask = df_main["glycemic_status"] == status
    cat_row["Overall"] = f"{mask.sum()} ({100*mask.mean():.1f}%)"
    for g in groups:
        gdf = group_dfs[g]
        n_cat = (gdf["glycemic_status"] == status).sum()
        cat_row[g] = f"{n_cat} ({100*n_cat/len(gdf):.1f}%)"
    cat_row["p-value"] = ""
    rows.append(cat_row)

table1 = pd.DataFrame(rows)
col_order = ["Variable"] + groups + ["Overall", "p-value"]
table1 = table1[col_order]
table1.to_csv("tables/table1.csv", index=False)

print("\n--- Table 1 ---\n")
print(table1.to_markdown(index=False))
print(f"\nSaved: tables/table1.csv")

# ============================================================
# PART B: WEIGHTED PREVALENCE ESTIMATES
# ============================================================
print("\n" + "=" * 60)
print("PART B: Survey-Weighted Diabetes Prevalence by BMI Category")
print("=" * 60)

prev_rows = []
for g in groups:
    gdf = group_dfs[g]
    w = gdf["survey_weight"]
    weighted_prev = np.average(gdf["diabetes"], weights=w)
    unweighted_prev = gdf["diabetes"].mean()
    n_diabetes = gdf["diabetes"].sum()
    n_total = len(gdf)
    lo, hi = wilson_ci(n_diabetes, n_total)
    prev_rows.append({
        "BMI Category": g, "n": n_total, "n diabetes": n_diabetes,
        "Prevalence (%)": f"{100*unweighted_prev:.1f}",
        "95% CI lower": f"{100*lo:.1f}", "95% CI upper": f"{100*hi:.1f}",
        "Weighted prevalence (%)": f"{100*weighted_prev:.1f}",
    })

w_all = df_main["survey_weight"]
weighted_overall = np.average(df_main["diabetes"], weights=w_all)
lo, hi = wilson_ci(df_main["diabetes"].sum(), len(df_main))
prev_rows.append({
    "BMI Category": "Overall", "n": len(df_main),
    "n diabetes": df_main["diabetes"].sum(),
    "Prevalence (%)": f"{100*df_main['diabetes'].mean():.1f}",
    "95% CI lower": f"{100*lo:.1f}", "95% CI upper": f"{100*hi:.1f}",
    "Weighted prevalence (%)": f"{100*weighted_overall:.1f}",
})

prev_df = pd.DataFrame(prev_rows)
prev_df.to_csv("tables/prevalence_by_bmi.csv", index=False)
print("\n")
print(prev_df.to_markdown(index=False))
print(f"\nSaved: tables/prevalence_by_bmi.csv")

# ============================================================
# PART C: LOGISTIC REGRESSION
# ============================================================
print("\n" + "=" * 60)
print("PART C: Weighted Logistic Regression")
print("=" * 60)

reg_df = df_main.dropna(subset=["bmi", "age", "gender", "race_ethnicity",
                                 "education", "survey_weight", "diabetes"]).copy()

reg_df["female"] = (reg_df["gender"] == "Female").astype(int)
reg_df["overweight"] = (reg_df["bmi_category"] == "Overweight").astype(int)
reg_df["obese"] = (reg_df["bmi_category"] == "Obese").astype(int)

for race in ["Non-Hispanic Black", "Non-Hispanic Asian", "Mexican American"]:
    safe = race.replace(" ", "_").replace("-", "_").replace("/", "_")
    reg_df[safe] = (reg_df["race_ethnicity"] == race).astype(int)

reg_df["edu_less_hs"] = reg_df["education"].isin(["Less than 9th grade", "9-11th grade"]).astype(int)
reg_df["edu_hs"] = (reg_df["education"] == "High school/GED").astype(int)
reg_df["edu_some_college"] = (reg_df["education"] == "Some college/AA").astype(int)

print(f"Regression sample: {len(reg_df)}")

raw_w = reg_df["survey_weight"].values
w_norm = raw_w * len(reg_df) / raw_w.sum()
reg_df["w_norm"] = w_norm

# Model 1: Unadjusted
X1 = reg_df[["overweight", "obese"]]
X1 = sm.add_constant(X1)
y = reg_df["diabetes"]

model1 = sm.GLM(y, X1, family=sm.families.Binomial(), freq_weights=w_norm)
result1 = model1.fit()

print("\n--- Model 1: Unadjusted ---\n")
print(result1.summary2().tables[1].to_string())

# Model 2: Adjusted
X2 = reg_df[["overweight", "obese", "age", "female",
             "Non_Hispanic_Black", "Non_Hispanic_Asian", "Mexican_American",
             "edu_less_hs", "edu_hs", "edu_some_college"]]
X2 = sm.add_constant(X2)

model2 = sm.GLM(y, X2, family=sm.families.Binomial(), freq_weights=w_norm)
result2 = model2.fit()

print("\n--- Model 2: Adjusted ---\n")
print(result2.summary2().tables[1].to_string())


def extract_or_table(result, var_names, var_labels):
    rows = []
    for var, label in zip(var_names, var_labels):
        coef = result.params[var]
        ci = result.conf_int().loc[var]
        p = result.pvalues[var]
        or_val = np.exp(coef)
        or_lo = np.exp(ci[0])
        or_hi = np.exp(ci[1])
        rows.append({
            "Variable": label, "OR": f"{or_val:.2f}",
            "95% CI": f"{or_lo:.2f}-{or_hi:.2f}", "p-value": format_p(p),
        })
    return pd.DataFrame(rows)


vars1 = ["overweight", "obese"]
labels1 = ["Overweight vs Normal", "Obese vs Normal"]
or_table1 = extract_or_table(result1, vars1, labels1)

vars2 = ["overweight", "obese", "age", "female",
         "Non_Hispanic_Black", "Non_Hispanic_Asian", "Mexican_American"]
labels2 = ["Overweight vs Normal", "Obese vs Normal",
           "Age (per year)", "Female vs Male",
           "NH Black vs NH White", "NH Asian vs NH White", "Mexican American vs NH White"]
or_table2 = extract_or_table(result2, vars2, labels2)

print("\n--- Odds Ratios: Model 1 (Unadjusted) ---\n")
print(or_table1.to_markdown(index=False))
print("\n--- Odds Ratios: Model 2 (Adjusted) ---\n")
print(or_table2.to_markdown(index=False))

or_table1["Model"] = "Unadjusted"
or_table2["Model"] = "Adjusted"
or_combined = pd.concat([or_table1, or_table2], ignore_index=True)
or_combined = or_combined[["Model", "Variable", "OR", "95% CI", "p-value"]]
or_combined.to_csv("tables/regression_results.csv", index=False)

# Extract key ORs for manifest
or_adj = or_combined[or_combined["Model"] == "Adjusted"]
ow_row = or_adj[or_adj["Variable"] == "Overweight vs Normal"].iloc[0]
ob_row = or_adj[or_adj["Variable"] == "Obese vs Normal"].iloc[0]
print(f"\nSaved: tables/regression_results.csv")

# ============================================================
# PART D: FIGURES
# ============================================================
print("\n" + "=" * 60)
print("PART D: Figures")
print("=" * 60)

COLORS = {"Normal": "#009E73", "Overweight": "#E69F00", "Obese": "#D55E00"}

# Figure 1: Diabetes prevalence by BMI category
fig, ax = plt.subplots(figsize=(5, 4))
categories = ["Normal", "Overweight", "Obese"]
prev_vals = [float(prev_df[prev_df["BMI Category"] == c]["Prevalence (%)"].values[0]) for c in categories]
ci_lo = [float(prev_df[prev_df["BMI Category"] == c]["95% CI lower"].values[0]) for c in categories]
ci_hi = [float(prev_df[prev_df["BMI Category"] == c]["95% CI upper"].values[0]) for c in categories]
yerr_lo = [max(0, p - l) for p, l in zip(prev_vals, ci_lo)]
yerr_hi = [max(0, h - p) for p, h in zip(prev_vals, ci_hi)]

bars = ax.bar(categories, prev_vals, color=[COLORS[c] for c in categories],
              edgecolor="black", linewidth=0.5, width=0.6)
ax.errorbar(categories, prev_vals, yerr=[yerr_lo, yerr_hi],
            fmt="none", color="black", capsize=4, linewidth=1.2)

for bar, val in zip(bars, prev_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.8,
            f"{val:.1f}%", ha="center", va="bottom", fontsize=10, fontweight="bold")

ax.set_ylabel("Diabetes Prevalence (%)")
ax.set_xlabel("BMI Category")
ax.set_title("Diabetes Prevalence by BMI Category\n(NHANES 2017-2018)")
ax.set_ylim(0, max(prev_vals) * 1.3)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
fig.savefig("figures/prevalence_by_bmi.png", dpi=300, bbox_inches="tight")
fig.savefig("figures/prevalence_by_bmi.pdf", bbox_inches="tight")
plt.close(fig)
print("Saved: figures/prevalence_by_bmi.{png,pdf}")

# Figure 2: OR forest plot
fig, ax = plt.subplots(figsize=(6, 4))
plot_vars = or_table2[or_table2["Model"] == "Adjusted"][["Variable", "OR", "95% CI"]].copy()
plot_vars = plot_vars.iloc[::-1].reset_index(drop=True)

for i, row in plot_vars.iterrows():
    or_val = float(row["OR"])
    ci_str = row["95% CI"].split("-")
    ci_lo_val = float(ci_str[0])
    ci_hi_val = float(ci_str[1])

    color = "#D55E00" if or_val > 1 else "#0072B2"
    ax.plot(or_val, i, "D", color=color, markersize=8, zorder=3)
    ax.plot([ci_lo_val, ci_hi_val], [i, i], color=color, linewidth=2, zorder=2)
    ax.text(max(ci_hi_val, or_val) + 0.1, i,
            f"{or_val} ({ci_lo_val:.2f}-{ci_hi_val:.2f})",
            va="center", fontsize=8)

ax.axvline(x=1, color="gray", linestyle="--", linewidth=0.8, zorder=1)
ax.set_yticks(range(len(plot_vars)))
ax.set_yticklabels(plot_vars["Variable"], fontsize=9)
ax.set_xlabel("Odds Ratio (95% CI)")
ax.set_title("Adjusted Odds Ratios for Diabetes\n(NHANES 2017-2018)")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_xlim(left=0)

fig.tight_layout()
fig.savefig("figures/or_forest_plot.png", dpi=300, bbox_inches="tight")
fig.savefig("figures/or_forest_plot.pdf", bbox_inches="tight")
plt.close(fig)
print("Saved: figures/or_forest_plot.{png,pdf}")

# Figure 3: HbA1c distribution by BMI category
fig, ax = plt.subplots(figsize=(6, 4))
for g in categories:
    gdf = group_dfs[g]
    hba1c_clipped = gdf["hba1c"].clip(upper=12)
    ax.hist(hba1c_clipped, bins=50, alpha=0.5, color=COLORS[g],
            label=f"{g} (n={len(gdf)})", density=True, edgecolor="none")

ax.axvline(x=6.5, color="red", linestyle="--", linewidth=1.2, label="Diabetes threshold (6.5%)")
ax.axvline(x=5.7, color="orange", linestyle=":", linewidth=1.0, label="Prediabetes threshold (5.7%)")
ax.set_xlabel("HbA1c (%)")
ax.set_ylabel("Density")
ax.set_title("HbA1c Distribution by BMI Category\n(NHANES 2017-2018)")
ax.legend(fontsize=7, loc="upper right")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
fig.savefig("figures/hba1c_distribution.png", dpi=300, bbox_inches="tight")
fig.savefig("figures/hba1c_distribution.pdf", bbox_inches="tight")
plt.close(fig)
print("Saved: figures/hba1c_distribution.{png,pdf}")

# Figure 4: Prevalence by age group and BMI
fig, ax = plt.subplots(figsize=(6, 4))
df_main["age_group"] = pd.cut(df_main["age"], bins=[20, 40, 60, 80], labels=["20-39", "40-59", "60-79"])
age_bmi_prev = df_main.groupby(["age_group", "bmi_category"])["diabetes"].mean() * 100
age_bmi_prev = age_bmi_prev.reset_index()
age_bmi_prev = age_bmi_prev[age_bmi_prev["bmi_category"].isin(categories)]

x_positions = np.arange(3)
width = 0.25
for i, bmi_cat in enumerate(categories):
    subset = age_bmi_prev[age_bmi_prev["bmi_category"] == bmi_cat]
    vals = subset["diabetes"].values
    ax.bar(x_positions + i * width, vals, width, color=COLORS[bmi_cat],
           label=bmi_cat, edgecolor="black", linewidth=0.3)

ax.set_xticks(x_positions + width)
ax.set_xticklabels(["20-39", "40-59", "60-79"])
ax.set_xlabel("Age Group (years)")
ax.set_ylabel("Diabetes Prevalence (%)")
ax.set_title("Diabetes Prevalence by Age and BMI\n(NHANES 2017-2018)")
ax.legend(fontsize=8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
fig.savefig("figures/prevalence_by_age_bmi.png", dpi=300, bbox_inches="tight")
fig.savefig("figures/prevalence_by_age_bmi.pdf", bbox_inches="tight")
plt.close(fig)
print("Saved: figures/prevalence_by_age_bmi.{png,pdf}")

# ============================================================
# OUTPUT MANIFEST
# ============================================================
manifest = f"""# Analysis Outputs — Demo 3: NHANES Obesity & Diabetes
Generated: {datetime.date.today()}
Study type: Cross-sectional epidemiological (NHANES 2017-2018)
Sample: {len(df_main)} US adults aged 20+ (excluding underweight)

## Key Results
- Overall diabetes prevalence: {100*df_main['diabetes'].mean():.1f}%
- Normal BMI: {prev_df[prev_df['BMI Category']=='Normal']['Prevalence (%)'].values[0]}%
- Overweight: {prev_df[prev_df['BMI Category']=='Overweight']['Prevalence (%)'].values[0]}%
- Obese: {prev_df[prev_df['BMI Category']=='Obese']['Prevalence (%)'].values[0]}%
- Adjusted OR (obese vs normal): {ob_row['OR']} (95% CI: {ob_row['95% CI']})

## Tables
- `tables/table1.csv` — Baseline characteristics by BMI category
- `tables/prevalence_by_bmi.csv` — Diabetes prevalence with Wilson CIs
- `tables/regression_results.csv` — Logistic regression ORs (unadjusted + adjusted)

## Figures
- `figures/prevalence_by_bmi.{{pdf,png}}` — Diabetes prevalence bar chart
- `figures/or_forest_plot.{{pdf,png}}` — Adjusted OR forest plot
- `figures/hba1c_distribution.{{pdf,png}}` — HbA1c density by BMI category
- `figures/prevalence_by_age_bmi.{{pdf,png}}` — Prevalence by age and BMI subgroup

## Data
- `data/nhanes_2017_2018.csv` — Prepared NHANES dataset
"""
with open("_analysis_outputs.md", "w") as f:
    f.write(manifest)
print("\nSaved: _analysis_outputs.md")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)
