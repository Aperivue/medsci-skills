# Phase 2.5e — Confounding Completeness (observational only)

Load-on-demand procedure for self-review Phase 2.5e. Loaded only when the manuscript is
observational and the central claim is an adjusted exposure–outcome association — an RCT,
diagnostic-accuracy, SR/MA, or descriptive review never pays the cost of reading it.

---

For an observational study, the highest-yield reviewer finding is also the most
mechanical, and a prose pass misses it because the manuscript text is internally
consistent: a covariate that was **measured**, is **imbalanced across exposure
groups** in the baseline table, and is **absent from the adjustment set** is
residual confounding by a measured variable. Only a join of the exposure-
stratified Table 1 against the Methods adjustment set exposes it. This is probe
O1 of `references/domain-probes/observational_confounding.md`, run here as a
deterministic gate so the finding lands without the `--panel` cost.

**When to run:** manuscript type is observational (cohort, case-control,
cross-sectional, health-screening registry) and the central claim is an
adjusted exposure–outcome association. Skip for RCTs and descriptive studies.

**Precedent failure pattern:**
> A cross-sectional screening-cohort manuscript reported an adjusted association
> while Table 1 showed uric acid, smoking pack-years, HDL, total cholesterol, and
> HbA1c all significantly imbalanced across the exposure groups — none of which
> were in the age/sex/BMI/hypertension/diabetes adjustment set. The single-pass
> review passed it; only an epidemiology panel reviewer who read the Table 1 CSV
> against the Methods caught the gap. After refitting with extended adjustment the
> primary estimate held, but the manuscript had claimed robustness it had not shown.

**Procedure:**

1. **Locate the exposure-stratified baseline table** as a CSV (e.g.
   `table1_by_<exposure>.csv` from `/analyze-stats`) and the Methods adjustment
   set (the variables after "adjusted for ...").

2. **Run the deterministic gate:**

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/check_confounding_completeness.py" \
     --table1 table1_by_<exposure>.csv \
     --adjusted-list "age, sex, BMI, hypertension, diabetes" \
     --exposure-defining-list "body mass index, waist, fasting glucose, triglycerides, HDL cholesterol" \
     --out qc/confounding_completeness.json --strict
   ```

   It emits a reconciliation table (covariate | imbalance p | SMD | in adjustment
   set? | verdict) and flags each **measured-but-unadjusted imbalanced** covariate
   as an `UNADJUSTED_IMBALANCED` Major candidate. The gate resolves DB column codes
   against a prose adjustment set (alias map), and when the Table 1 has no p / SMD
   column it **computes the SMD from per-stratum "mean ± SD" group columns**
   (`--group-cols A,B`, or auto-detected). When the CSV is unavailable, apply probe
   O1 by hand from the published Table 1.

   **Guideline-defined exposures (MASLD / metabolic syndrome / CKM / sarcopenia /
   frailty):** pass `--exposure-defining-list` (the components of the exposure's own
   diagnostic criteria). Those rows are marked `EXPOSURE_DEFINING_EXEMPT`, **not**
   Major — adjusting for them is over-adjustment (probe O7), not a confounding fix.
   Without the exemption the gate false-positives a Major on every metabolic-criteria
   covariate. The residual-confounding remedy is an extended-adjustment model adding
   only **non-defining prognostic** covariates.

3. **Each `UNADJUSTED_IMBALANCED` covariate is an Anticipated Major Comment**
   (category: A. Study Design & Data Integrity), with the suggested fix: report an
   **extended-adjustment sensitivity model** that adds the omitted covariates and
   states whether the primary estimate is materially unchanged; the original model
   stays primary only if the extended model agrees.

4. **Then apply the rest of the observational probe set** (O2 adjustment-set
   provenance, O3 selection/collider bias, O4 exposure measurement validity, O5
   missing-data mechanism & complete-case collapse, O6 residual-confounding
   E-value, O7 over-adjustment, O8 analysis unit, O9 outcome construct validity,
   O10 overlapping-subset gradient) from
   `references/domain-probes/observational_confounding.md` — these are prose
   probes (O1/O7/O8 are the data-checkable ones), and complement the generic
   Phase 2 categories rather than replacing them.

5. **Extended-adjustment frame discipline.** When the extended-adjustment model
   adds covariates that carry missingness, its analytic n shrinks. Comparing the
   adjusted estimate to the **full-frame** unadjusted estimate confounds adjustment
   with case-concentrated missingness ("adjustment inflated the estimate" when the
   drift is who-was-dropped). The fair anchor is the **unadjusted estimate refit on
   the reduced complete-case frame**; flag any "adjustment changed the estimate"
   claim that compares across different frames, and route the refit to
   `/analyze-stats` (`requires_reanalysis`).

**Adjustment-set matching is fuzzy** (a table row "Smoking, pack-years" vs an
adjustment token "smoking"): read the reconciliation table rather than trusting
the count, and confirm each flagged covariate is a plausible cause of the outcome
(not a mediator or collider, which O2 covers) before raising it.
