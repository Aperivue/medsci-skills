---
name: check-reporting
description: Check manuscript compliance with medical research reporting guidelines. Supports 49 guidelines including STROBE, STROBE-MR, RECORD, REMARK (prognostic tumor-marker studies), TARGET (target trial emulation), GATHER (burden-of-disease / health-estimate modeling), CONSORT, CONSORT-AI, STARD, STARD-AI, TRIPOD, TRIPOD+AI, TRIPOD-LLM, PGS-RS, ARRIVE, PRISMA, PRISMA 2020 for Abstracts, PRISMA-DTA, PRISMA-P, PRISMA-ScR (scoping reviews), CARE, SPIRIT, SPIRIT-AI, CLAIM, DECIDE-AI, MI-CLEAR-LLM, SQUIRE 2.0, CLEAR, MOOSE, GRRAS, SWiM, AMSTAR 2, CHEERS 2022, CROSS (survey studies), SRQR and COREQ (qualitative research), and risk of bias tools (QUADAS-3, QUADAS-2, QUADAS-C, RoB 2, ROBINS-I, ROBINS-E, ROBIS, ROB-ME, PROBAST, PROBAST+AI, NOS, COSMIN, RoB NMA). Generates item-by-item assessment with PRESENT/MISSING/PARTIAL status.
triggers: checklist, QUADAS-3, abstract checklist, structured abstract, reporting guideline, STROBE, STROBE-MR, Mendelian randomization, CONSORT, CONSORT-AI, STARD, STARD-AI, TRIPOD, TRIPOD-LLM, PGS-RS, PRS-RS, polygenic risk score, polygenic score, PRISMA, PRISMA-DTA, PRISMA-P, PRISMA-ScR, scoping review, scoping, evidence map, ARRIVE, CARE, CLAIM, DECIDE-AI, MI-CLEAR-LLM, SPIRIT, SPIRIT-AI, QUADAS, QUADAS-C, RoB, ROBINS, ROBINS-E, ROBIS, ROB-ME, PROBAST, NOS, COSMIN, AMSTAR, SWiM, CHEERS, economic evaluation, cost-effectiveness, cost-utility, QALY, ICER, RECORD, RECORD-PE, routinely-collected data, registry, claims, electronic health records, EHR, real-world data, CROSS, CHERRIES, survey, questionnaire, KAP, e-survey, response rate, SRQR, COREQ, qualitative research, interviews, focus groups, thematic analysis, grounded theory, reflexivity, REMARK, tumor marker, prognostic marker, prognostic biomarker, molecular residual disease, TARGET, target trial emulation, target trial, causal inference, estimand, immortal time bias, GATHER, burden of disease, global burden, GBD, health estimates, attributable burden, comparative risk assessment, population attributable fraction, disability-adjusted life years, DALY, forecasting, decomposition, risk of bias, compliance check, LLM accuracy, large language model, clinical deployment
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Check-Reporting Skill

## Reference Files

Checklists are vendored under `${CLAUDE_SKILL_DIR}/references/checklists/`, one file per
instrument. Each file's header gives its version, source citation and licence, and says when its
item text is an own-words summary rather than the published wording.

