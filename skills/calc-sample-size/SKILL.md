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

## Decision Tree

Walk the user through this tree one question at a time; do not assume answers. Reader studies,
segmentation and model-comparison designs sit outside the tree: see Tests 14–17.

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
|   |       +-- Multivariable model       --> single-predictor hypothesis test? --> [9] Logistic regression
|   |                                     --> clinical prediction / AI model for use?
|   |                                         +-- developing the model  --> [12] Prediction-model development (Riley)
|   |                                         +-- externally validating  --> [13] External-validation (Riley)
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

## Tests 1–11

Once the test is chosen, read `${CLAUDE_SKILL_DIR}/references/formulas.md` § Test N — the
parameter table with defaults, the effect-size interpretation, the formula, R/Python code and the
methodological reference.

| # | Test | Use when |
|---|------|----------|
| 1 | Diagnostic accuracy — Se/Sp precision | desired 95% CI half-width for sensitivity or specificity |
| 2 | ICC agreement (Bonett 2002) | inter-/intra-rater agreement on continuous measurements (tumor size, angle) |
| 3 | Kappa agreement (Donner & Eliasziw 1992) | agreement on categorical ratings (BI-RADS category, lesion present/absent) |
| 4 | Two-proportion comparison (chi-square) | two independent groups (AI vs conventional detection rate) |
| 5 | McNemar (paired proportions) | paired binary outcomes (two readers on the same cases, before/after) |
| 6 | Independent t-test | means in two independent groups (lesion size, malignant vs benign) |
| 7 | Survival / log-rank (Schoenfeld 1981) | time-to-event between two groups |
| 8 | One-way ANOVA | means across 3+ independent groups |
| 9 | Logistic regression (Peduzzi EPV + Hsieh 1989) | multivariable binary outcome, single-predictor hypothesis test |
| 10 | Non-inferiority / equivalence | new method not worse than standard by more than a pre-specified margin, or equivalent within it |
| 11 | Cox regression EPV | multivariable Cox model — enough events for stable estimates |

- **Test 9**: Peduzzi EPV ≥ 10 is a minimum baseline for a single-predictor hypothesis test only. For
  a clinical prediction / medical-AI model intended for use, EPV-10 is outdated and
  reviewer-vulnerable — use Test 12 (development) / Test 13 (validation). Always report both Peduzzi
  and Hsieh and recommend the larger N.
- **Test 10**: NI alpha is one-sided (typically 0.025); equivalence is TOST. The margin must be clinically
  justified (see `formulas.md` § Margin selection).
- **Test 11**: EPV ensures model stability, not power for a specific HR. If an HR is available, also
  run Test 7 (Schoenfeld) and recommend the larger N.

## Tests 12–17 (specialised designs)

Each has its own reference file (parameters, method, reporting); read it once the test is chosen.

- **Test 12 — Prediction-model development (Riley).** Developing a clinical prediction /
  classification model (including a medical-AI model evaluated as one) for use. EPV-10 does not
  apply: N is the largest satisfying all four Riley criteria (R `pmsampsize`).
- **Test 13 — External validation (Riley).** Validating an existing prediction/AI model: size for the
  CI width of the C-statistic, calibration slope, O:E and (if claimed) net benefit (R
  `pmvalsampsize`); ≥ 100 events and ≥ 100 non-events is only a floor.
  For Tests 12–13 read `${CLAUDE_SKILL_DIR}/references/prediction_model_sample_size.md`.
- **Test 14 — MRMC reader study (Obuchowski–Rockette).** Readers with vs without the AI, or AI
  non-inferior to readers. Test 1 under-sizes it because readers are a random effect: size readers
  `J` × cases from pilot/literature variance components with `RJafroc` / `MRMCaov` / `iMRMC` (do not
  hand-roll the OR algebra) and report the `J × N` power grid. Read
  `${CLAUDE_SKILL_DIR}/references/mrmc_reader_study_sample_size.md`.
- **Test 15 — Segmentation-metric precision (Dice / HD95 / NSD).** The outcome is a per-case score,
  not a proportion: `n ≈ (1.96·SD/δ)²` from the pilot SD of per-case Dice, sized on the worst
  structure; CI by patient-level bootstrap (BCa). Read
  `${CLAUDE_SKILL_DIR}/references/segmentation_metric_sample_size.md`.
