---
name: design-study
description: >
  Study design and validity review for radiology and medical AI research. Identifies analysis unit,
  cohort logic, leakage risks, comparator design, validation strategy, and reporting guideline fit before
  drafting or submission.
triggers: study design, leakage check, cohort design, analysis plan, validation strategy, comparator design, bias check
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Design-Study Skill

## Core Review Questions

Always inspect:

1. The exact research question.
2. The analysis unit: patient, lesion, exam, study, phase, report.
3. The index date or decision point.
4. How inclusion and exclusion criteria are applied.
5. Any information leakage.
6. The reference standard or endpoint definition.
7. A clinically meaningful comparator.
8. The validation strategy.
9. The uncertainty reporting required.
10. The best-fitting reporting guideline.
11. Whether exposure/outcome/covariate **definitions are literature-grounded** or invented ad hoc from the data dictionary. If ad hoc, defer to `/define-variables` before drafting Methods.

---

## Standard Output

```text
## Study Design Review
Question: ...
Study type: ...
Analysis unit: ...
Index date / prediction timepoint: ...

### Strengths
- ...

### Major validity risks
1. ...
2. ...

### Minimal fixes
- ...

### Reporting fit
- Recommended guideline: ...

### Decision
- Ready for analysis / Needs redesign / Drafting can proceed with limitations
```

Cite a reference only with a `/search-lit`-confirmed DOI or PMID; mark any other `[UNVERIFIED - NEEDS MANUAL CHECK]`. Never invent a clinical definition, diagnostic criterion, or guideline recommendation: flag an unconfirmed one `[VERIFY]` and ask the user.

---

## Workflow

### Phase 1: Reconstruct the study

Extract from the protocol, draft, slides, tables, or notes: clinical problem, intended use case,
population, inputs, outputs, outcome definition, and timing of variable availability.

**Gate:** Present the reconstructed study summary (question, analysis unit, intended use) to the
user and confirm it before proceeding — a wrong reconstruction misdirects the entire validity review.

### Phase 2: Check structural validity

Read a reference only when its condition holds:

| File | Read it when |
|---|---|
| `references/dag_adjustment.md` | confounding control needs an explicit adjustment set |
| `references/target_trial_emulation.md` | the design emulates a target trial |
| `references/venue_accept_recipe.md` | a clinical DL / AI-validation study must decide **which venue tier the achievable design can be accepted at, and the one design move that reaches the tier above** (the bridge into `/find-journal`); skip when there is no publication-tier decision |
| `references/combine_models_ablation_design.md` | the model is built by **combining / adapting / fine-tuning existing models** (nnU-Net, TotalSegmentator, SAM/MedSAM, a pretrained backbone) and the comparator must be designed as an ablation; skip for a model trained de novo |
| `references/multi_model_comparison_design.md` | the contribution is **comparing several models / architectures head-to-head** and the comparison must be fair; skip for a single-model study (one model's ablation → the row above; AI-vs-human → `/design-ai-benchmarking`) |
| `references/segmentation_failure_characterization_design.md` | the claim is that a segmentation model is **clinically usable**, not that it scores well; skip when the endpoint is benchmark accuracy (metric choice → `/model-assessment`; abstention / risk–coverage → `/model-assessment`) |

#### A. Analysis unit

Look for mismatches: a patient-level claim from lesion-level analysis; an exam-level split with
patient overlap; phase-level samples treated as independent.

#### B. Leakage

Look for:
- postoperative features used for preoperative prediction
- normalization or thresholding performed before the data split
- repeated exams across train/test
- reader annotations derived from outcome information
- **input-text contamination for NLP/LLM extraction tasks**: if the input includes clinical history,
  indication, impression, prior diagnosis, or referral text, confirm it does not name or strongly imply
  the target label. If it does, the task is information retrieval under label leakage, not phenotype
  inference: redesign the input mask, report a sensitivity analysis excluding those fields, or reframe.
- **construct dependence** (a predictor that is a definitional component of the outcome): (i) an input
  that computes the outcome (fasting insulin and glucose when the outcome is HOMA-IR), or (ii) a
  near-tautological composite of the outcome's defining components (inflated, near-circular
  association). Test: "could this predictor be derived, in whole or part, from the outcome's definition
  or the same measurement?" If yes, exclude it, or keep it only as a labeled calibration probe.

#### F. Time origin & survivorship (incident / transition models)

