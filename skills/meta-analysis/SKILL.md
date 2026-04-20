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
- **Phase 9 Co-author Circulation**: `${CLAUDE_SKILL_DIR}/references/phase9_circulation.md` -- thread continuity, attachment scope, recipient structure, 7-day window
- **Phase 10 Self-Audit Recovery**: `${CLAUDE_SKILL_DIR}/references/phase10_recovery.md` -- trigger conditions, 12-step rebuild sprint, PROSPERO amendment, re-circulation framing

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
   - Minimum 3 databases: PubMed, Embase, and Cochrane CENTRAL (add Scopus, Web of Science as needed)
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

**Goal**: Systematic title/abstract and full-text screening with two independent reviewers.

#### 3a. Round 1 — Initial Title/Abstract Screening (single reviewer)
1. Define exclusion codes from protocol (e.g., E1=Not target population, E2=Not intervention, E3=Ineligible type, E4=Non-human, E5=Duplicate).
2. For each record, screen title+abstract against eligibility criteria.
3. Mark each record as INCLUDE / EXCLUDE / MAYBE with reason code.
4. Output: `round1_{date}.tsv` with color-coded decisions.

#### 3b. Round 2 — Dual Independent Title/Abstract Screening
1. A second independent reviewer (or AI as a documented second-pass tool with human verification) re-screens all R1 records.
2. Compute Cohen's kappa at title/abstract stage; report in Methods.
3. Tag each record's `round2_tag` as INCLUDE / EXCLUDE / MAYBE based on R1+R2 agreement (MAYBE = disagreement OR either reviewer flagged uncertain).
4. Output: `round2_{date}.tsv` (adds `round2_tag`, `round2_reason` columns).

#### 3c. Round 3 — Adjudication of Disagreements (first reviewer)
1. Build R3 sheet: all MAYBE records first, followed by INCLUDE records (which receive a brief confirmation pass).
2. The **first reviewer** independently adjudicates each row, recording `round3_decision` (INCLUDE/EXCLUDE) and `round3_reason` (only when overturning R2).
3. **Optional AI-assisted pre-screening** to compress R3 effort:
   - Use `references/ai_pre_screening_template.py` (customize per project).
   - Pre-screen produces `ai_suggestion` (INCLUDE/EXCLUDE/UNCERTAIN/CONFIRM-INCLUDE) + `ai_reason` columns.
   - Sort priority: UNCERTAIN → EXCLUDE → INCLUDE → CONFIRM-INCLUDE.
   - First reviewer must independently confirm or overturn every AI suggestion against the title, abstract, and (when needed) full text. AI suggestions are **not** final decisions.
   - Methods boilerplate: "Round 3 adjudication was performed by the first reviewer with AI-assisted pre-screening ({model name and version}). The AI was prompted with the prespecified PECOS criteria and produced a suggestion plus brief justification for each record; the first reviewer independently confirmed or overturned every suggestion. AI suggestions were not used as final inclusion decisions."
4. Output: `round3_{date}.tsv` with finalized `round3_decision`.

#### 3d. Round 4 — Full-text Screening
1. For records with `round3_decision = INCLUDE`, retrieve full-text PDFs (use `/fulltext-retrieval`).
2. Apply full-text exclusion criteria (F1=No extractable outcome, F2=No comparative data, F3=Cannot separate target population data, F4=Inadequate sample/follow-up, F5=Full-text unavailable).
3. Two independent reviewers; compute Cohen's kappa at full-text stage.
4. Resolve disagreements by consensus or third reviewer.
5. Flag comparative studies for priority extraction.

#### 3e. PRISMA Flow
Track numbers at each stage for PRISMA flow diagram (R1 → R2 → R3 → R4 → final included).
Use `/make-figures` to generate PRISMA flow diagram when numbers are finalized.

#### 3f. Post-Consensus Count Reconciliation Gate (MANDATORY before Phase 5 write-up)

Before handing the screening artifacts to Phase 5 (statistical synthesis) or to `/write-paper` / `/self-review`, run an explicit ID-set reconciliation and record the canonical totals in a single source-of-truth file (typically `2_Screening/screening_consensus_final.md` §Net Impact or equivalent):

