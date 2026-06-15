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

## Purpose

This skill pressure-tests whether a study is answerable, interpretable, and defensible before large amounts of drafting or analysis work accumulate.

Use it when:
- a study question is known but the analysis plan is still fluid
- the user wants a methods sanity check
- a manuscript feels vulnerable to reviewer criticism
- a peer review requires explicit methodological diagnosis

---

## Communication Rules

- Communicate with the user in their preferred language.
- Use English for statistical, radiologic, and reporting-guideline terminology.
- Be direct about validity risks, but always propose the smallest feasible fix first.

---

## Core Review Questions

Always inspect these dimensions:

1. What is the exact research question?
2. What is the analysis unit: patient, lesion, exam, study, phase, report?
3. What is the index date or decision point?
4. How are inclusion and exclusion criteria applied?
5. Is there any information leakage?
6. What is the reference standard or endpoint definition?
7. What comparator is clinically meaningful?
8. What validation strategy is used?
9. What uncertainty reporting is required?
10. Which reporting guideline best fits?
11. Are exposure/outcome/covariate **definitions literature-grounded**, or invented ad-hoc from the data dictionary? If ad-hoc, defer to `/define-variables` before drafting Methods.

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

---

## Workflow

### Phase 1: Reconstruct the study

Extract from protocol, draft, slides, tables, or notes:
- clinical problem
- intended use case
- population
- inputs
- outputs
- outcome definition
- timing of variable availability

**Gate:** Present the reconstructed study summary (question, analysis unit, intended use)
to the user. Confirm before proceeding — if the reconstruction is wrong, the entire
validity review will be misdirected.

### Phase 2: Check structural validity

#### A. Analysis unit

Look for mismatches such as:
- patient-level claim from lesion-level analysis
- exam-level split with patient overlap
- phase-level samples treated as independent

#### B. Leakage

Look for:
- postoperative features used for preoperative prediction
- normalization or thresholding performed before data split
- repeated exams across train/test
- reader annotations derived from outcome information
- **input-text contamination for NLP/LLM extraction tasks**: if the model input includes report
  sections such as clinical history, indication, impression, prior diagnosis, or referral text, confirm
  that those fields do not literally name or strongly imply the target label. If the target is already
  present in the supplied text, the task is information retrieval under label leakage, not phenotype
  inference; redesign the input mask, report a sensitivity analysis excluding leaky fields, or reframe the
  claim.
- **construct dependence** (a predictor that is a definitional component of the outcome). Two cases:
  (i) *mathematical definition* — an input that computes the outcome (when the outcome is HOMA-IR =
  f(fasting insulin, fasting glucose), those two inputs are not independent predictors); (ii)
  *near-tautological composite* — a ratio or score built from the outcome's defining components, which
  shows an inflated, near-circular association. Test: "could this predictor be derived, in whole or
  part, from the outcome's definition or the same measurement?" If yes, exclude it, or retain it only
  as a labeled calibration probe rather than a reported discovery.

#### F. Time origin & survivorship (incident / transition models)

For any time-to-event or incident/transition design, check before drafting:
- **Time origin per model.** Each incident model starts its at-risk clock at the correct origin. Watch for **immortal-time bias** (a span in which the event cannot occur, misattributed to one group) and **left-truncation / delayed entry** (subjects entering the risk set after the origin).
- **Mediator-ascertainment-window survivorship.** A "progressor" / transition label that is conditional on *surviving to* a later ascertainment (a second scan, a follow-up visit) is survivorship-biased; plan a landmark time or an explicit intermediate-state (multistate / illness-death) model.
- **Primary-analysis-set selection.** If the primary will not be the full cohort (e.g., complete-case while a large fraction is missing), pre-specify the selection justification and a MAR rationale; do not let the complete-case model become primary because it is the significant one (an outcome-dependent choice).
- A design that cannot yet answer these should say so honestly — but note that at review time a Methods/Limitations admission that the issue was *"not formally assessed"* is escalated to a MAJOR by the survival probe (S1), not waved through as a limitation.

#### C. Reference standard

