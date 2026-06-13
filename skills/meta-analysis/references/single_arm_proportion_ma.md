# Single-Arm Proportion Meta-Analysis — Conventions

Pooling a single proportion (event rate) across single-arm studies — common when randomized comparators are scarce (interventional radiology, surgery, device/technique case series). These conventions prevent the failure modes a methodological reviewer reliably flags. They are distinct from DTA (sensitivity/specificity) pooling; see also `dta_meta_analysis.R`.

## 1. Model: GLMM logit, not inverse-variance with continuity correction

Pool with a **random-effects generalized linear mixed model (binomial-normal, logit link)** — e.g. R `meta::metaprop(..., method = "GLMM", sm = "PLOGIT")`. The GLMM uses the exact binomial likelihood and **handles zero-event studies natively — do NOT add a 0.5 continuity correction** (continuity corrections bias proportion estimates and are unnecessary under the GLMM). Inverse-variance pooling of raw or arcsine-transformed proportions with `incr = 0.5` is an older default to avoid here. Report between-study variance τ² on the **logit scale** and a **95% prediction interval** for every pool.

## 2. Lead with dispersion, not a single pooled point estimate

Thin, heterogeneous single-arm evidence does not yield a generalizable benchmark. Foreground:
- the **per-study range** and the **95% prediction interval** (often very wide, e.g. a pooled 18% with a 3–59% PI), and
- frame pooled values as **descriptive summaries of the existing evidence base**, not as effect estimates or as a guidance/technique "advantage".
Do not let an Abstract/Key-Points headline a precise pooled percentage that the body then disclaims.

## 3. Boundary-degenerate pools (near 0% or 100%)

When most studies sit at the proportion boundary (e.g. 5/6 studies at 100%), the GLMM is near-degenerate: the **Q-based I² can read 0% while the logit-scale τ² and the prediction interval are large** — these are not contradictory, they reflect boundary estimation. Also, Hartung-Knapp intervals are unstable at small k and can give an uninformatively wide CI (e.g. 69–100%). Handling:
- present such an outcome **descriptively** (e.g. "five of six studies reported 100%; one reported 97.5%"),
- keep the pooled value only "for completeness" with an explicit footnote explaining the I²=0 vs τ²>0 artifact,
- do not call the heterogeneity "negligible" on the strength of I²=0 alone.

## 4. Report the crude rate alongside the pooled estimate

With sparse events the logit-scale random-effects estimate **shrinks below the crude rate** (Σevents/Σdenominator). Report both and say so (e.g. "crude 3.3%; pooled 2.2%, the pooled value lower because of logit-scale shrinkage with sparse events"), so a reviewer does not read pooled < crude as an error.

## 5. Symmetric handling of zero-event studies

Decide one inclusion rule for an outcome and apply it **symmetrically**. The common defect: including narrative-zero studies (a study that says "no major complications" with a borrowed denominator) while **excluding a study that explicitly reported 0/N** — this drops zeros asymmetrically and inflates the rate. Default: **include every study that reported the outcome's status, zero or not**; exclude only studies whose arm-specific count is genuinely not separable from a comparator. State borrowed denominators explicitly.

## 6. Pre-specify the event definition and verify it against each source

For composite/graded outcomes (e.g. "major complication"), state an **a-priori definition** (e.g. SIR major / CTCAE Grade ≥3) in Methods, and **verify each study's count against that study's own grading table in the primary PDF** — do not trust a structured-extraction cell that disagrees with the paper's narrative. A single high-contributing study can drive the pooled estimate, so its grading must be source-confirmed. When a structured value and an extraction note conflict, the primary source decides.

## 7. Publication-bias / small-study tests are invalid for proportions

The standard error of a proportion is a deterministic function of the proportion, so funnel-plot asymmetry and Egger/Begg regression are **uninterpretable for pooled proportions** and must not be reported as evidence of (no) publication bias. If shown at all, a contour-enhanced funnel plot is descriptive only, with a caption stating it cannot infer small-study effects. Do not write "no publication bias was found."

## 8. Unit of analysis

Single-arm series mix per-patient, per-lesion, and per-session denominators. Use the most granular available unit per outcome, **disclose the mixing**, and treat the pooled CI as a descriptive-precision statement (study-level independence assumed), not an inferential interval. Where feasible, a within-study single-unit sensitivity analysis strengthens the key efficacy outcome.

## 9. Certainty of evidence

Formal GRADE is not standardized for single-arm proportion syntheses; use a **GRADE-informed** narrative — start at low certainty (non-comparative observational), rate down for inconsistency and imprecision (wide PIs, I²) — and **report the per-outcome rating** (commonly "very low"), not merely a statement that certainty "was not assessed".

## 10. Risk of bias

Use an instrument matched to the design (e.g. JBI Critical Appraisal Checklist for case series; ROBINS-I for the non-randomized comparative subset). When two instruments are used, **report agreement per instrument** (do not pool a single κ across incompatible rating scales), and get the item denominator right (Σ items per instrument).

## Reviewer-facing summary

A defensible single-arm proportion MA: pre-registered; GLMM logit with τ² + prediction intervals; crude reported alongside pooled; symmetric zero handling; source-verified event definitions; no Egger on proportions; descriptive (non-comparative) framing; per-outcome GRADE-informed certainty; comprehensive search with honest disclosure of database scope.