1. **Enumerate ID sets from raw artifacts (not from prose summaries):**
   - A = screening TSV INCLUDE IDs
   - B = consensus spreadsheet Exclude IDs
   - C = consensus spreadsheet Include-qualitative IDs (FLAG-resolved additions)
   - T = Table 1 / bivariate-eligible IDs (2×2-extractable studies)

2. **Compute canonical totals via set algebra:**
   - k_qualitative = |A \ B| + |C|
   - k_bivariate = |T|
   - k_narrative-only = k_qualitative − k_bivariate
   - k_FT-excluded = |full-text reviewed| − k_qualitative

3. **List the narrative-only IDs explicitly.** The highest-yield red flag is a numeric claim ("10 narrative-only studies") that does not match the enumerable ID set (A ∪ C) \ B \ T.

4. **Prohibit "N → M" transitions without ID receipts.** Any sentence of the form "k rose from 30 to 32 after FLAG consensus" must cite the specific added/removed IDs. A transition claim with no enumerable ID set is a P0 error and blocks the Phase 5 hand-off.

5. **Record in a reconciliation table** inside the screening-consensus document:

   | Quantity | v_prev draft | v_current (ID-verified) | Derivation |
   |---|---|---|---|
   | k_full-text | ... | ... | ... |
   | k_FT-excluded | ... | ... | |TSV EXCLUDE| + |consensus-downgrades| |
   | k_qualitative | ... | ... | |A \ B| + |C| |
   | k_bivariate | ... | ... | |T| |
   | k_narrative-only | ... | ... (explicit IDs listed) | (A ∪ C) \ B \ T |

**Precedent incident (CBCT Biopsy MA-1, 2026-04-20):** v11 manuscript shipped with k_qualitative = 32 / k_narrative-only = 10 / k_FT-excluded = 46. ID-set reconciliation (only performed after Codex adversarial audit at post-Stage 4 QC) revealed true counts 24/2/54. The prose "30 → 32 after FLAG consensus" had been carried from v7 without ever being reconciled against `fulltext_screening_final.tsv` ∩ `MA1_Consensus_Sheet.xlsx`; four downstream artifacts echoed the same wrong total. This gate would have caught the drift at Phase 5 hand-off.

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

#### 4b. Special cases (KM reconstruction, composite exposure)

When studies report outcomes only as Kaplan-Meier curves (no raw event counts) or
when the intervention is a composite of multiple techniques, load
`${CLAUDE_SKILL_DIR}/references/phase4_km_composite.md` for the WebPlotDigitizer
→ `IPDfromKM` reconstruction procedure (cite Guyot et al. 2012,
doi:10.1186/1471-2288-12-9) and the 4-path composite-exposure disaggregation
decision tree. Pre-specify a sensitivity analysis excluding composite-exposure
studies and document extraction strategy in the form's Notes column.

#### Data Extraction Cross-Verification

When comparing extraction results between independent reviewers (minimum 2), check:

0. **Inter-reviewer agreement**: Calculate and report screening agreement: % agreement or Cohen's kappa at title/abstract and full-text stages. If kappa was not calculated, report the exact number of discrepant records and the resolution method.

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
See `${CLAUDE_SKILL_DIR}/references/r_templates.md` for full code templates.

| Analysis family | Primary tool | Key output |
|-----------------|-------------|-----------|
| DTA | `mada::reitsma()` (bivariate) | Pooled Se/Sp + SROC with confidence/prediction regions |
| Intervention | `meta::metagen()` / `meta::metabin()` | Pooled OR/RR, I², Egger's test, leave-one-out |
| Dual (comparative + single-arm) | `metabin` + `metaprop` | PRIMARY vs SECONDARY per pre-specified protocol |

**Load-on-demand**: Read `${CLAUDE_SKILL_DIR}/references/phase6_statistical_synthesis.md`
for the full R code templates, the dual-approach decision table (comparative vs
single-arm), practical cautions (method.tau, HK CI, zero-cell correction),
publication-bias test power, sensitivity-analysis menu, and error-handling rules.

