---
name: write-protocol
description: Use when drafting an IRB or ethics research protocol. Writes Background, Study Design, Sample Size and Statistical Plan in full prose and leaves institution-specific sections as TODO skeletons. Filling an institutional Word form is /fill-protocol.
metadata:
  triggers: "write protocol, IRB protocol, ethics protocol, research protocol, IRB submission, ethics submission, protocol draft"
---

# Write-Protocol Skill

Draft the scientific core of an IRB/ethics protocol and leave institution-specific sections as
`[TODO]` skeletons. Read both reference files before generating a protocol draft:

- `${CLAUDE_SKILL_DIR}/references/protocol_template.md` -- the 10-section structure, per-section
  guidance, and the `[TODO]` blocks for Sections 5-9
- `${CLAUDE_SKILL_DIR}/references/ethics_checklist.md` -- jurisdiction-specific ethical requirements

## Inputs

Collect the required inputs before generating; ask for any that are missing.

- **Required**: research question / hypothesis (specific, testable); study type (retrospective
  cohort, prospective cohort, cross-sectional, RCT, diagnostic accuracy, case-control, case
  series); target population (who, where, when); primary outcome; secondary outcomes (if any).
- **Optional**: key references (DOIs or search terms); institution name (header and ethics
  guidance); regulatory context -- Korea (PIPA), US (HIPAA/Common Rule), EU (GDPR), other.

Use prior skill outputs directly when they exist; when they do not, ask the user or call the skill:

- **design-study**: design recommendations, analysis unit, comparator design, validation strategy.
- **calc-sample-size**: `protocol/sample_size_justification.md` (canonical IRB-ready prose) and
  `protocol/sample_size_calc.{R,py}` (reproducible code).
- **search-lit**: Background references with verified citations.
- **define-variables**: `variable_operationalization.md` -- literature-grounded definitions,
  cutoffs, DB-variable mappings for the Methods section. **Precondition**: if the study is
  observational and no operationalization artifact exists, call `/define-variables` before
  drafting Methods. Do not invent phenotype/cutoff definitions from the data dictionary inside
  this skill.

---

## Protocol Structure -- 10 Sections

### Core Sections (Fully Generated)

#### Section 1: Background and Rationale (400-600 words)

Full paragraphs, no bullet points, flowing from clinical context (disease burden, current
practice) through the knowledge gap and rationale (what this study adds) to the research question
or hypothesis. Call `/search-lit` if key references are not provided. Cite a reference only with a
`/search-lit`-confirmed DOI or PMID; otherwise mark it `[UNVERIFIED - NEEDS MANUAL CHECK]`.

#### Section 2: Study Design and Eligibility Criteria (300-500 words)

Prose covering the study design with its justification (why this design answers this question),
the setting (single-center vs multi-center, institution description) and the study period,
followed by numbered inclusion and numbered exclusion criteria. If design-study output is
available, incorporate its analysis unit (patient vs lesion vs exam), comparator design,
validation strategy, and leakage risks with mitigations. Mark any clinical definition, diagnostic
criterion or guideline recommendation you cannot confirm `[VERIFY]` and ask the user.

#### Section 3: Sample Size Justification (150-300 words)

- If `protocol/sample_size_justification.md` exists (calc-sample-size output): embed it VERBATIM.
  Do not rephrase numbers.
- If not available: prompt the user to run `/calc-sample-size` first; only fall back to a basic
  justification if the user explicitly declines.
- Must include: test type, expected effect size (with literature source), alpha level, power,
  attrition adjustment.
- Final statement: "We plan to enroll N participants."

#### Section 4: Statistical Analysis Plan (300-500 words)

Full prose covering: descriptive statistics (continuous as mean (SD) or median (IQR); categorical
as count (%)); the primary analysis (test, assumptions, handling of violations); pre-specified
secondary analyses; pre-specified subgroup analyses with interaction tests; missing-data handling
(complete case, multiple imputation, sensitivity analysis); software name and version (e.g.,
R 4.4.0, Python 3.12, SAS 9.4); two-sided alpha = 0.05 unless otherwise justified.

### Skeleton Sections (TODO Markers)

Sections 5-9 are the `[TODO]` blocks from `protocol_template.md`, copied as they are; never fill
them with invented institutional content.

- Section 5: Study Title and Registration
- Section 6: Data Collection and Management
- Section 7: Ethical Considerations -- also add the template's jurisdiction guidance for the
  regulatory context, and use `ethics_checklist.md` for the full checklist.
- Section 8: Timeline and Milestones
- Section 9: Budget

#### Section 10: References

A numbered list of the Section 1 citations, the Section 3 effect-size sources, and any references
in the calc-sample-size output. Every entry has a verified DOI or PMID or is marked
`[UNVERIFIED - NEEDS MANUAL CHECK]`.

---

## Output Format

Generate a single markdown file: `protocol_draft.md`

- All 10 sections with clear numbering (1. through 10.)
- Core sections (1-4) in full prose; the Section 2 eligibility criteria are the only lists
- Skeleton sections (5-9) with `[TODO]` markers clearly visible
- Word count targets noted in comments at the start of each core section
- Institution name in the header if provided

After generating, tell the user which sections are ready for review, which `[TODO]` items need
their input, and the next steps (e.g., "Fill in Section 5 title and registration, then adapt
Section 7 to your IRB form").

## Quality Checks

Before delivering the protocol:

1. **Citation integrity**: every reference has a DOI or PMID, or is marked
   `[UNVERIFIED - NEEDS MANUAL CHECK]`
2. **Internal consistency**: sample size in Section 3 matches the analysis plan in Section 4
3. **Design alignment**: study type in Section 2 matches the statistical approach in Section 4
4. **TODO completeness**: all institution-specific items have `[TODO]` markers
5. **Word counts**: core sections fall within target ranges
6. **No AI patterns**: avoid phrases like "it is worth noting", "comprehensive", "plays a crucial role"
