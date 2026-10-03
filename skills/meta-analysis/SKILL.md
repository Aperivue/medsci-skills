---
name: meta-analysis
description: Use when running a systematic review and meta-analysis, DTA or intervention. Covers PROSPERO protocol, search, screening, extraction, risk of bias (QUADAS-3, RoB 2, ROBINS-I), bivariate/HSROC or random-effects pooling, forest plots, heterogeneity and PRISMA reporting. Topic scouting is /ma-scout.
metadata:
  triggers: "meta-analysis, systematic review, PROSPERO, QUADAS-3, forest plot, funnel plot, PRISMA, QUADAS, ROBINS, HSROC, bivariate model, pooled sensitivity, pooled specificity, search strategy, study selection, data extraction form"
---

# Meta-Analysis Skill

## Meta-Analysis Types

| Type | RoB Tool | Statistical Model | Reporting Guideline |
|------|----------|-------------------|-------------------|
| **DTA** (diagnostic test accuracy) | **QUADAS-3** (QUADAS-2 for legacy reviews) | Bivariate / HSROC | PRISMA-DTA |
| **Intervention** (treatment effect) | RoB 2 (RCT) / ROBINS-I (NRSI) | Random-effects (REML, Hartung-Knapp CI) | PRISMA 2020 |
| **Prognostic factor** (association of one factor with outcome) | QUIPS | Random-effects | PRISMA 2020 |
| **Prediction model** (model performance) | PROBAST | Random-effects | PRISMA 2020 |
| **Observational** (prevalence/association) | NOS / JBI | Random-effects | MOOSE |

If the type is ambiguous (DTA vs intervention), ask the user to clarify before proceeding.

---

## Workflow Phases

### Phase 1: Protocol Development

**Goal**: Produce a PROSPERO-ready protocol document. Write the protocol, extraction forms and
manuscript text in English whatever language the user writes in — PROSPERO records and the
target journals are English-language.

1. **Research question**: PIRD (Population, Index test, Reference standard, Diagnosis) for DTA;
   PICO (Population, Intervention, Comparator, Outcome) for intervention.

2. **DTA only — do QUADAS-3 phases 1 and 2 now, not at risk-of-bias time.** They are
   review-level and belong in the protocol: phase 1 states the **synthesis question(s)**
   (population, index test(s), target condition — a review may have more than one); phase 2
   defines the **ideal test accuracy trial** for each (objective, participants, index test(s),
   definition of the target condition, analysis). Every later risk-of-bias and applicability
   judgement is made against that trial. Write the review-specific guidance for answering each
   signalling question here too, with clinical **and** methodological input, and publish it as a
   web appendix. Defining the ideal trial after seeing the studies is a judgement fitted to the
   results, not an assessment. See `references/checklists/QUADAS3.md`.

3. **Eligibility criteria**: study design, population, index test / intervention, comparator /
   reference standard, outcomes (Se/Sp for DTA; effect size for intervention), and exclusion
   criteria with justification.

4. **Search plan**: at least 3 databases — PubMed, Embase, and Cochrane CENTRAL (add Scopus / Web
   of Science as needed); a Boolean strategy from the PIRD/PICO components; a grey-literature plan
   (conference abstracts, trial registries); language restrictions and date range stated
   explicitly, with justification.

5. **RoB plan**: tool by type (table above), at least 2 independent assessors, and the
   disagreement-resolution method (consensus, third reviewer).

6. **Synthesis plan**: bivariate random-effects (Reitsma) or HSROC (Rutter & Gatsonis) for DTA;
   random-effects for intervention (Phase 6); heterogeneity, subgroup / sensitivity, and
   publication-bias plans.

7. **PROSPERO registration document**: read `${CLAUDE_SKILL_DIR}/references/PROSPERO_template.md`
   and follow its field guide, word limits, output format (Markdown + DOCX via pandoc), and Common
   Pitfalls Checklist. Save to the project's `7_Submission/` or equivalent directory.
   - **Registration-ID format gate.** A PROSPERO ID is `CRD42` + 9 digits (14 characters total),
     e.g. `CRD42024500001`. Validate any ID that appears in the manuscript or registration doc with
     `grep -oE 'CRD42[0-9]+'` and assert a 14-character length / `^CRD42\d{9}$` — a 15-character ID
     (a stray digit) is a transcription error a reviewer will check against the live record.
   - **Review-type selection.** Pick the *least-wrong* portal review type for the actual design and
     state any portal constraint in the protocol. A descriptive single-arm proportion synthesis is
     not an "Intervention review"; choosing that type only to satisfy a portal field contradicts a
     later GRADE / effect-certainty statement. Whatever certainty language the protocol commits to
     (GRADE vs "evidence statements only") must match the manuscript verbatim — a guideline-style
     "we recommend" is not licensed by a descriptive review type.

