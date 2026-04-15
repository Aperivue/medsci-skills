---
name: meta-analysis
description: Systematic review and meta-analysis pipeline for medical research. Covers protocol registration (PROSPERO), search strategy, screening, data extraction, risk of bias assessment (QUADAS-2/ROBINS-I), statistical synthesis (bivariate/HSROC for DTA, random-effects for intervention), and PRISMA-compliant reporting. Supports both DTA and intervention meta-analyses.
triggers: meta-analysis, systematic review, PROSPERO, forest plot, funnel plot, PRISMA, QUADAS, ROBINS, HSROC, bivariate model, pooled sensitivity, pooled specificity, search strategy, study selection, data extraction form
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Meta-Analysis Skill

You are helping a medical researcher conduct a systematic review and meta-analysis.
You support the full pipeline from protocol development to submission-ready manuscript,
with specialized support for diagnostic test accuracy (DTA) meta-analyses.

## Communication Rules

- Communicate with the user in their preferred language.
- All output documents, code, and checklists in English.
- Medical terminology always in English.

## Reference Files

### Built-in References (`${CLAUDE_SKILL_DIR}/references/`)

- **PROSPERO template**: `${CLAUDE_SKILL_DIR}/references/PROSPERO_template.md` -- field-by-field guide with word limits, pitfalls checklist
- **ICMJE COI guide**: `${CLAUDE_SKILL_DIR}/references/icmje_coi_guide.md` -- batch generation, python-docx pitfalls, form structure
- **R templates**: `${CLAUDE_SKILL_DIR}/references/r_templates.md`
- **Checklists**: `${CLAUDE_SKILL_DIR}/references/checklists/`
  - `PRISMA_DTA.md` -- 27-item checklist
  - `QUADAS2.md` -- 4 domains + signalling questions
  - `ROBINS_I.md` -- 7 domains + pre-assessment + synthesis recommendation
  - `RoB2.md` -- 5 domains + signalling questions + overall judgment
  - `PROBAST.md` -- 4 domains + AI extension + validation studies
  - `NOS.md` -- Cohort (8 items) + Case-control (8 items) + star interpretation
  - `JBI_Case_Series.md` -- 10-item critical appraisal checklist for case series

---

## Meta-Analysis Types

| Type | RoB Tool | Statistical Model | Reporting Guideline |
|------|----------|-------------------|-------------------|
| **DTA** (diagnostic test accuracy) | QUADAS-2 | Bivariate / HSROC | PRISMA-DTA |
| **Intervention** (treatment effect) | RoB 2 (RCT) / ROBINS-I (NRSI) | Random-effects (DL/REML) | PRISMA 2020 |
| **Prognostic** (prediction model) | QUIPS / PROBAST | Random-effects | PRISMA 2020 |
| **Observational** (prevalence/association) | NOS / JBI | Random-effects | MOOSE |

Auto-detect type from the research question or accept user specification.

---

## Workflow Phases

### Phase 1: Protocol Development

**Goal**: Produce a PROSPERO-ready protocol document.

1. **Structure the research question**:
   - DTA: PIRD (Population, Index test, Reference standard, Diagnosis)
   - Intervention: PICO (Population, Intervention, Comparator, Outcome)

2. **Define eligibility criteria**:
   - Study design (cross-sectional DTA, cohort, RCT, etc.)
   - Population characteristics
   - Index test / intervention specifics
   - Comparator / reference standard
   - Outcome measures (Se/Sp for DTA; effect size for intervention)
   - Exclusion criteria with justification

3. **Plan the search**:
   - Minimum 2 databases (PubMed, Embase recommended; add Scopus, Web of Science, Cochrane as needed)
   - Draft Boolean search strategy using PIRD/PICO components
   - Grey literature plan (conference abstracts, trial registries)
   - Language restrictions (state explicitly)
   - Date range with justification

4. **Plan RoB assessment**:
   - Select tool based on type (see table above)
   - State number of independent assessors (minimum 2)
   - Plan for disagreement resolution (consensus, third reviewer)

