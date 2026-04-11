# Repeated Measures / Mixed Models Guide

Analysis methods for longitudinal data where the same subjects are measured at multiple time points.

---

## When to Use

- Same subjects measured at 2+ time points
- Key research question: does change over time differ between groups? (Time x Group interaction)
- Examples: treatment response over weeks, serial imaging measurements, before/after/follow-up

---

## Method Selection

| Condition | Recommended method |
|-----------|-------------------|
| No missing data + few time points + sphericity met | RM ANOVA |
| Missing data (MAR) + continuous outcome | **LMM (preferred)** |
| Missing data + binary/count outcome | GEE (or GLMM) |
| Individual trajectory estimation needed | LMM (random slope) |
| Population-averaged effect only | GEE |
| Non-normal outcome | GLMM or GEE |

**Default recommendation: LMM** — handles missing data, does not require sphericity, allows unequal time spacing.

---

## Data Format

All methods (LMM, GEE) require **long format**:

| id | time | group | outcome |
|----|------|-------|---------|
| 1 | 0 | A | 45.2 |
| 1 | 1 | A | 42.8 |
| 1 | 2 | A | 38.1 |

Convert from wide format before analysis.

---

## 1. RM ANOVA

### Sphericity Check (Mandatory)
- **Mauchly's test**: H0 = sphericity holds
  - P >= 0.05 → use standard F-test
  - P < 0.05 → apply correction

### Corrections for Sphericity Violation
1. **Greenhouse-Geisser (G-G)**: conservative, recommended
2. **Huynh-Feldt**: slightly liberal
3. **Multivariate test** (Pillai's trace): no sphericity assumption needed

### Limitations
- Complete cases only — any missing time point drops the entire subject
- Difficult to add covariates
- Equal time spacing required

### Key Results to Report
- Mauchly's test result (W statistic, P-value, epsilon)
- Correction method used (if sphericity violated)
- Within-subject effect: Time (F, df, P)
- Between-subject effect: Group (F, df, P)
- **Interaction: Time x Group** (most important)

---

## 2. Linear Mixed Model (LMM)

### Structure
```
Y = Xβ (fixed effects) + Zb (random effects) + ε
```

### Random Effects Selection
- **Random intercept only**: subjects differ in baseline (default, start here)
- **Random intercept + slope**: subjects differ in both baseline and rate of change
- Decision: visualize individual trajectories (spaghetti plot). If slopes vary → add random slope.
- If model does not converge with random slope → simplify to random intercept only

### Covariance Structure Selection
| Structure | Property | When to use |
|-----------|----------|-------------|
| **CS** (Compound Symmetry) | Equal correlation between all time pairs | Equivalent to RM ANOVA |
| **AR(1)** | Correlation decays with time lag | Equally spaced measurements |
| **UN** (Unstructured) | Free correlation for each pair | Few time points only (many parameters) |

Compare structures using **AIC/BIC** (lower = better).

### Advantages over RM ANOVA
- Handles missing data under MAR assumption
- No sphericity requirement
- Allows unequal time intervals
- Easy covariate adjustment
- Estimates individual trajectories

---

## 3. GEE (Generalized Estimating Equations)

### Key Properties
- Estimates **population-averaged (marginal) effects** — not individual-level
- Specify working correlation: exchangeable, AR(1), unstructured
- Works for non-normal outcomes (binary, count)
- Requires **MCAR** assumption for missing data (or use weighted GEE for MAR)
- Needs sufficient clusters: subjects >= 30-40

### LMM vs GEE Decision
| Question | LMM | GEE |
|----------|-----|-----|
| "How does each patient change?" | Yes | No |
| "How does the group average change?" | Yes | Yes |
| Binary/count outcome without GLMM | No | Yes |
| MAR missing data tolerance | Yes | No (MCAR only) |

---

## Required Outputs

1. **Spaghetti plot**: individual trajectories by group
2. **Model summary table**: fixed effects (β, 95% CI, P), random effects variance
3. **Time x Group interaction** result prominently reported
4. Model fit: AIC/BIC for covariance structure comparison
5. Missing data description (n per time point, mechanism assumed)

---

## Reporting Templates

**RM ANOVA**: "Repeated-measures ANOVA was performed with Greenhouse-Geisser correction for violation of sphericity (Mauchly's test P < 0.001, ε = 0.42). There was a significant time × group interaction (F(X, Y) = Z, P = exact)."

**LMM**: "A linear mixed-effects model with random intercepts for subjects and [CS/AR(1)] correlation structure was fitted. The time × group interaction was significant (β = -2.34, 95% CI -3.87 to -0.81; P = 0.003), indicating that the rate of change in [outcome] differed between groups."

**GEE**: "GEE with exchangeable correlation structure was used to estimate population-averaged effects. The time × group interaction was ..."

---

## Common Reviewer Flags

1. Sphericity test not reported (for RM ANOVA)
2. Covariance structure selection rationale not stated (for LMM)
3. Time × Group interaction not interpreted
4. Missing data handling not described
5. Using RM ANOVA with substantial missing data (should use LMM)
6. Not reporting individual trajectories (spaghetti plot)

---

## Python Packages
- `pingouin` — RM ANOVA with G-G correction
- `statsmodels.formula.api.mixedlm` — LMM
- `statsmodels.genmod.generalized_estimating_equations.GEE` — GEE

## R Packages
- `lme4` + `lmerTest` — LMM (standard)
- `nlme` — LMM with correlation structures (CS, AR1, UN)
- `geepack` — GEE
- Base R `aov()` with `Error()` — RM ANOVA