### Phase 2: Search Strategy

**Goal**: Develop and validate reproducible search strategies.

1. Build search blocks from the PIRD/PICO components and execute them per database with
   `/search-lit` (PubMed: MeSH + free text; Embase: Emtree + free text; further databases as the
   protocol specifies).
2. **Report per PRISMA-S** (Rethlefsen et al. 2021, PMID:33499930): one section per database with
   date of search, number of results, and any limits applied.
3. **Merge and deduplicate** into a single spreadsheet: by DOI first, then PMID. Save raw counts
   for the PRISMA flow.

### Phase 3: Screening & Selection

**Goal**: Systematic title/abstract and full-text screening with two independent reviewers. Read
`references/phase3_screening_detail.md` when executing a round (exclusion-code sets, AI pre-screening
template and Methods boilerplate) or when a 3f/3f.5 gate fires (set algebra, reconciliation table).

**3a. Round 1 — title/abstract (single reviewer).** Define the exclusion codes from the protocol.
Mark every record INCLUDE / EXCLUDE / MAYBE with a reason code → `round1_{date}.tsv`.

**3b. Round 2 — dual independent title/abstract.** A second independent reviewer (or AI as a
*documented* second-pass tool with human verification) re-screens all R1 records. Report Cohen's κ
in Methods. `round2_tag` = INCLUDE / EXCLUDE / MAYBE (MAYBE = disagreement **or** either reviewer
flagged uncertainty), plus `round2_reason`.

**3c. Round 3 — adjudication (first reviewer).** MAYBE records first, then INCLUDE records for a
brief confirmation pass → `round3_decision` (plus `round3_reason` only when overturning R2).
Optional AI pre-screening may compress the effort, but **AI suggestions are not decisions**: the
reviewer independently confirms or overturns every one.

**3d. Round 4 — full text** (`/fulltext-retrieval`) for `round3_decision = INCLUDE`: full-text
exclusion codes, two independent reviewers, Cohen's κ, consensus or a third reviewer. Flag
comparative studies for priority extraction.

**3e. PRISMA flow.** Track counts at every stage (R1 → R2 → R3 → R4 → final included); draw it with
`/make-figures` once final.

**3f. Post-consensus count reconciliation gate (MANDATORY before Phase 5 write-up).** Reconcile
counts from the **raw ID sets, never from prose summaries**, into one source-of-truth file:

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
   decision; silence is a gap. Never let it settle into narrative-only.

Two more gates at 3f; a non-zero exit from either blocks the Phase 5 write-up:

```bash
# every applied exclusion code vs the *registered* eligibility criteria
python3 ${CLAUDE_SKILL_DIR}/scripts/check_exclusion_code_validity.py --protocol 0_Protocol/protocol.md --screening 2_Screening/*.tsv --strict
# DI-6: PRISMA numbers on 5 surfaces (abstract/main text/flow figure/supplement/CSV) vs YAML SSOT;
# re-run on every revision that touches PRISMA numbers
python3 ${CLAUDE_SKILL_DIR}/scripts/prisma_5way_consistency.py --ssot prisma.yaml
```

Exclusion-code verdicts: `CODE_CONTRADICTS_ELIGIBILITY` (a code excludes a design the protocol
includes — bulk study loss no other gate can see), `CODE_NOT_REGISTERED`, `CODE_RENUMBERED`. Verdicts,
`NOT_ASSESSED` cases and known limits of all 3f gates: `references/phase3_screening_detail.md` §3f.

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

### Phase 4: Data Extraction

**Goal**: Create standardized extraction forms and extract 2x2 or effect-size data. Read
`references/phase4_extraction_detail.md` when building the form (DTA / intervention field lists),
when an AI draft was shared, for the optional `extract_assist.py` suggestions (`AI_SUGGESTED`, a
human confirms each before `dta_extraction_qc.py`), or when a QC flag fires.

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

```bash
# before the first extraction row (DI-1): comparative arm rows never live in R-script comments
python3 ${CLAUDE_SKILL_DIR}/scripts/extraction_consensus_log_init.py --output 2_Data/extraction_consensus_log.md
```

