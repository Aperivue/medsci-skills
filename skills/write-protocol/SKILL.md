---
name: write-protocol
description: >
  IRB/ethics committee research protocol generator. Produces 4 core sections (Background,
  Study Design, Sample Size, Statistical Plan) with full prose, plus 6 skeleton sections
  with TODO markers for institution-specific content. Integrates outputs from design-study,
  calc-sample-size, and search-lit.
triggers: write protocol, IRB protocol, ethics protocol, research protocol, IRB submission, ethics submission, protocol draft
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Write-Protocol Skill

You are helping a medical researcher draft a research protocol for IRB/ethics committee
submission. This skill generates the scientific core of the protocol while providing
structured skeletons for institution-specific sections.

## Scope

This skill generates **4 core sections** with full prose:
1. Background and Rationale
2. Study Design and Eligibility Criteria
3. Sample Size Justification
4. Statistical Analysis Plan

The remaining **6 sections** are provided as structured skeletons with `[TODO]` markers,
because they vary significantly across institutions, countries, and regulatory frameworks.

**Important**: This protocol is a STARTING POINT. Every institution has its own IRB
submission form and requirements. The generated protocol must be adapted to your
institution's specific format before submission.

## Reference Files

- **Protocol template**: `${CLAUDE_SKILL_DIR}/references/protocol_template.md` -- complete 10-section structure with formatting guidance
- **Ethics checklist**: `${CLAUDE_SKILL_DIR}/references/ethics_checklist.md` -- jurisdiction-specific ethical requirements

Read both reference files before generating a protocol draft.

## Cross-Skill Integration

- **Input from design-study**: Study design recommendations, analysis unit, comparator design, validation strategy
- **Input from calc-sample-size**: Sample size calculation results and IRB justification text
- **Input from search-lit**: Background references with verified citations
- **Pipeline position**: search-lit -> design-study -> calc-sample-size -> **write-protocol** -> manage-project

When prior skill outputs are available, incorporate them directly. When they are not,
prompt the user or call the relevant skill.

---

## Communication Rules

- Communicate with the user in their preferred language.
- Use English for all protocol content, statistical terminology, and medical terminology.
- Be explicit about what is generated versus what requires institutional input.

---

## Required Inputs

Collect all required inputs before generating. Ask one question at a time if information is missing.

1. **Research question / hypothesis** -- specific, testable
2. **Study type** -- retrospective cohort, prospective cohort, cross-sectional, RCT, diagnostic accuracy, case-control, case series
3. **Target population** -- who, where, when
4. **Primary outcome** -- what you are measuring
5. **Secondary outcomes** (if any)

## Optional Inputs (enhance quality if available)

6. **design-study output** -- if `/design-study` was already run, load its recommendations
7. **calc-sample-size output** -- if `/calc-sample-size` was already run, load its results and IRB text
8. **Key references** -- DOIs or search terms for background section
9. **Institution name** -- for header and ethics section guidance
10. **Regulatory context** -- Korea (PIPA), US (HIPAA/Common Rule), EU (GDPR), other

---

## Protocol Structure -- 10 Sections

### Core Sections (Fully Generated)

#### Section 1: Background and Rationale (400-600 words)

Generate full prose covering:
- **Clinical context**: disease burden, current practice, knowledge gap
- **Literature support**: call `/search-lit` if key references are not provided; every citation must have a verified DOI or PMID
- **Rationale**: why this study is needed, what it adds to existing evidence
- **Research question**: clear statement of the hypothesis or research question

Do not use bullet points in the output. Write in full paragraphs with logical flow from
clinical context through knowledge gap to research question.

#### Section 2: Study Design and Eligibility Criteria (300-500 words)

Generate full prose plus structured criteria lists:
- **Study design** with justification (why this design answers this question)
- **Setting**: single-center vs multi-center, institution description
- **Study period**: start and end dates or planned duration
- **Inclusion criteria** (numbered list)
- **Exclusion criteria** (numbered list)

If design-study output is available, incorporate its recommendations on:
- Analysis unit (patient vs lesion vs exam)
- Comparator design
- Validation strategy
- Potential leakage risks and mitigations

#### Section 3: Sample Size Justification (150-300 words)

- If calc-sample-size output is available: paste its IRB justification text directly
- If not available: prompt the user to run `/calc-sample-size` or generate a basic justification
- Must include: test type, expected effect size (with literature source), alpha level, power, attrition adjustment
- Final statement: "We plan to enroll N participants."

