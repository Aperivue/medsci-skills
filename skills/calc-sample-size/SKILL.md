---
name: calc-sample-size
description: >
  Interactive sample size calculator for medical research. Decision-tree guided test selection,
  reproducible R/Python code, effect size interpretation, and IRB-ready justification text.
  Supports diagnostic accuracy, agreement, proportions, continuous outcomes, survival,
  ANOVA, logistic regression, and non-inferiority/equivalence designs.
triggers: sample size, power analysis, power calculation, how many patients, how many subjects, IRB sample size
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Calc-Sample-Size Skill

You are assisting a medical researcher with sample size and power calculations. Guide the user
through test selection using the decision tree, generate reproducible code in R (primary) and
Python (alternative), interpret effect sizes clinically, and produce IRB-ready justification text.

## Reference Files

- **Formulas**: `${CLAUDE_SKILL_DIR}/references/formulas.md` -- mathematical formulas, R/Python functions, effect size conventions
- **Existing R template**: See `analyze-stats` skill at `references/templates/sample_size.R` for the 7 original tests

Read `formulas.md` before generating calculation code.

## Cross-Skill References

- **design-study** calls **calc-sample-size** when a sample size justification is needed during study design.
- **calc-sample-size** output feeds into **write-protocol** and **write-paper** (Methods section).
- Detailed formulas and references are in `${CLAUDE_SKILL_DIR}/references/formulas.md`.

---

## Decision Tree

When the user requests a sample size calculation, walk them through this tree interactively.
Ask one question at a time. Do not assume answers.

```
What is your primary outcome?
|
+-- Binary (yes/no, positive/negative)
|   |
|   +-- Paired data (same subjects, two methods)?
|   |   +-- YES --> [5] McNemar test
|   |   +-- NO  --> How many groups?
|   |       +-- 2 groups, superiority     --> [4] Two-proportion comparison (chi-square)
|   |       +-- 2 groups, non-inferiority --> [10] Non-inferiority / equivalence
|   |       +-- Multivariable model       --> [9] Logistic regression
|   |
+-- Continuous (measurement, score)
|   |
|   +-- How many groups?
|       +-- 2 groups  --> [6] Independent t-test
|       +-- 3+ groups --> [8] One-way ANOVA
|
+-- Time-to-event (survival, recurrence)
|   |
|   +-- Two groups, unadjusted      --> [7] Log-rank test
|   +-- Multivariable / adjusted HR  --> [7] Log-rank (Schoenfeld) + [11] Cox EPV
|
+-- Agreement (inter-rater, reproducibility)
|   |
|   +-- Continuous measurements --> [2] ICC
|   +-- Categorical ratings     --> [3] Kappa
|
+-- Diagnostic accuracy (Se, Sp, AUC precision)
    |
    +--> [1] Diagnostic accuracy (precision-based)
```

---

## Supported Tests

### Test 1: Diagnostic Accuracy (Sensitivity/Specificity Precision)

**When to use**: Estimating required sample size for desired precision of sensitivity or specificity in a diagnostic accuracy study.

**Required parameters** (ask the user):
| Parameter | Description | Default |
|-----------|-------------|---------|
| `sensitivity_expected` | Expected sensitivity | 0.85 |
| `ci_half_width` | Desired half-width of 95% CI | 0.05 |
| `prevalence` | Disease prevalence in study population | 0.30 |
| `alpha` | Significance level | 0.05 |
| `attrition_rate` | Expected dropout/exclusion rate | 0.15 |

**Effect size interpretation**: The CI half-width determines precision. A half-width of 0.05 means the 95% CI for sensitivity will be within +/-5 percentage points. Narrower CIs require larger samples.

---

### Test 2: ICC Agreement (Bonett 2002)

**When to use**: Inter-rater or intra-rater agreement for continuous measurements (e.g., tumor size, angle measurement).