5. **Plan synthesis**:
   - DTA: bivariate random-effects model (Reitsma) or HSROC (Rutter & Gatsonis)
   - Intervention: random-effects (DerSimonian-Laird or REML)
   - Heterogeneity assessment plan
   - Subgroup / sensitivity analysis plan
   - Publication bias assessment plan

6. **Generate PROSPERO registration document**:
   - Read `${CLAUDE_SKILL_DIR}/references/PROSPERO_template.md` for field-by-field guidance
   - Generate all fields with word counts (stay within limits per field)
   - Structure: title, review question, PICO, searches, data collection, outcomes, synthesis, subgroups, stage, affiliation
   - For mixed designs (comparative + single-arm): explicitly address comparator for both arms
   - For RoB: map tool to study design (NOS for comparative, JBI for case series → select "Other" in form)
   - Output: Markdown + DOCX (via pandoc) for copy-paste into PROSPERO web form
   - Append Common Pitfalls Checklist (HTML entities, word limits, stage constraint)
   - Save to project `7_Submission/` or equivalent directory

### Phase 2: Search Strategy

**Goal**: Develop and validate reproducible search strategies.

1. **Build search blocks** from PIRD/PICO:
   - Population block (MeSH + free text)
   - Index test / Intervention block
   - Comparator / Reference standard block (optional)
   - Study design filter (if applicable)

2. **Combine with Boolean operators**:
   - Within blocks: OR
   - Between blocks: AND

3. **Execute search per database** using `/search-lit`:
   - PubMed: MeSH + free text
   - Embase: Emtree + free text
   - Additional databases as specified in protocol

4. **Report search per PRISMA-S** (Rethlefsen et al. 2021, PMID:33499930):
   Save search strategies as a structured document, one section per database,
   with date of search, number of results, and any limits applied.

5. **Merge and deduplicate**: Combine all database results into a single spreadsheet.
   Deduplicate by DOI first, then PMID. Save raw counts for PRISMA flow.

### Phase 3: Screening & Selection

**Goal**: Systematic title/abstract and full-text screening.

#### 3a. 1st Screening (Title/Abstract)
1. Define exclusion codes from protocol (e.g., E1=Not target population, E2=Not intervention, E3=Ineligible type, E4=Non-human, E5=Duplicate).
2. For each record, screen title+abstract against eligibility criteria.
3. Mark each record as INCLUDE or EXCLUDE with reason code.
4. Output: Screening spreadsheet with color-coded INCLUDE (green) / EXCLUDE (red).

#### 3b. 2nd Screening (Full-text)
1. For INCLUDE records, match with available PDFs.
2. Apply full-text exclusion criteria (F1=No extractable outcome, F2=No comparative data, F3=Cannot separate target population data, F4=Inadequate sample/follow-up, F5=Full-text unavailable).
3. Flag comparative studies for priority review.

#### 3c. PRISMA Flow
Track numbers at each stage for PRISMA flow diagram.
Use `/make-figures` to generate PRISMA flow diagram when numbers are finalized.

### Phase 4: Data Extraction

**Goal**: Create standardized extraction forms and extract 2x2 or effect size data.

#### DTA Meta-Analysis:
Generate a data extraction form with:
- Study ID (first author, year)
- Study characteristics (country, design, setting, enrollment period)
- Population (n, age, sex, disease prevalence)
- Index test details (technique, threshold, manufacturer, reader experience)
- Reference standard details
- 2x2 table (TP, FP, FN, TN)
- Additional outcomes (AUC per study, if reported)
- Notes on partial verification, differential verification, uninterpretable results

#### Intervention Meta-Analysis:
Generate a data extraction form with:
- Study ID
- Study characteristics
- Population
- Intervention / comparator details
- Outcome data (means, SDs, event counts, sample sizes)
- Effect measures (OR, RR, HR, MD, SMD as appropriate)

Output: Excel/CSV template for data entry.

#### 4b. KM Curve Reconstruction (when raw events not reported)

When studies report outcomes only as Kaplan-Meier curves without raw event counts:

