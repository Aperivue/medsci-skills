<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; a task- or
         design-level flaw is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# AI / ML overclaiming probes (AO0–AO6)

A 5-probe checklist (AO1–AO5, with AO0 as a gate) for medical-AI/ML primary studies (diagnostic, prognostic, triage, detection) where the **conclusion's reach exceeds the evidence**. These probes complement (do not replace) the generic Phase 2 issue checklist and the signature "Overclaiming vs evidence level" check. The aim is to keep a framing-level over-reach from passing as a wording nitpick: a paper can report sound metrics yet draw a clinical claim — generalizable, outperforms clinicians, deployment-ready — that the design does not support, and that claim is what a reader carries away. AO1–AO4 target over-reach in the *claim sentences*; AO5 targets over-reach baked into the *reported metric itself* (an optimistically- or unreproducibly-reported number that makes the result look stronger than a faithful estimate). Run AO0 first.

**AO0 — Locate the strongest claim, then its support (run before AO1; gates any over-reach finding)**:
- Identify the load-bearing claims in the Title, Abstract, and Conclusion (the sentences a reader quotes). For each, find the specific evidence cited (which dataset, which comparison, which metric + uncertainty).
- An over-reach finding is a **lead until the claim and its support are read together against the manuscript** — do not strawman a stray adjective. Escalate only when a headline claim genuinely outruns the cited evidence.
- If the claim is already appropriately hedged to the evidence, record "claim matched to evidence" and move on.

**AO1 — Generalizability claimed from limited external validation**:
- Does the Abstract/Conclusion assert the model "generalizes," is "transferable/robust across settings," or is suitable for broad populations, while external validation is a single site / single scanner-vendor / single source (or absent)?
- Sub-check: is the external set demographically narrow (single ethnicity, single sex-dominant, narrow age) relative to the population the claim names?
- If the generalizability claim outruns the external evidence → recommend softening to the evidence ("validated at one external site") and moving multi-setting generalizability to a stated limitation + next step. MAJOR candidate when it is a headline claim; MINOR when it is a single qualifier in the Discussion.

**AO2 — Superiority language against overlapping or under-powered comparison**:
- Flag "outperforms", "superior to", "beats", "can replace [clinician/radiologist]" when (a) the model vs comparator 95% CIs overlap, (b) no test of the *difference* is reported (two separate AUCs are not a comparison), or (c) the comparison rests on a small test set / few readers.
- Ask for the difference in the metric with its CI and a paired test of that difference, not two standalone estimates.
- If the difference is not statistically supported → recommend reframing from "outperforms" to "comparable to" (still a meaningful result). MAJOR when a superiority/replacement claim is the headline; otherwise MINOR.

**AO3 — Comparison-frame mismatch (model task ≠ human task)**:
- When a model-vs-clinician comparison drives a claim, verify the two performed the **same task on the same inputs under the same constraints**: same images/inputs available, same time budget, same question asked, same decision point.
- Common mismatches: the model sees a curated single view while readers see the full study; readers are timed or work from a different modality; the "reader" benchmark is a literature value on a different cohort.
- A mismatch makes "outperforms clinicians" non-interpretable as a clinical claim → ask the authors to state exactly which task the comparison establishes, or to align the conditions. MAJOR candidate when it underpins a headline.

**AO4 — Deployment / clinical-readiness claim from retrospective internal evidence**:
- Flag "ready for clinical deployment", "can be used to triage/guide treatment", "will reduce workload/cost", or a recommended decision threshold, when the evidence is a retrospective, internally-split (or even external but observational) accuracy study with no prospective, silent-trial, or decision-impact data and (often) no calibration or decision-curve analysis.
- Discrimination on retrospective data does not establish that acting on the model helps patients; a probability that drives a decision must also be calibrated, and net benefit must be shown.
- Recommend reframing deployment/utility language to "supports further prospective evaluation", and (where a threshold is proposed) adding calibration + decision-curve evidence. MAJOR when a deployment/care-directive claim is made; MINOR when only a hedged "potential utility" sentence.

