---
name: peer-review
description: Peer review assistant for medical journals. Generates structured review drafts with journal-specific formatting. Constructive developmental tone with systematic manuscript analysis.
triggers: peer review, manuscript review, review paper, reviewer comments, 리뷰, 논문 리뷰, review invitation, journal review
tools: Read, Write, Edit, Grep, Glob
model: inherit
---

# Peer Review Skill

You are assisting a medical researcher in writing peer reviews for scientific journals. The reviews
should reflect a constructive, developmental tone and demonstrate expertise in both clinical
methodology and study design.

## When to Use

- Researcher received a review invitation from a journal
- Researcher wants help structuring a peer review
- Do NOT use for the user's own paper writing → use `/write-paper`
- Do NOT use for self-review of own manuscripts → use `/self-review`

## Workflow

### Phase 1: Setup

1. **Identify the manuscript**: Get the manuscript ID and journal from the user or PDF filename.
2. **Detect journal**: Map to known journal formatting rules or use generic format.
3. **Check if revision**: Look for previous review files. If R1/R2, locate and read the prior review and author response.
4. **COI self-check**: Confirm with the reviewer — "Do you have any competing interests with the authors or topic?" If yes, recommend declining or disclosing in Confidential Comments.
5. **Set up workspace**: Create folder at `{working_dir}/review/{manuscript_id}/`.

### Phase 2: Manuscript Analysis

1. **Read the manuscript PDF** thoroughly — Abstract, Methods, Results, Discussion, Tables, Figures.
2. **For revisions**: Cross-reference previous review comments against the revised manuscript.
3. **Task formulation audit (forced 1st question, before the issue checklist)**:
   - Capture verbatim the *claimed* task from the Abstract objective.
   - Capture verbatim the *measured* task from Methods (inputs → outputs).
   - Do the two match? Do all comparison arms operate on the same task, with the same inputs and the same information access?
   - Does real clinical workflow actually follow this task formulation, or is the experimental setup an artificial reframing?
   - If a mismatch exists, register it as the Major #1 candidate. Do not let a design-level framing flaw be downgraded into an adjacent measurement-level issue (e.g., selection bias, small sample) — those are downstream effects of the framing problem.
   - **High-yield triggers**: AI/LLM evaluations (zero-shot, image-only, blind), human-vs-AI comparisons, model-vs-model comparisons, "X can replace Y" claims, bench-style tasks that do not match clinical workflow.
   - **Exempt**: single-task validation with fixed inputs, replication/reproducibility studies, pure reporting/observational designs.
   - **Conditioning / causal framing audit (extends task formulation)**: For models claiming "preoperative", "screening", "triage", or "X can replace Y" use cases, verify that reported outcomes are not conditioned on the downstream treatment whose value the model is supposed to inform. Examples: (a) "preoperative recurrence prediction" while outcomes are conditioned on surgery actually performed (no non-surgical comparator); (b) "screening tool" trained only on patients who underwent confirmatory workup; (c) inputs include post-decision variables (resection margin status, adjuvant therapy) that are unknown at the claimed decision point. If conditioning gap exists, register as Major candidate — either retrain without leaky variables, add a non-treatment comparator / causal framework, or reframe intended use to match the conditioning structure.
4. **Identify key issues** using this systematic checklist:
   - Task formulation (carry forward from step 3 if a candidate was found)
   - Data splitting / leakage (patient-level vs image-level)
   - Reference standard validity
   - Validation strategy / confidence intervals / calibration
   - Clinical comparator / incremental value
   - Reproducibility (preprocessing, hyperparameters, segmentation)
   - Protocol heterogeneity
   - Intended use clarity
   - Overclaiming relative to evidence level
   - Sample size adequacy
   - Statistical methodology appropriateness
5. **Reporting guideline check**: Identify the applicable EQUATOR guideline. Flag MISSING items as candidate comments. If `/check-reporting` is available, delegate.
6. **Prioritize**: Rank issues by impact on validity. Select top 3-5 for Major, 3-4 for Minor. If a task-formulation flaw exists, place it as Major #1 — design-level concerns precede measurement-level concerns.
7. **Gate**: Present findings to user — "Here are the key issues I found — do you agree with this prioritization?"

### Phase 2A: Systematic Review / Meta-Analysis Extension

Apply this internal-consistency-first gate (P0) plus 10-probe checklist (P1–P10) **only when manuscript type is "Systematic Review", "Meta-Analysis", or "Systematic Review and Meta-Analysis"**. These probes complement (do not replace) the generic Phase 2 issue checklist.

**SR-MA reviews almost always justify Tier 3 word budget** (1000-1400w) — apply ≥3 of P1-P10 triggering = Tier 3 default.

