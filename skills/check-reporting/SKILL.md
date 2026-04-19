---
name: check-reporting
description: Check manuscript compliance with medical research reporting guidelines. Supports 33 guidelines including STROBE, CONSORT, STARD, STARD-AI, TRIPOD, TRIPOD+AI, ARRIVE, PRISMA, PRISMA-DTA, PRISMA-P, CARE, SPIRIT, CLAIM, MI-CLEAR-LLM, SQUIRE 2.0, CLEAR, MOOSE, GRRAS, SWiM, AMSTAR 2, and risk of bias tools (QUADAS-2, QUADAS-C, RoB 2, ROBINS-I, ROBINS-E, ROBIS, ROB-ME, PROBAST, PROBAST+AI, NOS, COSMIN, RoB NMA). Generates item-by-item assessment with PRESENT/MISSING/PARTIAL status.
triggers: checklist, reporting guideline, STROBE, CONSORT, STARD, STARD-AI, TRIPOD, PRISMA, PRISMA-DTA, PRISMA-P, ARRIVE, CARE, CLAIM, MI-CLEAR-LLM, SPIRIT, QUADAS, QUADAS-C, RoB, ROBINS, ROBINS-E, ROBIS, ROB-ME, PROBAST, NOS, COSMIN, AMSTAR, SWiM, risk of bias, compliance check, LLM accuracy
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Check-Reporting Skill

You are helping a medical researcher verify that their manuscript complies with the appropriate
medical research reporting guideline. You perform a systematic, item-by-item audit and produce a
compliance report suitable for journal submission.

## Communication Rules

- Communicate with the user in their preferred language.
- Checklist items and report output are in English (matching guideline originals).
- Medical terminology is always in English.

## Reference Files

- **Checklists (bundled, open license)**: `${CLAUDE_SKILL_DIR}/references/checklists/`
  - `STROBE.md` -- observational studies (CC BY)
  - `STARD.md` -- diagnostic accuracy studies (CC BY 4.0)
  - `STARD_AI.md` -- AI diagnostic accuracy studies (CC BY, Sounderajah et al. Nat Med 2025)
  - `TRIPOD.md` -- prediction models, classic 2015 version (CC BY, Moons et al. Ann Intern Med 2015)
  - `TRIPOD_AI.md` -- prediction models with AI/ML (CC BY 4.0, Collins et al. BMJ 2024)
  - `PRISMA_2020.md` -- systematic reviews (CC BY)
  - `ARRIVE_2.md` -- animal studies (CC0)
  - `PRISMA_DTA.md` -- DTA systematic reviews (CC BY, McInnes et al. JAMA 2018)
  - `QUADAS2.md` -- diagnostic accuracy risk of bias (CC BY, Whiting et al. Ann Intern Med 2011)
  - `RoB2.md` -- RCT risk of bias (CC BY, Sterne et al. BMJ 2019)
  - `ROBINS_I.md` -- non-randomised studies risk of bias (CC BY, Sterne et al. BMJ 2016)
  - `PROBAST.md` -- prediction model risk of bias (CC BY, Wolff et al. Ann Intern Med 2019)
  - `NOS.md` -- observational study quality (public domain, Ottawa Hospital)
  - `CONSORT.md` -- randomised controlled trials
  - `CARE.md` -- case reports
  - `SPIRIT.md` -- study protocols
  - `CLAIM_2024.md` -- AI/ML in clinical imaging
  - `MI_CLEAR_LLM.md` -- LLM accuracy studies in healthcare (CC BY-NC 4.0, Park et al. KJR 2024; 2025 update)
  - `SQUIRE_2.md` -- quality improvement in healthcare/education (CC BY, Ogrinc et al. BMJ Qual Saf 2016)
  - `CLEAR.md` -- radiomics studies (CC BY 4.0, Kocak et al. Insights Imaging 2023)
  - `MOOSE.md` -- meta-analysis of observational studies (Stroup et al. JAMA 2000)
  - `GRRAS.md` -- reliability and agreement studies (Kottner et al. J Clin Epidemiol 2011)
  - `QUADAS_C.md` -- comparative DTA risk of bias, extension to QUADAS-2 (CC BY 4.0, Yang et al. 2021)
  - `ROBINS_E.md` -- non-randomised exposure studies risk of bias (CC BY-NC-ND 4.0, Higgins et al. Environ Int 2024)
  - `ROBIS.md` -- risk of bias in systematic reviews (Whiting et al. J Clin Epidemiol 2016)
  - `ROB_ME.md` -- risk of bias due to missing evidence in meta-analysis (CC BY-NC-ND 4.0, Page et al. BMJ 2023)
  - `PROBAST_AI.md` -- prediction model risk of bias, updated for AI/ML (Moons et al. BMJ 2025)
  - `COSMIN_RoB.md` -- reliability/measurement error risk of bias (Mokkink et al. BMC Med Res Methodol 2020)
  - `RoB_NMA.md` -- risk of bias in network meta-analysis (Lunny et al. 2024)
  - `AMSTAR2.md` -- quality of systematic reviews (Shea et al. BMJ 2017)
  - `PRISMA_P.md` -- systematic review protocols (Shamseer et al. BMJ 2015)
  - `SWiM.md` -- synthesis without meta-analysis reporting (Campbell et al. BMJ 2020)
