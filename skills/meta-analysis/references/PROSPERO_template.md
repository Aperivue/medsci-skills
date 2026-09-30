# PROSPERO Registration Template

## Overview

PROSPERO (International Prospective Register of Systematic Reviews) requires completion of
a structured web form. This template provides field-by-field guidance with word limits and
common pitfalls from real registration experience.

**Key constraint**: Initial registrations are NOT allowed after data extraction is completed.
Searching and screening may be completed.

---

## Form Fields Reference

### REVIEW TITLE AND BASIC DETAILS

#### 1. Review title (max 50 words)
Include: study design (systematic review, meta-analysis, pooled analysis), condition,
intervention, population qualifier if relevant.

#### 2. Review question (max 250 words)
Structure around PICO/PIRD. State both primary and secondary objectives clearly.
For pooled analysis designs, distinguish between pooled proportion and comparative questions.

#### 3. Condition/domain being studied (max 200 words)
Define the condition. Explain why it matters. Note the clinical gap.

#### 4. Keywords
Semicolon-separated. Include MeSH-equivalent terms.

---

### ELIGIBILITY CRITERIA

#### 5. Population (max 200 words)
State included and excluded populations. Include age, disease status, anatomical specifics.

#### 6. Intervention/exposure (max 200 words)
Define all eligible interventions with specifics (technique, device, imaging guidance).
State minimum reporting requirement ("must report at least one clinical outcome").

#### 7. Comparator/control (max 200 words)
If both comparative and single-arm studies are included, state this explicitly:
"For the comparative analysis, [comparator description]. For the pooled proportion analysis,
single-arm studies without a comparator are also included."

#### 8. Type of study to be included (max 150 words)
List included and excluded study designs separately. Be specific about minimum sample size
(e.g., "case reports with fewer than 5 patients excluded").

---

### SEARCHING AND SCREENING

#### 9. Searches (max 300 words)
Name databases, date range, language restrictions. Reference supplementary search strategies.

#### 10. Search strategy (max 300 words)
Show actual search blocks with Boolean structure. No need for full line-by-line syntax here
(reference supplementary materials for that).

#### Sub-fields in the web form:
- **Search for unpublished studies**: Yes/No (select based on protocol)
- **Main databases**: Select from checklist (PubMed, Embase.com vs Embase via Ovid — distinguish!)
- **Language restrictions**: State explicitly
- **Date restrictions**: State explicitly
- **Other methods**: Check ONLY what was actually done:
  - reference list checking (backward citation)
  - contacting authors
  - conference proceedings
  - trial registers
  - forward citation searching (snowballing)
  - **WARNING**: Do not check methods you did not perform — reviewers may ask for results
- **Link to search strategy**: Reference protocol or supplementary materials
- **Selection process**: "Two reviewers independently..." with disagreement resolution
- **Other info about screening**: PRISMA flow diagram reference (optional)

---

### DATA COLLECTION PROCESS

#### 11. Data extraction (max 300 words)
List extracted variables by category: study characteristics, population, intervention,
outcomes. State unit of analysis policy (patient vs tumor level). If Kaplan-Meier
reconstruction is used, cite methods (Tierney 2007, Guyot 2012).

#### Sub-fields:
- **Extraction method**: Select "independently by at least two people"
- **Author contact**: Yes/No
- **IPD**: Usually No for standard MA

#### 12. Risk of bias/Quality assessment (max 200 words)
Name tool(s) per study design. If using tools not in the PROSPERO checklist (e.g., JBI),
select "Other" and describe in text.

Common tool mapping:
| Study design | Tool |
|---|---|
| RCT | Cochrane RoB 2 |
| Non-randomized comparative | Newcastle-Ottawa Scale (NOS) or ROBINS-I |
| Single-arm / case series | JBI Critical Appraisal Checklist (select "Other") |
| DTA | QUADAS-3 (QUADAS-2 for a legacy review) |
| Prediction model | PROBAST |

State number of assessors and disagreement resolution.