Check:
- who established ground truth
- when it was established
- whether blinding was possible
- whether only a subset had gold standard verification
- **Construct ↔ nominal-definition match.** Does the exposure/finding *construct* stay inside its stated definition, or does it quietly exceed it? An "incidentaloma" defined as an *indeterminate* finding must not include frank malignancy reads; a label that overshoots its definition inflates the apparent cohort and breaks the κ. For each construct, restate the nominal definition and confirm every included case satisfies it.
- **Per-flag reference-standard concordance.** When the index finding is flagged against a reference standard, report the concordance *per flag category* (not just overall). A construct where a large fraction of flags do not match the reference standard (e.g., ~86% non-match) is measuring something other than the named construct.
- **Manuscript definition ↔ `variable_operationalization.md`.** The variable definitions written in Methods must match the operationalization table verbatim (dictionary-first). A blinded re-classification form must quote the analytic protocol's definition verbatim — paraphrase / "common-sense extension" in the form (but not the Methods) is the documented cause of a low κ that is a *definition mismatch*, not real disagreement. Cross-check with `/define-variables` output before drafting.

#### D. Validation

Classify:
- apparent only
- internal split
- cross-validation
- temporal validation
- external validation
- multi-center external validation

#### E. Reader / Expert-Elicitation Study Design

When the study elicits expert ratings (reader study, annotation panel, AI-output evaluation), check
the following before data collection.

**Rubric design**
- **Decouple the axes.** Each rated dimension should measure one construct. Keep "is the finding
  valid/correct" separate from "is it novel", "is it feasible to measure", "does it add value over
  current tools", and "would it change action". A candidate can be high-validity yet low-added-value
  ("real but redundant"); a single blended score hides this.
- **Anchor every Likert point** with a short verbal descriptor; pilot the anchors with at least one
  reviewer before locking.
- **Pre-specify discriminant validity**: hypothesize which dimensions should correlate vs be
  orthogonal, then report the full inter-dimension correlation matrix to confirm the rubric measures
  distinct constructs.

**Calibration probes (planted control items)**
Insert a small number of deliberate control items, blinded and randomized across raters (record who
received which, e.g. a `probe_arm` flag), to (i) anchor the scale, (ii) measure rater drift and
fatigue, and (iii) audit the rubric and pipeline itself. Four useful flavors:
- **Positive control / "too-good" item** — a known-strong or near-tautological item; tests whether
  raters equate "largest effect" with "best", and whether an upstream construct-independence gate works.
- **Known-bad negative control** — an engineered defect (fabricated reference, missing key statistic);
  expected to score low.
- **Instability item** — an estimate that reverses or fails to replicate on holdout; tests caveat handling.
- **Mechanism-contradiction item** — an empirical direction that opposes the proposed mechanism.

Report inter-rater reliability **on the control items separately** as primary evidence of rubric and
scale validity; a low overall ICC is interpretable only if raters at least converge on the controls.

**Operational rigor**
- Randomize item order **per reviewer** (not one global seed); analyze order and fatigue effects.
- Collect reviewer metadata (years of experience, prior AI-evaluation experience, subspecialty) for
  descriptive reporting.
- Define a structured export schema (per-item ratings, free-text justifications, follow-ups, timing) up front.
- Require each item to be judged standalone; discourage cross-item references in free-text, which
  signal non-independent rating.

For an AI-system-versus-human-expert benchmark specifically, route to `/design-ai-benchmarking`, which
extends this subsection with arm definition, LLM-as-judge versus human-as-judge adjudication, and a
structured export schema.

### Phase 3: Clinical framing

Ask whether the comparator and endpoint support the stated claim:
- is the model better than current practice or just another model?
- is the endpoint clinically meaningful?
- does performance translate to action?
- **incremental value**: if the study frames the model/marker as adding value *beyond* / *on top of* / *incremental to* an existing tool (a clinical score, a routine test, a baseline model), the design must pre-specify the baseline comparator built from the in-routine-use predictors **and** an incremental-value metric — ΔC-index / ΔAUC (with a paired CI, e.g. DeLong), categorical or continuous NRI, IDI, or decision-curve net benefit. A standalone discrimination number ("our model's AUC was 0.84") does not support a "beyond X" claim; without the nested-model comparison the finding may be real but redundant. Plan this at design time — it cannot be added post hoc without the baseline model.
- **fine-tuning contribution baseline**: if an NLP/LLM study claims that fine-tuning, LoRA, prompt
  engineering, or a multi-agent wrapper improves extraction/classification, pre-specify a same-backbone
  zero-shot or few-shot comparator on the identical input, output schema, and test split. A comparison
  only against a weaker or unrelated baseline cannot establish that the proposed adaptation adds value.
