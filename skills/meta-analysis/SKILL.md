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
- **Data integrity checklist**: `${CLAUDE_SKILL_DIR}/references/data_integrity_checklist.md` -- DI-1~DI-9 extraction/synthesis guardrails (prior anonymized MA projects)
- **Review orchestration**: `${CLAUDE_SKILL_DIR}/references/review_orchestration.md` -- RO-1~RO-5 circulation discipline (extends phase9_circulation.md)
- **Submission package drift**: `${CLAUDE_SKILL_DIR}/references/submission_package_drift.md` -- multi-journal folder hygiene, `DO_NOT_EDIT_HERE` gate, `_build.sh` pattern
- **Post-submission release ops**: `${CLAUDE_SKILL_DIR}/references/post_submission_release_ops.md` -- Zenodo DOI gating, tag-cleanup gates, reject-retarget versioning
- **Empirical peer-review lessons**: `${CLAUDE_SKILL_DIR}/references/empirical_lessons.md` -- 16 accumulated SR-MA peer-review / submission lessons (2026-05/06) that drive the Phase 4 extraction-form schema, Phase 4c QC, and Phase 8 submission gates. Load before designing the extraction form and before submission.

### Built-in Templates (`${CLAUDE_SKILL_DIR}/templates/`)

- **Extraction Form v2** (`templates/extraction_form_v2.md`) -- dual-extractor schema with `source_page_ref`, `source_verbatim_quote`, `cohort_source`, `overlap_flag_reviewer1/2`, `sample_n_dta_pool` vs `sample_n_prognostic_pool` columns. Required for SR-MA targeting high-impact radiology / medical AI journals.
- **Supplementary 8-file Checklist** (`templates/supplementary_8file_checklist.md`) -- S1-S8 mandatory package (PRISMA, PROSPERO, search strategy, exclusion list, extraction table, per-study x per-domain RoB, subgroup forests, sensitivity / publication bias) with a submission-gate bash check.

### Built-in Scripts (`${CLAUDE_SKILL_DIR}/scripts/`)

- **`screening_reconcile.py`** -- Phase 3f ID-set screening reconciliation.
- **`check_pool_consistency.py`** -- pool-composition / PRISMA count consistency.
- **`cohort_overlap_check.py`** -- shared-database cohort-overlap detection.
- **`extract_assist.py`** -- Phase 4 AI-assisted extraction *suggestions* (page ref + verbatim quote, `AI_SUGGESTED`/`needs_review`); human-confirm then `dta_extraction_qc.py`. Challenge card: `scripts/extract_assist_challenge/`.
- **`dta_extraction_qc.py`** -- 2x2 cell ↔ source sens/spec QC on the **confirmed** extraction CSV.

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
   - **Registration-ID format gate.** A PROSPERO ID is `CRD42` + 9 digits (14 characters total), e.g. `CRD42024500001`. Validate any ID that appears in the manuscript or registration doc with `grep -oE 'CRD42[0-9]+'` and assert a 14-character length / `^CRD42\d{9}$` — a 15-character ID (a stray digit) is a transcription error a reviewer will check against the live record.
   - **Review-type selection.** Pick the *least-wrong* portal review type for the actual design and state any portal constraint in the protocol. A descriptive single-arm proportion synthesis is not an "Intervention review"; choosing "Intervention review" only to satisfy a portal field contradicts a later GRADE / effect-certainty statement. Whatever certainty language the protocol commits to (GRADE vs "evidence statements only") must match the manuscript verbatim — a guideline-style "we recommend" is not licensed by a descriptive review type.
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

**3a. Round 1 — initial title/abstract screening (single reviewer).** Define the exclusion codes
from the protocol (E1=Not target population, E2=Not intervention, E3=Ineligible type, E4=Non-human,
E5=Duplicate). Mark every record INCLUDE / EXCLUDE / MAYBE with a reason code → `round1_{date}.tsv`.

**3b. Round 2 — dual independent title/abstract screening.** A second independent reviewer (or AI
as a *documented* second-pass tool with human verification) re-screens all R1 records. Compute
Cohen's κ and report it in Methods. `round2_tag` = INCLUDE / EXCLUDE / MAYBE, where MAYBE means
disagreement **or** either reviewer flagged uncertainty → `round2_tag`, `round2_reason` columns.