### Phase 6b: Post-Analysis Source Fidelity Audit (MANDATORY)

**Goal**: Catch numerical hallucinations that survived the forward pipeline (CSV → .R → manuscript).

**Precedent failure pattern** — treat this as a lived near-miss, not hypothetical:
> In a revision-era comparative meta-analysis, a safety outcome was reported as "3/45 vs
> 0/56, p=0.085." The primary-source Table actually recorded "0/45 vs 1/56, p=0.37" —
> direction reversed. The extraction CSV was correct; the R script's Fisher exact
> `matrix()` was hand-typed after a column in the source Table was misread. Internal
> consistency checks passed because every downstream artifact (Abstract, Discussion,
> Table, forest caption) echoed the same wrong number. The reversal was caught only on
> a second-pass audit with random extraction sampling against the primary paper.

**Non-negotiable rules:**

1. **No hand-typed numerical matrices when a CSV exists.**
   - Use `read.csv(...)` + subset / filter. Never copy a 2x2 table from a paper's Table into
     `matrix(c(...), ...)` by eye.
   - If hand entry is truly unavoidable (e.g., text-only extraction), the `matrix`, `c()`, or
     `data.frame` line MUST carry a comment citing the exact CSV row + column OR the exact
     primary-source Table/Page coordinate. Example:
     ```r
     # source: data_extraction_final.csv row <N> (<first-author> <year>), cols <event_arm1>=0, <event_arm2>=1
     # verified against primary source Table <X>, page <P>
     fisher.test(matrix(c(0, 45, 1, 55), nrow = 2, byrow = FALSE))
     ```

2. **Comparative-arm subsets are a separate consensus-log row.**
   - When one study's arm-specific values (e.g., one arm of a multi-arm study) are used in a
     comparative analysis while the full cohort of that study appears elsewhere,
     `extraction_consensus_log.md` must carry an explicit row for the arm-specific values.
     Pooled totals and arm-specific values MUST NOT share a row.

3. **Random 3-claim back-check before closing Phase 6.**
   - After the forest/funnel/subgroup outputs stabilize, randomly sample 3 numerical claims
     from the Results section of the draft manuscript and trace each back to (a) the R output
     log and (b) the original paper's Table/Figure.
   - Record the back-check as a small table in `peer_review_<vN>_internal.md`:

     | Claim (manuscript line) | R output file:line | Primary source (paper, Table/Fig, page) | Match? |
     |---|---|---|---|

   - A single mismatch is a P0 blocker — do not advance to Phase 7 until resolved.

4. **Revision-introduced numbers must be tagged.**
   - Any new number added after v1 — including numbers produced by a new comparative / subgroup /
     sensitivity script — MUST be wrapped inline as `[VERIFY-CSV]` in the manuscript until the
     Phase 2.5a audit in `/self-review` clears it.

**When this phase triggers:** every time Phase 6 outputs change (first draft, revision, reviewer-
requested re-analysis). Not optional on "minor" re-runs — the precedent reversal above
occurred inside a "minor" revision-era re-analysis.

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

### Phase 9: Co-author Circulation

**Goal**: Standardized pre-submission circulation of the manuscript to co-authors and
senior methodologist / reviewer, with a bounded review window and a controlled attachment
scope.

**Trigger**: Phase 8 is complete, and the draft has cleared Phase 6b source-fidelity
audit.

**Summary**: Reply to the prior-version email thread to preserve `In-Reply-To` continuity
(v1 → v2 → v3 tracked in one place). Attach the manuscript body with figures inline and,
for v≥2, a change summary — exclude graphical abstract, cover letter, COI forms, and
supplementary until the target journal is confirmed. TO = corresponding author + one
senior methodologist; CC = remaining co-authors. Set a 7-day deadline (5 business days +
weekend). Ask the corresponding author for target-journal preference, reviewer candidates,
and cover-letter framing.