- **endpoint↔conclusion scope**: decide up front what *kind* of conclusion the design can support, so the manuscript does not overreach. A cross-sectional / single-visit / prevalence design cannot support a prognostic or surveillance claim (rescreen interval, disease progression) — that needs longitudinal follow-up. A binary surrogate endpoint (present/absent, >0, dichotomized) is risk stratification, not a patient-care directive (defer/withhold/initiate therapy). At review time `/self-review` §D + `check_scope_coherence.py` flag `CROSS_SECTIONAL_PROGNOSTIC` / `SURROGATE_CARE_DIRECTIVE` against the conclusion.

### Phase 4: Reporting fit

Recommend one primary guideline:
- `TRIPOD-AI`
- `CLAIM`
- `STARD`
- `STROBE`
- `PRISMA`
- `CARE`
- `ARRIVE`
- journal-specific additions if needed

---

## Frequent Failure Modes

### Diagnostic AI
- no clinically relevant comparator
- exam-level split instead of patient-level split
- unclear reference standard
- AUROC-only reporting without threshold metrics

### Prognostic modeling
- unclear time zero
- immortal time bias
- feature timing mismatch
- no calibration

### Retrospective cohort / screening database
- **time zero misalignment**: cohort entry ≠ follow-up start → immortal time bias
- interval-censored outcomes treated as exact → underestimation of event times
- healthy volunteer bias unacknowledged → inflated external validity claims
- surveillance bias from unequal follow-up frequency between groups
- **3 bias classification (Hernan/Robins)**: selection bias (who enters), information bias (how measured), confounding (what else differs) — explicitly map each threat
- **confounding completeness**: pre-specify the adjustment set from a DAG (not a Table-1 p < 0.05 rule), and plan to report whether any measured covariate that turns out imbalanced by exposure but outside the adjustment set leaves the primary estimate robust (an extended-adjustment sensitivity model). At review time `/self-review` Phase 2.5e + the O1–O9 probes in `observational_confounding.md` check this against Table 1 (including O7 over-adjustment, the opposite-direction failure: do not adjust for a consequence/mediator of the outcome, e.g. serum uric acid in an eGFR model).

### Multimodal LLM / report generation
- no clear rubric for clinical correctness
- benchmark labels derived from noisy reports without adjudication
- unsupported claims about safety or workflow benefit
- input text contains the target label or diagnosis being predicted
- no same-backbone zero-shot/few-shot baseline for a fine-tuning or prompt-engineering claim

### Imaging meta-analysis
- overlapping cohorts
- paired modalities analyzed as independent
- heterogeneity metrics missing
- zero-cell handling unspecified

---

## Minimal-Fix Principle

Whenever possible, recommend the smallest feasible repair first:

- clarify the claim
- narrow the target population
- add a limitation statement
- add a clinically relevant baseline
- re-run one key sensitivity analysis
- redefine the endpoint more explicitly

Escalate to redesign only when the central claim is not defensible otherwise.

---

## Handoff Rules

- route to `analyze-stats` when the design is basically sound but analysis details need refinement
- route to `check-reporting` after the design is locked
- route to `self-review` when the user wants a pre-submission quality check on their own manuscript
- route back to `write-paper` only after the main validity risks are documented

---

## What This Skill Does NOT Do

- It does not compute statistics directly
- It does not draft full manuscript prose
- It does not resolve raw data engineering issues
- It does not replace a full peer review when journal-facing tone is required

## Anti-Hallucination

- **Never fabricate references.** All citations must be verified via `/search-lit` with confirmed DOI or PMID. Mark unverified references as `[UNVERIFIED - NEEDS MANUAL CHECK]`.
- **Never invent clinical definitions, diagnostic criteria, or guideline recommendations.** If uncertain, flag with `[VERIFY]` and ask the user.
- **Never fabricate numerical results** — compliance percentages, scores, effect sizes, or sample sizes must come from actual data or analysis output.
- If a reporting guideline item, journal policy, or clinical standard is uncertain, state the uncertainty rather than guessing.