**3c. Round 3 — adjudication of disagreements (first reviewer).** Build the R3 sheet with all MAYBE
records first, then INCLUDE records for a brief confirmation pass. The first reviewer independently
adjudicates each row (`round3_decision`, plus `round3_reason` only when overturning R2). Optional
AI-assisted pre-screening can compress the effort — but **AI suggestions are not decisions**: the
reviewer independently confirms or overturns every one. Template, sort priority, and the required
Methods boilerplate are in the reference file.

**3d. Round 4 — full-text screening.** Retrieve full texts for `round3_decision = INCLUDE` (use
`/fulltext-retrieval`), apply the full-text exclusion codes (F1=No extractable outcome, F2=No
comparative data, F3=Cannot separate target population, F4=Inadequate sample/follow-up,
F5=Full-text unavailable), with two independent reviewers, Cohen's κ, and consensus or a third
reviewer for disagreements. Flag comparative studies for priority extraction.

**3e. PRISMA flow.** Track counts at every stage (R1 → R2 → R3 → R4 → final included); generate the
diagram with `/make-figures` once the numbers are final.

**3f. Post-consensus count reconciliation gate (MANDATORY before Phase 5 write-up).** Reconcile the
counts from the **raw ID sets, never from prose summaries**, and record the canonical totals in one
source-of-truth file:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/screening_reconcile.py" \
  --screening 2_Screening/fulltext_screening.tsv \
  --consensus 2_Screening/consensus_decisions.tsv \
  --table1 6_Tables/table1_studies.csv \
  --output 2_Screening/screening_consensus.json
```

Downstream stages consume `screening_consensus.json` for counts and ID sets; the Markdown consensus
document remains the human explanation. Three hard rules:

1. **List the narrative-only IDs explicitly.** The highest-yield red flag is a numeric claim ("10
   narrative-only studies") that does not match the enumerable set `(A ∪ C) \ B \ T`.
2. **No "N → M" transition without ID receipts.** "k rose from 30 to 32 after FLAG consensus" must
   cite the added/removed IDs. A transition claim with no enumerable ID set is a **P0** and blocks
   the Phase 5 hand-off.
3. **`STAGE_TRANSFER_LOSS` is a P0.** Exit 1 when a record is included at screening but **absent
   from the consensus artifact altogether** — no adjudication was ever recorded. An exclusion is a
   decision; silence is a gap. Never let it settle into narrative-only (why: reference file).

The set algebra, the reconciliation-table template, and the precedent (a manuscript shipped 32/10/46
where the ID sets said 24/2/54, with four artifacts echoing the same unreconciled prose total) are
in the reference file.

**3f.5 Pool composition lock (MANDATORY at adjudication freeze).** Once 3f passes, freeze the pool
into a single source-of-truth YAML that every downstream artifact can be checked against:

```bash
cp "${CLAUDE_SKILL_DIR}/templates/FINAL_POOL_LOCK.yaml.template" 2_Data/FINAL_POOL_LOCK.yaml
# fill counts + UID lists from 3f, compute the SHA-256 over the sorted UID list,
# and COMMIT THE LOCK before any Phase 4 extraction
```

- **Never re-derive `k included` from the extraction TSV at manuscript build time** — always
  reference `final_pool_n` from the lock.
- **Aggregate patient/lesion totals are locked too**, not just study counts. Distinguish
  **arm-separable** from **both-arm** rows: a study contributing one arm must not have its
  full-cohort count folded into a pooled total. A hand-carried headline total that does not
  re-derive from the locked per-study values is a **P0**.
- A late post-freeze change to the pool is a **formal PROSPERO amendment**: file it, re-freeze as
  `FINAL_POOL_LOCK_v2.yaml`, and propagate to every artifact.

**Read on demand:**

| File | Read it when | Cost if read blindly |
|---|---|---|
| `references/phase3_screening_detail.md` | you are executing a screening round, using AI pre-screening, or a reconciliation/lock gate fired | ~3,600 tokens; the round procedures are needed one round at a time, not all at invocation |
### Phase 4: Data Extraction

**Goal**: Create standardized extraction forms and extract 2x2 or effect-size data.

**4.0 Entry gate (MANDATORY) — pool composition lock ↔ adjudication TSV.** Before any extraction
work begins, confirm the round-3 adjudication TSV and `FINAL_POOL_LOCK.yaml` (Phase 3f.5) agree on
which UIDs are included:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/check_pool_consistency.py" \
    --lock 2_Data/FINAL_POOL_LOCK.yaml \
    --adjudication-tsv 2_Screening/round3_adjudication.tsv \
    --decision-col round3_decision --uid-col uid \
    --include-labels "INCLUDE,INCLUDE_MIXED" \
    --out qc/pool_consistency.json
```