**Load-on-demand procedural detail** (thread continuity, attachment scope rationale,
size-to-method table, journal-undetermined framing, response-tracking log):
`${CLAUDE_SKILL_DIR}/references/phase9_circulation.md`.

---

### Phase 10: Self-Audit Recovery (v{N} → v{N+1} sprint)

**Goal**: When an audit uncovers a structural data or protocol-application error,
withdraw the current version, rebuild, and re-circulate with a transparent audit trail.
Catching the error yourself before a journal reviewer does is the principal trust-building
move in this phase.

**Trigger conditions (any one):**

| # | Trigger | Source |
|---|---------|--------|
| T1 | Extraction CSV ↔ primary source disagreement for a cell feeding a pooled/subgroup estimate or reported proportion | Phase 6b audit |
| T2 | Included/excluded study violates the pre-specified criteria on re-read | Protocol review |
| T3 | Hand-typed numerical literal in the analysis script traces to a wrong value | Phase 6b audit |
| T4 | PROSPERO protocol ↔ delivered analysis disagreement on outcome, subgroup, or eligibility | Protocol ↔ analysis diff |
| T5 | Dual-reviewer consensus record ↔ locked dataset disagreement on inclusion | Consensus log diff |

**Non-negotiable rule**: if the trigger fires after Phase 9 circulation but before
journal submission, withdraw the current version within 24 hours. Reviewer discovery is
a strictly worse failure mode than self-withdrawal.

**Sprint outline (12 steps)**: (10.1) audit log at `qc/audit_vN_to_vNplus1.md` →
(10.2) CSV re-verification with `[VERIFY-CSV]` tagging → (10.3) fresh script re-run
(fixed seed, logged) → (10.4) manuscript auto-sync (grep for v{N} residue) → (10.5)
supplementary regeneration (consensus log, RoB, GRADE/SoF, PRISMA flow) → (10.6) figure
regeneration via `/make-figures` → (10.7) change summary with delta table → (10.8)
PROSPERO amendment (application correction, not criteria change) → (10.9) re-circulation
in the Phase 9 thread with the "On re-review" framing → (10.10) anti-patterns to avoid
(hide-and-submit, "minor revision" reframe, cover-letter-only disclosure) → (10.11) post-
submission escalation path → (10.12) post-recovery loop (Phase 9 restart; tighten Phase
6b if a second sprint is needed).

**Load-on-demand procedural detail** (exact audit-log fields, delta-table template,
amendment language template, re-circulation paragraph template, anti-pattern rationale):
`${CLAUDE_SKILL_DIR}/references/phase10_recovery.md`.

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
| Need reporting check | `/check-reporting` | PRISMA-DTA / PRISMA 2020 compliance (includes Step 4c registration / amendment timing) |
| Need manuscript writing | `/write-paper` | Full IMRAD manuscript generation |
| Need self-review | `/self-review` | Pre-submission quality check |
| Co-author circulation (Phase 9) | `/gws` + `/handoff` | Thread-reply send, deadline task registration |
| Self-audit recovery entrypoint (Phase 10) | `/write-paper` Step 7.4a | Recovery branch for polish pipelines that surface structural audit failures |

---

## Error Handling

- If study type is ambiguous (DTA vs intervention), ask user to clarify before proceeding.
- If fewer than 4 studies for DTA, warn that bivariate model may not converge.
- If data extraction is incomplete (missing 2x2 cells), suggest contacting authors or sensitivity analysis with imputed values.
- If PROSPERO ID is missing, flag as a limitation but continue.
- Always remind user: this is a methodological support tool; final decisions rest with the research team and ideally include a biostatistician/methodologist.

## Anti-Hallucination

- **Never fabricate variable names, dataset column names, or variable codings.** If a variable mapping is uncertain, output `[VERIFY: variable_name]` and ask the user to confirm against the data dictionary.
- **Never fabricate statistical results** — no invented p-values, effect sizes, confidence intervals, or sample sizes. All numbers must come from executed code output.
- **Never generate references from memory.** Use `/search-lit` for all citations.
- If a function, package, or API does not exist or you are unsure, say so explicitly rather than guessing.