- `STROBE.md` -- STROBE
- `STROBE_MR.md` -- STROBE-MR 2021
- `RECORD.md` -- RECORD 2015 (RECORD-PE for drug studies)
- `REMARK.md` -- REMARK
- `TARGET.md` -- TARGET 2025
- `GATHER.md` -- GATHER 2016
- `CHEERS_2022.md` -- CHEERS 2022
- `CROSS.md` -- CROSS 2021 + CHERRIES (internet surveys)
- `SRQR.md` -- SRQR 2014 (all qualitative approaches)
- `COREQ.md` -- COREQ 2007 (interviews and focus groups)
- `STARD.md` -- STARD 2015
- `STARD_AI.md` -- STARD-AI 2025
- `TRIPOD.md` -- TRIPOD 2015
- `TRIPOD_AI.md` -- TRIPOD+AI 2024
- `TRIPOD_LLM.md` -- TRIPOD-LLM 2025
- `PGS_RS.md` -- PGS-RS / PRS-RS 2021
- `CONSORT.md` -- CONSORT 2025
- `CONSORT_AI.md` -- CONSORT-AI 2020
- `SPIRIT.md` -- SPIRIT 2025
- `SPIRIT_AI.md` -- SPIRIT-AI 2020
- `CLAIM_2024.md` -- CLAIM 2024
- `DECIDE_AI.md` -- DECIDE-AI 2022
- `MI_CLEAR_LLM.md` -- MI-CLEAR-LLM
- `CLEAR.md` -- CLEAR (radiomics)
- `ARRIVE_2.md` -- ARRIVE 2.0
- `CARE.md` -- CARE 2013
- `SQUIRE_2.md` -- SQUIRE 2.0
- `GRRAS.md` -- GRRAS
- `PRISMA_2020.md` -- PRISMA 2020
- `PRISMA_2020_Abstracts.md` -- PRISMA 2020 for Abstracts, 12 items. A separate instrument, not a subset of the 27-item checklist (main item 2 defers to it): score it with its own denominator.
- `PRISMA_DTA.md` -- PRISMA-DTA
- `PRISMA_P.md` -- PRISMA-P
- `PRISMA_ScR.md` -- PRISMA-ScR
- `MOOSE.md` -- MOOSE
- `SWiM.md` -- SWiM
- `AMSTAR2.md` -- AMSTAR 2
- `QUADAS3.md` -- QUADAS-3
- `QUADAS2.md` -- QUADAS-2
- `QUADAS_C.md` -- QUADAS-C
- `RoB2.md` -- RoB 2
- `ROBINS_I.md` -- ROBINS-I
- `ROBINS_E.md` -- ROBINS-E
- `ROBIS.md` -- ROBIS
- `ROB_ME.md` -- ROB-ME
- `RoB_NMA.md` -- RoB NMA
- `PROBAST.md` -- PROBAST
- `PROBAST_AI.md` -- PROBAST+AI
- `NOS.md` -- NOS
- `COSMIN_RoB.md` -- COSMIN RoB

---

## Workflow

### Step 0: Existing-checklist staleness pre-check

If a checklist already exists for this project (`qc/reporting_checklist.json` or a prior `.md`
report), verify it targets the **current** manuscript before reusing it — one generated against an
older version carries stale section/line references and a stale version label:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_checklist_version.py" \
  --checklist qc/reporting_checklist.json --manuscript manuscript_v8.md
