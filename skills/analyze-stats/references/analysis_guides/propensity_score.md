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
| **ATO** | Effect on Overlap population | Units weighted by PS(1−PS) across the whole PS range (most weight near 0.5; no cut-off) | Overlap weighting |

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
- Nearest-neighbor matching with caliper = 0.2 x SD(logit PS); greedy, without replacement,
  each treated unit taking the nearest *available* control within the caliper (MatchIt
  `method = "nearest"` defaults; `propensity_score.py` reproduces its matched set)
- 1:1 matching is standard; 1:k (`matching_ratio = k`) and full matching available
- Estimand: ATT — **only if every treated unit is matched**. Treated units with no control within
  the caliper are dropped, and the estimand becomes the effect in the matched treated
  (Rosenbaum & Rubin 1985, doi:10.2307/2530647); report how many were dropped
- Drawback: unmatched subjects are excluded → sample size reduction

**Option B — IPTW (Inverse Probability of Treatment Weighting)**
- Weights: treated = 1/PS, control = 1/(1-PS) for ATE
- Stabilized weights: treated = P(T=1)/PS, control = P(T=0)/(1-PS). Stabilization rescales each
  arm's weights (the weighted sample size stays near N, which helps variance estimation and
  ESS reporting) but does **not** change the ratio of weights within an arm, so it does not
  remove extreme weights. Extreme weights come from PS near 0 or 1: inspect the PS overlap,
  and consider trimming the population or overlap weights (Austin & Stuart 2015,
  doi:10.1002/sim.6607)
- All subjects included (no exclusion)
- Flag extreme weights > 10

**Option C — SIPTW (Stabilized Inverse Probability of Treatment Weighting)**
- Weights: treated = P(T=1)/PS, control = P(T=0)/(1-PS)
- Mathematically equivalent to stabilized IPTW (Option B with stabilized=True)
- Named explicitly as SIPTW in emulated target trial literature
- Maintains entire cohort sample size (no exclusion)
- Allows appropriate variance estimation of main effect
- Estimand: ATE
- Increasingly used in large-scale NHIS cohort studies
- Report effective sample size (ESS) alongside raw N

**Option D — Overlap Weighting (Recommended for most cases)**
- Weights: treated = (1-PS), control = PS
- Weights are bounded in [0, 1], so no single subject dominates; subjects near PS 0 or 1 get
  weight near 0 (Li, Morgan & Zaslavsky 2018, doi:10.1080/01621459.2016.1260466)
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
- **After PSM**: regress the outcome on treatment in the matched sample with the matching
  weights and a **cluster-robust SE by matched set** (or conditional logistic / stratified Cox
  by matched set)
- **After IPTW/OW**: weighted regression with **robust (sandwich) standard errors** — never the
  model-based SE of a weighted fit, and never `freq_weights` (weights are not case counts). In a
  simulation (400 samples, true null) the model-based CI covered the truth in 80% (continuous)
  and 79% (binary) of unstabilised-IPTW analyses; the robust HC0 CI in 94% and 96% (Austin
  2016, doi:10.1002/sim.7084). The robust SE ignores PS estimation and is conservative for the
  ATE; bootstrap the whole pipeline when precision matters
- `propensity_score.py` does both (OR and risk difference for a binary outcome)

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

**PSM**: "Propensity scores were estimated using logistic regression with the following covariates: [list]. PS matching was performed using 1:[k] greedy nearest-neighbor matching without replacement with a caliper of 0.2 SD of the logit PS; [n] of [N] treated patients were matched. After matching, the largest absolute SMD was [X.XX] (Figure X). The effect was estimated in the matched cohort with cluster-robust standard errors by matched set: ..."

**IPTW/OW**: "Inverse probability of treatment weighting (or overlap weighting) was applied [with stabilized weights]. After weighting, the largest absolute SMD was [X.XX] (Figure X). Effects were estimated by weighted regression with robust (sandwich) standard errors: ..."

**SIPTW**: "Stabilized inverse probability of treatment weighting was used to balance covariate distributions between the [exposed] and [unexposed] groups. After weighting, the largest absolute SMD was [X.XX] (Figure X); effects were estimated with robust (sandwich) standard errors."

Fill each bracket from the script output. Write "all SMDs < 0.10" only when the balance table
shows it.

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
- `statsmodels` — PS model (unpenalised logistic) and weighted regression with robust /
  cluster-robust SEs (see `propensity_score.py`)
- Note: `sklearn`'s `LogisticRegression` is L2-penalised by default (C = 1.0), which is not the
  standard PS model

## R Packages
- `MatchIt` — PS matching
- `WeightIt` — IPTW, overlap weighting
- `cobalt` — balance assessment, Love plot
- `survey` — weighted outcome analysis
- `tableone` — baseline table with SMD
- `EValue` — sensitivity analysis