- **Test 16 — Between-model comparison.** Model A beats B, C, …: power the paired per-case
  *difference*, not each model's precision; for > 2 models pre-specify one primary contrast or pay the
  family-wise correction; a ranking claim needs multiple seeds. Read
  `${CLAUDE_SKILL_DIR}/references/multi_model_comparison_sample_size.md`.
- **Test 17 — Segmentation usability.** Clinicians can use it (acceptability rate, catastrophic-failure
  bound, edit time): acceptability is a proportion sized per structure class; ratings by m readers are
  nested (`DE ≈ 1 + (m−1)ρ`); bounding failures at ≤ 1% needs ~300 clean cases (rule of three). Read
  `${CLAUDE_SKILL_DIR}/references/segmentation_acceptability_sample_size.md`.

## Out of Scope

Do not compute adaptive trials (group-sequential, sample size re-estimation), cluster-randomized
trials (design effect, ICC-based inflation), Bayesian sample size determination, crossover designs, or
multi-endpoint correction (mention Bonferroni if asked, but do not compute corrected sample sizes).
Say the design is beyond this skill and point to G*Power (free, https://www.psychologie.hhu.de/gpower),
PASS, or a biostatistician.

## Workflow

### Phase 1: Understand the Study

1. Ask the user to describe the study briefly (design, primary outcome, groups).
2. Walk the decision tree to a test, and confirm it with the user before proceeding.

### Phase 2: Collect Parameters

1. Present the selected test's parameter table.
2. For each parameter without a user-provided value, explain it and offer the default.
3. Estimate effect sizes from prior literature (ask for the references) or pilot data; use Cohen's
   conventions only as a last resort, noting that convention-based estimates are less precise.

### Phase 2b: Retrospective Studies

When the dataset already exists, formal power analysis is often impractical. Offer:

- **Fixed extract**: read `${CLAUDE_SKILL_DIR}/references/observational_cohort.md` and report
  event budget / confidence-interval precision instead of forcing a prospective recruitment-style
  power calculation.
- **Experience-based justification** (acceptable for IRB and many journals):
  - *Institution volume*: `total exams in period × prevalence × (1 − exclusion rate) = expected N`.
    Ask for the annual exam volume for the modality, study period, prevalence and exclusion rate. This
    gives a realistic upper bound for N.
  - *Prior studies*: report the N of 3–5 comparable published studies and cite them; the user's N
    should be in the same range or larger.
  - IRB templates for both: `${CLAUDE_SKILL_DIR}/references/justification_examples.md` § Retrospective.

Use a formal calculation (Phase 3) even for a retrospective study when a subset is enrolled
prospectively, the primary analysis tests a hypothesis (not just estimation), the journal's
Instructions for Authors require a power analysis, or the IRB requires it.

### Phase 3: Calculate and Report

1. Generate R code (primary) and Python code (alternative) from the reference formula.
2. Run the R code via Bash; the reported N is the number it prints, not a hand calculation.
3. Present the result in the Output Format below. Cite methodological sources only from
   `formulas.md` or the test's reference file; any other reference needs a DOI/PMID confirmed via
   `/search-lit`, otherwise mark it `[UNVERIFIED - NEEDS MANUAL CHECK]`. Mark an effect size,
   clinical definition or threshold you could not confirm `[VERIFY]`.
4. In a project, save the IRB text as `protocol/sample_size_justification.md` and the scripts as
   `protocol/sample_size_calc.R` / `.py`: `/write-protocol` and `/write-paper` embed that text
   verbatim, so the numbers are never retyped.

### Phase 4: Sensitivity Analysis (Optional)

If a parameter is uncertain or the effect-size estimate is vague, flag it and offer a table of N
across plausible values (e.g., varying effect size, or power from 0.80 to 0.90).

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

The IRB text must state N; name the test and its formula source; give every assumed parameter
(effect size, alpha, power); state the attrition adjustment and final enrollment target; cite the
methodological reference (e.g., "Schoenfeld, 1981"); and use formal, third-person language. Read
`${CLAUDE_SKILL_DIR}/references/justification_examples.md` for per-design exemplars when writing it.