1. **Digitise the KM curve**: Use WebPlotDigitizer (https://automeris.io/WebPlotDigitizer/)
   - Calibrate X/Y axes carefully — verify output range matches the original axis labels
   - If coordinates come out in 0–1 range, multiply X by the actual time range (e.g., ×30 for months)
   - Clip negative Y values to 0 (digitisation artifact)
   - Export as CSV: `time, cumulative_event_rate` (or survival)

2. **Extract number-at-risk**: Record from the table below the KM plot at each time point.

3. **Reconstruct IPD**: Use the R `IPDfromKM` package (Guyot et al. 2012 method):
   ```r
   library(IPDfromKM)
   dat <- read.csv("digitised_curve.csv")
   preproc <- preprocess(dat, trisk, nrisk, totalpts, maxy = 1)
   ipd <- getIPD(preproc, armID = 1)  # armID starts at 1, NOT 0
   ```
   - ⚠️ `preprocess()` does NOT accept a `mateflag` parameter (common error)
   - ⚠️ `armID` starts at 1 (not 0)

4. **Verify**: Generate a reconstructed KM plot and visually compare to the original figure.

5. **Report in Methods**: Cite Guyot et al. 2012 (doi:10.1186/1471-2288-12-9) and
   state which studies required reconstruction.

**Alternative — Text-based extraction**: When no subgroup-specific KM curve exists but the
text reports "0% LTP at 12 months" or similar, extract directly from text. Document the
page number and exact quote.

#### Composite Exposure Disaggregation

When a study's intervention is a composite of multiple techniques:

1. **Subgroup-specific KM curve** → use KM reconstruction (section 4b)
2. **Component-specific Table/multivariate** → extract per-component data from Tables
3. **Text-based subgroup report** → extract from narrative (e.g., "APE arm: 0% LTP")
4. **None available** → include as composite, flag in sensitivity analysis for exclusion

Always pre-specify a sensitivity analysis excluding composite-exposure studies.
Document the extraction strategy in the data extraction form Notes column.

#### Data Extraction Cross-Verification

When comparing extraction results between independent reviewers (minimum 2), check:

1. **Denominator consistency**: Verify sample sizes match between reviewers.
   Watch for per-patient vs per-lesion/per-tumor unit confusion.
   **CRITICAL**: The denominator may differ across outcomes within the same study
   (e.g., LTP assessed only among treatment-naive nodules, but complications assessed
   among all treated tumors). For each outcome, back-calculate: `event ÷ denominator`
   must equal the percentage reported in the paper's Tables. If it does not match,
   investigate the analysis population definition in the Methods section.
   If denominators differ, return to the original paper's Tables/Flow diagram.
2. **Arithmetic verification**: Back-calculate proportions from event/total counts and cross-check against original text (e.g., 78/91 = 85.7%).
3. **Kaplan-Meier estimate distinction**: KM curve estimates differ from raw event counts. Always record the data source (Table vs KM curve vs text) during extraction.
4. **Discrepancy resolution**: List all discrepancies → verify against original text → reach consensus → if consensus fails, use third reviewer. Log all consensus decisions in `{project}/consensus_log.md`.
5. **Dataset lock**: After resolving all discrepancies, lock the final dataset. Any subsequent changes require documented justification with date.

### Phase 5: Risk of Bias Assessment

**Goal**: Guide structured RoB assessment with the appropriate tool.

Select tool based on meta-analysis type (see table above), then read the corresponding checklist:

| Tool | Checklist File |
|------|---------------|
| QUADAS-2 (DTA) | `${CLAUDE_SKILL_DIR}/references/checklists/QUADAS2.md` |
| RoB 2 (RCT) | `${CLAUDE_SKILL_DIR}/references/checklists/RoB2.md` |
| ROBINS-I (NRSI) | `${CLAUDE_SKILL_DIR}/references/checklists/ROBINS_I.md` |
| PROBAST (Prediction) | `${CLAUDE_SKILL_DIR}/references/checklists/PROBAST.md` |
| NOS (Observational) | `${CLAUDE_SKILL_DIR}/references/checklists/NOS.md` |
| JBI (Case Series) | `${CLAUDE_SKILL_DIR}/references/checklists/JBI_Case_Series.md` |

For AI/ML prediction models, also apply PROBAST+AI extensions.

**Output**: Summary table + traffic light plot (use `/make-figures`).

### Phase 6: Statistical Synthesis

**Goal**: Execute meta-analysis and generate publication-ready outputs.

**IMPORTANT**: Always use R for meta-analysis (packages: `meta`, `metafor`, `mada`).
See `${CLAUDE_SKILL_DIR}/references/r_templates.md` for code templates.

#### DTA Meta-Analysis (R code):

```r
library(mada)      # bivariate model, forest/SROC plots
library(meta)      # general meta-analysis utilities
library(metafor)   # advanced models

# Bivariate model (recommended for DTA)
fit <- reitsma(data, formula = cbind(tsens, tfpr) ~ 1)
summary(fit)

# SROC curve with confidence and prediction regions
plot(fit, sroclwd = 2, main = "SROC Curve")

# Forest plot (paired: sensitivity + specificity)
forest(fit, type = "sens")
forest(fit, type = "spec")
```

Key outputs for DTA:
- Pooled sensitivity (95% CI)
- Pooled specificity (95% CI)
- Pooled positive LR, negative LR
- Pooled DOR
- SROC curve with AUC, confidence region, prediction region
- Heterogeneity: I-squared for sensitivity and specificity separately
- Threshold effect: Spearman correlation between sensitivity and FPR

#### Intervention Meta-Analysis (R code):

```r
library(meta)
library(metafor)

res <- metagen(TE, seTE, data = dat, studlab = study,
               method.tau = "REML", sm = "OR")
forest(res)
funnel(res)

summary(res)  # I-squared, tau-squared, Q test
metabias(res, method.bias = "Egger")
metainf(res, pooled = "random")  # leave-one-out
```

#### Dual Approach: Comparative + Single-Arm Pooled Proportion

When both comparative and single-arm studies are available, use dual analysis
(precedent: Lin 2025 PMID:41419890, Su 2026 PMID:41653198).
The assignment of PRIMARY vs SECONDARY depends on the research question and
available evidence:

| Scenario | Primary | Secondary | Rationale |
|----------|---------|-----------|-----------|
| Enough comparative studies (k≥8) | Comparative OR/RR | Pooled proportion | Direct comparison answers efficacy |
| Limited comparative (k<6), many single-arm | Pooled proportion | Comparative OR/RR | Insufficient power for comparative; pooled proportion provides descriptive evidence |
| Mixed (moderate k, each) | Discuss with co-authors | — | PI/methodologist decision |

The choice should be pre-specified in the PROSPERO protocol and remain consistent
throughout the manuscript.

```r
# Comparative MA (binary outcomes)
res_comp <- metabin(ei, ni, ec, nc, data = dat,
                     studlab = study, sm = "OR",
                     method = "Inverse", method.tau = "DL",
                     common = FALSE, random = TRUE,
                     method.random.ci = "HK", incr = 0.5)

# Single-arm pooled proportion
res_prop <- metaprop(event, n, data = dat_single,
                      studlab = study, sm = "PLOGIT",
                      method.tau = "DL", method.ci = "CP")
```

Key points:
- Comparative answers "is adjunct effective?" -- single-arm answers "what outcomes to expect?"
- Single-arm uses `metaprop()` with logit transformation + Clopper-Pearson CI
- GRADE certainty lower for single-arm -- state explicitly
- Report both in Results: label PRIMARY/SECONDARY per pre-specified assignment

#### Practical R Notes:
- Use `method = "Inverse"` not `"MH"` to avoid method.tau conflict
- Use `method.tau = "DL"` (DerSimonian-Laird) -- REML may not converge with sparse data
- Use `method.random.ci = "HK"` (Hartung-Knapp) instead of deprecated `hakn = TRUE`
- Use `common = FALSE, random = TRUE` instead of deprecated `comb.fixed/comb.random`
- For zero cells, `incr = 0.5` continuity correction
- Egger's test underpowered for k < 10 -- note this in results

#### Subgroup / Meta-Regression:
- Subgroup analysis for pre-specified covariates
- Meta-regression for continuous moderators
- Report interaction test p-value, not just within-subgroup p-values

#### Publication Bias:
- DTA: Deeks' funnel plot asymmetry test (standard funnel plots inappropriate for DTA)
- Intervention: Funnel plot + Egger's or Peters' test
- Note: Tests underpowered for <10 studies

#### Sensitivity Analysis:
- Leave-one-out analysis (`metainf()`)
- Excluding high RoB studies
- Excluding overlapping populations (same institution + enrollment period)
- Including/excluding borderline studies (sensitivity to inclusion criteria)
- Alternative model specifications

#### Error Handling:
- If R script fails, capture the error message, diagnose the likely cause (missing package,
  data format mismatch, convergence failure), and present a fix. Do not silently re-run.
- When reporting R output, separate statistical results (pooled estimates, heterogeneity
  metrics, I-squared) from interpretation. Present numbers first in a "Statistical Results"
  block, then interpretation guidance in a separate "Interpretation Notes" block.

### Phase 7: GRADE / Certainty of Evidence

**Goal**: Assess certainty of the body of evidence.

For DTA meta-analysis, apply GRADE-DTA framework:
1. Risk of bias (from QUADAS-2)
2. Indirectness (applicability concerns)
3. Inconsistency (heterogeneity)
4. Imprecision (wide CIs, small sample)
5. Publication bias

For intervention meta-analysis, apply standard GRADE.

Output: Summary of Findings table.

### Phase 8: Reporting & Manuscript

**Goal**: Generate PRISMA-compliant manuscript sections.

1. **Check reporting compliance**: Use `/check-reporting` with PRISMA-DTA or PRISMA 2020
2. **Write manuscript**: Use `/write-paper` with meta-analysis type selected
3. **Figures**: Use `/make-figures` for:
   - PRISMA flow diagram
   - Forest plots (paired for DTA)
   - SROC curve (DTA)
   - Funnel plot
   - RoB summary (traffic light plot)
4. **Tables**:
   - Characteristics of included studies
   - 2x2 data per study (DTA)
   - RoB assessment results
   - Summary of findings / GRADE table

---

## DTA-Specific Pitfalls (Always Check)

| Pitfall | Problem | Solution |
|---------|---------|----------|
| Separate pooling of Se/Sp | Ignores correlation | Use bivariate/HSROC model |
| Ignoring threshold effect | False heterogeneity | Check Spearman correlation, SROC plot |
| Standard funnel plot for DTA | Inappropriate | Use Deeks' funnel plot |
| I-squared only for heterogeneity | Doesn't capture threshold effect | Use prediction region on SROC |
| Missing GRADE | Common omission in DTA MA | Apply GRADE-DTA. If <4 studies, assess each domain narratively and state the limitation explicitly |
| Partial verification bias | Inflates sensitivity | Assess in QUADAS-2 Flow & Timing domain |
| Unevaluable results excluded | Biases accuracy estimates | Report intent-to-diagnose analysis |

---

## Small Study Considerations

When the number of included studies is small (< 10):
- Bivariate/HSROC model may not converge -- consider univariate random-effects as fallback
- Publication bias tests are underpowered -- state this limitation
- Subgroup/meta-regression analysis not recommended
- Wide prediction regions expected -- emphasize uncertainty in conclusions
- Consider narrative synthesis as alternative/complement

---

## Skill Interactions

| When | Call | Purpose |
|------|------|---------|
| Need literature search | `/search-lit` | PubMed/Semantic Scholar search with verified citations |
| Need statistical code | `/analyze-stats` | Execute R/Python analysis scripts |
| Need figures | `/make-figures` | PRISMA flow, forest plots, SROC, funnel plots |
| Need reporting check | `/check-reporting` | PRISMA-DTA / PRISMA 2020 compliance |
| Need manuscript writing | `/write-paper` | Full IMRAD manuscript generation |
| Need self-review | `/self-review` | Pre-submission quality check |

---

## Error Handling

- If study type is ambiguous (DTA vs intervention), ask user to clarify before proceeding.
- If fewer than 4 studies for DTA, warn that bivariate model may not converge.
- If data extraction is incomplete (missing 2x2 cells), suggest contacting authors or sensitivity analysis with imputed values.
- If PROSPERO ID is missing, flag as a limitation but continue.
- Always remind user: this is a methodological support tool; final decisions rest with the research team and ideally include a biostatistician/methodologist.