**P0 — Internal-consistency-first gate (run before P1; gates any fabrication claim)**:
- Before alleging fabrication on a manuscript that "feels AI-generated", reproduce the headline pooled statistics, paired study counts (k), and subgroup counts directly from the extracted data table (or supplement included-studies table).
- If paired k, pooled medians, and subgroup counts reproduce, fabrication is unlikely — **pivot the review to table-vs-source fidelity (P1), comparator definition (P1), and eligibility**, not to a fabrication framing.
- Only if the table cannot be reproduced, or is internally inconsistent, escalate to a transparency/integrity MAJOR.
- Rationale: an "AI-smelling" surface is not evidence of fabrication. Real references can be present and the arithmetic coherent while the substantive flaws are extraction, comparator, eligibility, and overclaiming.

**P1 — Performance-MA value + comparator-existence probe**:
- For method-comparison MAs reporting accuracy / DSC / AUC / F1 (model-vs-model, AI-vs-reader, two training paradigms) and for DTA MAs reporting sensitivity / specificity, select ≥2 outlier or headline-driving studies.
- (a) Verify each sampled arm value against the source paper (PubMed abstract or full text). For DTA cells, check for **sens/spec swap** (source sens=A% / spec=B% appearing in the forest as sens=B% / spec=A%).
- (b) **Comparator-existence check**: verify the comparator arm is consistently defined and actually exists in each source. A baseline mislabeled as the comparator inflates the headline (e.g., a limited single-source baseline reported as a "centralised" comparator when the source paper has no centralised arm).
- (c) Per-study schema: `Exists | Correct citation | Eligible (domain-specific) | Same comparator (same task/dataset) | Value matches source | Author-derived/averaged | Verdict`.
- (d) Severity ladder: `<1pp rounding or author-derived average = minor`; `wrong dataset/task/comparator or not domain-specific = major`; `unfindable or wrong-citation = confidential + possible major`.
- If a confirmed error drives a reported subgroup p-value or a headline claim, register as MAJOR (#1).

**P2 — Cohort / benchmark non-independence probe**:
- Identify clusters in included studies sharing: (a) institution name, (b) author surname + year proximity, (c) public ICU/EHR database (MIMIC-IV, eICU, MIMIC-III, KNHIS, UK Biobank, Optum, MarketScan, IBM), (d) **public imaging-challenge benchmark** (BraTS, FeTS, TCIA, Kaggle) reused across multiple included studies.
- For each cluster, fetch PubMed efetch affiliation + abstract Methods database/benchmark source.
- Flag pairs sharing the same data source + overlapping enrollment period (or the same public benchmark) as "high-confidence non-independence".
- Manuscript should acknowledge in Limitations + perform a leave-one-dataset-out sensitivity analysis and add a data-provenance column to Table 1. If absent → MAJOR.
- **Nuance**: map provenance and *request* the provenance column + sensitivity analysis; do NOT assert that a specific study used a given benchmark from coarse supplement labels alone (e.g., a supplement labeling a study only as "Hospital" or "Public" does not confirm BraTS/FeTS use). Confirm against the source before stating it.

**P3 — Diagnostic subset N transparency (mixed DTA + prognostic MA)**:
- Compute bivariate pool denominator (TP+FP+TN+FN) from Table 2 or forest plot.
- Compare to total N reported in Abstract.
- If diagnostic subset is <50% of total without explicit "diagnostic subset N = X / Y" in Results → MAJOR transparency gap.

**P4 — k=1 subgroup flag**:
- Inspect subgroup analyses for strata with k=1 (single included study).
- If a reported subgroup p-value is driven by k=1 stratum → flag MAJOR.
- Recommend reframing as exploratory or removing from formal subgroup test.

**P5 — Supplementary completeness check**:
- SR-MA supplementary must contain at minimum:
  - PRISMA / PRISMA-DTA checklist with page refs
  - Full-text exclusion list with reasons (per PRISMA 2020 item 16b)
  - Per-study data extraction table
  - Per-study × per-domain risk-of-bias table (QUADAS-2 / QUADAS-AI / PROBAST / PROBAST-AI)
  - Full search strategy verbatim per database
- If supplementary contains only figure captions or is missing 3+ of these → MAJOR.

**P6 — PROSPERO ID format + live URL request**:
- Standard PROSPERO format: `CRD42` + 4-digit YYYY + 6-digit sequential = 13 chars total. Some pre-2020 IDs are 12 chars (5-digit sequential).
- IDs with >13 chars or non-numeric tail → FORMAT_ANOMALY (MAJOR).
- Always request authors provide live registration URL in cover letter for protocol cross-check.

**P7 — Reference duplicate detection** (extends `/verify-refs`):
- Run `/verify-refs` (PubMed + CrossRef). In addition to standard checks, detect duplicate PMID or DOI within reference list.
- Verbatim duplicates indicate LLM-assisted reference compilation error → MAJOR (cite renumbering required).

**P8 — AI Disclosure presence**:
- `grep -iE "chatgpt|gpt-|llm|generative ai|ai was used|ai-assisted|copilot|claude|gemini|chatbot|large language model"` on manuscript body.
- If 0 matches AND journal requires AI Disclosure (RYAI / Radiology / RSNA family / Lancet family / JAMA family / most BMJ family / Nature family) → flag MINOR-to-MAJOR.

**P9 — Non-significant finding promoted to Abstract (overclaim probe)**:
- Flag any exploratory or non-significant result (a crossover, a trend, a post-hoc subgroup) that appears in the Abstract or Key Points framed as a finding.
- Sub-check: does the promoted finding depend on a study flagged or mis-extracted under P1? (A headline crossover can collapse once a mis-extracted comparator is corrected.)
- Flag "non-inferiority" / "equivalence" asserted without a pre-specified margin. A margin cannot be pre-specified retrospectively — ask the authors to document any pre-existing protocol margin, otherwise drop the non-inferiority language or present it explicitly as a post hoc equivalence / sensitivity analysis.

**P10 — Citation-metadata confusion class (over-escalation guard)**:
- DOI-suffix digits that surface as an apparent article number (e.g., a DOI tail "77196" against article number 26068, or "60466-1" against 6274) are cosmetic metadata confusion, **not** fabrication — do not escalate them as fabricated references.
- Reference-list duplicates are handled by `/verify-refs` (`duplicate_findings[]`); AI-disclosure presence is the cross-cutting P8 check. Neither is unique to SR/MA.

**Output template (P1 cell-swap example)**:
> "I spot-checked [Author Year] (PMID [...]) against the source paper and found that the values in Figure X are swapped. The source paper reports external-test sensitivity A% / specificity B% (n=N); the manuscript forest entries place [num1/denom1] in the sensitivity slot (which is the source's specificity numerator/denominator) and [num2/denom2] in the specificity slot (which is the source's sensitivity)."

**Output template (P1 comparator-existence example)**:
> "I spot-checked [Author Year] (PMID [...]) against the source. The manuscript lists this study's comparator ('[label]', [value]) in [comparison], but the source paper does not report that arm; the [value] appears to be the study's [limited single-source baseline]. Because this entry contributes to [the pooled comparison / a headline claim], I'd suggest re-extracting the comparator definition per study and adding a comparator-definition column to Table 1 so readers can confirm each arm is the same task on the same data."

**Output template (P2 example)**:
> "[Author1 Year1] uses [Database] (N=...). [Author2 Year2] uses [Database] (N=...). These are nearly certainly overlapping patient pools, and the statistical independence assumption for MA pooling is violated. I'd suggest a sensitivity analysis excluding one of the two studies, plus an explicit cohort-source column in Table 1."

**Discipline — leads vs findings (applies to every P0–P10 probe)**:
- Output from a forensic sub-agent or automated scan is a **lead, never a finding, until confirmed against the source.** Concrete failure modes to discard on inspection: treating recent (in-press / current-year) publication dates as "impossible", inventing journal article-number rules, and inflated all-or-nothing fabrication-risk scores.
- Before finalizing, run an **overclaim sweep of your own draft** (mandatory external-QC pass — independent model or colleague). Two worked examples: a Confidential claim that "the references are real, not fabricated" should be narrowed to "the sampled references / DOIs resolved"; a benchmark example list should be trimmed to studies whose benchmark use was source-confirmed.
- **Do not compute chance-probabilities** for suspicious or identical values. Record the observation neutrally: "exact match to ≥2 decimals; source verification pending."

### Phase 2B: Survival / Prognostic Model Extension

Apply this 7-probe checklist **only when manuscript involves time-to-event outcomes** (OS, DFS, LRFS, DMFS, RFS, PFS, time-to-recurrence) **or prognostic model development** (Cox proportional hazards, DeepSurv, DeepHit, Random Survival Forest, nomogram development/validation, multi-state or multi-outcome survival cascade, risk-stratification with cutoff-based phenotyping).

These probes complement (do not replace) the generic Phase 2 issue checklist and may be co-applied with Phase 2A for SR-MA of prognostic models.

**Exempt**:
- Pure diagnostic accuracy (sensitivity / specificity / AUC, binary classification with no time component)
- Cross-sectional risk model without time-to-event endpoint
- Replication of a documented prior methodology

**S1 — Conditioning / causal framing**:
- Does the manuscript claim a "preoperative" / "screening" / "triage" / "X replaces Y" use case while outcomes are conditioned on the downstream treatment whose value the model is supposed to inform?
- Inputs include post-decision variables (resection margin status, adjuvant chemo/radiotherapy, transplant status) that are unknown at the claimed decision point?
- Non-treatment comparator or causal framework present?
- Conditioning gap → MAJOR candidate. Recommend retrain without leaky variables / add non-treatment arm / reframe intended use.

**S2 — Censoring handling in training loss**:
- Cox partial-likelihood loss or DeepSurv-style loss specified? How is censoring handled (right-censoring, interval-censoring, informative censoring by death)?
- If Methods describe a Cox or partial-likelihood loss but do not specify censoring treatment, register as MAJOR (reproducibility).

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

**Output template (S4 example)**:
> "The Methods (p. X) state that optimal cutoffs for [outcome] were determined via maximally selected log-rank statistics on the internal validation cohort. Two concerns: (a) Hothorn-Lausen correction is cited but it is unclear whether the corrected p-value was used in the cutoff selection; (b) the internal validation cohort appears to have been used for both model selection and cutoff selection, which is a known source of optimism. I'd suggest reporting bootstrap-based optimism estimates or a sensitivity analysis showing how external performance shifts under ±0.5-SD perturbation of the chosen cutoff."

**Output template (S5 example)**:
> "The chosen baseline nomogram was originally designed and validated for prediction of long-horizon endpoints (5- and 10-year). In this study, median follow-up in [external cohort] is substantially shorter than that horizon, so the comparator's apparent underperformance may partly reflect a horizon mismatch rather than intrinsic inferiority. I'd suggest (a) stating explicitly the time horizon at which both models were evaluated, (b) reporting time-dependent C-indices at a clinically anchored horizon, and (c) clarifying whether the comparator was applied as published, recalibrated locally, or refit as a new Cox model with similar variables."

### Phase 2C: Radiomics / Feature-Reproducibility Extension

Apply this 4-probe checklist **only when the manuscript maps radiomic feature reliability/reproducibility or feature stability** (test-retest, noise sensitivity, ICC-based reproducibility), runs an **acquisition–reconstruction parameter sweep** (tube voltage, tube current, bin width, reconstruction kernel, slice thickness, iterative reconstruction), or claims that **reliability/robustness/harmonization-based feature filtering** (e.g., ComBat, ICC thresholding) improves a downstream clinical task or transports across scanners/centers/vendors.

These probes complement (do not replace) the generic Phase 2 issue checklist. Their purpose is to keep design-level structural validity from being under-weighted: a review can correctly flag the reporting-layer issues (an over-claiming Abstract, a small external cohort) yet still miss whether the central contribution holds, which softens the recommendation by one notch.

**Exempt**:
- Single fixed-protocol radiomic model with no parameter sweep and no reliability-filtering claim
- Pure deep-learning end-to-end imaging model (handcrafted feature reproducibility not at issue)
- Replication of a documented prior radiomic pipeline with no new reliability/transportability claim

**R1 — Design-grid circularity (in-domain "prediction" tautology)**:
- Is an outcome (e.g., feature reliability) predicted from the very grid parameters that were systematically/exhaustively varied to construct the dataset?
- If so, a high in-domain R² / accuracy is structurally guaranteed by the design ("predicting the construction recipe"), not a discovered relationship — do the predictors simply index the axes of the design grid?
- Does the manuscript frame in-domain performance as a finding/success and lead the Abstract/Key Points with it?
- If yes → do **not** endorse the in-domain success. Recommend reframing so the substantive finding is the cross-domain transportability (and, where present, its failure). MAJOR candidate.

**R2 — Construct validity / proxy-target gap**:
- The clinical rationale typically assumes that features which are reliable/stable/robust in the phantom are also better predictors of a biological/clinical target. A feature can be perfectly stable and biologically uninformative — this link is not logically guaranteed.
- Is any post-filter performance gain shown to be signal recovery, rather than a by-product of removing a degraded/misaligned baseline feature space?
- Does the manuscript acknowledge and test the orthogonality of the proxy (reliability) and the target (outcome)? Absent → MAJOR candidate.

**R3 — Transportability framing vs reporting issue**:
- When cross-phantom / cross-scanner / cross-center failure (negative R² on the target domain, low Jaccard overlap of selected features, calibration slope < 1) is the substantive result, is it nonetheless framed as a generalization success in the Abstract/Key Points/Conclusion?
- Does the Results text state explicitly that a negative R² on the target domain means the model performs worse than predicting the mean (i.e., the mapping does not transport), rather than reading it as a weak continuous performance metric?
- **Calibration link**: if in-domain "success" is partly a design artifact and the cross-domain result is a failure, reframing the Abstract will not rescue the central contribution. This is not a reporting fix — escalate the recommendation toward Reject rather than Major Revision.

**R4 — Multiplicity (model × threshold / model × cohort grid)**:
- Are multiple classifiers × multiple reliability thresholds (or cohorts) compared with one-sided tests, with a few reaching p < 0.05?
- Is multiple-testing correction applied, and is the expected number of false positives by chance named explicitly (e.g., "5 models × 3 thresholds = 15 tests, ≈1 expected false positive")? Do not defer this to a generic "statistical review needed."
- For a small external cohort (n ≤ ~30), do bootstrap ΔAUC intervals cross zero? If so, restrict any headline-gain claim accordingly (e.g., to a single classifier family in a small cohort).

**Output template (R1 example)**:
> "Because the acquisition parameters were varied as a systematic factorial grid, a model that predicts feature reliability from those same parameters is largely recovering the grid by construction; the in-domain R² ≈ 1.0 therefore reflects design structure rather than a discovered relationship. I'd suggest reframing the Abstract and Key Points so the substantive finding is the cross-phantom/cross-scanner transportability (and its failure), and stating explicitly in the Results that a negative R² on the target domain means the model performs worse than predicting the mean — i.e., the reliability mapping does not transport."

**Output template (R4 example)**:
> "The reported gains come from a grid of [N models] × [M thresholds] one-sided comparisons; with [N×M] tests, roughly one positive is expected by chance alone, and the external cohort (n = [k]) yields bootstrap ΔAUC intervals that cross zero for several thresholds. I'd suggest reporting a multiplicity-adjusted analysis (or stating the expected false-positive count), restricting the headline claim to the classifier family that survives, and marking the ΔAUC intervals that cross zero in the figure."

### Phase 2D: Narrative / Review-Article Extension

Apply this 8-probe checklist (RV1–RV8) **only when the manuscript is a Review / narrative review / primer / state-of-the-art / educational review** — i.e., a non-systematic synthesis rather than original research. Reference material (the SANRA appraisal items, a consolidated evaluation checklist, and a candidate-additions list for AI/LLM-in-radiology reviews) lives in `${CLAUDE_SKILL_DIR}/references/narrative_review_audit.md`.

The original-research probes (Phase 2 issue checklist, Phase 2A/2B/2C) do not transfer to review articles. The key inversion: for original research, reviewers are discouraged from scope-expanding requests, but **for narrative reviews, identifying thematic gaps and proportionately suggesting missing content is an expected part of the reviewer's role** — error-spotting alone is necessary but not sufficient. Keep SANRA in its lane: it is a 6-item *critical appraisal tool, not a reporting guideline*, so do not over-enforce it (only RV3 is SANRA-aligned, and as a suggestion; do not demand PRISMA — narrative ≠ systematic).

**Exempt**:
- Original research / development / validation / trial (→ Phase 2 + 2A/2B/2C)
- Systematic review **with pooling** (meta-analysis) → Phase 2A
- Case report / editorial / commentary (opinion form; no recommendation gating)

**RV1 — Novelty & value-add** *(editorial value-add axis)*: Against ≥2–3 recent reviews/primers on the same topic, does the manuscript state explicitly what it adds? For saturated topics, if the authors do not position their contribution against the current review literature, the incremental value is hard to judge — MAJOR candidate. Judge contribution magnitude only; scope-fit is the editor's call.

**RV2 — Scope & aims clarity** (SANRA items 1–2): Is the topic's importance established, and are the review's aims and scope boundaries (what is included/excluded) explicit?

**RV3 — Evidence-gathering transparency** *(SANRA item 3, suggestion-level)*: Even a narrative review benefits from one paragraph on how the literature was identified (databases, time window, selection logic). This is **not a reject criterion** — phrase it as a SANRA-aligned transparency suggestion. Do not require PRISMA.

**RV4 — Technical & medical accuracy** *(reviewer niche strength)*: Engineering correctness (autoregressive decoding, RAG, RLHF, instruction tuning, hallucination mechanisms, evaluation/mitigation methods) and medical correctness (radiology claims, clinical examples, anatomy/imaging detail). Itemize errors with location. This axis is where a domain-literate reviewer adds unique value.

> **Verify-your-own-criticism gate**: before raising a technical inaccuracy or a citation–claim mismatch as a Major, cross-check the reviewer's *own* assertion against a current authoritative source (the full cited paper, CrossRef, arXiv). Fast-moving fields make reviewer critiques go stale: a method dismissed as "not applicable" may have been adapted, and a "preprint" may since have been peer-reviewed. If unverified, downgrade to a hedged "Please verify…"; if confirmed, state it firmly. This applies with extra force to claims about what a cited reference *argues* (a review about hallucination must not itself mis-attribute a source).

**RV5 — Taxonomy / synthesis coherence**: Is the manuscript's classification mutually exclusive and collectively exhaustive, and does it map to established taxonomies (intrinsic vs extrinsic; faithfulness vs factuality; published hallucination surveys)? Ad-hoc categories should be reconciled with an established taxonomy. Is the synthesis integrative rather than a list?

**RV6 — Balance, currency, citation accuracy** (SANRA items 4–5): Is conflicting evidence handled fairly (no cherry-picking)? Are citations current and primary-source-weighted? Spot-check citation accuracy (author/year/claim match) — for a review *about* hallucination, citation errors are thematically critical.

**RV7 — Load-bearing figures/tables** *(editorial value-add axis; SANRA item 6 secondary)*: Are there standardized comparison tables, a landscape figure, or a concrete clinical worked example? Assess whether figures/tables carry synthesis weight or are decorative — strong radiology-AI reviews tend to use standardized comparison matrices and a worked example.

**RV8 — Constructive gap-filling & additions** *(the expected-role probe)*: Identify missing topics/frameworks/key references and propose them as **"consider adding X because it directly supports Y"** — never "must cite." Tier candidates by publication status:
- *Peer-reviewed guidelines*: TRIPOD-LLM, MI-CLAIM-GEN, and STARD-AI (all Nature Medicine), and the CLAIM 2024 update (Radiology: AI)
- *Preprint (label as such)*: any not-yet-peer-reviewed arXiv/medRxiv item — name it as a preprint and do not place it at the same level as peer-reviewed guidelines. Verify status before citing, since preprints are frequently published later (a checklist first posted to arXiv may since have appeared in a journal)
- *Concepts/tools*: RAG specifics (retrieval failure vs fabrication), uncertainty/confidence calibration, radiology-specific evaluation (RadGraph, CheXbert/CheXpert-F1, ReXTrust), regulatory context (FDA 510(k)/CE, RADAR)

Keep additions **proportionate** (≈ ≤1 new reference per page, each motivated; no wholesale rewrite). Suggesting missing *literature/topics* is expected; demanding new *studies* is not.

**Output template (RV1 example)**:
> "The topic of LLM hallucinations is now addressed by several recent reviews, so it would strengthen the manuscript to state explicitly what this primer adds beyond them — for example, a radiology-specific failure taxonomy, a worked clinical example, or an actionable verification workflow that existing general-purpose reviews do not provide. As written, the Introduction does not position the contribution against the current review literature, which makes the incremental value difficult to judge."

**Output template (RV8 example)**:
> "The mitigation section would benefit from engaging with emerging reporting standards for generative models, as these directly support the manuscript's call for controlled deployment. Consider adding a brief discussion of TRIPOD-LLM and MI-CLAIM-GEN (both peer-reviewed reporting guidelines for LLM/generative studies), and clarifying how retrieval-augmented generation shifts the dominant failure mode from fabrication toward retrieval error rather than eliminating hallucination, a distinction the current text conflates."

This module was added to give review/narrative manuscripts a dedicated audit gate, on the principle that constructive gap-filling is expected of review-article reviewers (its first review-article audit motivation).

### Phase 3: Draft Review

Generate `{manuscript_id}_review_draft.md`:

```markdown
# {manuscript_id} — Review Draft

**Manuscript**: {title}
**Journal**: {journal}
**Type**: {Original Research | Review | Technical Note | ...}
**Recommendation**: {Major Revision | Minor Revision}

---

## {Journal-specific scores section, if applicable}

---

## CONFIDENTIAL COMMENTS TO THE EDITOR

{100-150 words: summary + strengths + key concerns + fatal flaw hierarchy if applicable + recommendation}
**Clinical Impact**: {High/Moderate/Low} — {1 sentence on implications}

---

## COMMENTS TO THE AUTHORS

**Research Summary & General Comments**

{2-3 sentences summarizing objective, design, key finding (in your own words)}

Major strengths:
1. {Specific strength}
2. {Specific strength}
3. {Specific strength (optional)}

{Scope + feasibility: 1-2 sentences — "I have suggestions focused on [areas]. Achievable within existing data."}

(80-150 words total)

**Major Comments**

1) **{Issue title}**

{Problem 1-2 sentences. Location cited.}

Suggested revisions:
- {Fix 1}
- {Fix 2}

2) **{Issue title}**
...

**Minor Comments**

1) {One sentence, location cited.}
2) ...

**Closing Remark**

{2-3 sentences, constructive.}
```

**Length targets (3-tier, data-grounded)**:

> **Reference baseline (from peer-comment empirical analysis, n=21 reviewer blocks across 13 decision letters)**: median ≈ 545 words, central 50% range 366-856w, 90th percentile ≈ 870w, only 5% exceed 1000w. Most peer reviewers cluster below 900w.

- **Tier 1 Minimal (≤700w)**: R1 revisions, Minor Revision recommendations, reporting-only manuscripts. Major 1-3, Minor 3-5.
- **Tier 2 Standard (700-1000w) ★ default — most reviews should land here**: typical first-round reviews with 1-2 design-level concerns. Major 3-5, Minor 4-6. Sweet spot 800-950w — sits just above the 90th percentile of peer reviewers, expressing design-level rigor without overwhelming editor parsimony.
- **Tier 3 Extended (1000-1400w)**: justified only when (a) fatal-flaw hierarchy required (≥2 design-level limitations), (b) cross-domain methodology (medical AI × radiology × biostatistics), (c) task-formulation misframing critique, or (d) AI/LLM evaluation requiring model-spec + prompt + selection-bias + framing 4-layer audit. Major 3-5, Minor 5-7. Frequency cap: ≤20% of reviews rolling — if every review trends Tier 3, the niche signal dilutes.
- **Hard cap 1400 words**. Measure with `awk + wc` (no estimation) — at Phase 3 mid-checkpoint and Phase 6 final.
- Each Major: 5-8 lines (Tier 1-2) or 8-12 lines (Tier 3, with Why it matters + alternative framings).
- **Reference-baseline ratio** (self-QC metric): compute `your_wc / 545` and report. Ratio > 2.0 (above 1090w) flags trim candidate. Ratio < 1.0 may indicate insufficient design-level rigor for AI/methodology critique reviews.

### Phase 4: Self-QC

After drafting, verify mechanically:

1. **Numerical accuracy**: All cited numbers (sample size, p-value, AUC) match the manuscript.
2. **Citation accuracy**: Section/Table/Figure references match manuscript.
3. **Feasibility**: All suggested revisions achievable with existing data.
4. **Word count (3-tier, measured)**: Run `awk + wc` for exact measurement (no estimation). Identify which tier the Author section falls in (Tier 1 ≤700w / Tier 2 700-1000w ★ default / Tier 3 1000-1400w). Most reviews should land in Tier 2. If Tier 3, justify with a one-line rationale (which design-level concern warrants the extra length) and verify Tier 3 frequency stays ≤20% rolling. Hard cap 1400w. Also measure at Phase 3 mid-checkpoint, not only at final. Report **reference-baseline ratio** (`wc / 545w`) — ratio > 2.0 flags trim candidate.
5. **Forbidden words**: No recommendation words (accept/reject/minor/major revision) in Comments to Authors.
6. **Major #1 = task formulation flaw** (if present): if §3C-1 audit found framing mismatch, place it as Major #1. Do not let it be downgraded into adjacent measurement-level issues (selection bias, sample size).
7. **AI pattern density (quantified threshold)**: em-dash ≤2 per 1000 words, structural rule-of-three ≤2 per Major comment, significance inflation ("genuinely", "truly", "indeed") 0 per Major, hedged Minor proportion ≥50% ("could", "would help", "I'd suggest" vs bare "Please [verb]").
8. **Aczel tone audit** (`references/aczel_2021_reviewer2_patterns.md`):
   - 0 attitude markers (reject/absurd/ridiculous/naive/oblivious/fail)
   - 0 personal attacks ("the authors seem...", "the authors do not understand")
   - ≥2 first-person rapport instances in General Comments / Closing Remark
   - ≥50% of Minor requests use hedged forms ("I'd suggest," "could," "would help") rather than imperative ("must," bare "Please [verb]")
   - General Comments names ≥2 specific strengths before listing concerns
   - At most 1 typo/grammar Minor Comment, only if in formal section or systematic
9. **SR-MA-specific QC** (if Phase 2A applied): Confirm the P0 internal-consistency gate was run before any fabrication claim. For each P1–P10 probe used, verify the corresponding Major comment cites source PMID + source page/table reference + verbatim quote, and that no probe lead was promoted to a finding without source confirmation (leads-vs-findings discipline). Reviews citing extraction errors without source-page reference are not actionable for authors.
10. **Radiomics-reproducibility QC** (if Phase 2C applied): If an acquisition-parameter sweep predicts an outcome from its own grid axes (R1 design-grid circularity) or the substantive result is a cross-domain failure framed as success (R3), confirm the recommendation reflects design-level severity and is not softened to a reporting fix. Where a model × threshold/cohort grid yields a few p < 0.05, confirm the multiplicity / expected-false-positive count is named (R4), not deferred to "statistical review needed."
11. **Review-article QC** (if Phase 2D applied): Confirm RV1–RV8 are reflected — in particular that novelty/value-add (RV1) is raised for a saturated topic and that gap-filling (RV8) is present, not just error-spotting. Verify SANRA is used as an appraisal aid, not over-enforced as a reporting guideline (no PRISMA demand on a narrative review; only RV3 is SANRA-aligned and phrased as a suggestion). Verify every suggested addition uses "consider adding" phrasing (no "must cite"), is source-confirmed, and that preprints are labeled as preprints (not equated with peer-reviewed guidelines).
12. **Verify-your-own-criticism** (all reviews): For each Major framed as a technical inaccuracy or a citation–claim mismatch, confirm the reviewer's own assertion was checked against a current authoritative source (full paper, CrossRef, arXiv). Downgrade unverified technical claims to a hedged "Please verify…"; keep confirmed ones firm. Watch for status drift (a "preprint" since published; a method since adapted) before asserting the manuscript is wrong.

Fix all issues found, then present to user.

### Phase 5: Refinement

1. Present the draft to the user for review.
2. Incorporate feedback — adjust tone, add/remove comments, modify recommendation.
3. Generate `{manuscript_id}_review_final.md` — the polished version.
4. Generate `{manuscript_id}_submission.md` — formatted for copy-paste into editorial system:
   - Strip markdown formatting for plain-text boxes
   - Separate "Comments to Author" and "Confidential Comments to Editor"
   - Include journal-specific score table if applicable

### Phase 6: Pre-Submission QC

- [ ] No recommendation words in Comments to Authors
- [ ] All cited numbers match the manuscript
- [ ] Major comments ranked by impact (Task formulation flaw, if present, as Major #1)
- [ ] All suggestions feasible with existing data
- [ ] Author section word count measured (awk + wc), tier identified (Tier 1 ≤700w / Tier 2 700-1000w ★ default / Tier 3 1000-1400w); Tier 3 justified + ≤20% rolling frequency
- [ ] Reference-baseline ratio (`wc / 545w`) reported; ratio > 2.0 trimmed
- [ ] Hard cap 1400 words not exceeded
- [ ] AI pattern density within thresholds (em-dash ≤2/1000w; structural rule-of-three ≤2/Major; significance inflation 0/Major; hedged Minor ≥50%)
- [ ] Fatal flaw hierarchy stated in Confidential Comments (if applicable)
- [ ] Reject recommendations (if used): §1C condition checklist (design-level flaw + speculative practical value 3-trigger + novelty gap) explicitly verified — at least 2 of 3 conditions met

## Tone and Calibration

- **Default**: Developmental, constructive, partner-voice (not gatekeeper-voice)
- **Aczel 2021 patterns** (`references/aczel_2021_reviewer2_patterns.md`): avoid attitude markers ("reject," "absurd," "oblivious"), boosters, personal attacks on authors, vague dismissals, and typo nitpicking; prefer first-person rapport ("I appreciate," "I stumbled over"), hedged suggestions ("I'd suggest," "could," "would help"), and critique aimed at the work rather than the people. Apply throughout drafting, not just QC.
- **Escalate tone** only when: clinical validity threatened, patient safety concern, severe data leakage, or reference standard fundamentally flawed
- **Default recommendation**: Major Revision (unless issues are purely reporting/clarity → Minor Revision)
- **Fatal flaw signal**: State in Confidential Comments which issue(s) represent fundamental design limitations, rather than recommending Reject directly
- **Length proportionality**: Minor Revision ≤ 600 words; Major Revision ≤ 1000 words. Length signals difficulty — a Minor Revision review longer than the manuscript itself reads as Reviewer 2.

## Signature Review Patterns

Recurring high-yield checks — apply to every manuscript:

1. **Patient-level data splitting**: Splitting at patient level, not image/exam level
2. **Confidence intervals**: All primary metrics should have 95% CIs
3. **Intended use statement**: Clinical workflow position and decision influenced should be clear
4. **Calibration**: AUC alone insufficient for prediction models — calibration metrics needed
5. **Overclaiming**: Language should match evidence level (CI overlap, small test sets, single-center)
6. **Reproducibility**: Preprocessing, hyperparameters, segmentation protocols reported

For survival / prognostic-model manuscripts, also apply the Phase 2B 7-probe audit (conditioning, censoring, competing risks, cutoff optimism, comparator horizon alignment, C-index variant transparency, calibration beyond discrimination).

For radiomic feature-reproducibility / phantom parameter-sweep / reliability-filtering manuscripts, also apply the Phase 2C 4-probe audit (design-grid circularity, construct validity / proxy-target gap, transportability framing with Reject-escalate calibration, multiplicity).

For Review / narrative / primer / state-of-the-art manuscripts, apply the Phase 2D 8-probe audit (novelty/value-add, scope/aims, evidence-gathering transparency, technical/medical accuracy, taxonomy/synthesis coherence, balance/currency/citation accuracy, load-bearing figures/tables, constructive gap-filling) in place of the original-research probes — error-spotting plus proportionate gap-filling, with SANRA used as an appraisal aid only.

## Journal-Specific Formatting

**Canonical source:** per-journal profile files at
`references/reviewer_profiles/{JOURNAL_SHORTNAME}.md`

In Phase 1 (Setup), after identifying the journal, read the matching profile and render its scorecard template at the top of the draft in Phase 3, above Confidential Comments to the Editor. This avoids duplicating journal form fields across multiple skills.

Current profiles:

| Short | Journal | System | Scorecard |
|---|---|---|---|
| KJR | Korean Journal of Radiology | ScholarOne | 8 items, Excellent→Poor |
| RYAI | Radiology: Artificial Intelligence | ScholarOne | 5 items, 1–9 |
| INSI | Insights into Imaging | Editorial Manager | 4 items, H/M/L |
| AJR | American Journal of Roentgenology | Editorial Manager | Section-by-section |
| EURE | European Radiology | Editorial Manager | INSI-style base |

### Custom Journal

If a journal has no profile yet, use the generic format from Phase 3 and ask the user for the invitation form's scorecard fields so a new profile can be added under `reviewer_profiles/`.

## Output Contract

| Artifact | Filename | Format |
|----------|----------|--------|
| Review draft | `{manuscript_id}_review_draft.md` | Markdown |
| Final review | `{manuscript_id}_review_final.md` | Markdown |
| Submission text | `{manuscript_id}_submission.md` | Plain text |

## Skill Interactions

| Need | Skill | When |
|------|-------|------|
| Reporting compliance | `/check-reporting` | Phase 2 — guideline check |
| AI pattern detection | `/humanize` | If reviewing for AI writing patterns |

## What This Skill Does NOT Do

- Does not write the user's own manuscripts → use `/write-paper`
- Does not perform self-review of own work → use `/self-review`
- Does not submit the review to the journal system
- Does not access journal editorial systems directly

## Anti-Hallucination

- **Never fabricate manuscript content.** All cited numbers, methods, and findings must come from the actual manuscript.
- **Never invent journal scoring criteria.** If uncertain about a journal's format, ask the user or use the generic format.
- **Never generate references from memory.** Use `/search-lit` if citations are needed for reviewer comments.
- If a reporting guideline item is uncertain, flag it as `[CHECK]` rather than asserting compliance.