```

A non-zero exit means the checklist is stale (older `target_version`, changed `source_sha256`,
different `target_manuscript`) or pre-dates the version contract: regenerate it against the current
manuscript (Steps 1–5) rather than reusing it. Every report you generate carries the
`target_manuscript` / `target_version` / `source_sha256` fields (Part A header + Part D JSON) so
this check works next round.

### Step 1: Select Guideline

Use the guideline the user names; otherwise auto-detect it from the study type. If the study type
is ambiguous, ask the user to confirm before selecting a guideline.

**Auto-detection mapping:**

| Study Type | Primary Guideline | AI Extension |
|------------|------------------|--------------|
| Observational study | STROBE | -- |
| Mendelian randomization study | STROBE-MR (base STROBE + MR extension) | -- |
| Health economic evaluation (cost-effectiveness / cost-utility / cost-benefit / budget-impact) | CHEERS 2022 | -- |
| Observational study using routinely-collected data (claims / EHR / registry / health-checkup DB) | RECORD (base STROBE + RECORD extension; RECORD-PE for drug studies) | -- |
| Survey / questionnaire study (KAP, physician/patient, cross-sectional, e-survey) | CROSS (+ CHERRIES for internet surveys) | -- |
| Scoping review (maps breadth/nature of evidence, clarifies concepts, identifies gaps — not a focused effectiveness/accuracy question) | PRISMA-ScR (base PRISMA + scoping-review extension) | -- |
| Qualitative study (interviews, focus groups, ethnography, grounded theory, phenomenology, document analysis) | SRQR (all qualitative approaches); COREQ (interviews/focus groups specifically) | -- |
| Randomized controlled trial | CONSORT 2025 | CONSORT-AI |
| Diagnostic accuracy study | STARD 2015 | STARD-AI |
| Prediction model (development/validation) | TRIPOD | TRIPOD+AI |
| Polygenic (risk) score prediction study | PGS-RS (with TRIPOD / TRIPOD+AI) | -- |
| Prognostic tumor-marker / biomarker study (single or multiple markers; e.g., ctDNA / molecular residual disease) | REMARK (pair with STROBE for the observational-design items; TRIPOD / TRIPOD+AI if a prognostic model is developed) | -- |
| Causal / comparative-effectiveness question emulated on observational data (treatment vs treatment, screening vs none, drug A vs B on registry / EHR / claims data) | TARGET (pair with the /design-study target-trial-emulation module for design; RECORD / STROBE for the routinely-collected-data items) | -- |
| Health-estimate / burden-of-disease modeling study (GBD or GBD-satellite, comparative-risk / population-attributable-fraction, cause-of-death or prevalence/incidence estimation, with or without forecasts) | GATHER (pair with `/analyze-stats` burden-decomposition-forecasting guide for the analytic layer) | -- |
| Systematic review / meta-analysis | PRISMA 2020 | PRISMA 2020 for Abstracts (run on the abstract, scored separately) |
| DTA systematic review / meta-analysis | PRISMA-DTA | PRISMA 2020 for Abstracts (run on the abstract, scored separately) |
| Meta-analysis of observational studies | MOOSE | PRISMA 2020 (use both) |
| Risk of bias (DTA studies) | **QUADAS-3** (current recommended version) | QUADAS-2 only when appraising or reproducing a review that used it |
| Risk of bias (RCTs) | RoB 2 | -- |
| Risk of bias (non-randomised intervention studies) | ROBINS-I | -- |
| Risk of bias (non-randomised exposure studies) | ROBINS-E | -- |
| Risk of bias (comparative DTA studies) | QUADAS-C | **QUADAS-3** (use both; apply the E&E's adaptation — see *Using QUADAS-C with QUADAS-3* in `QUADAS3.md`) |
| Risk of bias (prediction models) | PROBAST | PROBAST+AI |
| Risk of bias (systematic reviews) | ROBIS | AMSTAR 2 |
| Risk of bias (missing evidence in MA) | ROB-ME | -- |
| Risk of bias (network meta-analysis) | RoB NMA | -- |
| Risk of bias (measurement properties) | COSMIN RoB | -- |
| Quality assessment (observational) | NOS | -- |
| Case report | CARE | -- |
| Study protocol | SPIRIT 2025 | SPIRIT-AI |
| Animal study | ARRIVE 2.0 | -- |
| AI/ML study in clinical imaging | CLAIM 2024 | -- |
| Study using a large language model (develop/fine-tune/prompt/evaluate an LLM) | TRIPOD-LLM | MI-CLEAR-LLM (use alongside when LLM accuracy is an outcome) |
| Early-stage / live clinical evaluation of an AI decision-support system (human factors, workflow, safety) | DECIDE-AI | -- |
| LLM accuracy evaluation in healthcare | MI-CLEAR-LLM | STARD-AI or CLAIM 2024 (use alongside) |
| Reliability / agreement study | GRRAS | -- |
| SR protocol | PRISMA-P | -- |
| Synthesis without meta-analysis | SWiM | PRISMA 2020 (use both) |
| Quality of systematic reviews | AMSTAR 2 | ROBIS |
| Radiomics study | CLEAR | CLAIM 2024 (if deep learning component) |
| Educational / QI study | SQUIRE 2.0 | -- |
| Generative AI **images ARE the study object** (realism / real-vs-synthetic reader study / model-vs-model quality) | (no single guideline -- assemble) | see decision aid below |

> **QUADAS-3 has two protocol-stage phases, and this skill usually runs too late for them.**
> Phase 1 (state the synthesis question) and phase 2 (define the **ideal test accuracy trial**
> each judgement is made against) are review-level and belong in the protocol, with the
> review-specific guidance for answering each signalling question. Reaching them for the first
> time during manuscript QC means writing the comparator after seeing the results. If they are
> missing, say so as a limitation rather than reconstructing them, and route the protocol work to
> `/meta-analysis` Phase 1. Phases 3–6 are what a QC pass can genuinely run.

**Rules:**
- If the study involves AI/ML, always apply the AI extension in addition to the base guideline.
  - **Exception — TRIPOD**: TRIPOD+AI 2024 (Collins et al., BMJ 2024) is a complete rewrite, not an addendum to TRIPOD 2015 (Moons et al., Ann Intern Med 2015). For non-AI prediction models, use TRIPOD 2015 only. For AI/ML prediction models, use TRIPOD+AI 2024 only. Do NOT apply both simultaneously.
- **STARD-AI** (Sounderajah et al., Nat Med 2025) extends STARD 2015 with 14 new and 4 modified items (40 total) and incorporates all STARD 2015 items. For AI diagnostic accuracy studies use STARD-AI only — do NOT apply STARD 2015 and STARD-AI simultaneously.
- **TRIPOD-LLM** (Gallifant et al., Nat Med 2025) is the reporting guideline for studies that develop, fine-tune, prompt, or evaluate a large language model for a clinical/biomedical task. It extends the TRIPOD family (TRIPOD 2015 → TRIPOD+AI 2024 → TRIPOD-LLM 2025); name the base instrument and the extension and cite each. It is modular — task-specific items (Annotation, Prompting, Summarization, Instruction-tuning) are N/A when that component is absent. Use TRIPOD-LLM for LLM studies in place of TRIPOD+AI; pair with MI-CLEAR-LLM when LLM accuracy is an evaluated outcome. The vendored checklist is an educational summary (own-words paraphrase of item intent); complete the official instrument for a submission checklist.
- **MI-CLEAR-LLM** is a supplementary checklist (8 item categories in the 2025 update; the 2024 original had 6), not a standalone reporting guideline. Always pair it with the study's primary guideline (e.g., STARD-AI for AI diagnostic accuracy, CLAIM for imaging AI). Apply it whenever the study evaluates LLM accuracy as an outcome — do NOT apply it merely because the manuscript was written with LLM assistance. Its scope is **LLM accuracy** studies (including VLMs interpreting images); it does **not** apply at study level when a generative model *produces* the images under study (next bullet).
- **Generative-AI images as the study object** (a generative model synthesizes images and the study evaluates their realism, controllability, real-vs-synthetic distinguishability, or model-vs-model quality) has **no single dominant checklist**. Assemble: CLAIM 2024 (imaging-AI umbrella; model-development items N/A when commercial models are used as-is) + FUTURE-AI traceability + MI-CLEAR-LLM **transparency items only** (prompt/model/version/params/runs — for generation provenance, not study-level compliance) on the generator side; STARD-AI (for real-vs-synthetic detection) + GRRAS (reader reliability) + MRMC reporting on the evaluation side. Map applicable items and cite base + extension; never claim wholesale compliance. Full decision aid: `${CLAUDE_SKILL_DIR}/references/genai_image_study_object_decision_aid.md`.
- If multiple guidelines apply (e.g., a diagnostic accuracy study that is also an AI study), check against all relevant guidelines and merge into one report.

### Step 2: Load Checklist

1. **Run the fail-fast guard first** for every guideline you intend to apply:

   ```bash
   python "${CLAUDE_SKILL_DIR}/scripts/check_checklist_exists.py" --guideline "STARD-AI"
   ```

   - Exit 0 → the vendored checklist exists; read it from
     `${CLAUDE_SKILL_DIR}/references/checklists/` and proceed.
   - Exit 1 (`MISSING_CHECKLIST_CONTRACT_VIOLATION`) → the guideline is routed but no checklist
     file is vendored. **Do not construct items from memory.** Halt, report the violation to the
     user, and stop unless they explicitly opt in (next bullet).
   - Exit 2 (`UNKNOWN_GUIDELINE`) → the name is not recognised; confirm the correct guideline
     with the user.

2. **No silent fallback.** A from-memory checklist is permitted only when the user explicitly
   accepts it — re-run the guard with `--allow-from-memory` (exit 0 + a NON-AUTHORITATIVE
   warning). The report MUST then carry a prominent banner that the assessment was constructed
   from model knowledge and is not backed by a vendored checklist, and `submission_safe` must not
   be asserted on its basis.

### Step 3: Scan Manuscript

Read the whole manuscript before assessing any item — including tables, figures and their
captions, supplementary material, and the reference list (registration numbers and protocol
references often sit there).

### Step 4: Assess Each Item

Items most often missing in medical manuscripts — look for these first, whichever guideline applies:
registration number and registration/amendment date consistency (run Step 4c), sample-size
justification, missing-data handling, blinding, funding and conflicts of interest, ethics approval
with committee name and approval number, and a data availability statement; for AI studies, the
training/validation/test split, model architecture and hyperparameters, failure-mode analysis,
fairness/bias assessment, and commercial interests with data/code availability.

For every checklist item, determine:

| Status | Criteria |
|--------|----------|
| **PRESENT** | The item is fully addressed with sufficient detail. |
| **PARTIAL** | The item is mentioned or partially addressed but lacks required detail. |
| **MISSING** | The item is not found anywhere in the manuscript. |
| **N/A** | The item does not apply to this particular study (justify why). |

For each item, record:
- **Status**: PRESENT / PARTIAL / MISSING / N/A
- **Location**: Section name and paragraph or approximate position (e.g., "Methods, paragraph 3")
- **Notes**: What was found (if PRESENT/PARTIAL) or what should be added (if MISSING)

**Be strict.** PARTIAL means the item is mentioned but lacks specificity; a vague reference does
not count as PRESENT — the detail level must match what the guideline expects. "We used
appropriate statistical tests" = PARTIAL (which tests?); "We used the Mann-Whitney U test for
continuous variables and Fisher's exact test for categorical variables" = PRESENT. If an item is
genuinely unclear in its applicability, mark it N/A with justification.

Two gaps that are easy to pass:

- **Power-aware framing of a null result** (STROBE 16a / 18 / 20) — for an observational study whose headline is a **non-significant** association, a flat "X was not associated with Y" overreads the data when the analysis is not powered to *exclude* a clinically meaningful effect. Mark item 18/20 PARTIAL unless the manuscript states the precision as an exclusion (e.g., "the 95% CI excluded an eGFR difference larger than ~1.7") or reports a minimum detectable effect — "no effect" vs "could not exclude an effect of size X" are different claims, and a negative conclusion needs the latter.
- **Confounder-selection rationale, not "adjust for everything that differs"** (STROBE 16a explicitly asks *which confounders were adjusted for and why*) — flag a kitchen-sink adjustment set chosen because variables differ in Table 1. The Methods must give a causal rationale (DAG / prior literature) and must not adjust for a **mediator or consequence of the outcome** (over-adjustment, e.g. serum uric acid in an eGFR model); both an unjustified inclusion and an unjustified omission are item-16a gaps.

**What is appraised is the source paper's reporting — never your convenience in using it.** This
holds for every instrument here, reporting checklists and risk-of-bias / quality tools alike, and is
easiest to lose in a systematic review, where you read each paper *in order to extract from it*.
An item asking "are the results clearly reported?" is not asking "were they reported in the unit my
pool needs". If a downgrade's stated reason turns on a **denominator, an analysis unit, a subgroup
you needed and they did not report separately, or a format you could not parse**, it is an
extraction note, not a scoring reason: record it in a separate **extraction-note** column and
restore the score. An extraction limitation often belongs in your limitations paragraph; folded
into the score it makes the appraisal unreproducible, because another assessor with a different
pool would score the same paper differently.

### Step 4b: Section Boundary Check

In addition to checklist items, verify that:
- **Results section** contains only factual findings: no interpretation, no "why" explanations,
  no prior literature comparisons, no evaluative adjectives without numbers.
- **Discussion section** does not introduce new data not presented in Results.
- Flag any boundary violation as a separate finding in Part C Action Items with the label
  `[BOUNDARY]`.

### Step 4c: Registration / Protocol Timing Consistency Check

**Applies to:** systematic reviews, meta-analyses, and intervention studies with prospective
registration (PRISMA 2020, PRISMA-DTA, PRISMA-P, MOOSE, CONSORT, SPIRIT). The registration
identifier is a single checklist item and can pass Step 4 while the manuscript is inconsistent
about *when* registration and amendments happened relative to the analysis.

Read `${CLAUDE_SKILL_DIR}/references/step4c_registration_timing.md` (item-by-item procedure,
JSON schema, flagging edge cases) and run its five checks: (1) registration identifier present in
Methods, Abstract, and cover letter; (2) initial registration date precedes — or is explicitly
disclosed as post-dating — the extraction milestone; (3) amendment dates appear in Methods, the
described change is visible in Methods, analysis was re-run if the amendment post-dates the lock,
and no amendment post-dates submission; (4) Methods agree with the registry record (PROSPERO PDF,
ClinicalTrials.gov export) — a silent discrepancy is a finding; (5) a retrospective-registration
disclosure paragraph when evidence suggests post-extraction filing.

**Flagging:** any failure is logged in Part C Action Items with label `[REGISTRATION-TIMING]`.
`fixable_by_ai: false` when reconciliation requires an external amendment filing; `true` only when
the fix is a Methods-text insertion of a date already disclosed elsewhere. Part D JSON includes a
`registration_timing` object (registry, id, initial_registration_date, amendments[],
timing_consistency, findings[]).

**Registration-ID format gate:** a PROSPERO ID is `CRD42` + 9 digits = 14 characters
(`^CRD42\d{9}$`, e.g. `CRD42024500001`). Run `grep -oE 'CRD42[0-9]+' manuscript.md` and
assert each match is 14 characters long; a 15-character ID (a stray inserted digit) is a
transcription error logged as `[REGISTRATION-TIMING]` (`fixable_by_ai: false` — verify against
the live PROSPERO record, do not guess the correct digit).

### Step 4d: PRISMA Figure 1 Arithmetic & Cross-Reference Audit

**Applies to:** systematic reviews and meta-analyses using PRISMA 2020 / PRISMA-DTA /
PRISMA-P. Triggers when Item 16a (flow diagram) is PRESENT — the diagram can pass Step 4 while its
numbers do not add up or disagree with the text.

1. Choose the Figure 1 source, in this order: (a) `analysis/figures/Figure1_PRISMA.md` markdown
   manifest, (b) caption text in `manuscript.md`, (c) PPTX text run if a `.pptx` exists,
   (d) manual entry from PNG/SVG.
2. Run the audit. It checks the four subtractions (screened = identified − duplicates;
   sought-for-retrieval = screened − excluded at screening; retrieved = sought − not retrieved;
   included = assessed for eligibility − excluded with reasons) and that the body-text PRISMA
   numbers match the Figure 1 boxes 1:1, and writes `qc/prisma_figure_audit.json`:

   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/check_prisma_figure.py \
     --md <manuscript.md> --figure <Figure 1 source: .md manifest / caption / text export> \
     --out qc/prisma_figure_audit.json
   ```

   Exit `1` = an arithmetic or cross-reference MISMATCH; exit `2` = missing/unparsable input.
   When the Figure 1 numbers exist only in a PNG/SVG, transcribe them by hand and run the same
   checks manually as `${CLAUDE_SKILL_DIR}/references/step4d_prisma_figure_audit.md` specifies
   (regex set, JSON schema, and edge cases: duplicates across databases, the citation-searching
   strand, dual-reviewer screening).