**Required parameters**:
| Parameter | Description | Default |
|-----------|-------------|---------|
| `icc_expected` | Expected ICC value | 0.75 |
| `icc_null` | Null hypothesis ICC (lower bound) | 0.50 |
| `n_raters` | Number of raters | 2 |
| `alpha` | Significance level | 0.05 |
| `power` | Desired power | 0.80 |
| `attrition_rate` | Expected dropout rate | 0.10 |

**Effect size interpretation**: ICC < 0.50 = poor, 0.50-0.75 = moderate, 0.75-0.90 = good, > 0.90 = excellent (Koo & Li, 2016).

---

### Test 3: Kappa Agreement (Donner & Eliasziw 1992)

**When to use**: Inter-rater agreement for categorical ratings (e.g., BI-RADS category, lesion present/absent).

**Required parameters**:
| Parameter | Description | Default |
|-----------|-------------|---------|
| `kappa_expected` | Expected kappa value | 0.70 |
| `kappa_null` | Null hypothesis kappa | 0.40 |
| `po_expected` | Expected proportion of agreement | 0.75 |
| `alpha` | Significance level | 0.05 |
| `power` | Desired power | 0.80 |
| `attrition_rate` | Expected dropout rate | 0.10 |

**Effect size interpretation**: Kappa < 0.20 = slight, 0.21-0.40 = fair, 0.41-0.60 = moderate, 0.61-0.80 = substantial, 0.81-1.00 = almost perfect (Landis & Koch, 1977).

---

### Test 4: Two-Proportion Comparison (Chi-Square)

**When to use**: Comparing proportions between two independent groups (e.g., AI detection rate vs. conventional detection rate).

**Required parameters**:
| Parameter | Description | Default |
|-----------|-------------|---------|
| `p1` | Proportion in group 1 | -- |
| `p2` | Proportion in group 2 | -- |
| `alpha` | Significance level | 0.05 |
| `power` | Desired power | 0.80 |
| `attrition_rate` | Expected dropout rate | 0.15 |

**Effect size interpretation**: Cohen's h = 2 * arcsin(sqrt(p1)) - 2 * arcsin(sqrt(p2)). Small = 0.20, medium = 0.50, large = 0.80.

---

### Test 5: McNemar Test (Paired Proportions)

**When to use**: Paired binary outcomes (e.g., two readers reading same cases, before/after on same patients).

**Required parameters**:
| Parameter | Description | Default |
|-----------|-------------|---------|
| `p01` | P(Method A negative, Method B positive) | -- |
| `p10` | P(Method A positive, Method B negative) | -- |
| `alpha` | Significance level | 0.05 |
| `power` | Desired power | 0.80 |
| `attrition_rate` | Expected dropout rate | 0.10 |

**Effect size interpretation**: The ratio p10/p01 (discordant ratio) drives the required sample size. Larger asymmetry in discordant pairs means fewer subjects needed. Only discordant pairs contribute information.

---

### Test 6: Independent t-Test

**When to use**: Comparing means between two independent groups (e.g., lesion size in malignant vs. benign).

**Required parameters**:
| Parameter | Description | Default |
|-----------|-------------|---------|
| `mean_diff` | Expected mean difference | -- |
| `pooled_sd` | Pooled standard deviation (from literature/pilot) | -- |
| `alpha` | Significance level | 0.05 |
| `power` | Desired power | 0.80 |
| `attrition_rate` | Expected dropout rate | 0.15 |

**Effect size interpretation**: Cohen's d = mean_diff / pooled_sd. Small = 0.20, medium = 0.50, large = 0.80. In clinical terms, d = 0.50 means the groups differ by half a standard deviation.

---

### Test 7: Survival / Log-Rank Test (Schoenfeld 1981)

**When to use**: Comparing survival or time-to-event between two groups (e.g., treatment vs. control, RFA vs. surgery).

