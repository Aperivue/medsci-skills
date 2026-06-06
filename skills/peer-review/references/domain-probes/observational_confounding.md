<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; a confounding /
         design-level flaw is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# Observational / Confounding probes (O1–O6)

A 6-probe checklist for observational studies (cohort, case-control, cross-sectional, health-screening registry) where the central claim is an exposure–outcome association estimated by adjustment rather than randomization. These probes complement (do not replace) the generic Phase 2 issue checklist and the STROBE reporting items; they target the gap between what a manuscript *says* it adjusted for and what the exposure-stratified data show. O1 is data-checkable and the highest-yield probe — the self-review skill automates it as a deterministic gate (Phase 2.5e, `scripts/check_confounding_completeness.py`) that reads the exposure-stratified Table 1 and the Methods adjustment set.

**O1 — Confounding completeness (measured-but-unadjusted)**:
- Does the exposure-stratified baseline table (Table 1 by exposure) show covariates that are **significantly imbalanced** across exposure groups (p < 0.05, or a standardized mean difference > 0.1) yet are **absent from the adjustment set**?
- A covariate that was measured, is imbalanced by exposure, and is a plausible cause of the outcome is residual confounding by a *measured* variable — the most preventable kind. Common offenders in metabolic / screening cohorts: smoking pack-years, uric acid, HDL, total cholesterol, HbA1c, eGFR.
- Is the adjustment set justified (DAG, prior literature, or a pre-specified plan), or is it a short default (age/sex/BMI + a few comorbidities) that silently omits imbalanced labs?
- Measured-but-unadjusted imbalanced covariate(s) → MAJOR. Recommend an extended-adjustment sensitivity model that adds the omitted covariates and reports whether the primary estimate is robust; the original model stays primary only if the extended model agrees.

**O2 — Adjustment-set provenance (DAG vs Table-1-stepwise)**:
- Was the adjustment set chosen by a causal structure (DAG / explicit confounder reasoning) or by a data-driven "include if Table 1 p < 0.05" / stepwise rule?
- Data-driven selection risks both directions: **over-adjustment** for mediators or colliders (a variable on the causal path, or a common effect of exposure and outcome, biases the estimate) and **under-adjustment** for a confounder that happens to be balanced in this sample.
- No stated rationale for inclusion/exclusion of each adjustment variable → MAJOR (the same model can be confounded and over-adjusted at once).

**O3 — Selection / collider bias at enrollment**:
- Is the cohort a self-selected or conditioned sample (health-screening attendees, survivors, a registry conditioned on having had the index test) such that enrollment is a collider opening a backdoor path?
- Index-event bias (conditioning on a first event), immortal-time bias (exposure defined over a window during which subjects must survive), and prevalent-user bias addressed?
- Unaddressed selection/collider structure that could generate the reported association → MAJOR; at minimum require an explicit selection-bias paragraph and, where possible, a sensitivity analysis.

**O4 — Exposure measurement validity**:
- Is the exposure a validated/quantitative measure or an unvalidated binary flag (e.g., a single reader's visual call, an ICD code, a self-report) with no in-cohort reliability (κ / ICC) and no severity gradient?
- Structural-zero dose covariates: a dose/duration variable anchored to a categorical exposure (never-smoker → pack-years = 0, never-drinker → grams = 0) must be treated as a structural zero, not missing — misclassification here both mismeasures the exposure and (O5) collapses the analytic sample.
- Non-differential misclassification biases toward the null (an underpowered null is not reassurance); differential misclassification can bias either way. Binary/unvalidated exposure with no reliability estimate → MAJOR (or a prominent limitation with a quantitative bias argument).

**O5 — Missing-data mechanism & complete-case collapse**:
- Is the missing-data mechanism (MCAR / MAR / MNAR) stated and justified, with the missingness fraction per key variable reported (ideally by exposure stratum)?
- Does a dose/duration covariate (pack-years, cessation duration, alcohol grams) entering a complete-case multivariable model collapse n in the unexposed stratum (structural zeros dropped as missing), distorting subgroup estimates? Report n before and after model fitting.
- If multiple imputation is used, are the mechanism assumption, the number of imputations, the imputation model, and a seed reported, and are structural zeros kept out of the imputation? Unjustified MAR for a large missing fraction, or an undisclosed complete-case collapse → MAJOR.

**O6 — Residual confounding quantification (E-value)**:
- Is an E-value (or a comparable quantitative-bias / negative-control analysis) reported for the **primary** estimate and its confidence limit, so a reader can judge how strong an unmeasured confounder would need to be to explain the association?
- An E-value computed for a non-primary, supporting estimate but quoted as if it bounds the primary claim is a provenance error (the E-value must trace to the declared primary contrast).
- For a non-null primary association presented as actionable with no residual-confounding quantification → MAJOR (request an E-value at the point estimate and the bound nearest the null); for a null primary, residual confounding is less load-bearing but power (see the power-aware null check) should be addressed instead.

**Output template (O1 example)**:
> "Table 1 shows that uric acid (p < 0.001), smoking pack-years (p = 0.001), HDL (p < 0.001), total cholesterol (p = 0.010), and HbA1c (p < 0.001) differ significantly across exposure groups, but the multivariable model adjusts only for age, sex, BMI, hypertension, and diabetes. Because these imbalanced laboratory covariates are plausible causes of the outcome, the reported association may carry residual confounding by measured variables. I'd suggest reporting an extended-adjustment sensitivity model that adds the imbalanced covariates and stating whether the primary estimate is materially unchanged; if the extended model attenuates the association, that should be reflected in the Abstract and Conclusions."

**Output template (O5 example)**:
> "The multivariable model appears to be complete-case, and pack-years is included as a continuous covariate. Because never-smokers carry a structural zero rather than a measured value, complete-case deletion can drop a large share of the unexposed stratum (here the analytic n falls from 5,203 to 1,993, with the female subgroup reduced to n ≈ 58), which distorts the subgroup estimates. I'd suggest adjusting for smoking status (never/former/current) rather than pack-years, reserving pack-years for an ever-smoker-restricted secondary analysis, and reporting the missingness fraction by exposure stratum with the MCAR/MAR/MNAR rationale."