3. By hand (the script does not do this): the reasons for exclusion in Methods and the Figure
   legend must agree on counts and category names.
4. If `analysis/figures/_figure_manifest.md` (from `/make-figures`) exists, verify that the row
   whose `Type = prisma` (or `Type = prisma-dta`) points at the same file used as the audit
   source, and that its `Critic` field is `yes` or `partial` (not `no`). A missing row,
   mismatched path, or `Critic = no` logs `[MANIFEST-XREF]` (advisory); the arithmetic check
   still runs.

**Flagging:** any MISMATCH or arithmetic failure logs a Part C Action Item with label
`[PRISMA-FIGURE]`, `fixable_by_ai: false` (the author must reconcile the numbers).

### PRISMA Cascade Arithmetic Auto-Verify

When PRISMA 2020 or PRISMA-DTA is selected and round-by-round screening TSV artifacts are
available, recompute the screening cascade from the raw decisions. Off-by-one errors in the prose
cascade are a high-frequency reviewer red flag (e.g., `151 + 108 + 39 + 1 + 1 + 4 = 304`
followed by a prose summary "305" four lines later).

```bash
python "${CLAUDE_SKILL_DIR}/scripts/prisma_cascade_check.py" \
    --round1 2_Screening/round1.tsv \
    --round2 2_Screening/round2.tsv \
    --round3 2_Screening/round3_adjudication.tsv \
    --manuscript manuscript.md \
    --out qc/prisma_cascade.json
```