**The gate fails closed: any UID disagreement blocks extraction.** Resolve by re-freezing the lock
with the corrected UID set (and propagating downstream) or by correcting a mis-labelled TSV row. Do
NOT proceed with a mismatch — the extraction matrix will not align with the locked pool, and the
drift surfaces as a fabrication-grade red flag at peer review.

> **Failure-mode cross-ref** → `references/data_integrity_checklist.md` DI-1~DI-5 are mandatory
> during extraction (2x2 arm-swap, KM audit trail, methodology mismatch, PRISMA 5-way drift,
> single-source k).

**Extraction form.** For an SR-MA targeting high-impact radiology / medical AI journals use
`${CLAUDE_SKILL_DIR}/templates/extraction_form_v2.md` — its dual-extractor, source-page-reference,
and verbatim-quote columns are what close the 2x2 cell-swap and cohort-overlap blind spots. The
DTA and intervention field lists are in the reference file.

**AI-drafted starting document — treat as hallucination-suspect.** If a mentor or collaborator
shared an AI-drafted study list, 2x2 set, or effect estimates (*even* flagged "for reference
only"): save it with a `_DO_NOT_USE_VERBATIM` suffix and re-verify **every** N, denominator, event
count, OR/CI, and author/year against the source PDF. Trust hierarchy: **source PDF + own analysis
stdout > the mentor's direct text > the attached AI draft** — never promote a draft up that ladder.
Procedure and precedent: reference file.

**4b. Special cases (KM reconstruction, composite exposure).** When studies report outcomes only as
Kaplan-Meier curves, or the intervention is a composite of techniques, load
`${CLAUDE_SKILL_DIR}/references/phase4_km_composite.md` for the WebPlotDigitizer → `IPDfromKM`
procedure (cite Guyot et al. 2012, doi:10.1186/1471-2288-12-9) and the 4-path composite-exposure
decision tree. Pre-specify a sensitivity analysis excluding composite-exposure studies.

**Cross-verification (≥2 independent reviewers).** Report inter-reviewer agreement (% or Cohen's
κ) at title/abstract and full-text stages. Verify denominator consistency — **the denominator may
differ across outcomes within one study**, so for each outcome back-calculate `event ÷ denominator`
and confirm it reproduces the paper's reported percentage. Distinguish KM-curve estimates from raw
event counts and record the data source (Table / KM / text). Log every consensus decision in
`{project}/consensus_log.md`, then **lock the dataset**; later changes need a dated justification.

**4c. Extraction QC & cohort overlap.** After dual-extractor consensus, run both before locking:

```bash
# 2x2 cell integrity: validates TP/FN/TN/FP against source-reported sens/spec (catches arm-swap)
python3 "${CLAUDE_SKILL_DIR}/scripts/dta_extraction_qc.py" \
  --input 2_Extraction/extraction.csv --tolerance 0.02 \
  --out 2_Extraction/qc/dta_extraction_qc.tsv

# cohort overlap: shared public DB / same institution+period / same first author ±2y
python3 "${CLAUDE_SKILL_DIR}/scripts/cohort_overlap_check.py" \
  --input 2_Extraction/studies.csv --enrich \
  --out 2_Extraction/qc/cohort_overlap.md
```

Any `FLAG_SWAP` / `FLAG_MISMATCH` requires third-reviewer adjudication before Phase 6. **A
confirmed flag is not resolved until the extraction form itself is edited** — a flag corrected only
in a review note silently re-enters synthesis, so re-run the QC and confirm zero open flags before
locking. HIGH-confidence overlap pairs require a Limitations acknowledgment plus a sensitivity
analysis excluding one of the pair. Cross-links: `/peer-review` Phase 2A P1 + P2.

**Read on demand:**

| File | Read it when | Cost if read blindly |
|---|---|---|
| `references/phase4_extraction_detail.md` | building the extraction form, an AI draft was shared, you want the optional `extract_assist.py` scaffolding, or a QC flag fired | ~4,700 tokens; a clean dual-extraction with no AI draft needs none of it |
| `references/phase4_km_composite.md` | studies report only KM curves, or the exposure is composite | ~2,200 tokens |
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

> **Failure-mode cross-ref** → `references/data_integrity_checklist.md` DI-6/DI-7/DI-9 are the consistency gate (CSV ↔ script ↔ prose; single-source k; 3-way numeric reconciliation before Stage 4).

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

5. **Sensitivity analyses must be recomputed on the modified data, not copied.**
   - When you add a sensitivity / leave-one-out / erosion / alternative-model analysis, every
     reported effect size (Cohen's dz/f, AUC, OR, HR, β, sens/spec, ICC) MUST be re-derived from
     the modified dataset. If a sensitivity-table effect size is **identical to the primary
     analysis to two decimals across ≥4 values**, the recomputation almost certainly did not run
     and the primary values were transcribed — re-run the script on the modified data.
   - The underlying means/SDs/counts will change even when the effect size looks similar; if the
     effect sizes are byte-identical while the inputs differ, that is the tell. Probability of ≥4
     independent values coinciding to 2 decimals by chance is ≈ (0.01)^4 — essentially zero.
   - Precedent: a revision-era sensitivity analysis (1-voxel erosion) reported 8 effect-size values
     (Cohen's dz + f across 4 VOIs) byte-identical to the primary tables while the means/SDs
     differed — the erosion analysis had not actually been recomputed. Caught only by external QC.

6. **A "fixed" / "resolved" audit note requires re-run evidence, not a claim.**
   - When a prior audit note records a number as `fixed`, `resolved`, or `corrected`, that status is
     only valid if it carries the re-run evidence: a timestamp and the relevant stdout / output-file
     line showing the corrected value, or the commit that changed it. A bare "fixed in v10" with no
     re-run artifact does NOT clear the finding — re-run the script and attach the output.
   - The forward pipeline can echo a stale value through every artifact while an audit note claims it
     was fixed (e.g., a major-comparison N still reading the old total after a "fixed" note). The
     outcome-denominator cross-check (`/self-review` Phase 2.5b, the cohort-arithmetic / pool-lock
     assertions) must pass against the *current* outputs before any "fixed" status is accepted.

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

> **Failure-mode cross-ref** → `references/submission_package_drift.md` — apply the `_build.sh` pattern + `DO_NOT_EDIT_HERE` gate when staging multi-journal submission folders.

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

5. **Supplementary & analysis-code pre-submission gate** (run before Phase 9 circulation and before portal upload). Presence of the 8-file package (Empirical Lesson 5) is necessary but not sufficient — each item must also be reviewer-ready:
   - **De-scaffold**: strip internal-QC / tool artifacts before bundling — raw `/check-reporting` output ("Assessed by: <tool>", JSON blocks, "READY FOR SUBMISSION" verdicts, action-item lists), search-development planning docs (decision logs, expected-yield estimates, `[Check on execution]` placeholders, version-history dev notes), and stale version stamps. Ship a clean PRISMA 2020 checklist (27-item / 42-subitem table only) and an executed-method search-strategy doc, not the working drafts.
   - **Blind**: supplementary goes to reviewers — remove author names/initials and sibling-project cross-references ("Designed by: <name>", "identical to a sibling review"). Same standard as the blinded manuscript.
   - **Cross-consistency with the manuscript**: every supplementary number must match the main text — PRISMA counts, pool k/N, the Cochrane/CENTRAL search description, RoB counts. A supplement that says "Cochrane — NOT SEARCHED" while Methods report a confirmatory CENTRAL search is a contradiction reviewers catch.
   - **Submitted analysis code must reproduce and be self-contained**: run it from a clean copy of the bundle. It must (a) read the bundled locked dataset (not an out-of-bundle path) and write to the working directory, and (b) regenerate every pool reported in the results table. A hard-coded study-id subset that drifts from the manuscript (e.g., a pool computed over k=7 while the manuscript reports k=9) is a P0 — fix and re-run; never ship stale code or stale figures derived from it.
   - **Run a supplementary-only review pass** — the manuscript self-review/panel does not see the supplement; mirror `/self-review` Phase 2.5c–2.5d (reference + cross-reference QC) over the supplementary files.

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

> **Failure-mode cross-ref** → `references/review_orchestration.md` RO-1~RO-5 (dual-rating completeness, defensive-tone bias audit, response-matrix numeric tracking, 2nd-reviewer availability blocking).

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

> **Failure-mode cross-ref** → `references/post_submission_release_ops.md` Gate 4 covers reject/revise Zenodo versioning, tag-cleanup gate, and re-target workflow (avoid "new version" misuse on re-target).

---

## Failure Modes (prior MA projects, anonymized)

Failure patterns observed across three prior MA projects (anonymized). Each topical reference extends the phase it cross-references above — consult alongside phase procedural docs, not in isolation.

| Domain | Phase span | Load-on-demand reference |
|---|---|---|
| Data integrity (2x2 arm-swap, KM audit, methodology mismatch, PRISMA 5-way drift, single-source k) | Phase 3 → 6 | `references/data_integrity_checklist.md` (DI-1~DI-9) |
| Review orchestration (2nd-reviewer blocking, dual-rating completeness, defensive-tone audit, response-matrix tracking) | Phase 9 circulation (extends `phase9_circulation.md`) | `references/review_orchestration.md` (RO-1~RO-5) |
| Submission package drift (multi-journal folder hygiene, `DO_NOT_EDIT_HERE` gate, build artifact vs master) | Phase 8 → submission | `references/submission_package_drift.md` |
| Post-submission release ops (Zenodo DOI timing, tag-cleanup gate, reject-retarget versioning) | Submission → Phase 10 | `references/post_submission_release_ops.md` |

### Automation hooks (invoke at the phase listed)

| When | Script | Gate |
|---|---|---|
| Phase 4 kickoff (before first extraction row) | `python3 ${CLAUDE_SKILL_DIR}/../../scripts/extraction_consensus_log_init.py --output 2_Data/extraction_consensus_log.md` | DI-1: creates standalone consensus log so comparative arm-specific rows are never folded into R-script comments. |
| Phase 3f reconciliation + every revision touching PRISMA numbers | `python3 ${CLAUDE_SKILL_DIR}/../../scripts/prisma_5way_consistency.py --ssot prisma.yaml` | DI-6: 5-surface drift check (abstract / main text / flow figure / supplement / CSV) against YAML SSOT. Non-zero exit blocks Phase 5 writeup. |
| Phase 8 pre-submission + every journal retarget | `bash ${CLAUDE_SKILL_DIR}/../../scripts/tag_cleanup_gate.sh` | DI-8: fails if `VERIFY-CSV`/`TODO`/`FIXME`/`XXX` survive in `7_Manuscript`, `supplement`, `SUBMISSION`, etc. |
| Phase 8 on first build per journal (`--record`), then before every re-submission (`--verify`) | `python3 ${CLAUDE_SKILL_DIR}/../../scripts/verify_package_integrity.py --record --journal <name>` then `--verify --journal <name>` | SPD: checksum-based drift detection between master manuscript and built `SUBMISSION/{journal}/` folder. Journal-editable files (cover letter, response, MANIFEST, `DO_NOT_EDIT_HERE.md`) are auto-excluded. |

All four scripts are repo-shipped as of 2026-04 (FOLLOWUPS P10). Non-zero exit = gate failure; resolve before proceeding to the next phase.

---

## Empirical Lessons (peer-review cycles)

Sixteen accumulated SR-MA peer-review / submission lessons (2026-05 and 2026-06) — the
drivers behind the Phase 4 extraction-form schema, the Phase 4c QC scripts, and the Phase 8
submission gates. To keep this entry point lean they live load-on-demand in
`${CLAUDE_SKILL_DIR}/references/empirical_lessons.md`. **Load that file when designing the
extraction form (before Phase 4) and before submission (Phase 8)** — it covers dual-extractor
2x2 integrity, cohort-overlap clustering, small-k subgroup caution, the supplementary 8-file
bar, PROSPERO ID format, AI-disclosure presence, recompute-don't-copy sensitivity analyses,
outcome harmonization, heterogeneous-RoB κ, survival-specific concerns, supplement blinding /
de-scaffolding, self-contained reproducible analysis scripts, sidecar re-sync, methodological
+ software citations, wide-table PDF rendering, and submission-portal journal-identity checks.

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
| Self-audit recovery entrypoint (Phase 10) | `/write-paper` Step 7.4a | Recovery branch for polish pipelines that surface structural audit failures |
| `/sync-submission` SR-MA gate | `/sync-submission` | Before submission, verify supplementary package matches all 8 files in `templates/supplementary_8file_checklist.md` (PRISMA, PROSPERO, search strategy, exclusion list, extraction table, per-study x per-domain RoB, subgroup forests, sensitivity / publication bias). AI Disclosure presence check (cross-link `/peer-review` Phase 2A P8). Cite-list duplicate check via `/verify-refs` Gate 5 (duplicate PMID/DOI). |

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
