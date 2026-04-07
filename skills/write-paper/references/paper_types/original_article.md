# Original Article — IMRAD Template

## Overview

Standard template for medical original research articles. Follows the Introduction, Materials and Methods, Results, and Discussion (IMRAD) structure used by virtually all biomedical journals.

---

## Title

- Concise and specific, under 20 words.
- Include the study design if space allows (e.g., "A Retrospective Cohort Study").
- Avoid questions, abbreviations (except universally known ones like CT, MRI, AI), and clever wordplay.
- Good: "Deep Learning Detection of Pulmonary Embolism on CT Angiography: A Multicenter Validation Study"
- Bad: "Can AI Find Clots? A Novel Approach Using Advanced Neural Networks"

---

## Abstract (Structured, 250 words max)

Four sections matching the journal's required headings (common variants shown):

### Purpose / Objective
- One to two sentences stating the study aim.
- Template: "To {evaluate/compare/assess/determine} {what} in {population/context}."

### Materials and Methods
- Study design, setting, dates, participants (N), key methods, primary outcome measure, statistical approach.
- Three to four sentences maximum.

### Results
- Key findings with specific numbers (effect sizes, CIs, p-values).
- Start with primary endpoint, then most important secondary findings.
- Three to four sentences maximum.

### Conclusion
- One to two sentences. Restate the main finding and its implication.
- Do NOT end with "further studies are needed."
- Be specific: "This model achieved diagnostic accuracy comparable to fellowship-trained radiologists and may reduce interpretation time for emergency CT studies."

---

## Introduction (3-4 paragraphs, ~400-500 words)

### Paragraph 1: Clinical Context
- Establish the clinical importance of the topic.
- Cite prevalence, incidence, or burden data.
- Describe current clinical practice or diagnostic approach.

### Paragraph 2: Knowledge Gap
- What is known from prior work (cite key studies).
- What remains unknown, uncertain, or unresolved.
- Why this gap matters clinically.

### Paragraph 3: Study Objective
- State the specific aim of this study.
- Include hypothesis if applicable (for confirmatory studies).
- Template: "The purpose of this study was to {aim}. We hypothesized that {hypothesis}."
- Optional final sentence previewing the approach: "We evaluated this in a {study design} of {N} patients at {setting}."

### Rules
- Do not review the entire literature; cite only what is needed to establish the gap.
- Do not describe methods or results.
- Do not state conclusions.
- Funnel structure: broad context to narrow focus.

---

## Materials and Methods (~800-1200 words)

### 3.1 Study Design and Setting
- One paragraph: design (retrospective/prospective, single/multicenter), institution(s), date range.
- Template: "This {retrospective cohort / prospective cross-sectional / etc.} study was conducted at {institution} between {start date} and {end date}."

### 3.2 Participants / Study Population
- Inclusion and exclusion criteria, stated explicitly.
- How participants were identified (database query, consecutive enrollment, random sampling).
- Final sample size with brief explanation of exclusions.
- For AI studies: dataset split (training/validation/test) with rationale.

### 3.3 Procedures / Intervention / Index Test
- Describe what was done in enough detail for replication.
- For imaging: scanner model, sequence parameters, contrast protocol.
- For AI: model architecture, input data, preprocessing, training procedure, hyperparameters.
- For reader studies: number of readers, experience level, blinding, reading environment.

### 3.4 Outcome Measures
- Define primary and secondary endpoints explicitly.
- State the reference standard and how it was established.
- Define any composite endpoints or derived variables.

### 3.5 Statistical Analysis
- Descriptive statistics approach (mean +/- SD or median [IQR]).
- Specific tests for each comparison (name the test, state the rationale).
- Significance level (two-sided, alpha = 0.05).
- Software and version.
- Sample size justification if applicable.
- See `section_templates/methods_statistical.md` for common paragraph templates.

### 3.6 Ethics
- IRB/Ethics committee approval (name, protocol number).
- Informed consent status (obtained, waived with reason).
- For retrospective studies: "The institutional review board of {institution} approved this retrospective study and waived the requirement for informed consent."

---

## Results (~800-1200 words)

### 4.1 Study Population
- Start with the total number screened, excluded (with reasons), and included.
- Reference the flow diagram (Figure 1) if applicable.
- Describe demographics and baseline characteristics, referencing Table 1.
- Template: "A total of {N} patients ({N} male, {N} female; mean age, {X} +/- {Y} years) were included."

