---
name: check-reporting
description: Check manuscript compliance with medical research reporting guidelines. Supports 32 guidelines including STROBE, CONSORT, STARD, STARD-AI, TRIPOD, TRIPOD+AI, ARRIVE, PRISMA, PRISMA-DTA, PRISMA-P, CARE, SPIRIT, CLAIM, MI-CLEAR-LLM, SQUIRE 2.0, CLEAR, MOOSE, GRRAS, SWiM, AMSTAR 2, and risk of bias tools (QUADAS-2, QUADAS-C, RoB 2, ROBINS-I, ROBINS-E, ROBIS, ROB-ME, PROBAST, PROBAST+AI, NOS, COSMIN, RoB NMA). Generates item-by-item assessment with PRESENT/MISSING/PARTIAL status.
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
  - `CONSORT.md` -- randomised controlled trials, CONSORT 2025 (CC BY 4.0, Hopewell et al. BMJ 2025)
  - `CARE.md` -- case reports, CARE 2013 (CC BY-NC 4.0, Gagnier et al. J Clin Epidemiol 2014)
  - `SPIRIT.md` -- clinical trial protocols, SPIRIT 2025 (CC BY 4.0, Chan et al. BMJ 2025)
  - `CLAIM_2024.md` -- AI/ML in clinical imaging, CLAIM 2024 Update (RSNA open access, Tejani et al. Radiol Artif Intell 2024)
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
- Fail-fast contract: if a routed guideline has no vendored checklist file, the skill does **not** silently construct items from memory. It halts with a `MISSING_CHECKLIST_CONTRACT_VIOLATION` and surfaces the gap. A from-memory assessment is allowed only with the explicit `--allow-from-memory` opt-in, and that report must be clearly labelled NON-AUTHORITATIVE. See Step 2 and `scripts/check_checklist_exists.py`.
- **Critical-item floor**: `${CLAUDE_SKILL_DIR}/references/critical_item_floor.md` -- the small set of non-waivable items per study type (presence outranks the headline %), plus the AI/radiomics methodological-quality / risk-of-bias instruments (PROBAST+AI, METRICS/RQS, APPRAISE-AI) kept distinct from their reporting counterparts. Loaded in Step 4f.

---

## Workflow

### Step 0: Existing-checklist staleness pre-check

If a checklist already exists for this project (`qc/reporting_checklist.json` or a prior `.md` report), verify it targets the **current** manuscript before reusing it — a checklist generated against an older version carries stale section/line references and a stale version label that a reviewer who cross-checks will catch:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_checklist_version.py" \
  --checklist qc/reporting_checklist.json --manuscript manuscript_v8.md