The script counts `INCLUDE` / `EXCLUDE` / `MAYBE` decisions per round, computes the cascade, and
reports per-stage drift where the manuscript's stage counts disagree. Treat any
`manuscript_drift` entry as a P0 blocker — fix the prose to match the computed cascade and re-run.

### Step 4e: Reporting-Framework Naming Audit

**Applies to:** any manuscript that invokes an AI/extension reporting framework
(PROBAST+AI, STARD-AI, TRIPOD+AI, TRIPOD-LLM, CONSORT-AI, SPIRIT-AI, PRISMA-DTA, QUADAS-C).
A base reporting tool and its extension are distinct instruments with separate citations, and
Step 1 does not police how the framework is *named* in prose. The recurring failures: invoking an
extension without ever naming or citing the base instrument it extends; mixing `+AI` and `-AI`
hyphenation for one family within a single document; coining item labels like "12-AI"; and waving
at "recent guidance" instead of naming the framework.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_framework_naming.py" \
  --manuscript manuscript.md --out qc/framework_naming.json --strict
```

**Verdicts:** `BASE_MISSING` (extension used, base instrument never named standalone) is a
Major and logs `[FRAMEWORK-NAMING]` in Part C with `fixable_by_ai: true` (insert the base
name + its citation). `HYPHEN_MIX`, `CITE_MISSING`, `SELF_COINED_LABEL`, and `VAGUE_GUIDANCE`
are Minor (`fixable_by_ai: true`). Part D JSON includes a `framework_naming` object mirroring
the script's `claims[]`.

### Step 4f: Critical-item floor cross-check

**Applies to:** every guideline assessment **for which the floor defines a row** (load and
check only those; do not invent a floor for an unlisted guideline). After the item-by-item
table, read `${CLAUDE_SKILL_DIR}/references/critical_item_floor.md` and check the small set of
**non-waivable** items for this study type — and, for AI/ML and radiomics manuscripts, the
methodological-quality / risk-of-bias instrument (PROBAST+AI, METRICS/RQS, APPRAISE-AI) and
concerns it lists. A MISSING critical item is surfaced as a **Critical gap** and becomes the
report's headline regardless of the overall percentage — a high percentage with a missing
critical item (undefined reference standard, no leakage-controlled partition, calibration absent
for a prediction model, an unreconciled flow diagram) is not "broadly acceptable."

### Step 5: Generate Report

This report is an **internal working audit** — it carries auto-fix annotations, a
machine-readable JSON block (`compliance_pct`, `fixable_by_ai`, …), and Action Items. It is
**NOT** the official reporting checklist a journal expects (that is the blank guideline form with
`Item | Recommendation | Reported in page/section`, which the authors fill in). **Never submit
this report as the submission checklist.** So that the file is self-identifying and cannot be
reused by filename into a later submission package, **the report MUST begin with this banner as
its very first line**:

```
<!-- INTERNAL AUDIT — NOT FOR SUBMISSION. This is the /check-reporting working
report, not the official journal checklist. Do not upload to a submission portal. -->
```

Write the checklist content and report in English (matching the guideline originals), whatever
language you use with the user. Save it as `qc/reporting_checklist.md` and the Part D JSON as
`qc/reporting_checklist.json`.

Read `${CLAUDE_SKILL_DIR}/references/report_templates.md` when you write the report — it holds the
literal templates for the four parts:

- **Part A — Summary.** Header (manuscript file, version token, guideline, date), the
  PRESENT/PARTIAL/MISSING/N-A count table, and overall compliance. The **headline is the critical
  items (Step 4f)**, not the percentage: report `{present}/{total}` and name every missing
  critical item with the section it belongs in.
- **Part B — Item-by-item checklist.** One row per item: `# | Section | Item | Status | Location | Notes`.
- **Part C — Action items** (MISSING and PARTIAL only), ordered by: items most journals enforce
  strictly (ethics approval, registration, sample size) → items in Methods (easiest to fix) →
  everything else.
