# Materials and Methods Writing Guide

Reference for write-paper Phase 3 (Methods).
Loaded on-demand when drafting the Materials and Methods section.

---

## Core Principles

1. **Reproducible**: Another researcher should be able to replicate your study from the Methods alone
2. **Sequential**: Describe procedures in the order they occurred
3. **Concise but thorough**: No unnecessary detail, but no critical omissions
4. **Checklist-aligned**: Every applicable item in the reporting guideline (STARD, STROBE, CONSORT, PRISMA) must have a corresponding sentence in Methods

---

## PICO-Based Structure

Write Methods in PICO order. This provides a natural, logical flow that reviewers expect.

### 1. Study Design + Ethics

- Single-center or multicenter
- Retrospective or prospective
- IRB approval statement with approval number
- Informed consent status ("informed consent was waived for this retrospective study")
- Reporting guideline declaration: "This study was reported in accordance with [STARD/STROBE/etc.]"

### 2. Population (P)

- Study period (start and end dates)
- Inclusion criteria (specific, operationalized)
- Exclusion criteria (with clinical justification for each)
- How patients were identified (database query, consecutive enrollment, etc.)
- **Time zero definition** (critical for retrospective cohorts): State explicitly when follow-up begins. For screening cohorts, time zero is typically the date of the first qualifying examination. For treatment studies, time zero is the date of treatment initiation. Misaligned time zero introduces immortal time bias. If there is a gap between eligibility assessment and time zero (e.g., cohort entry defined by a lab value but follow-up starting at a later visit), describe how this was handled.

**Common pitfalls to avoid**:
- Including inappropriate subjects (e.g., young adults in a pediatric study)
- Excessive interval between index test and reference standard
- Including only elective/surgical cases → selection bias
- Study period too long → equipment/protocol changes
- Including non-contrast studies when contrast is required

### 3. Intervention / Index Test (I)

- Imaging protocol: scanner model (manufacturer, city, country), acquisition parameters
- For CT/MR protocols: ask the technologist for exact parameters
- **Reader setup**: Number of readers, years of experience, subspecialty
  - Using only senior readers → overestimation risk (acknowledge in limitations)
- **Blinding**: State explicitly what information readers were blinded to
- **Quantitative measurements**: How cut-off values were determined
- **Reader disagreement resolution**: Consensus reading, third reader, or statistical approach
- Software used (name, version, manufacturer)

### 4. Comparator / Reference Standard (C)

- Does not need to be the "gold standard" — use the best available method
- State what reference standard was used and why
- Verify:
  - Was the same reference standard applied to all patients?
  - Was the reference standard interpreter blinded to index test results?
  - Was the interval between index test and reference standard reasonable?

### 5. Outcome / Statistical Analysis (O)

- Primary and secondary endpoints defined before describing statistical tests
- Statistical tests matched to data types and study design
- Software and version for statistical analysis
- Significance threshold (typically P < .05, two-sided)

---

## Backbone Article Strategy

**Before writing Methods, identify a backbone article** — a published study with a similar
design in a similar journal that serves as a structural template.

### Selection Criteria

1. Same study design (diagnostic accuracy → diagnostic accuracy, cohort → cohort)
2. Same modality (CT → CT, MRI → MRI)
3. Published in the target journal or a comparable journal
4. Recent publication (within 3-5 years)
5. Well-cited (validated structure)

### How to Use

- Mirror the M&M section structure and subsection order
- Reference the same statistical methods where applicable
- Use similar Table/Figure formatting
- Adopt the reference standard description approach
- **Never copy sentences** — structure and logic only

### Where to Find

1. **Auto-scan `manuscript/_src/refs.bib` first** — Phase 0 Step 5 ranks entries by study design + modality + target journal + PDF attachment. If one strong candidate emerges, the skill proposes it proactively rather than asking.
2. Search the target journal for recent studies with matching design (fallback when refs.bib has no candidate)
3. Check the reference lists of papers you are already citing
4. Ask the corresponding author or mentor for recommendations

---

## Checklist Cross-Reference

When writing Methods, keep the reporting checklist open and verify 1:1 coverage:

| Study Design | Checklist | Key M&M Items |
|-------------|-----------|---------------|
| Diagnostic accuracy | STARD | Blinding, index test detail, reference standard, sample size justification |
| RCT | CONSORT | Randomization, allocation concealment, blinding, ITT analysis |
| Observational | STROBE | Selection criteria, bias direction, confounders, missing data handling |
| Meta-analysis | PRISMA | Search strategy, selection process, data extraction, risk of bias tool |
| AI study | CLAIM 2024 | Data partitioning, model architecture, training details, external validation |

After drafting, go through the checklist item by item. For each item, confirm there is
a corresponding sentence in your Methods. Missing items are the most common reason for
desk rejection.

---

## Terminology Conventions

| Avoid | Use Instead |
|-------|-------------|
| "Increase" / "Decrease" (comparing two groups) | "Higher" / "Lower" or "Larger" / "Smaller" |
| "Show" (for patient actions) | "Had" / "Demonstrated" / "Exhibited" |
| "Prove" | "Suggest" / "Indicate" |
| "Efficacy" (outside RCTs) | "Effectiveness" |
| "Significant" (without p-value) | Always pair with exact p-value |

---

## Self-Check

Before finalizing Methods:

- [ ] Every checklist item has a corresponding sentence?
- [ ] Procedures described in chronological order?
- [ ] Reader blinding explicitly stated?
- [ ] Scanner/software details include manufacturer and location?
- [ ] Reference standard clearly defined with justification?
- [ ] Statistical methods match the data types and endpoints?
- [ ] IRB and consent statements present?
- [ ] Backbone article identified and structure referenced?