- If a local checklist file is not found for a requested guideline, the skill constructs checklist items from its knowledge of the guideline.

---

## Workflow

### Step 1: Select Guideline

Determine the appropriate reporting guideline. Auto-detect from the manuscript type or accept
user specification.

**Auto-detection mapping:**

| Study Type | Primary Guideline | AI Extension |
|------------|------------------|--------------|
| Observational study | STROBE | -- |
| Randomized controlled trial | CONSORT 2010 | CONSORT-AI |
| Diagnostic accuracy study | STARD 2015 | STARD-AI |
| Prediction model (development/validation) | TRIPOD | TRIPOD+AI |
| Systematic review / meta-analysis | PRISMA 2020 | -- |
| DTA systematic review / meta-analysis | PRISMA-DTA | -- |
| Meta-analysis of observational studies | MOOSE | PRISMA 2020 (use both) |
| Risk of bias (DTA studies) | QUADAS-2 | -- |
| Risk of bias (RCTs) | RoB 2 | -- |
| Risk of bias (non-randomised intervention studies) | ROBINS-I | -- |
| Risk of bias (non-randomised exposure studies) | ROBINS-E | -- |
| Risk of bias (comparative DTA studies) | QUADAS-C | QUADAS-2 (use both) |
| Risk of bias (prediction models) | PROBAST | PROBAST+AI |
| Risk of bias (systematic reviews) | ROBIS | AMSTAR 2 |
| Risk of bias (missing evidence in MA) | ROB-ME | -- |
| Risk of bias (network meta-analysis) | RoB NMA | -- |
| Risk of bias (measurement properties) | COSMIN RoB | -- |
| Quality assessment (observational) | NOS | -- |
| Case report | CARE | -- |
| Study protocol | SPIRIT | SPIRIT-AI |
| Animal study | ARRIVE 2.0 | -- |
| AI/ML study in clinical imaging | CLAIM 2024 | -- |
| LLM accuracy evaluation in healthcare | MI-CLEAR-LLM | STARD-AI or CLAIM 2024 (use alongside) |
| Reliability / agreement study | GRRAS | -- |
| SR protocol | PRISMA-P | -- |
| Synthesis without meta-analysis | SWiM | PRISMA 2020 (use both) |
| Quality of systematic reviews | AMSTAR 2 | ROBIS |
| Radiomics study | CLEAR | CLAIM 2024 (if deep learning component) |
| Educational / QI study | SQUIRE 2.0 | -- |