```

A non-zero exit means the existing checklist is stale (older `target_version`, changed `source_sha256`, different `target_manuscript`) or pre-dates the version contract — regenerate it against the current manuscript (Steps 1–5) rather than reusing it. Every report you generate must carry the `target_manuscript` / `target_version` / `source_sha256` fields (Part A header + Part D JSON) so this check works next round.

### Step 1: Select Guideline

Determine the appropriate reporting guideline. Auto-detect from the manuscript type or accept
user specification.

**Auto-detection mapping:**

| Study Type | Primary Guideline | AI Extension |
|------------|------------------|--------------|
| Observational study | STROBE | -- |
| Randomized controlled trial | CONSORT 2025 | CONSORT-AI |
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
| Study protocol | SPIRIT 2025 | SPIRIT-AI |
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

1. **Run the fail-fast guard first** for every guideline you intend to apply:

   ```bash
   python "${CLAUDE_SKILL_DIR}/scripts/check_checklist_exists.py" --guideline "STARD-AI"
   ```

   - Exit 0 → the vendored checklist exists; read it from
     `${CLAUDE_SKILL_DIR}/references/checklists/` and proceed.
   - Exit 1 (`MISSING_CHECKLIST_CONTRACT_VIOLATION`) → the guideline is routed
     but no checklist file is vendored. **Do not construct items from memory.**
     Halt, report the violation to the user, and stop unless they explicitly
     opt in (next bullet).
   - Exit 2 (`UNKNOWN_GUIDELINE`) → the name is not recognised; confirm the
     correct guideline with the user.

2. **No silent fallback.** A from-memory checklist is permitted only when the
   user explicitly accepts it — re-run the guard with `--allow-from-memory`
   (exit 0 + a NON-AUTHORITATIVE warning). In that case the output report MUST
   carry a prominent banner that the assessment was constructed from model
   knowledge and is not backed by a vendored checklist, and `submission_safe`
   must not be asserted on its basis.

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

**Registration-ID format gate:** a PROSPERO ID is `CRD42` + 9 digits = 14 characters
(`^CRD42\d{9}$`, e.g. `CRD42024500001`). Run `grep -oE 'CRD42[0-9]+' manuscript.md` and
assert each match is 14 characters long; a 15-character ID (a stray inserted digit) is a
transcription error logged as `[REGISTRATION-TIMING]` (`fixable_by_ai: false` — verify against
the live PROSPERO record, do not guess the correct digit).

**Flagging:** any failure is logged in Part C Action Items with label
`[REGISTRATION-TIMING]`. `fixable_by_ai: false` when reconciliation requires an external
amendment filing; `true` only when the fix is a Methods-text insertion of a date already
disclosed elsewhere. Part D JSON includes a `registration_timing` object
(registry, id, initial_registration_date, amendments[], timing_consistency, findings[]).

**Load-on-demand procedural detail** (exact item-by-item procedure, JSON schema,
flagging edge cases): `${CLAUDE_SKILL_DIR}/references/step4c_registration_timing.md`.

### Step 4d: PRISMA Figure 1 Arithmetic & Cross-Reference Audit

**Applies to:** systematic reviews and meta-analyses using PRISMA 2020 / PRISMA-DTA /
PRISMA-P. Triggers when Item 16a (flow diagram) is PRESENT.

**Why this step exists:** the flow diagram is a single checklist item and can pass Step 4
visually while still containing arithmetic errors (records screened ≠ identified − duplicates;
sought-for-retrieval ≠ screened − excluded) or text↔figure number disagreements. Senior
MA reviewers commonly require strict PRISMA 2020 diagram conformance and explicit body↔
figure number agreement; reviewers who detect these mismatches lose confidence in the
study's data integrity immediately.

**Four arithmetic checks:**
1. records screened = records identified − duplicates removed
2. records sought-for-retrieval = records screened − records excluded (screening)
3. reports retrieved = sought − reports not retrieved
4. studies included = reports assessed for eligibility − reports excluded (with reasons)

**Two cross-reference checks:**
- Body text PRISMA numbers (e.g., "315 records identified, 122 duplicates removed,
  186 records screened") match Figure 1 box labels 1:1.
- Reasons for exclusion (Methods + Figure legend) agree on counts and category names.

**Procedure:**
1. Extract numbers from manuscript Results / PRISMA flow paragraph (regex: integers near
   keywords `identified`, `duplicates`, `screened`, `excluded`, `sought`, `retrieved`,
   `assessed`, `included`).
2. Extract numbers from Figure 1 source — preferred order: (a) `analysis/figures/Figure1_PRISMA.md`
   markdown manifest, (b) caption text in `manuscript.md`, (c) PPTX text run if `.pptx`
   exists, (d) manual entry from PNG/SVG.
3. **Cross-check `analysis/figures/_figure_manifest.md`** (produced by `/make-figures`):
   verify that the row whose `Type = prisma` (or `Type = prisma-dta`) points at the same
   file path used as the audit source, and that the row's `Critic` field is `yes` or
   `partial` (not `no`). A missing manifest row, mismatched path, or `Critic = no` flag
   logs `[MANIFEST-XREF]` (advisory) — the arithmetic check still runs against the source
   identified in step 2. Skip this sub-step if `_figure_manifest.md` does not exist (older
   projects).
4. Run 4 arithmetic checks; emit PRESENT / MISSING / MISMATCH per equation.
5. Run 2 cross-reference checks; emit PRESENT / MISSING / MISMATCH per number.
6. Output `qc/prisma_figure_audit.json` and a short table.

**Flagging:** any MISMATCH or arithmetic failure logs a Part C Action Item with label
`[PRISMA-FIGURE]`. `fixable_by_ai: false` (numbers must be reconciled by the author).

**Load-on-demand procedural detail** (exact regex set, JSON schema, edge cases —
duplicates handled across databases, citation searching strand, dual-reviewer screening):
`${CLAUDE_SKILL_DIR}/references/step4d_prisma_figure_audit.md`.

**Cross-cutting**: integrates with `~/.claude/rules/numerical-safety.md` (PRISMA 5-way
consistency: text ↔ Figure ↔ extraction CSV ↔ analysis script ↔ supplementary).

### Step 4e: Reporting-Framework Naming Audit

**Applies to:** any manuscript that invokes an AI/extension reporting framework
(PROBAST+AI, STARD-AI, TRIPOD+AI, TRIPOD-LLM, CONSORT-AI, SPIRIT-AI, PRISMA-DTA, QUADAS-C).

**Why this step exists:** a base reporting tool and its extension are distinct instruments
with separate citations (manuscript-style-classical §14). Step 1 routes to the right
checklist but does not police how the framework is *named* in prose. The recurring failures
are: invoking an extension without ever naming or citing the base instrument it extends;
mixing `+AI` and `-AI` hyphenation for one family within a single document; coining item
labels like "12-AI"; and waving at "recent guidance" instead of naming the framework.

**Run the deterministic gate:**

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
table, load `${CLAUDE_SKILL_DIR}/references/critical_item_floor.md` and check the small set
of **non-waivable** items for this study type. A MISSING critical item is surfaced as a
**Critical gap** and becomes the report's headline regardless of the overall percentage —
a high percentage with a missing critical item (undefined reference standard, no
leakage-controlled partition, calibration absent for a prediction model, an unreconciled
flow diagram) is not "broadly acceptable."

For AI/ML and radiomics manuscripts, also confirm the chosen **methodological-quality /
risk-of-bias** instrument (PROBAST+AI, METRICS/RQS, APPRAISE-AI) and its non-waivable
concerns — a fully *reported* paper can still be at high risk of bias. Keep these distinct
from the reporting counterparts (CLEAR, DECIDE-AI), which route through the normal checklist
flow. Do not assert a numeric journal desk-reject threshold; the hard signals are a missing
critical item and the journal's own required elements.

### Step 5: Generate Report

Produce a structured compliance report in two parts.

#### Part A: Summary

```
## Reporting Guideline Compliance Report