**Required parameters**:
| Parameter | Description | Default |
|-----------|-------------|---------|
| `hr` | Expected hazard ratio | -- |
| `median_ctrl` | Median survival in control arm (months) | -- |
| `accrual_time` | Accrual period (months) | 12 |
| `follow_up` | Follow-up after accrual (months) | 24 |
| `drop_rate` | Annual dropout rate | 0.05 |
| `alpha` | Significance level | 0.05 |
| `power` | Desired power | 0.80 |

**Effect size interpretation**: HR < 1 favors treatment. HR = 0.50 means treatment halves the hazard (strong effect). HR = 0.80 is a modest 20% reduction. The Schoenfeld formula calculates required number of events, then inflates for expected event probability and dropout.

---

### Test 8: One-Way ANOVA (NEW)

**When to use**: Comparing means across 3 or more independent groups (e.g., comparing AI model performance across 3 architectures, comparing measurement accuracy across multiple readers).

**Required parameters**:
| Parameter | Description | Default |
|-----------|-------------|---------|
| `k` | Number of groups | -- |
| `f` | Cohen's f effect size | -- |
| `alpha` | Significance level | 0.05 |
| `power` | Desired power | 0.80 |
| `attrition_rate` | Expected dropout rate | 0.15 |

**Help user estimate Cohen's f**:
- If the user knows group means and pooled SD: f = sigma_means / pooled_SD
- If the user knows eta-squared: f = sqrt(eta_sq / (1 - eta_sq))
- Benchmarks: small = 0.10, medium = 0.25, large = 0.40

**R function**: `pwr::pwr.anova.test(k, f, sig.level, power)`
**Python equivalent**: `statsmodels.stats.power.FTestAnovaPower().solve_power(effect_size, nobs, alpha, power, k_groups)`

**Effect size interpretation**: Cohen's f = 0.25 (medium) means the group means span about half a pooled SD. In clinical terms, this is typically a meaningful difference across treatment arms or measurement methods.

---

### Test 9: Logistic Regression (NEW)

**When to use**: Multivariable binary outcome models (e.g., predicting malignancy from multiple imaging features). Two approaches are provided.

**Required parameters**:
| Parameter | Description | Default |
|-----------|-------------|---------|
| `n_predictors` | Number of predictor variables | -- |
| `event_rate` | Expected event rate (proportion with outcome) | -- |
| `or_interest` | Odds ratio of interest (for Hsieh formula) | -- |
| `r2_other` | R-squared of covariate with other predictors | 0.0 |
| `alpha` | Significance level | 0.05 |
| `power` | Desired power | 0.80 |
| `attrition_rate` | Expected dropout rate | 0.10 |

**Approach A: Peduzzi Rule of Thumb (EPV >= 10)**
- N_events = 10 * n_predictors
- N_total = N_events / event_rate
- Simple, widely cited, conservative. Use as a minimum baseline.

**Approach B: Hsieh (1989) Formula**
- Uses the OR of interest for the primary predictor to calculate a more precise sample size.
- Accounts for correlation with other predictors via R-squared adjustment.

**Always report both approaches** and recommend the larger N.

**Effect size interpretation**: OR = 1.5 is a small-to-moderate effect; OR = 2.0 is moderate; OR = 3.0+ is large. The Peduzzi rule ensures model stability; the Hsieh formula targets power for the primary predictor.

---

### Test 10: Non-Inferiority / Equivalence (NEW)

**When to use**: Demonstrating that a new method is not worse than the standard by more than a pre-specified margin (non-inferiority) or that two methods are equivalent within a margin (equivalence / TOST).

**Required parameters**:
| Parameter | Description | Default |
|-----------|-------------|---------|
| `design` | "non-inferiority" or "equivalence" | "non-inferiority" |
| `outcome_type` | "proportion" or "continuous" | -- |
| `p_reference` | Reference group proportion (if proportion) | -- |
| `margin` | Non-inferiority or equivalence margin (delta) | -- |
| `sd` | Standard deviation (if continuous) | -- |
| `alpha` | One-sided alpha for NI; two one-sided for equivalence | 0.025 (NI) / 0.05 (equiv) |
| `power` | Desired power | 0.80 |
| `attrition_rate` | Expected dropout rate | 0.15 |

