---
name: check-reporting
description: Check manuscript compliance with medical research reporting guidelines. Supports STROBE, CONSORT, STARD, TRIPOD+AI, ARRIVE, PRISMA, CARE, SPIRIT, CLAIM, and their AI extensions. Generates item-by-item assessment with PRESENT/MISSING/PARTIAL status.
triggers: checklist, reporting guideline, 보고 가이드라인, STROBE, CONSORT, STARD, TRIPOD, PRISMA, ARRIVE, CARE, CLAIM, SPIRIT, compliance check
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
  - `TRIPOD_AI.md` -- prediction models with AI/ML (CC BY 4.0)
  - `PRISMA_2020.md` -- systematic reviews (CC BY)
  - `ARRIVE_2.md` -- animal studies (CC0)
- **External checklists (not bundled due to license restrictions)**:
  Users should download these from official sources when needed:
  - CONSORT 2010 -- https://www.consort-statement.org
  - CARE -- https://www.care-statement.org
  - SPIRIT -- https://www.spirit-statement.org
  - CLAIM 2024 -- https://pubs.rsna.org/doi/10.1148/radiol.2020200267
  If a local checklist file is not found, the skill constructs checklist items from its knowledge of the guideline.

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
| Case report | CARE | -- |
| Study protocol | SPIRIT | SPIRIT-AI |
| Animal study | ARRIVE 2.0 | -- |
| AI/ML study in clinical imaging | CLAIM 2024 | -- |
| Educational study | SQUIRE 2.0 (if applicable) | -- |

**Rules:**
- If the study involves AI/ML, always apply the AI extension in addition to the base guideline.
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
2. **Sample size justification** (CONSORT, STROBE, STARD)
3. **Missing data handling** (all guidelines)
4. **Blinding details** (CONSORT, STARD)
5. **Funding and conflicts of interest** (all guidelines)
6. **Ethics approval with committee name and approval number** (all guidelines)
7. **Data availability statement** (increasingly required)
8. **AI-specific: training/validation/test split details** (TRIPOD+AI, CLAIM)
9. **AI-specific: model architecture and hyperparameters** (TRIPOD+AI, CLAIM)
10. **AI-specific: failure mode analysis** (CLAIM)

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