**Rules:**
- If the study involves AI/ML, always apply the AI extension in addition to the base guideline.
  - **Exception — TRIPOD**: TRIPOD+AI 2024 (Collins et al., BMJ 2024) is a complete rewrite, not an addendum to TRIPOD 2015 (Moons et al., Ann Intern Med 2015). For non-AI prediction models, use TRIPOD 2015 only. For AI/ML prediction models, use TRIPOD+AI 2024 only. Do NOT apply both simultaneously.
- **STARD-AI** (Sounderajah et al., Nat Med 2025) extends STARD 2015 with 14 new and 4 modified items (40 total). For AI diagnostic accuracy studies, use STARD-AI (which incorporates all STARD 2015 items). Do NOT apply both STARD 2015 and STARD-AI simultaneously — STARD-AI supersedes STARD 2015 for AI studies.
- **MI-CLEAR-LLM** is a supplementary checklist (6 items), not a standalone reporting guideline. Always pair it with the study's primary guideline (e.g., STARD-AI for AI diagnostic accuracy, CLAIM for imaging AI). Apply MI-CLEAR-LLM whenever the study evaluates LLM accuracy as an outcome — do NOT apply it merely because the manuscript was written with LLM assistance.
- If multiple guidelines apply (e.g., a diagnostic accuracy study that is also an AI study), check against all relevant guidelines and merge into one report.
- If the user requests a specific guideline, use that one regardless of auto-detection.

### Step 2: Load Checklist

1. Read the checklist file from `${CLAUDE_SKILL_DIR}/references/checklists/`.
2. If the checklist file does not exist for the requested guideline, use your knowledge of the guideline to construct the checklist items and inform the user that a local checklist file was not found.

### Step 3: Scan Manuscript

Read all sections of the manuscript thoroughly:
1. Title and abstract
2. Introduction
3. Methods (all subsections)
4. Results (all subsections)
5. Discussion
6. Tables, figures, and their captions
7. Supplemental materials (if available)
8. References (for registration numbers, protocol references)

Gather context from the full document before starting the item-by-item assessment.

### Step 4: Assess Each Item

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

### Step 4b: Section Boundary Check

In addition to checklist items, verify that:
- **Results section** contains only factual findings: no interpretation, no "why" explanations,
  no prior literature comparisons, no evaluative adjectives without numbers.
- **Discussion section** does not introduce new data not presented in Results.
- Flag any boundary violation as a separate finding in Part C Action Items with the label
  `[BOUNDARY]`.

### Step 4c: Registration / Protocol Timing Consistency Check

**Applies to:** systematic reviews, meta-analyses, and intervention studies with
prospective registration (PRISMA 2020, PRISMA-DTA, PRISMA-P, MOOSE, CONSORT, SPIRIT).

**Why this step exists:** the registration identifier is a single checklist item and can
pass Step 4 even when the manuscript is internally inconsistent about *when* the
registration or its amendments occurred relative to the analysis. An undisclosed
post-hoc amendment is a common rejection trigger.

**Five audit items (summary):** (1) registration identifier present in Methods, Abstract,
and cover letter; (2) initial registration date precedes — or is explicitly disclosed as
post-dating — the extraction milestone; (3) amendment dates appear in Methods, the
described change is visible in Methods, analysis was re-run if amendment post-dates the
lock, and no amendment post-dates submission; (4) cross-artifact agreement between
Methods and the registry record (PROSPERO PDF, ClinicalTrials.gov export) — silent
discrepancy is a finding; (5) retrospective-registration disclosure paragraph when
evidence suggests post-extraction filing.

**Flagging:** any failure is logged in Part C Action Items with label
`[REGISTRATION-TIMING]`. `fixable_by_ai: false` when reconciliation requires an external
amendment filing; `true` only when the fix is a Methods-text insertion of a date already
disclosed elsewhere. Part D JSON includes a `registration_timing` object
(registry, id, initial_registration_date, amendments[], timing_consistency, findings[]).