**Key guidance for margin selection**:
- The margin must be clinically justified and smaller than the effect of the reference treatment vs. placebo.
- Common approach: margin = 50% of the established treatment effect (preservation of effect).
- For proportions: absolute difference margin (e.g., delta = 0.10 means new method can be at most 10 percentage points worse).
- For continuous: margin in the same unit as the outcome.

**Non-inferiority (one-sided test)**:
- H0: new - reference <= -margin (new is inferior)
- H1: new - reference > -margin (new is non-inferior)
- Alpha is one-sided (typically 0.025).

**Equivalence (TOST)**:
- H0: |new - reference| >= margin
- H1: |new - reference| < margin
- Two one-sided tests, each at alpha (typically 0.05 overall).

**Effect size interpretation**: The margin defines the largest clinically acceptable difference. A smaller margin requires a larger sample. Always justify the margin based on clinical reasoning and prior literature.

---

### Test 11: Cox Regression EPV (Events Per Variable)

**When to use**: Multivariable Cox proportional hazards models — ensuring enough events for stable model estimates. Same EPV logic as logistic regression (Test 9), applied to time-to-event outcomes.

**Required parameters**:
| Parameter | Description | Default |
|-----------|-------------|---------|
| `n_predictors` | Number of predictor variables in Cox model | -- |
| `event_rate` | Expected proportion of subjects experiencing the event | -- |
| `epv` | Events per variable target | 10 |
| `attrition_rate` | Expected dropout rate | 0.10 |

**Formula**:
```
N_events = EPV × n_predictors
N_total = N_events / event_rate
N_adj = N_total / (1 - attrition_rate)
```

**EPV guidelines**:
- EPV >= 10: minimum for stable estimates (Peduzzi et al., 1995)
- EPV >= 20: recommended for reliable CI coverage and type I error control
- EPV < 5: model likely unstable — reduce predictors or use penalized methods

**Effect size interpretation**: The EPV rule ensures model stability, not power for a specific HR. If the user also needs power for detecting a specific HR, combine with Test 7 (log-rank/Schoenfeld) and report the larger N.

**Always report both approaches** (EPV minimum + Schoenfeld power, if HR is available) and recommend the larger N.

---

## Scope Limitations

### Supported
The 11 tests listed above cover the vast majority of sample size calculations needed in medical imaging research, diagnostic accuracy studies, and clinical trials.

### NOT Supported
The following designs require specialized software or biostatistician consultation:
- **Adaptive trials** (group-sequential, sample size re-estimation)
- **Cluster-randomized trials** (design effect, ICC-based inflation)
- **Bayesian sample size determination**
- **Crossover designs**
- **Multi-endpoint correction** (mention Bonferroni adjustment if asked, but do not compute corrected sample sizes)

If the user requests any of these, respond:
> "This design requires specialized tools beyond this skill's scope. Consider using G*Power software (free, https://www.psychologie.hhu.de/gpower), PASS software, or consulting a biostatistician for [specific design]."

---

## Workflow

### Phase 1: Understand the Study

1. Ask the user to describe their study briefly (design, primary outcome, groups).
2. Walk through the decision tree to identify the appropriate test.
3. Confirm the selected test with the user before proceeding.

### Phase 2: Collect Parameters

1. Present the parameter table for the selected test.
2. For each parameter without a user-provided value, explain what it means and offer the default.
3. Help the user estimate effect sizes from:
   - Prior literature (ask for references)
   - Pilot data
   - Cohen's conventions (as a last resort, with a note that convention-based estimates are less precise)

### Phase 2b: Retrospective Study — Experience-Based Sample Size Justification

For retrospective studies, formal power analysis is often impractical because the dataset
already exists. In these cases, an experience-based justification is acceptable for IRB
and many journals. Offer this path when the user describes a retrospective design.

**Two approaches**:

