<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; a task- or
         design-level flaw is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# Survival / Prognostic Model probes (S1–S8)

An 8-probe checklist for time-to-event outcomes and prognostic model development. These probes complement (do not replace) the generic Phase 2 issue checklist and may be co-applied with the SR-MA probes for a meta-analysis of prognostic models.

**S1 — Conditioning / causal framing**:
- Does the manuscript claim a "preoperative" / "screening" / "triage" / "X replaces Y" use case while outcomes are conditioned on the downstream treatment whose value the model is supposed to inform?
- Inputs include post-decision variables (resection margin status, adjuvant chemo/radiotherapy, transplant status) that are unknown at the claimed decision point?
- Non-treatment comparator or causal framework present?
- Conditioning gap → MAJOR candidate. Recommend retrain without leaky variables / add non-treatment arm / reframe intended use.
- **Time origin & survivorship** (incident / transition models): is the at-risk clock started at the correct origin for each incident model, with immortal time (a span in which the event cannot occur, misattributed to one group) and left-truncation / delayed entry handled? Is a "progressor" / transition label conditioned on *surviving to* a later ascertainment (a second scan, a follow-up visit) — a survivorship that needs a landmark time or an explicit intermediate-state model? If the primary analysis is **not** the full cohort (e.g., complete-case while a large fraction is missing) and the complete-case model is the significant one, that selection needs a stated justification and a MAR rationale — an outcome-dependent choice of the analysis set is the S8 concern. Any of these unhandled → MAJOR.
- **Self-confession escalation**: a Methods or Limitations admission that a time-origin, immortal-time, return-conditioning, or selection issue was *"not formally assessed"* (or equivalent) is itself a MAJOR — it names a known bias that was left unaddressed, not a mitigated limitation.

**S2 — Censoring handling in training loss**:
- Cox partial-likelihood loss or DeepSurv-style loss specified? How is censoring handled (right-censoring, interval-censoring, informative censoring by death)?
- If Methods describe a Cox or partial-likelihood loss but do not specify censoring treatment, register as MAJOR (reproducibility).
- Covariate incompleteness in the model fit is part of the same disclosure: is a structural-zero covariate (a never-smoker's pack-years = 0 by definition, not missing) handled as a zero, or dropped under complete-case so the unexposed stratum and the events-per-variable silently collapse? An undisclosed complete-case collapse from a dose/duration covariate is a reproducibility + power issue — adjust on the categorical status and reserve the continuous dose for an exposed-only secondary analysis.

**S3 — Competing risks**:
- 2+ event types (local recurrence + distant metastasis + death, or cause-specific mortality) modeled?
- Cause-specific hazards or Fine-Gray subdistribution hazards used?
- Patient developing one event still at risk for the other (informative censoring by death)?
- If competing-risks structure is ignored and outcomes are treated as independent right-censored events → MAJOR.

**S4 — Cutoff derivation optimism**:
- Cutoffs derived via maximally selected log-rank statistics, AUC-based Youden's J, or similar data-driven methods?
- Hothorn-Lausen correction or equivalent optimism correction applied?
- Was the same cohort used for both model selection (hyperparameter tuning) AND cutoff selection? (Optimism bias)
- Bootstrap optimism estimate or sensitivity analysis on cutoff choice (e.g., ±0.5 SD perturbation)?
- Same-cohort dual use without correction → MAJOR.

**S5 — Comparator horizon alignment**:
- External baseline prognostic nomogram (commonly designed for 5- or 10-year endpoints) applied as the comparator?
- Manuscript's available follow-up duration aligned with that horizon?
- Mismatch → baseline C-index degradation may reflect design-horizon mismatch ≠ intrinsic inferiority. Recommend time-dependent C-index or time-stratified analyses.
- Baseline implementation specified: applied as published, locally recalibrated, or refit as a new Cox model with similar variables?
- Unclear implementation → MAJOR (a refit local model should be described as a clinicopathologic comparator, not a "guideline model").

**S6 — C-index variant + reverse Kaplan-Meier follow-up**:
- Which C-index variant: Harrell's C, Uno's C, time-dependent AUC, IPCW-C?
- Variant appropriate for the censoring distribution and sample size?
- Time-dependent AUC at a clinically anchored horizon (e.g., 2-year, 3-year) reported alongside Harrell's C?
- Reverse Kaplan-Meier median follow-up reported per cohort and per outcome (LR vs DM separately) with censoring date?

**S7 — Calibration beyond discrimination**:
- Calibration plot (intercept / slope) across all cohorts?
- Brier score / Integrated Brier Score (IBS)?
- Decision-curve analysis at clinically relevant probability thresholds?
- For a prognostic model intended to guide surveillance intensity, treatment intensification, or eligibility for adjuvant therapy, discrimination alone is insufficient. If Methods mention calibration but Results/supplement contain no calibration plot or numeric metrics → MAJOR.

**S8 — Estimand provenance**:
- Is the survival estimand stated explicitly and held consistent across Abstract / Methods / Results — event-free survival, cause-specific cumulative incidence, all-cause mortality — and at the subject vs population level? A subdistribution hazard (Fine-Gray) answers a different question than a cause-specific hazard; quoting an sHR for an etiologic claim, or a cause-specific HR for an absolute-risk claim, is an estimand mismatch.
- Is the evaluation horizon (2-/3-/5-year) and the primary model fixed in advance and consistent with the registered/pre-specified primary endpoint, or was the primary endpoint, model, or horizon re-designated after the results were known (outcome-dependent primary selection)?
- Does every derived statistic (E-value, an sHR-vs-cause-specific-HR contrast) trace to the *declared primary* estimand, or is a supporting/non-primary estimate quoted as if it bounded the headline claim?
- Estimand drift — a primary re-designated post-hoc, or a derived statistic computed on a non-primary estimate but presented as primary → MAJOR. Recommend reporting the pre-specified and revised models coequally, disclosing the change, and recomputing any E-value for the primary estimate. (The self-review skill automates the registration ↔ manuscript and E-value arithmetic checks as Phase 2.5f, `scripts/check_claim_artifact.py`.)

**Output template (S4 example)**:
> "The Methods (p. X) state that optimal cutoffs for [outcome] were determined via maximally selected log-rank statistics on the internal validation cohort. Two concerns: (a) Hothorn-Lausen correction is cited but it is unclear whether the corrected p-value was used in the cutoff selection; (b) the internal validation cohort appears to have been used for both model selection and cutoff selection, which is a known source of optimism. I'd suggest reporting bootstrap-based optimism estimates or a sensitivity analysis showing how external performance shifts under ±0.5-SD perturbation of the chosen cutoff."

**Output template (S5 example)**:
> "The chosen baseline nomogram was originally designed and validated for prediction of long-horizon endpoints (5- and 10-year). In this study, median follow-up in [external cohort] is substantially shorter than that horizon, so the comparator's apparent underperformance may partly reflect a horizon mismatch rather than intrinsic inferiority. I'd suggest (a) stating explicitly the time horizon at which both models were evaluated, (b) reporting time-dependent C-indices at a clinically anchored horizon, and (c) clarifying whether the comparator was applied as published, recalibrated locally, or refit as a new Cox model with similar variables."