> **Failure-mode cross-ref** → `references/data_integrity_checklist.md` DI-1~DI-5 are mandatory
> during extraction (2x2 arm-swap, KM audit trail, methodology mismatch, PRISMA 5-way drift,
> single-source k).

**Extraction form.** Read `${CLAUDE_SKILL_DIR}/references/empirical_lessons.md` before designing
it. For high-impact radiology / medical AI targets use
`${CLAUDE_SKILL_DIR}/templates/extraction_form_v2.md`: its dual-extractor, source-page-reference,
and verbatim-quote columns close the 2x2 cell-swap and cohort-overlap blind spots.

**AI-drafted starting document — treat as hallucination-suspect.** If a mentor or collaborator
shared an AI-drafted study list, 2x2 set, or effect estimates (*even* flagged "for reference
only"): save it with a `_DO_NOT_USE_VERBATIM` suffix and re-verify **every** N, denominator, event
count, OR/CI, and author/year against the source PDF. Trust hierarchy: **source PDF + own analysis
stdout > the mentor's direct text > the attached AI draft** — never promote a draft up that ladder.

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
`2_Data/extraction_consensus_log.md`, then **lock the dataset**; later changes need a dated
justification. If 2x2 cells are missing, suggest contacting the authors or a sensitivity analysis
with imputed values.

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
analysis excluding one of the pair.

### Phase 5: Risk of Bias Assessment

**Goal**: Guide structured RoB assessment with the appropriate tool.

**DTA**: this phase runs QUADAS-3 **phases 3–6** (flow diagram, identify the estimates to
assess, assess, overall judgement). Phases 1–2 — the synthesis question and the ideal test
accuracy trial — were written in Phase 1 above. If they were not, stop and write them before
judging anything; they are the comparator every judgement is made against.

Select the tool by meta-analysis type (see table above), then read its checklist:

| Tool | Checklist File |
|------|---------------|
| QUADAS-3 (DTA, current) | `${CLAUDE_SKILL_DIR}/references/checklists/QUADAS3.md` |
| QUADAS-2 (DTA, legacy) | `${CLAUDE_SKILL_DIR}/references/checklists/QUADAS2.md` |
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

**Always use R** (packages: `meta`, `metafor`, `mada`); every reported estimate, CI, p-value, and
sample size comes from executed code output (Phase 6b audits this). Never guess dataset column names
or codings — if a mapping is uncertain, output `[VERIFY: variable_name]` and ask the user to confirm
against the data dictionary.

| Analysis family | Primary tool | Key output |
|-----------------|-------------|-----------|
| DTA | `mada::reitsma()` (bivariate) | Pooled Se/Sp + SROC with confidence/prediction regions |
| Intervention | `meta::metagen()` / `meta::metabin()` | Pooled OR/RR, τ² + I² + prediction interval, measure-matched funnel test (k ≥ 10), leave-one-out |
| Dual (comparative + single-arm) | `metabin` + `metaprop` | PRIMARY vs SECONDARY per pre-specified protocol |

Read `${CLAUDE_SKILL_DIR}/references/phase6_statistical_synthesis.md` before running the pooled
analysis — full R code templates (companion: `${CLAUDE_SKILL_DIR}/references/r_templates.md`), the
dual-approach decision table (comparative vs single-arm), practical cautions (method.tau, HK CI,
zero-cell correction), publication-bias test power, the sensitivity-analysis menu, and
error-handling rules. Write the pooled estimates, heterogeneity statistics, and k for each analysis,
taken from the executed R output, to `analysis/meta_analysis_outputs.json`.

**Three checks before the pool is written up** — each is a Methods sentence, not only a
setting. R and detail in the same reference:

1. **Is the event rare?** A pooled event rate < 1%, or any zero-event arm, moves the
   analysis off the inverse-variance default onto Peto / Mantel-Haenszel without a
   zero-cell correction / GLMM. Inverse-variance methods including DerSimonian-Laird are
   to be *avoided* for rare events, and so are 0.5 continuity corrections with them.
2. **Why this model?** Fixed vs random is a judgment about whether one common true effect
   exists — never derived from Cochran's Q or I². "A random-effects model was used
   because I² was 65%" is a reviewer catch, not a rationale.
3. **Does one study contribute several correlated effect sizes?** Multiple outcomes,
   readers, thresholds, or time points from the same participants need one pre-specified
   estimate per study, a multivariate model, or robust variance estimation — not
   independent pooling.

### Phase 6b: Post-Analysis Source Fidelity Audit (MANDATORY)

**Goal**: Catch numerical hallucinations that survived the forward pipeline (CSV → .R → manuscript).

**When it runs:** every time Phase 6 outputs change (first draft, revision, reviewer-requested
re-analysis) — including "minor" re-runs. The precedent: in a minor revision-era re-analysis, a
safety outcome's arm-level events (and so its p-value) were reported direction-reversed because a
Fisher `matrix()` was hand-typed from a misread source Table while the extraction CSV was correct.
Every downstream artifact echoed the wrong number, so internal consistency checks passed; only a
random back-check against the primary paper caught it.

**Non-negotiable rules:**

1. **No hand-typed numerical matrices when a CSV exists.** Use `read.csv(...)` + subset / filter;
   never copy a 2x2 table from a paper into `matrix(c(...), ...)` by eye. If hand entry is truly
   unavoidable (e.g., text-only extraction), the `matrix`, `c()`, or `data.frame` line MUST carry a
   comment citing the exact CSV row + column OR the exact primary-source Table/Page coordinate:
   ```r
   # source: data_extraction_final.csv row <N> (<first-author> <year>), cols <event_arm1>=0, <event_arm2>=1
   # verified against primary source Table <X>, page <P>
   fisher.test(matrix(c(0, 45, 1, 55), nrow = 2, byrow = FALSE))
   ```

2. **Comparative-arm subsets are a separate consensus-log row.** When one study's arm-specific
   values are used in a comparative analysis while its full cohort appears elsewhere,
   `extraction_consensus_log.md` must carry an explicit row for the arm-specific values. Pooled
   totals and arm-specific values MUST NOT share a row.

3. **Random 3-claim back-check before closing Phase 6.** After the forest/funnel/subgroup outputs
   stabilize, randomly sample 3 numerical claims from the draft Results and trace each back to (a)
   the R output log and (b) the original paper's Table/Figure. Record it in
   `peer_review_<vN>_internal.md`:

   | Claim (manuscript line) | R output file:line | Primary source (paper, Table/Fig, page) | Match? |
   |---|---|---|---|

   A single mismatch is a P0 blocker — do not advance to Phase 7 until resolved.

4. **Revision-introduced numbers must be tagged.** Any new number added after v1 — including
   numbers from a new comparative / subgroup / sensitivity script — MUST be wrapped inline as
   `[VERIFY-CSV]` in the manuscript until the Phase 2.5a audit in `/self-review` clears it.

5. **Sensitivity analyses must be recomputed on the modified data, not copied.** Every reported
   effect size in a sensitivity / leave-one-out / erosion / alternative-model analysis (Cohen's
   dz/f, AUC, OR, HR, β, sens/spec, ICC) MUST be re-derived from the modified dataset. If a
   sensitivity-table effect size is **identical to the primary analysis to two decimals across ≥4
   values** while the underlying means/SDs/counts differ, the recomputation did not run (chance
   coincidence ≈ (0.01)^4) and the primary values were transcribed — re-run the script on the
   modified data.

6. **A "fixed" / "resolved" audit note requires re-run evidence, not a claim.** A number recorded
   as `fixed`, `resolved`, or `corrected` counts only with a timestamp and the stdout / output-file
   line showing the corrected value, or the commit that changed it. A bare "fixed in v10" does NOT
   clear the finding — re-run the script and attach the output. The outcome-denominator
   cross-check (`/self-review` Phase 2.5b, the cohort-arithmetic / pool-lock assertions) must pass
   against the *current* outputs before any "fixed" status is accepted.

### Phase 7: GRADE / Certainty of Evidence

**Goal**: Assess certainty of the body of evidence.

DTA: GRADE-DTA — risk of bias (from QUADAS-3, or QUADAS-2 for a legacy review), indirectness
(applicability concerns), inconsistency (heterogeneity), imprecision (wide CIs, small sample),
publication bias. Intervention: standard GRADE.

**Certainty is assessed per outcome, not once for the review.** The domains resolve differently
for each outcome — one pooled from 12 studies with narrow CIs and one pooled from 3 with a wide CI
do not share a rating, and a single review-level "moderate certainty" sentence tells a reader
nothing about the outcome they came for. Rate every outcome carried into the Summary of Findings
table, and state the reason for each downgrade (which domain, why), not only the resulting label.

Output: Summary of Findings table — one row per outcome, carrying the pooled estimate with its
precision alongside the certainty rating (high / moderate / low / very low).

### Phase 8: Reporting & Manuscript

**Goal**: Generate PRISMA-compliant manuscript sections.

> **Failure-mode cross-ref** → `references/submission_package_drift.md` — apply the `_build.sh` pattern + `DO_NOT_EDIT_HERE` gate when staging multi-journal submission folders.

Re-read `references/empirical_lessons.md` before submission.

1. **Check reporting compliance**: `/check-reporting` with PRISMA-DTA (bundled copy:
   `references/checklists/PRISMA_DTA.md`) or PRISMA 2020, then a **second, separate** run over the
   **abstract** with PRISMA 2020 for Abstracts (`PRISMA_2020_Abstracts.md`, 12 items, its own
   denominator). Report that score separately: item 2 of the main checklist only defers to it, so a
   manuscript can satisfy all 42 main-text items and still fail most of the twelve, and folding
   them into one total is how they stay invisible.
2. **Write the manuscript**: `/write-paper` with the meta-analysis type → `manuscript/manuscript.md`.
   Never generate references from memory; use `/search-lit` for all citations.
3. **Figures** (`/make-figures`): PRISMA flow diagram, forest plots (paired for DTA), SROC curve
   (DTA), funnel plot (Deeks' for DTA — see DTA pitfalls), RoB summary (traffic light plot).
4. **Tables**: characteristics of included studies; 2x2 data per study (DTA); RoB assessment
   results; Summary of findings / GRADE table (one row per outcome — Phase 7).

5. **The items published radiology SR/MAs most often drop** — check these by hand before the
   compliance run. Park 2022 (Korean J Radiol; PMID:35213097) scored 24 SR/MAs against PRISMA
   2020 and found 24 of 42 items reported by fewer than 80%:

   | PRISMA item | What is missing | Observed |
   |---|---|---|
   | **20a** | For **each** synthesis, a brief summary of the contributing studies' characteristics and risk of bias — not one global paragraph covering all pools | 0/24 |
   | **27** | Data availability: which of the extraction forms, extracted data, analysis dataset, and analytic code are public, and where | 0/24 |
   | **24a–c** | Registration number, where the protocol can be read, and any amendment — an explicit "not registered" satisfies 24a | 0/24 |
   | **22 / 15** | Certainty of evidence per outcome, and the method used to assess it | 9% |
   | **13f / 20d** | Sensitivity analysis: method and result | 28% |
   | **18** | Risk of bias **per study**, shown study-by-study rather than as a pooled proportion | 32% |
   | **13d** | Rationale for the synthesis model (see Phase 6 check 2) | 35% |
   | **16b** | Studies that look eligible but were excluded, cited individually with the reason | 25% |
   | Abstract **#3, #12** | Eligibility criteria and registration inside the structured abstract | 0/24 each |

   If the PROSPERO ID is missing, flag it as a limitation but continue.

6. **Data availability statement**: name what is being shared (extraction template, locked
   dataset, analysis code, RoB judgments) and where — repository, DOI, or supplementary file.
   "Available from the corresponding author on reasonable request" satisfies few journals now and
   no longer satisfies item 27. If a Zenodo DOI is minted post-acceptance,
   `references/post_submission_release_ops.md` covers propagating it back into this statement.

7. **Supplementary & analysis-code pre-submission gate** (before Phase 9 circulation and before
   portal upload). Presence of the 8-file package (Empirical Lesson 5) is necessary but not
   sufficient — each item must also be reviewer-ready:
   - **De-scaffold**: strip internal-QC / tool artifacts — raw `/check-reporting` output ("Assessed by: <tool>", JSON blocks, "READY FOR SUBMISSION" verdicts, action-item lists), search-development planning docs (decision logs, expected-yield estimates, `[Check on execution]` placeholders, version-history dev notes), and stale version stamps. Ship a clean PRISMA 2020 checklist (27-item / 42-subitem table only) and an executed-method search-strategy doc, not the working drafts.
   - **Blind**: remove author names/initials and sibling-project cross-references ("Designed by: <name>", "identical to a sibling review") — same standard as the blinded manuscript.
   - **Cross-consistency**: every supplementary number matches the main text — PRISMA counts, pool k/N, the Cochrane/CENTRAL search description, RoB counts.
   - **Reproducible, self-contained analysis code**: run it from a clean copy of the bundle. It must read the bundled locked dataset (not an out-of-bundle path), write to the working directory, and regenerate every pool in the results table. A hard-coded study-id subset that drifts from the manuscript (a pool over k=7 while the manuscript reports k=9) is a P0 — fix and re-run; never ship stale code or figures derived from it.
   - **Supplementary-only review pass**: the manuscript self-review does not see the supplement; mirror `/self-review` Phase 2.5c–2.5d (reference + cross-reference QC) over the supplementary files.

8. **Submission gates** (on Phase 8 pre-submission and every journal retarget; a non-zero exit
   blocks submission):
   - `/sync-submission` SR-MA gate: the supplementary package matches all 8 files in
     `templates/supplementary_8file_checklist.md` (PRISMA, PROSPERO, search strategy, exclusion
     list, extraction table, per-study x per-domain RoB, subgroup forests, sensitivity /
     publication bias); AI Disclosure is present (cross-link `/peer-review` Phase 2A P8); no
     duplicate PMID/DOI in the cite list (`/verify-refs` Gate 5).
   - DI-8 tag gate — fails if `VERIFY-CSV`/`TODO`/`FIXME`/`XXX` survive in `7_Manuscript`,
     `supplement`, `SUBMISSION`, etc.: `bash ${CLAUDE_SKILL_DIR}/scripts/tag_cleanup_gate.sh`
   - SPD package integrity — checksum-based drift detection between the master manuscript and the
     built `SUBMISSION/{journal}/` folder (journal-editable files — cover letter, response,
     MANIFEST, `DO_NOT_EDIT_HERE.md` — are auto-excluded). On the first build per journal run
     `python3 ${CLAUDE_SKILL_DIR}/../sync-submission/scripts/verify_package_integrity.py --record --journal <name>`,
     then `--verify --journal <name>` before every re-submission.
   - ICMJE COI forms for every author: `${CLAUDE_SKILL_DIR}/references/icmje_coi_guide.md`.

---

### Phase 9: Co-author Circulation

**Goal**: Pre-submission circulation to co-authors and a senior methodologist / reviewer, with a
bounded review window and a controlled attachment scope.

**Trigger**: Phase 8 is complete, and the draft has cleared the Phase 6b source-fidelity audit.

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

**Sprint**: read `${CLAUDE_SKILL_DIR}/references/phase10_recovery.md` and run its 12 steps, from
10.1 (audit log at `qc/audit_vN_to_vNplus1.md`) through the PROSPERO amendment (application
correction, not criteria change) and re-circulation in the Phase 9 thread to 10.12 (post-recovery
loop).

> **Failure-mode cross-ref** → `references/post_submission_release_ops.md` Gate 4 covers reject/revise Zenodo versioning, tag-cleanup gate, and re-target workflow (avoid "new version" misuse on re-target).

---

## DTA-Specific Pitfalls (Always Check)

| Pitfall | Problem | Solution |
|---------|---------|----------|
| Separate pooling of Se/Sp | Ignores correlation | Use bivariate/HSROC model |
| Ignoring threshold effect | False heterogeneity | Judge from the SROC plot and the bivariate Se–FPR correlation (Spearman is descriptive only) |
| Standard funnel plot for DTA | Inappropriate | Use Deeks' funnel plot |
| I-squared only for heterogeneity | Doesn't capture threshold effect | Use prediction region on SROC |
| Missing GRADE | Common omission in DTA MA | Apply GRADE-DTA. If <4 studies, assess each domain narratively and state the limitation explicitly |
| Partial verification bias | Inflates sensitivity | QUADAS-3 **3.2** (target condition assessed in all participants). QUADAS-3 has no Flow & Timing domain — that was QUADAS-2 |
| Differential verification bias | Distorts both Se and Sp | QUADAS-3 **3.3** (target condition assessed the same way in all participants) |
| Unevaluable results excluded | Biases accuracy estimates | Report intent-to-diagnose analysis |

---

## Small Study Considerations

When the number of included studies is small (< 10):
- Bivariate/HSROC model may not converge (warn the user when a DTA review has fewer than 4
  studies) — consider univariate random-effects as fallback
- Publication bias tests are underpowered — state this limitation
- Subgroup/meta-regression analysis not recommended
- Wide prediction regions expected — emphasize uncertainty in conclusions
- Consider narrative synthesis as alternative/complement