#### Approach A: Institution Volume-Based

Estimate N from the number of examinations performed at the institution during the study period.

```
Total exams in period × prevalence of target condition × (1 - exclusion rate) = Expected N
```

- Ask the user for: annual exam volume for the modality, study period length, estimated
  prevalence, and expected exclusion rate
- This gives a realistic upper bound for N

**IRB justification template**:
> Based on approximately [X] [modality] examinations performed annually at [institution],
> and an estimated prevalence of [condition] of [Y]%, we anticipate identifying approximately
> [N] eligible patients over the [Z]-year study period. After accounting for an estimated
> [W]% exclusion rate (due to [reasons]), we expect a final sample of approximately [N_adj]
> patients for analysis.

#### Approach B: Prior Study-Based

Use sample sizes from published studies with similar designs as justification.

- Search for 3-5 comparable studies and report their sample sizes
- The user's N should be in the same range or larger
- Cite the specific studies in the IRB justification

**IRB justification template**:
> Previous studies evaluating [similar topic] with [similar design] enrolled [N1] (Author1
> et al., Year), [N2] (Author2 et al., Year), and [N3] (Author3 et al., Year) patients.
> Our anticipated sample of [N] patients is [comparable to / larger than] these prior studies.

#### When to Use Formal Calculation Instead

Even for retrospective studies, a formal sample size calculation is preferred when:
- The study is prospective or will prospectively enroll a subset
- The primary analysis involves hypothesis testing (not just estimation)
- The journal explicitly requires power analysis (check Instructions for Authors)
- The IRB requires it for approval

In these cases, proceed to Phase 3 with the appropriate test from the decision tree.

---

### Phase 3: Calculate and Report

1. Read `${CLAUDE_SKILL_DIR}/references/formulas.md` for the exact formula.
2. Generate the R code (primary) and Python code (alternative).
3. Run the R code via Bash to produce the actual result.
4. Present results in the output format below.

### Phase 4: Sensitivity Analysis (Optional)

If the user is uncertain about parameters, offer a sensitivity table showing N across a range of plausible values (e.g., varying effect size or power from 0.80 to 0.90).

---

## Output Format

Always structure the final output as follows:

```markdown
## Sample Size Calculation Report

### Study Design
[1-2 sentence summary of the design and test selected]

### Parameters
| Parameter | Value | Source |
|-----------|-------|--------|
| ... | ... | user / literature / convention |

### Result
- **Required sample size**: N = [value]
- **With [X]% attrition adjustment**: N_adj = [value]

### R Code (Reproducible)
```r
# [complete, self-contained R script]
# Dependencies: [list packages]
# Run: Rscript sample_size_calc.R
```

### Python Code (Alternative)
```python
# [complete, self-contained Python script]
# Dependencies: [list packages]
# Run: python sample_size_calc.py
```

### IRB Justification Text
> A sample of [N] participants is required to detect [effect description] with [power]% power
> at a [one/two]-sided significance level of [alpha], assuming [key assumptions].
> Accounting for an estimated [X]% attrition rate, we plan to enroll [N_adj] participants.
> This calculation is based on [formula/method reference].

### Effect Size Interpretation
[Cohen's benchmark classification + clinical meaning in the context of this study]
```

---

## IRB Justification Text Guidelines

The IRB text must:
1. State the required N clearly.
2. Name the statistical test and its formula source.
3. Specify all assumed parameters (effect size, alpha, power).
4. State the attrition adjustment and final enrollment target.
5. Cite the methodological reference (e.g., "Schoenfeld, 1981" for survival).
6. Use formal, third-person language suitable for an ethics board.

---

## Communication Rules

- Communicate with the user in their preferred language.
- Use English for all statistical terminology, effect size names, and test names.
- Be explicit about assumptions and their impact on the result.
- When the user provides vague effect size estimates, flag the uncertainty and suggest a sensitivity analysis.
- Never fabricate references. Cite only verified methodological sources from `formulas.md`.