For any time-to-event or incident/transition design, check before drafting:
- **Time origin per model.** Each incident model starts its at-risk clock at the correct origin.
  Watch for **immortal-time bias** (a span in which the event cannot occur, misattributed to one
  group) and **left-truncation / delayed entry**.
- **Mediator-ascertainment-window survivorship.** A "progressor" / transition label conditional on
  *surviving to* a later ascertainment (a second scan, a follow-up visit) is survivorship-biased; plan
  a landmark time or an explicit intermediate-state (multistate / illness-death) model.
- **Primary-analysis-set selection.** If the primary will not be the full cohort (e.g., complete-case
  while a large fraction is missing), pre-specify the selection justification and a MAR rationale;
  never make the complete-case model primary because it is the significant one (an outcome-dependent
  choice).
- A design that cannot yet answer these should say so — but at review time a Methods/Limitations
  admission that it was *"not formally assessed"* is escalated to MAJOR by the survival probe (S1).

#### C. Reference standard

Check who established ground truth, when, whether blinding was possible, and whether only a subset
had gold-standard verification. Then:
- **Construct ↔ nominal-definition match.** Restate each construct's nominal definition and confirm
  every included case satisfies it. An "incidentaloma" defined as an *indeterminate* finding must not
  include frank malignancy reads; a label that overshoots its definition inflates the cohort and
  breaks the κ.
- **Per-flag reference-standard concordance.** Report concordance *per flag category*, not only overall;
  a construct where most flags (e.g., ~86%) miss the reference standard measures something else.
- **Manuscript definition ↔ `variable_operationalization.md`.** Methods definitions must match the
  `/define-variables` operationalization table verbatim, and a blinded re-classification form must
  quote the analytic protocol's definition verbatim. A paraphrase or "common-sense extension" in the
  form is the documented cause of a low κ that is a *definition mismatch*, not real disagreement.

#### D. Validation

Classify: apparent only, internal split, cross-validation, temporal, external, or multi-center external.

#### E. Reader / expert-elicitation studies

When the study elicits expert ratings — a reader study, an annotation panel, an AI-output evaluation —
read `references/reader_elicitation_design.md` before data collection. The acceptance ceiling of a
perceptual / reader AI study is fixed at design time: no quality of execution lifts a ceiling baked
into the comparator, the estimand, or the reader cohort. For an AI-system-versus-human-expert
benchmark, route to `/design-ai-benchmarking` (arm definition, LLM-as-judge versus human-as-judge
adjudication, structured export schema).

### Phase 3: Clinical framing

Ask whether the comparator and endpoint support the stated claim:
- Is the model better than current practice, or just another model?
- Is the endpoint clinically meaningful?
- Does performance translate to action?
- **incremental value**: if the model/marker is framed as adding value *beyond* / *on top of* /
  *incremental to* an existing tool (a clinical score, a routine test, a baseline model), pre-specify
  the baseline comparator built from the in-routine-use predictors **and** an incremental-value
  metric — ΔC-index / ΔAUC (with a paired CI, e.g. DeLong), categorical or continuous NRI, IDI, or
  decision-curve net benefit. A standalone discrimination number does not support a "beyond X" claim,
  and the nested-model comparison cannot be added post hoc without the baseline model.
- **fine-tuning contribution baseline**: if an NLP/LLM study claims that fine-tuning, LoRA, prompt
  engineering, or a multi-agent wrapper improves extraction/classification, pre-specify a
  same-backbone zero-shot or few-shot comparator on the identical input, output schema, and test
  split; a weaker or unrelated baseline cannot show the adaptation adds value. For imaging:
  - a model built by combining / adapting / fine-tuning existing models → the full ablation ladder
    (un-adapted base, best single component, direct-train vs transfer), per
    `references/combine_models_ablation_design.md`;
  - a **head-to-head comparison of several models** → comparison *fairness*: one frozen
    split/preprocessing through every model, a strong fairly-tuned baseline, a matched (or disclosed)
    compute budget, and a paired delta test, per `references/multi_model_comparison_design.md`;
  - a claim that a segmentation model is **clinically usable** → a pre-specified failure taxonomy, an
    acceptability endpoint with a named judge and adjudication rule, the tail beside the mean, and edit
    effort paired against manual-from-scratch, per
    `references/segmentation_failure_characterization_design.md`. A mean DSC cannot be converted into
    a usability claim after the fact.