**AO5 — Optimistic / non-reproducible performance reporting (the metric overstates the evidence)**:
- Triggered when a primary AI/ML study reports discrimination or accuracy as a headline result. Check how the number was produced before taking it at face value.
- (a) **Best-fold vs cross-fold**: is the headline metric the single best cross-validation fold (or one favorable train/test split) rather than the mean across folds with its SD or a 95% CI? Best-fold figures are upward-biased; ask for the cross-fold mean ± SD (or CI).
- (b) **Operating point**: are sensitivity/specificity/F1 reported without stating the decision threshold and how it was chosen? A threshold tuned on the test set inflates the metric; ask for the operating point and that it was selected on training folds only (e.g., Youden's J on the training data). This probe is about whether the reported number is reproducible/optimistic, not whether the threshold is clinically deployable (that is AO4).
- (c) **Prevalence-representative metrics**: was training/evaluation done on an artificially balanced set while the real prevalence is much lower, with accuracy quoted as the headline? Accuracy — and PPV/NPV — on a re-balanced set do not transfer to the deployment base rate (PPV/NPV are prevalence-dependent). Ask for the evaluation class distribution, threshold-independent discrimination (AUROC, and AUPRC under imbalance, with CIs), sensitivity / false-negative rate at the stated threshold, and PPV / NPV estimated on a prevalence-representative holdout (or modelled for the target clinical prevalence, with uncertainty).
- (d) **Code-vs-claims fidelity**: where code is released, does the described tuning/metric match it? Common mismatches: a claimed hyperparameter search the code does not run; a metric (e.g., specificity) attributed to a library function that does not compute it. A confirmed mismatch is an integrity/reproducibility flag — verify against the released code before asserting it.
- Severity: MAJOR when the load-bearing performance claim rests on a best-fold number, an unstated/test-tuned threshold, a rebalanced-accuracy headline, or a code-vs-claims mismatch (the reported result is optimistic or not reproducible); MINOR when cross-validation was sound and only the cross-fold summary, the operating point, or a class-aware metric is missing from the write-up.

**AO6 — Arm-defining task vs deployment workflow (construct validity of the evaluation)**:
- Distinct from AO3 (model-task ≠ human-task *framing*) and from scope-coherence (claim ≠ result): AO6 asks whether the **task that defines the study arms mirrors the deployment workflow the claim targets**, or an artificial handicap/selection. Two recurrent failure modes:
  - (a) **Handicapped arm** — the AI (or comparator) arm is operationalized in a way the real workflow never imposes: e.g., AI read in pure blind interpretation while the actual deployment provides clinical context / priors / the report, so the evaluation measures a task no one performs.
  - (b) **Success-conditioned selection** — the arm or the analyzed subset is gated on an AI-success condition (cases where the model produced an output, segmentations that "passed", studies the pipeline did not fail on), so the comparison is conditioned on the very thing under test.
- This is a **design/paradigm-level** defect: the operationalized task, not the prose, is mis-specified, so it cannot be fixed by rewording the claim — escalate **past an ordinary Major** (editors read it as a Reject-grade construct-validity failure; a panel that files it as a fixable Major under-rates it). The fix is a re-designed arm whose task matches the intended deployment workflow and an unconditioned (consecutive / intention-to-diagnose) analysis set.

## Decision-impact / early-deployment probes (DECIDE-AI axis, DI1–DI5)

Co-apply when a study claims **clinical utility, deployment, or decision impact** of an AI system, or *is* an early-stage live clinical evaluation. The reporting axis is then DECIDE-AI (early-stage clinical evaluation of AI decision-support); these probes check that a utility/deployment claim rests on real-use evidence, not retrospective accuracy. They sharpen AO4 for the deployment-evaluation case.

**DI1 — Live/prospective evidence vs retrospective accuracy**:
- Is there any **prospective, in-workflow (silent-trial / shadow-deployment / live)** evidence of how the system performs and is used, or is the deployment/utility claim built only on a retrospective, internally-split accuracy study? A deployment claim from retrospective discrimination alone → MAJOR (reframe to "supports prospective evaluation").

**DI2 — Intended use + deployment pathway within early-stage limits**:
- Is the **intended use** (condition, decision supported, users, setting) stated, and is the claim kept within what an early-stage evaluation can show? Over-reach to "ready for routine clinical use" from a developmental/exploratory study → MAJOR.

**DI3 — Decision threshold + calibration/utility**:
- If a **decision threshold** or care directive is proposed, is it justified, with the predicted probabilities **calibrated** and **net benefit** (decision-curve) shown — not discrimination alone? An unjustified threshold or missing calibration/utility for a probability that drives a decision → MAJOR.

**DI4 — Workflow integration + human–computer interaction**:
- Does the study report **how the system was used in the real workflow** — user adherence/exposure, **human–computer agreement/override rates**, **usability and learning curve** (human factors)? A utility claim with no real-use interaction data is the central DECIDE-AI gap → MAJOR/PARTIAL.

**DI5 — Safety, error capture, and subgroup safety**:
- Were **significant errors/malfunctions pre-defined and captured**, the **safety profile** reported and discussed, and performance/safety examined across **relevant subgroups** (fairness)? Absent pre-defined error capture or subgroup-safety assessment where the claim is clinical deployment → MAJOR.

**Output template (AO1 example)**:
> "The Conclusion states the model 'generalizes across institutions,' but external validation appears limited to a single site ([Methods, External validation]). I'd suggest softening this to the evidence — e.g., 'validated at one external site' — and framing multi-institution generalizability as a stated limitation and a next step. If a broader claim is intended, an external set spanning multiple sites/vendors would be needed to support it."

**Output template (AO2 / AO3 example)**:
> "The 'outperforms radiologists' claim rests on a comparison whose 95% CIs for model and reader [metric] overlap ([Figure/Table]), and no test of the difference is reported; the reader task also differs from the model's in [inputs/time] ([Methods/Table]). I'd suggest (a) reporting the difference in [metric] with its CI and a paired test rather than two separate estimates, and (b) stating explicitly which clinical task the comparison establishes. If the difference is not statistically supported, reframing from 'outperforms' to 'comparable to' would be both defensible and still a meaningful result."

**Output template (AO5 example)**:
> "Table 2 appears to report the single best cross-validation fold; because best-fold figures are optimistically biased, I'd suggest reporting the mean across folds with its SD (or a 95% CI). Relatedly, the sensitivity/specificity depend on a classification threshold I could not find stated — reporting the operating point and how it was chosen (e.g., Youden's J on the training folds only, to avoid tuning on the test data) would make these numbers reproducible. Finally, since the training set was balanced to 1:1 while the clinical prevalence is much lower, accuracy (and PPV/NPV) on a re-balanced set may not reflect performance at the true base rate; stating the evaluation class distribution and adding AUROC/AUPRC with CIs alongside sensitivity/FNR at the stated threshold, with PPV/NPV on a prevalence-representative holdout, would make the clinical cost of a miss visible."

**Discipline — leads vs findings (applies to AO0–AO5)**:
- A claim-vs-evidence mismatch surfaced by a quick scan is a **lead, not a finding, until the claim sentence and its cited support are read together** against the manuscript. Do not escalate a hedged Discussion qualifier as if it were a headline.
- Anchor every over-reach comment to the exact claim location and the exact evidence (dataset, comparison, metric + CI). A comment that names the location and the gap is actionable; "the authors overclaim" is not.
- Keep severity tied to *where* the claim sits and *what it drives*: a headline/clinical-action claim that outruns the design is design-/framing-level (MAJOR, often Major #1); a stray adjective is MINOR.