#### 13. Reporting bias assessment
For pooled proportions: do not promise funnel-asymmetry or Egger/Begg tests — they are
uninterpretable for proportions (see `single_arm_proportion_ma.md` §7).
For comparative (k<10): funnel plot visual inspection only.
Do NOT promise trim-and-fill or contour-enhanced funnel unless actually planned.

#### 14. Certainty assessment
Select "No" unless GRADE or equivalent is explicitly planned in the protocol.
If "Yes": requires Summary of Findings table — significant additional work.

---

### OUTCOMES TO BE ANALYSED

#### 15. Primary outcomes (max 300 words)
Define each outcome precisely: what it measures, how it is defined, at what time points.
State the effect measure (proportion, OR, HR, etc.).

#### 16. Secondary outcomes (max 300 words)
List all secondary outcomes. Include exploratory outcomes that will be "extracted if reported."

---

### PLANNED DATA SYNTHESIS

#### 17. Strategy for data synthesis (max 400 words)
Structure as:
1. **Primary analysis**: model, estimator, transformation
2. **Secondary analysis**: model, estimator, CI adjustment
3. **Heterogeneity**: I-squared, Q test, interpretation thresholds
4. **Publication bias**: methods (reference field 13)
5. **Software**: R packages with versions

#### 18. Subgroups/subsets (max 250 words)
Number and list all pre-specified subgroup analyses.
Number and list all pre-specified sensitivity analyses.
State interaction test method.
Mention leave-one-out if planned.

---

### CURRENT REVIEW STAGE

#### 19. Review stage checklist
| Stage | Allowed at registration |
|---|---|
| Pilot work | Started or Completed OK |
| Formal searching | Started or Completed OK |
| Screening | Started or Completed OK |
| **Data extraction** | **Not started or Started ONLY** |
| Risk of bias | Not started |
| Data synthesis | Not started |

**CRITICAL**: If data extraction is "Completed", registration will be REJECTED.
If protocol restructuring invalidates prior extraction → defensible to mark "Not started."

#### 20. Review status
Usually: "The review is planned or ongoing"

---

### REVIEW AFFILIATION, FUNDING AND PEER REVIEW

#### 21. Review team members
All authors with ORCID and affiliation. One must be Guarantor + Named Contact.
Guarantor = typically first or corresponding author.

#### 22. Funding
- If no funding: "This review received no specific funding from any agency in the public,
  commercial, or not-for-profit sectors."
- Do NOT write "supported by academic institutions" unless there is actual institutional funding.

#### 23. Peer review
Usually "Not peer reviewed" for initial registration.

---

### ADDITIONAL INFORMATION

#### 24. Additional info (max 250 words)
Standard text: "Any important protocol amendments will be documented in the PROSPERO record
and clearly reported in the final publication."

#### 25. MeSH terms
Auto-generated but editable. Review and add missing terms (e.g., Microwaves for MWA studies).

---

## Common Pitfalls Checklist

Before submitting, verify:

- [ ] **HTML entities**: Preview PDF and check all `>=`, `<`, `&` symbols display correctly
      (common breakage: `&gt;`, `&lt;`, `&amp;` appearing literally)
- [ ] **Word limits**: Each field within stated maximum
- [ ] **Database names**: Embase.com vs Embase via Ovid (different options in form)
- [ ] **Other methods**: Only checked items actually performed
- [ ] **RoB tool**: JBI requires "Other" selection (not in standard list)
- [ ] **Certainty/GRADE**: "No" unless explicitly planned with SoF table
- [ ] **Funding text**: Matches actual funding status
- [ ] **Data extraction stage**: Not marked as "Completed"
- [ ] **Similar records**: All reviewed and confirmed "not similar"
- [ ] **All authors**: Listed with correct ORCID and affiliation
- [ ] **End date**: In the future (update if past)
- [ ] **Comparator field**: Addresses both comparative and single-arm inclusion if applicable

---

## Output Format

When generating PROSPERO content for the user:
1. Produce a single Markdown file with all fields, word counts per field
2. Convert to DOCX via pandoc for copy-paste convenience
3. Flag any fields requiring user decision (e.g., author contact, unpublished search)
4. Include the Common Pitfalls Checklist at the end