### 4.2 Primary Endpoint
- Present the main result with effect size and 95% CI.
- Reference the relevant table or figure.
- Template: "The {metric} was {value} (95% CI, {lower}-{upper}; P = {value})."

### 4.3 Secondary Endpoints
- Present in order of importance or in the order listed in Methods.
- Each gets its own paragraph or sub-paragraph.

### 4.4 Subgroup and Sensitivity Analyses
- Present if pre-specified in Methods.
- Acknowledge if exploratory (not powered for subgroup differences).

### Rules
- Do NOT interpret findings; state them. Results answers "What?" only — never "Why?"
- Every table and figure must be referenced in the text.
- Numbers in text must match tables exactly.
- Report exact p-values; use "P < .001" only when truly below 0.001.
- Present data in the same order as Methods subsections.
- NO comparisons with prior literature (save for Discussion).
- NO causal language ("caused," "led to," "due to") — use "was associated with."
- NO evaluative adjectives without numbers ("high," "notable," "remarkable").
- NO hedge words implying interpretation ("suggests," "implies," "indicates importance").
- Banned openers: "Interestingly," "Notably," "Remarkably," "Surprisingly," "As expected."

---

## Discussion (4-5 paragraphs, ~800-1200 words)

> **Before writing:** The user should provide anchor papers (3-5 key references for
> comparison) and key findings to emphasize. See SKILL.md Phase 5a for the interactive
> planning gate. If not provided, identify anchor papers from the reference list.

### Paragraph 1: Summary of Key Findings
- Restate the principal findings in the context of the study aim.
- Do not repeat exact numbers from Results (paraphrase).
- One paragraph, 3-5 sentences.

### Paragraphs 2-3: Comparison with Prior Literature (anchor paper driven)
- Organize around anchor papers provided by the user.
- For each anchor paper: state their finding → compare with ours → explain discrepancy.
- Pattern: "Smith et al. [ref] reported {X} in {population}. In contrast/Similarly, our
  study found {Y}, which may be attributable to {methodological/population difference}."
- Include both concordant and discordant studies.

### Paragraph 4: Clinical Implications
- What does this mean for clinical practice, training, or future research?
- Be specific: "{AI tool} could be integrated into {specific workflow} to {specific benefit}."
- Avoid vague statements about "future directions."

### Paragraph 5: Limitations
- Ordered by severity (most impactful first).
- Be specific and honest.
- Do NOT start with "Our study has several limitations."
- For each limitation: (a) what it is, (b) how it was mitigated, (c) direction of residual bias.
- Template: "This study has limitations. First, the retrospective design at a single
  institution limits generalizability; however, the multicenter external test set partially
  addresses this, and any selection bias would likely inflate performance estimates."

### Conclusion (within Discussion, final paragraph or sentence)
- One to two sentences restating the single most important finding.
- Must be a citable statement — memorable and specific.
- Template: "In summary, {main finding} in {context}, suggesting {implication}."

---

## References

- Typically 30-40 for original articles.
- Prioritize recent references (within 5 years) for establishing current knowledge.
- Include seminal/classic references where appropriate.
- Every citation must be referenced in the text.
- Self-citation should be limited and justified.

---

## Tables

- **Table 1**: Demographics and baseline characteristics (always required).
  - Columns: overall cohort, comparison groups (if applicable).
  - Rows: age, sex, relevant clinical variables.
  - Include p-values for between-group comparisons if relevant.
- **Table 2+**: Results tables (primary/secondary endpoints, model performance, etc.).
- Use footnotes for abbreviations and statistical details.
- Do not duplicate data that is better shown in a figure.

## Figures

- **Figure 1**: Flow diagram (CONSORT/STARD/PRISMA as appropriate).
- Additional figures: performance curves (ROC, calibration), representative images, forest plots.
- Each figure needs a descriptive legend that allows the figure to be understood without reading the text.
- Minimum 300 dpi resolution for submission.

---

## Checklist Before Submission

- [ ] Title under 20 words, specific and informative
- [ ] Abstract numbers match Results/Tables
- [ ] Introduction ends with clear objective
- [ ] Methods sufficient for replication
- [ ] All tables/figures referenced in text
- [ ] Numbers consistent between text, tables, and figures
- [ ] Limitations discussed honestly
- [ ] All reporting guideline items addressed
- [ ] References complete and correctly formatted
- [ ] Word count within journal limits