#### Section 4: Statistical Analysis Plan (300-500 words)

Generate full prose covering:
- **Descriptive statistics**: continuous variables as mean (SD) or median (IQR); categorical variables as count (%)
- **Primary analysis**: statistical test, assumptions, handling of violations
- **Secondary analyses**: pre-specified
- **Subgroup analyses**: pre-specified, with interaction tests
- **Missing data**: handling strategy (complete case, multiple imputation, sensitivity analysis)
- **Software**: name and version (e.g., R 4.4.0, Python 3.12, SAS 9.4)
- **Significance level**: two-sided alpha = 0.05 unless otherwise justified

### Skeleton Sections (TODO Markers)

#### Section 5: Study Title and Registration

```
[TODO: Full study title]
[TODO: Short title / acronym]
[TODO: Clinical trial registry number if applicable (e.g., ClinicalTrials.gov, CRIS)]
[TODO: Protocol version number and date]
```

#### Section 6: Data Collection and Management

```
[TODO: List variables to be collected -- use your institution's case report form (CRF) template]
[TODO: Data collection method (chart review / prospective forms / electronic extraction)]
[TODO: Data storage and security measures (encrypted database, access controls)]
[TODO: Quality assurance procedures (double data entry, range checks)]
[TODO: Data retention period per institutional policy]
```

#### Section 7: Ethical Considerations

```
[TODO: IRB/Ethics committee name and expected submission date]
[TODO: Informed consent process -- or justification for waiver]
[TODO: Patient privacy and data protection measures]
```

Include regulatory guidance by jurisdiction:
- **Korea**: Personal Information Protection Act (PIPA), Bioethics and Safety Act
- **United States**: HIPAA Privacy Rule, Common Rule (45 CFR 46)
- **European Union**: GDPR Article 9 (health data), Clinical Trials Regulation (EU 536/2014)

```
[TODO: Confirm applicable regulations with your IRB office]
```

Refer to `${CLAUDE_SKILL_DIR}/references/ethics_checklist.md` for the full checklist.

#### Section 8: Timeline and Milestones

```
[TODO: Adapt to your project schedule]

| Phase | Activity                              | Duration    | Target Date |
|-------|---------------------------------------|-------------|-------------|
| 1     | IRB approval                          | [X] weeks   | [TODO]      |
| 2     | Data collection / Patient enrollment  | [X] months  | [TODO]      |
| 3     | Data cleaning and analysis            | [X] months  | [TODO]      |
| 4     | Manuscript preparation                | [X] months  | [TODO]      |
| 5     | Submission                            | --          | [TODO]      |
```

#### Section 9: Budget

```
[TODO: Use your institution's budget template]
[TODO: Common cost categories below -- delete or add as needed]
- Personnel (research coordinator, statistician)
- Equipment and supplies
- Software licenses
- Statistical consultation
- Publication fees (open access APC)
- Patient compensation (if applicable)
```

#### Section 10: References

Generate a numbered reference list from:
- Citations used in Section 1 (Background and Rationale)
- Effect size sources from Section 3 (Sample Size Justification)
- Any additional references from calc-sample-size output

All references must have verified DOIs or PMIDs. Mark any unverified references
as `[UNVERIFIED - NEEDS MANUAL CHECK]`.

---

## Output Format

Generate a single markdown file: `protocol_draft.md`

Requirements:
- All 10 sections with clear numbering (1. through 10.)
- Core sections (1-4) in full prose, no bullet points in body text
- Skeleton sections (5-9) with `[TODO]` markers clearly visible
- Word count targets noted in comments at the start of each core section
- Institution name in the header if provided

After generating, inform the user:
1. Which sections are complete and ready for review
2. Which `[TODO]` items require their input
3. Recommended next steps (e.g., "Fill in Section 5 title and registration, then adapt Section 7 to your IRB form")

---

## Quality Checks

Before delivering the protocol:

1. **Citation integrity**: Every reference has a DOI or PMID, or is marked `[UNVERIFIED]`
2. **Internal consistency**: Sample size in Section 3 matches the analysis plan in Section 4
3. **Design alignment**: Study type in Section 2 matches the statistical approach in Section 4
4. **TODO completeness**: All institution-specific items have `[TODO]` markers
5. **Word counts**: Core sections fall within target ranges
6. **No AI patterns**: Avoid phrases like "it is worth noting", "comprehensive", "plays a crucial role"