**Load-on-demand procedural detail** (exact item-by-item procedure, JSON schema,
flagging edge cases): `${CLAUDE_SKILL_DIR}/references/step4c_registration_timing.md`.

### Step 5: Generate Report

Produce a structured compliance report in two parts.

#### Part A: Summary

```
## Reporting Guideline Compliance Report

Manuscript: {title}
Guideline: {name and version}
Date: {YYYY-MM-DD}
Assessed by: Claude (automated pre-screening)

### Summary

| Status | Count | Percentage |
|--------|-------|------------|
| PRESENT | {n} | {%} |
| PARTIAL | {n} | {%} |
| MISSING | {n} | {%} |
| N/A | {n} | {%} |
| **Total** | **{n}** | **100%** |

Overall compliance: {PRESENT count}/{applicable count} ({%})
```

#### Part B: Item-by-Item Checklist

```
### Detailed Checklist

| # | Section | Item | Status | Location | Notes |
|---|---------|------|--------|----------|-------|
| 1 | Title/Abstract | {item text} | PRESENT | Title | {notes} |
| 2 | Introduction | {item text} | MISSING | -- | {suggestion} |
| ... | ... | ... | ... | ... | ... |
```

#### Part C: Action Items (for MISSING and PARTIAL)

```
### Action Items (Priority Order)

1. **[MISSING] Item {N}: {item name}**
   - Required: {what needs to be added}
   - Suggested location: {section, paragraph}
   - Example text: "{draft sentence or phrase}"

2. **[PARTIAL] Item {N}: {item name}**
   - Current: {what was found}
   - Needed: {what additional detail is required}
   - Suggested revision: "{draft revision}"
```

Order action items by:
1. Items most journals enforce strictly (e.g., ethics approval, registration, sample size)
2. Items in the Methods section (easiest to fix)
3. Items in other sections

#### Part D: Machine-Readable JSON Summary

Append a fenced JSON block at the end of the report. This enables `/write-paper` Phase 7 and `/orchestrate` to parse compliance results programmatically. This block **MUST** be present when invoked with `--json` flag or when called from `/write-paper` Phase 7. It SHOULD also be present in standard invocations (appended after Part C).

```json
{
  "check_reporting_version": "1.0",
  "manuscript_title": "...",
  "guideline": "STARD-AI",
  "guideline_version": "2025",
  "date": "YYYY-MM-DD",
  "total_items": 40,
  "present": 32,
  "partial": 4,
  "missing": 3,
  "na": 1,
  "compliance_pct": 88.9,
  "action_items": [
    {
      "item_number": 12,
      "section": "Methods",
      "item_name": "Sample size justification",
      "status": "MISSING",
      "suggested_location": "Methods, after participant description",
      "suggested_fix": "Add: 'The sample size was determined based on [rationale]. A minimum of [N] cases was required to achieve [target] precision for the primary endpoint.'",
      "fixable_by_ai": true
    },
    {
      "item_number": 7,
      "section": "Methods",
      "item_name": "Blinding of index test to reference standard",
      "status": "PARTIAL",
      "current_text": "Readers were blinded",
      "needed": "Specify what readers were blinded to (reference standard results, clinical information, other reader results)",
      "suggested_fix": "Expand to: 'Readers interpreted [index test] images blinded to the reference standard results, clinical information, and other readers' assessments.'",
      "fixable_by_ai": true
    }
  ]
}
```

**Field definitions:**
- `compliance_pct`: `present / (total_items - na) * 100`, rounded to one decimal
- `action_items`: Array of MISSING and PARTIAL items only (PRESENT and N/A excluded)
- `fixable_by_ai`: `true` if the fix involves inserting or expanding text with information available in the manuscript or inferable from context; `false` if it requires external information (e.g., registration number, IRB approval number, specific protocol details only the author knows)
- `suggested_fix`: Concrete draft text that can be inserted or used to expand an existing sentence