Manuscript: {title}
Target manuscript file: {manuscript filename, e.g. manuscript_v8.md}
Target version: {version token from the filename or frontmatter, e.g. v8}
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

Critical items (Step 4f): {present}/{total} present.{ if any missing: " Critical gap — " + each MISSING critical item with the section it belongs in. This, not the percentage, is the headline.}
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
  "check_reporting_version": "1.1",
  "manuscript_title": "...",
  "target_manuscript": "manuscript_v8.md",
  "target_version": "v8",
  "source_sha256": "<first 12 hex chars of sha256 of the manuscript file bytes>",
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

## PRISMA Cascade Arithmetic Auto-Verify

PRISMA 2020 flow diagrams chain a cascade of subtractions (database
records → after dedup → title/abstract screened → full-text reviewed →
included in synthesis). Off-by-one errors in the prose cascade are a
high-frequency reviewer red flag (e.g., `151 + 108 + 39 + 1 + 1 + 4 =
304` followed by a prose summary "305" four lines later).

When PRISMA 2020 or PRISMA-DTA is selected and round-by-round
screening TSV artifacts are available, run the cascade auto-verify:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/prisma_cascade_check.py" \
    --round1 2_Screening/round1.tsv \
    --round2 2_Screening/round2.tsv \
    --round3 2_Screening/round3_adjudication.tsv \
    --manuscript manuscript.md \
    --out qc/prisma_cascade.json
```

The script:
1. Reads the round TSVs and counts `INCLUDE` / `EXCLUDE` / `MAYBE`
   decisions per round.
2. Computes the cascade arithmetic from raw decisions (no prose).
3. Optionally grep the manuscript for matching stage-count claims and
   emits per-stage drift when the prose disagrees.

Treat any `manuscript_drift` entry as a P0 blocker — fix the prose to
match the computed cascade and re-run.

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

---

## Gates

| Gate | Severity | Trigger | Action on fail |
|---|---|---|---|
| Mandatory items present | ENFORCED at submission | < 100% of guideline-mandatory items marked PRESENT | Auto-fix MISSING items where text exists; otherwise route to `/write-paper` Phase 7 for re-draft |
| Step 4d PRISMA Figure 1 arithmetic & cross-reference audit (PRISMA / PRISMA-DTA only) | ENFORCED for SR/MA | flow numbers don't sum (e.g., screened ≠ included + excluded), or in-text counts mismatch flow diagram | HALT; reconcile against extraction artifacts |
| Optional items (e.g., supplementary AI declarations) | ADVISORY | < 80% of optional items present | warn; user accepts |
| Cross-reporting-guideline routing (study type → guideline) | ENFORCED | study type undeclared or guideline missing | Ask user; do not silently default |
