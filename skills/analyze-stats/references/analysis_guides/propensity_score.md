# Propensity Score Analysis Guide

Methods for estimating causal treatment effects in observational studies by balancing
confounders between treatment groups.

---

## When to Use

- Observational study comparing treatment vs control (or two interventions)
- Multiple confounders to adjust for
- Goal: estimate causal effect analogous to an RCT
- NOT for: randomized trials (already balanced), single-arm studies

---

## Estimands — Choose Before Analysis

| Estimand | Definition | Target population | Method |
|----------|-----------|-------------------|--------|
| **ATE** | Average Treatment Effect | Entire study population | IPTW |
| **ATT** | Effect on Treated | Treatment group only | PSM, ATT weighting |
| **ATO** | Effect on Overlap population | PS 0.2-0.8 region | Overlap weighting |

Comparing PSM and IPTW results directly is inappropriate — they estimate different estimands.

---

## Step-by-Step Workflow

### Step 1: PS Estimation
- Model: logistic regression (standard)
- Dependent variable: treatment assignment (binary)
- Covariates: all variables that affect the outcome (confounders)
- Do NOT include: instrumental variables (affect treatment but not outcome)
- Individual PS model coefficients have no clinical meaning — only PS distribution matters

### Step 2: Apply PS Method

**Option A — PS Matching (PSM)**
- Nearest-neighbor matching with caliper = 0.2 x SD(logit PS)
- 1:1 matching is standard; 1:N or full matching available
- Estimand: ATT (typically)
- Drawback: unmatched subjects are excluded → sample size reduction

**Option B — IPTW (Inverse Probability of Treatment Weighting)**
- Weights: treated = 1/PS, control = 1/(1-PS) for ATE
- **Always use stabilized weights** to prevent extreme values
- Stabilized: treated = P(T=1)/PS, control = P(T=0)/(1-PS)
- All subjects included (no exclusion)
- Flag extreme weights > 10

**Option C — Overlap Weighting (Recommended for most cases)**
- Weights: treated = (1-PS), control = PS
- Naturally down-weights subjects at PS extremes
- No extreme weight problem (advantage over IPTW)
- Estimand: ATO
- Increasingly recommended in recent guidelines (JAMA 2020, AJE 2024)

### Step 3: Assess Balance
- **SMD < 0.10** for all covariates (Austin, 2009)
- SMD < 0.25 is acceptable but suboptimal
- Use SMD, NOT p-values (SMD is sample-size independent)
- **Love plot**: pre/post-matching SMD comparison (mandatory figure)
- Variance ratios: should be within 0.5-2.0
- PS distribution overlap: histogram comparing treated vs control

### Step 4: Outcome Analysis
- **After PSM**: paired analysis (paired t-test, conditional logistic, stratified Cox)
- **After IPTW/OW**: weighted regression using survey methods
- Always use robust/sandwich standard errors for weighted analyses

### Step 5: Sensitivity Analysis
- **E-value**: quantifies how strong unmeasured confounding would need to be to explain away the result
- Report E-value for the point estimate and lower CI bound

---

## Balance Table (Required Output)

| Variable | Before matching | | After matching | |
|----------|------|------|------|------|
| | Treated | Control | SMD | Treated | Control | SMD |
| Age, mean (SD) | 65.2 (12.1) | 58.7 (14.3) | 0.49 | 62.1 (11.8) | 61.8 (12.0) | 0.03 |

---

## Reporting Templates

**PSM**: "Propensity scores were estimated using logistic regression with the following covariates: [list]. PS matching was performed using 1:1 nearest-neighbor matching with a caliper of 0.2 SD of the logit PS. After matching, all SMDs were below 0.10 (Figure X). In the matched cohort (n = X pairs), ..."

**IPTW/OW**: "Inverse probability of treatment weighting (or overlap weighting) was applied using stabilized weights. Covariate balance was assessed using SMDs (all < 0.10; Figure X). The weighted analysis showed ..."

---

## Common Reviewer Flags

1. SMD not reported (using p-values instead)
2. Caliper width not specified
3. Estimand (ATE/ATT/ATO) not stated
4. No sensitivity analysis for unmeasured confounding
5. Number of unmatched subjects not reported (for PSM)
6. Extreme weights not assessed (for IPTW)
7. Individual PS model coefficients interpreted clinically

---

## Python Packages
- `sklearn.linear_model.LogisticRegression` — PS estimation
- `causalinference` — matching (limited)
- Manual implementation for IPTW/OW (see template)
- `statsmodels` — weighted regression

## R Packages
- `MatchIt` — PS matching
- `WeightIt` — IPTW, overlap weighting
- `cobalt` — balance assessment, Love plot
- `survey` — weighted outcome analysis
- `tableone` — baseline table with SMD
- `EValue` — sensitivity analysis