---

## Assessment Standards

### Be Strict

- PARTIAL means the item is mentioned but lacks specificity. For example:
  - "We used appropriate statistical tests" = PARTIAL (which tests?)
  - "We used the Mann-Whitney U test for continuous variables and Fisher's exact test for categorical variables" = PRESENT
- A vague reference does not count as PRESENT. The detail level must match what the guideline expects.

### Be Specific in Suggestions

- For MISSING items, provide a draft sentence the user can insert.
- For PARTIAL items, point to the exact gap and suggest specific additions.
- Reference the specific manuscript section where the addition should go.

### Common Gaps to Watch For

These items are frequently missing in medical manuscripts:

1. **Study registration number** (CONSORT, PRISMA, STARD)
2. **Registration / amendment date consistency** (PRISMA 2020, PRISMA-DTA, CONSORT, SPIRIT) — run Step 4c whenever a registration identifier is present
3. **Sample size justification** (CONSORT, STROBE, STARD)
4. **Missing data handling** (all guidelines)
5. **Blinding details** (CONSORT, STARD)
6. **Funding and conflicts of interest** (all guidelines)
7. **Ethics approval with committee name and approval number** (all guidelines)
8. **Data availability statement** (increasingly required)
9. **AI-specific: training/validation/test split details** (TRIPOD+AI, CLAIM, STARD-AI)
10. **AI-specific: model architecture and hyperparameters** (TRIPOD+AI, CLAIM, STARD-AI)
11. **AI-specific: failure mode analysis** (CLAIM, STARD-AI)
12. **AI-specific: fairness/bias assessment** (STARD-AI)
13. **AI-specific: commercial interests and data/code availability** (STARD-AI)

---

## Submission Checklist Export

Many journals require a filled reporting checklist to be submitted alongside the manuscript.
When the user asks for a submission-ready checklist, format the output as:

```
{Guideline Name} Checklist

Manuscript title: {title}
Date: {YYYY-MM-DD}

| Item # | Checklist Item | Reported on Page # | Reported in Section |
|--------|---------------|-------------------|-------------------|
| 1 | {item text} | {page or N/A} | {section} |
| 2 | {item text} | {page or N/A} | {section} |
| ... | ... | ... | ... |
```

Page numbers should be filled in by the user after final formatting. Use section names as placeholders.

---

## Skill Interactions

| When | Call | Purpose |
|------|------|---------|
| During manuscript writing | `/write-paper` Phase 7 | Final compliance check |
| Need to add Methods text | `/write-paper` Phase 3 | Draft missing Methods content |
| Need statistical details | `/analyze-stats` | Generate missing statistical reporting |
| Need flow diagram | `/make-figures` | Generate CONSORT/STARD/PRISMA diagram |

---

## Error Handling

- If the manuscript file cannot be read, ask the user for the correct path.
- If the study type is ambiguous, ask the user to confirm before selecting a guideline.
- If a checklist item is genuinely unclear in its applicability, mark as N/A with justification.
- This is a pre-screening tool. Always remind the user that final compliance should be verified by all co-authors and ideally by a methodologist.

## Language

- Checklist content and compliance report: English
- Communication with user: Match user's preferred language
- Medical terms: English only

## Anti-Hallucination

- **Never fabricate references.** All citations must be verified via `/search-lit` with confirmed DOI or PMID. Mark unverified references as `[UNVERIFIED - NEEDS MANUAL CHECK]`.
- **Never invent clinical definitions, diagnostic criteria, or guideline recommendations.** If uncertain, flag with `[VERIFY]` and ask the user.
- **Never fabricate numerical results** — compliance percentages, scores, effect sizes, or sample sizes must come from actual data or analysis output.
- If a reporting guideline item, journal policy, or clinical standard is uncertain, state the uncertainty rather than guessing.
