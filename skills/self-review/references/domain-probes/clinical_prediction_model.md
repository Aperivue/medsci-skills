<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; a task- or
         design-level flaw is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# Clinical Prediction-Model probes (CP1–CP4)

A 4-probe checklist for **cross-sectional / observational clinical prediction models** — a binary or multinomial outcome predicted from a covariate set, reported under TRIPOD / TRIPOD+AI, usually as a **nested predictor-set comparison** ("does adding marker X to a base model improve prediction of Y?"). This is the diagnostic/prognostic *prediction* counterpart to `survival_prognostic.md` (time-to-event) and complements the `observational_confounding.md` probes (a prediction model still has an analysis unit (O8) and can be over-adjusted (O7)). Route here when the manuscript develops or compares prediction models and reports discrimination (AUC/C-statistic), calibration, or decision-curve / net-benefit analysis.

**CP1 — Apparent vs optimism-corrected performance**:
- Discrimination, **calibration** (slope / intercept / calibration plot), and **decision-curve / net-benefit** all suffer optimism when computed in the same sample used to fit the model. A manuscript that optimism-corrects *only* the C-statistic (bootstrap / cross-validation) but reports calibration and net benefit **in-sample** has corrected one axis and left two apparent.
- An apparent calibration slope near unity (≈ 1.0) does **not** establish out-of-sample calibration — it is the expected in-sample result and says little about transportability.
- Calibration and DCA computed in-sample must be **labelled "apparent"**, or the optimism correction must be extended to them (e.g. bootstrap the calibration slope/intercept and the net-benefit curves). In-sample calibration/DCA described as "well calibrated" / "clinically useful" without the apparent caveat → MAJOR.

**CP2 — The two-null distinction (incremental value vs marginal effect)**:
- A "negative" prediction study conflates two different nulls that have different evidentiary status:
  - **Incremental value negligible** — a *well-powered* statement: ΔAUC ≈ 0, optimism correction does not favour the larger model (and may reverse sign toward the parsimonious one), net benefit does not exceed the base model. This is a genuine "adding X does not improve prediction."
  - **Marginal predictor effect null** — an *underpowered* statement: the predictor's adjusted OR/coefficient has a confidence interval that still admits a clinically relevant effect (e.g. OR up to ~1.7). This is "we could not exclude an effect," not "there is no effect."
- A manuscript that collapses both into a blanket "X did not predict Y" overstates the marginal-effect arm. Flag when a negative conclusion rests on a non-significant marginal OR whose CI admits a relevant effect, without separating it from the (better-powered) incremental-value finding → MAJOR. The honest reframe reports both explicitly.

**CP3 — Events-per-variable (EPV) per nested model**:
- Report EPV for **each** nested model, not just the full cohort. A model with 6 covariates and 60 events (EPV 10) is adequately supported; the same 6 covariates in an age≥60 subgroup with 13 events (EPV ≈ 2) is separation-prone and unstable.
- Penalization (Firth / ridge / LASSO) is justified and should be stated when EPV < 10; subgroup or interaction models with EPV in the low single digits are **separation-affected and must be descriptive-only**, not presented as estimated effects.
- Subgroup/interaction effect estimates from a model with EPV ≲ 5, presented as if reliably estimated, or no EPV disclosure for the nested models → MAJOR (subgroup) / MINOR (EPV simply not reported but adequate).

**CP4 — Net benefit is a model comparison, not a policy endorsement**:
- A decision curve showing the model exceeds treat-all / treat-none across a threshold range is a **model-vs-default** statement about ranking, not evidence that the underlying **imaging / test / screening strategy** should be adopted in practice. Net benefit is computed on the same outcomes and says nothing about cost, downstream harm, or whether the test should be ordered.
- A conclusion that reads decision-curve superiority as an endorsement of the clinical strategy ("supports using X for screening / triage") → MAJOR (scope; cross-link `scope-coherence-gate.md`). Reframe to the model-comparison claim the DCA actually supports.

**CP5 — Intended-use horizon leakage (claim-timepoint vs feature availability)**:
- Read the intended-use horizon off the title / abstract / aim — the adjectives **preoperative, pretreatment, baseline, screening, triage, pre-procedure** assert a decision made *before* some event X. Then check each predictor's **availability timepoint**: any feature that exists only *after* X (post-procedure pathology, treatment-response variables, post-contrast-only measures in a "pre-contrast screening" claim, follow-up-derived labels) is leakage relative to the claimed use, even if it is not train/test leakage.
- This is a **claim × feature-availability mismatch**: the model may be statistically clean yet unusable at the moment its claim targets. Distinct from ordinary data leakage (which is about train/test contamination) — this keys on the decision horizon.
- Flag the specific offending predictor(s) and either narrow the intended-use claim to the horizon at which all inputs exist, or drop the post-horizon features and re-fit. → MAJOR when a post-horizon variable supports a pre-horizon decision claim.

**CP6 — Validation-nomenclature conflation (development step vs test step)**:
- Distinguish the **development** step (including any internal cross-validation or bootstrap optimism correction) from a **held-out / external test** step. Flag phrasing that merges them: "developed with external validation" where a single external set is used *as* development data; "trained and validated on the external cohort"; an "external validation set" that was used for tuning/feature selection.
- Cross-validation and bootstrapping are development-time optimism corrections, **not** external validation; calling them "validation" overclaims out-of-sample evidence. Require an explicit statement of which data trained, which tuned, and which was touched only once for the final estimate.
- → MAJOR when the overclaim props up a generalisability/deployment-readiness conclusion; a clarify-request when the data flow is actually clean but the wording is loose.

**Output template (CP1 / CP2 example)**:
> "Discrimination is bootstrap optimism-corrected, but the calibration slope (0.99) and the net-benefit curves are computed in the development sample and described as 'well calibrated' and 'clinically useful' without the apparent caveat — an in-sample slope near 1.0 is expected and does not establish out-of-sample calibration. I'd suggest labelling the calibration and decision-curve results 'apparent' or extending the optimism correction to them. Relatedly, the Conclusion states that the marker 'did not predict' the outcome, but two distinct results are merged: the incremental-value analysis is well powered (ΔAUC ≈ 0, optimism correction favours the parsimonious model), whereas the marginal adjusted OR has a confidence interval that still admits an effect up to ~1.7 (underpowered). I'd report these separately — 'adding the marker did not improve prediction' is supported; 'the marker has no association' is not."