- **Part D — Machine-readable JSON**, appended as a fenced block. **MUST** be present under
  `--json` or when called from `/write-paper` Phase 7, which parses it.

**JSON field contract** (the part other skills depend on — get these right):

- `compliance_pct` — `present / (total_items - na) * 100`, one decimal.
- `action_items` — MISSING and PARTIAL only; PRESENT and N/A are excluded.
- `fixable_by_ai` — `true` when the fix inserts or expands text using information already in the
  manuscript or inferable from it; `false` when it needs external facts the author alone holds
  (registration number, IRB approval number, protocol details).
- `suggested_fix` — concrete draft text, insertable as written.
- `source_sha256` — first 12 hex chars of the SHA-256 of the manuscript bytes, so a stale report
  cannot be silently attributed to a newer manuscript.

In notes and suggested fixes, cite a reference only with a `/search-lit`-confirmed DOI or PMID and
mark any other `[UNVERIFIED - NEEDS MANUAL CHECK]`; never invent clinical definitions, diagnostic
criteria, or guideline recommendations — flag anything uncertain `[VERIFY]` and ask the user.

When the user asks for the filled checklist a journal requires, build it from the *Submission
checklist export* template in `${CLAUDE_SKILL_DIR}/references/report_templates.md`.

---

## Skill Interactions

| When | Call | Purpose |
|------|------|---------|
| During manuscript writing | `/write-paper` Phase 7 | Final compliance check |
| Need to add Methods text | `/write-paper` Phase 3 | Draft missing Methods content |
| Need statistical details | `/analyze-stats` | Generate missing statistical reporting |
| Need flow diagram | `/make-figures` | Generate CONSORT/STARD/PRISMA diagram |

## Gates

| Gate | Severity | Trigger | Action on fail |
|---|---|---|---|
| Mandatory items present | ENFORCED at submission | < 100% of guideline-mandatory items marked PRESENT | Auto-fix MISSING items where text exists; otherwise route to `/write-paper` Phase 7 for re-draft |
| Step 4d PRISMA Figure 1 arithmetic & cross-reference audit (PRISMA / PRISMA-DTA only) | ENFORCED for SR/MA | flow numbers don't sum (e.g., screened ≠ included + excluded), or in-text counts mismatch flow diagram | HALT; reconcile against extraction artifacts |
| Optional items (e.g., supplementary AI declarations) | ADVISORY | < 80% of optional items present | warn; user accepts |
| Cross-reporting-guideline routing (study type → guideline) | ENFORCED | study type undeclared or guideline missing | Ask user; do not silently default |
