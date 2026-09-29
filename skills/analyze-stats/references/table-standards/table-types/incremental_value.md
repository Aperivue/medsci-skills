# Table: Incremental (Added) Value Beyond a Baseline Model

The table standard for any "the new marker/model adds value **beyond** an established baseline"
claim — a new biomarker on top of a clinical score, an AI model on top of a radiologist or a
guideline nomogram. Discrimination alone (a higher AUROC) is not sufficient evidence of added
value; report the paired change in discrimination **with** a clinical-utility metric (and
reclassification, if used, reported as below), all on the **same patients** and the same held-out
data.

## Reporting Guidelines
- **TRIPOD / TRIPOD+AI**: prediction-model development/validation, model comparison and performance
- **TRIPOD-LLM**: when the augmenting model is an LLM
- **CLAIM**: AI in medical imaging
- **STARD / STARD-AI**: when the added value is framed as diagnostic accuracy

## Standard Structure

```
Table 4. Incremental Value of [New Predictor/Model] Added to [Baseline] (external test set, n = ___, events = ___)

Model                         C-statistic (95% CI)   ΔC (95% CI)         NRI events / non-events (95% CI)   IDI (95% CI)      ΔNet benefit @ threshold (95% CI)
Baseline ([predictors])       0.74 (0.70-0.78)       —  (reference)       —                                  —                 — (reference)
Baseline + [new predictor]    0.81 (0.77-0.85)       0.07 (0.04-0.10)     ___ / ___                          0.045 (0.02-0.07) +0.021 (___-___) @ 10%

Added-value test: likelihood-ratio test of [new predictor] in the development cohort
(n = ___, events = ___), χ²(df) = ___, P = ___. ΔC is the size of the gain on these held-out
patients with a paired 95% CI (DeLong or bootstrap) — an estimate, not a second test. NRI/IDI
from the paired risk estimates, NRI given separately for events and non-events. Net benefit from
decision-curve analysis at the prespecified threshold; full curve in Figure X.
```

## Rules
- **Nested / same-patient comparison**: the augmented model must be the baseline **plus** the new
  term, evaluated on the **identical** held-out patients — not two models on different cohorts.
- **Baseline named and justified**: state exactly what the baseline contains (clinical score,
  guideline nomogram, prior model) and that it was applied as published / recalibrated / refit.