- **endpoint↔conclusion scope**: decide up front what *kind* of conclusion the design can support. A
  cross-sectional / single-visit / prevalence design cannot support a prognostic or surveillance claim
  (rescreen interval, disease progression) — that needs longitudinal follow-up. A binary surrogate
  endpoint (present/absent, >0, dichotomized) is risk stratification, not a patient-care directive
  (defer/withhold/initiate therapy). At review time `/self-review` §D + `check_scope_coherence.py` flag
  `CROSS_SECTIONAL_PROGNOSTIC` / `SURROGATE_CARE_DIRECTIVE` against the conclusion.

### Phase 4: Reporting fit

Recommend one primary guideline — `TRIPOD+AI`, `CLAIM`, `STARD`, `STROBE`, `PRISMA`, `CARE`, or
`ARRIVE` — plus journal-specific additions if needed.

---

## Frequent Failure Modes

### Diagnostic AI
No clinically relevant comparator; exam-level instead of patient-level split; unclear reference
standard; AUROC-only reporting without threshold metrics.

### Prognostic modeling
Unclear time zero; immortal time bias; feature timing mismatch; no calibration.

### Retrospective cohort / screening database

- **Time zero misalignment**: cohort entry ≠ follow-up start → immortal time bias.
- Interval-censored outcomes treated as exact → underestimated event times.
- Unacknowledged healthy-volunteer bias → inflated external-validity claims.
- Surveillance bias from unequal follow-up frequency between groups.
- Map each threat explicitly to one of the three bias classes (Hernán/Robins): selection bias (who
  enters), information bias (how measured), confounding (what else differs).
- **Comparative / causal question → emulate a target trial.** For a treatment-vs-treatment,
  screening-vs-no-screening, or drug-A-vs-drug-B question on routinely-collected data, specify the
  seven target-trial components (eligibility, strategies, assignment, **time zero**, outcome, causal
  contrast, analysis plan) before extraction. This prevents immortal-time, prevalent-user, and
  confounding-by-indication bias and turns an association into a defensible causal contrast.
  New-user + active-comparator design, grace-period clone-censor-weight, and negative controls are in
  `references/target_trial_emulation.md`.
- **Confounding completeness**: pre-specify the adjustment set from a DAG (not a Table-1 p < 0.05
  rule), and plan an extended-adjustment sensitivity model to show whether any measured covariate that
  turns out imbalanced by exposure but lies outside the adjustment set leaves the primary estimate
  robust. Pre-screen the proposed covariates with `scripts/adjustment_set_helper.py` (flags mediator /
  collider / descendant adjustment and omitted confounders, and proposes a candidate backdoor set),
  then derive the **minimal** sufficient set with dagitty — see `references/dag_adjustment.md`. At
  review time `/self-review` Phase 2.5e and the O-probes in `observational_confounding.md` (O1–O18)
  check this against Table 1 — including O7 over-adjustment, O10 overlapping-subset-gradient
  discipline, O11 design-based weighting for complex-survey data, O12 data-driven-threshold mining,
  O13 (a cross-sectional mediation claim cannot order X→M→Y), and O14 (a synergy/joint-effect claim
  needs the additive interaction scale — RERI/AP/S — not a multiplicative-only test).

### Multimodal LLM / report generation
No clear rubric for clinical correctness; benchmark labels derived from noisy reports without
adjudication; unsupported claims about safety or workflow benefit; input text containing the target
label or diagnosis being predicted; no same-backbone zero-shot/few-shot baseline for a fine-tuning or
prompt-engineering claim.

### Imaging meta-analysis
Overlapping cohorts; paired modalities analyzed as independent; heterogeneity metrics missing;
zero-cell handling unspecified.

---

## Minimal-Fix Principle

Recommend the smallest feasible repair first: clarify the claim, narrow the target population, add a
limitation statement, add a clinically relevant baseline, re-run one key sensitivity analysis, or
redefine the endpoint more explicitly. Escalate to redesign only when the central claim is not
defensible otherwise.

---

## Handoff Rules

- route to `analyze-stats` when the design is basically sound but analysis details need refinement
- route to `check-reporting` after the design is locked
- route to `self-review` when the user wants a pre-submission quality check on their own manuscript
- route back to `write-paper` only after the main validity risks are documented

This skill does not compute statistics, draft full manuscript prose, resolve raw data-engineering
issues, or replace a full peer review when journal-facing tone is required.