- **One test for "adds anything", then an estimate for "how much"**: for a prespecified term added
  to a regression baseline, whether it adds information is tested through its coefficient in the
  full model. That is the **likelihood-ratio** (or Wald) test in the development data, with both
  models fitted on the same observations. ΔC-statistic is then reported as the **size** of the
  gain, with a paired 95% CI, not as a second significance test. A DeLong test of ΔAUC between
  nested models **fitted and evaluated on the same data** is the wrong test for added value. When
  the new term has no association, the statistic's null distribution is not normal, and the test
  is conservative for small and moderate effects (Demler, Pencina & D'Agostino, *Stat Med* 2012).
  In simulation its size fell below 0.006, with much lower power than the likelihood-ratio and
  Wald tests (Vickers, Cronin & Begg, *BMC Med Res Methodol* 2011). A marker with a modest real
  association can therefore "fail" it. On held-out data, comparing two models **frozen before
  evaluation** is what the DeLong method was built for: correlated ROC curves of given scores on
  the same patients. In simulation it held its nominal type I error there (Chen et al., *BMC Med
  Res Methodol* 2013). It then answers whether those two scores differ in AUC, not whether the
  new term carries information. When the augmented model is not a regression with a separable
  prespecified term, such as a retrained network or a data-selected predictor set, that held-out
  paired comparison is the evidence, not a coefficient test. Never compare two independent AUROCs
  by eye, side by side. A tiny ΔC with a wide CI is not evidence of added discrimination, though on
  its own it does not rule out a gain in calibration or net benefit.
- **Reclassification, if reported, reported correctly**: give NRI **separately for events and
  non-events**. An overall NRI can be positive from one side alone, and which side moved decides
  whether the change matters clinically: more events caught, or fewer non-events flagged. With two
  risk categories those components are simply the changes in sensitivity and specificity, so report
  them under those names. **Do not present the category-free (continuous) NRI as evidence of added
  value**: it can overstate a marker's incremental value even in independent validation data. With
  three or more categories the same review recommends against NRI altogether (Kerr et al.,
  *Epidemiology* 2014). If a categorical NRI is used anyway, prespecify and justify the categories
  (post-hoc categories inflate NRI), and bootstrap its CI rather than using published variance
  formulas. IDI, if reported, goes alongside with its CI.
- **Clinical utility, not just statistics**: include **net benefit** (decision-curve analysis) at a
  prespecified, clinically justified threshold (and reference the full curve —
  `make-figures` `exemplar_plots/decision_curve.md`). The improvement in net benefit is the
  preferred single-number summary of the increment (Kerr et al. 2014). Reclassification metrics
  without utility can mislead.
- **Calibration first**: NRI/IDI/net benefit all depend on predicted probabilities, so assess both
  models' calibration on the test data before computing them (pair with the calibration plot). If
  a model has to be recalibrated, do it on data other than the test set. Recalibrating on the test
  outcomes and then evaluating on them is no longer a validation of a frozen model.
- **One decimal discipline / CIs everywhere**: every estimate carries a 95% CI; bootstrap CIs state
  the number of replicates; the same bootstrap resamples are reused across paired metrics.

## Common pitfalls (flag in review)
- Reporting only ΔAUROC and calling it "added value" (no clinical-utility metric).
- NRI with post-hoc categories, or only the overall NRI without event/non-event split.
- A DeLong test of ΔAUC used as the significance test for an added predictor in nested models
  fitted and evaluated on the same data. It is conservative and underpowered there, so test the
  coefficient.
- A continuous (category-free) NRI offered as the evidence of added value.
- New vs baseline AUROCs from different cohorts or different n (not a paired comparison).
- Net benefit asserted in prose with no decision curve and no stated threshold.

## Code (illustrative)

```r
# 1) Does the new term add anything? One test: likelihood ratio, in the development data.
#    Fit both models on the same complete cases, or the comparison is not nested.
dev <- dev[complete.cases(dev[, c("y", "x1", "x2", "marker")]), ]
fit_base <- glm(y ~ x1 + x2,          family = binomial, data = dev)
fit_full <- glm(y ~ x1 + x2 + marker, family = binomial, data = dev)
anova(fit_base, fit_full, test = "LRT")        # Cox: anova(cox_base, cox_full)
# 2) How much? Paired ΔAUC with its CI on the held-out patients -- an estimate, not a 2nd test.
#    Fix the outcome levels and direction so roc() cannot flip a score on the test data.
library(pROC)
roc_base <- roc(y_test, p_baseline, levels = c(0, 1), direction = "<")
roc_full <- roc(y_test, p_full,     levels = c(0, 1), direction = "<")
roc.test(roc_full, roc_base, method = "delong", paired = TRUE)$conf.int   # CI of full - base
# NRI (events / non-events separately) and IDI from the paired risk vectors p_baseline, p_full;
# net benefit via the decision-curve template (analyze-stats references/templates/dca_plot.R).
```

```python
# 1) One test for "adds anything": likelihood ratio of the nested fits (development data),
#    both fitted on the same observations.
from scipy.stats import chi2
lr = 2 * (fit_full.llf - fit_base.llf)          # statsmodels Logit / GLM results
p = chi2.sf(lr, fit_full.df_model - fit_base.df_model)
# 2) ΔAUC on the SAME held-out patients with a paired bootstrap CI (an estimate, not a 2nd test);
# reuse one set of resamples across ΔAUC, NRI, IDI and net benefit so the CIs are consistent.
```
