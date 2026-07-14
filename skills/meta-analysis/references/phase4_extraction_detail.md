# Phase 4 — Data Extraction: gate detail and extraction forms

Load-on-demand companion to `/meta-analysis` Phase 4. SKILL.md keeps the mandatory
entry gate, the two QC commands, and the fail-closed rules; this file carries the
detail behind them.

Read the block you need:

- **AI-drafted starting document gate** — only when a mentor/collaborator has shared an
  AI-drafted study list, 2x2 set, or effect estimates.
- **AI-assisted extraction suggestions** (`extract_assist.py`) — optional scaffolding;
  suggestions, never decisions.
- **Extraction form fields** — the DTA and intervention field lists.
- **Cross-verification** — the six dual-reviewer checks, in full.
- **QC rationale** — what `dta_extraction_qc.py` and `cohort_overlap_check.py` catch, and
  the flag → form-edit forced transition.

**Goal**: Create standardized extraction forms and extract 2x2 or effect size data.

#### 4.0 Entry gate (MANDATORY): pool composition lock ↔ adjudication TSV

Before any extraction work begins, run the deterministic UID-set check
to confirm that the round-3 adjudication TSV and `FINAL_POOL_LOCK.yaml`
(produced in Phase 3f.5) agree on which UIDs are included.

```bash
python "${CLAUDE_SKILL_DIR}/scripts/check_pool_consistency.py" \
    --lock 2_Data/FINAL_POOL_LOCK.yaml \
    --adjudication-tsv 2_Screening/round3_adjudication.tsv \
    --decision-col round3_decision \
    --uid-col uid \
    --include-labels "INCLUDE,INCLUDE_MIXED" \
    --out qc/pool_consistency.json
```

Output `qc/pool_consistency.json`:

```json
{
  "submission_safe": false,
  "match": false,
  "lock_include_n": 42,
  "tsv_include_n": 43,
  "in_lock_not_tsv": ["UID_007"],
  "in_tsv_not_lock": ["UID_055"]
}
```

The gate fails closed: any UID disagreement blocks extraction. To
resolve, either (a) re-freeze the lock with the corrected set of UIDs
and propagate to downstream artifacts, or (b) correct the adjudication
TSV if a row was mis-labeled. Do NOT proceed to Phase 4 with a
mismatch — the resulting extraction matrix will not align with the
locked pool, and the drift surfaces as a fabrication-grade red flag at
peer review.


> **Failure-mode cross-ref** → `references/data_integrity_checklist.md` DI-1~DI-5 are mandatory during extraction (2x2 arm-swap, KM audit trail, methodology mismatch, PRISMA 5-way drift, single-source k).

**Recommended extraction form**: For SR-MA targeting high-impact radiology / medical AI journals, use `${CLAUDE_SKILL_DIR}/templates/extraction_form_v2.md`. Dual-extractor + source-page-reference + verbatim-quote columns prevent the 2x2 cell-swap and cohort-overlap blind spots surfaced in recent SR-MA peer-review cycles. New required columns: `cohort_source`, `source_page_ref`, `source_verbatim_quote`, `extraction_consensus_status`, `overlap_flag_reviewer1/2`, `sample_n_dta_pool` vs `sample_n_prognostic_pool`.

#### 4.0 AI-drafted starting document gate

Before opening the extraction form: if a senior mentor or collaborator has shared an AI-drafted starting document (Claude / ChatGPT / Gemini draft of the study list, 2x2 cells, or effect estimates) — even when the sender flags it as "for reference only" — apply `~/.claude/rules/ai-drafted-document-policy.md`:

- Save the file with a `_DO_NOT_USE_VERBATIM` (or `_AI_DRAFT_REFERENCE_ONLY`) filename suffix.
- Treat every per-study N, denominator, event count, OR/CI, and author/year as **hallucination-suspect** until re-verified against the source PDF + own analysis script. AI-drafts collapse multiple denominator definitions (treatment-naïve / full-cohort / per-arm) into one and silently mis-route counts.
- Record any reconciled discrepancy in `extraction_consensus_log.md` with a verbatim quote of the AI-draft value and the corrected value with PDF page coordinate.
- Trust hierarchy for this phase: **SSOT (source PDF + own analysis stdout) > mentor's direct text (email / track-changes) > attached AI-draft**. Do not promote an AI-draft from tier 3 to tier 2.

Precedent (an active meta-analysis project): Ishikawa 2017 "treatment support 5/70 vs no support 12/33" in Claude-drafted directive → source PDF was 35/68 (single arm). Verbatim absorption would have produced a denominator-hallucinated meta-analysis.

#### 4.0.1 AI-assisted extraction suggestions (optional, suggestions not decisions)

To scaffold (not replace) manual extraction from a full-text paper, use the
deterministic helper `scripts/extract_assist.py`. It scans a Markdown full text
(e.g. `/fulltext-retrieval`'s PDF→MD output) for schema-defined fields and emits
**candidate values, each with a `source_page_ref` and a verbatim source quote** —
the extraction-stage analog of the screening-stage `ai_pre_screening_template.py`.

```bash
python3 scripts/extract_assist.py \
  --md paper.md --schema schema.yaml --study-id StudyA_2021 --out suggestions.tsv
```

- **Suggestions, never decisions.** Every row is `extraction_consensus_status =
  AI_SUGGESTED` and `needs_review = true`. The tool invents nothing — values and
  quotes are copied literally from the text; absent fields become explicit
  `not_found` rows; unit-ambiguous values (e.g. `92%` vs `0.92`) are emitted as
  multiple candidates side by side so the reviewer reconciles them.
- **Human confirmation is mandatory.** Apply the 4.0 gate: treat every candidate
  N / denominator / 2x2 cell / effect estimate as hallucination-suspect until
  confirmed against the source PDF, recording reconciliations in
  `extraction_consensus_log.md`. Confirm or overturn each suggestion into the
  `extraction_form_v2.md` columns.
- **Then, and only then, QC.** Build the confirmed DTA CSV and run
  `dta_extraction_qc.py` on **that** table — never on the suggestion TSV.
  Passing QC is not extract-assist's acceptance criterion; per-cell human
  confirmation is.

A deterministic, network-free challenge card demonstrating the full
suggestions → confirm → QC pipeline lives in
`scripts/extract_assist_challenge/` (synthetic paper + schema + expected output
+ `verify.sh`).

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

#### Phase 4c: Extraction QC & Cohort Overlap Detection

After dual-extractor consensus, run two QC scripts before locking the extraction table for statistical synthesis.

**1. 2x2 Cell Integrity Check** -- `scripts/dta_extraction_qc.py`:

Validates manuscript forest-plot cells (TP / FN / TN / FP) against source-paper-reported sens/spec within a tolerance (default 0.02). Catches sens/spec swap at extraction stage -- a common error pattern where a single-study k=1 subgroup outlier flips conclusions due to cell-assignment swap.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/dta_extraction_qc.py" \
  --input 2_Extraction/extraction.csv \
  --tolerance 0.02 \
  --out 2_Extraction/qc/dta_extraction_qc.tsv
```

Any `FLAG_SWAP` or `FLAG_MISMATCH` row requires third-reviewer adjudication before Phase 6 statistical synthesis.

**Flag → form-edit forced transition.** A confirmed flag is not resolved until the extraction form itself is edited. Track each flag through `confirmed → acted`: after the adjudicator confirms a `FLAG_SWAP`/`FLAG_MISMATCH`/unit-of-analysis violation, the extraction CSV row MUST be corrected and the QC re-run to clear it. A flag that is "confirmed" but whose form row is unchanged (the correction lived only in a review note) silently re-enters synthesis. Verify the form's mtime advanced and the re-run QC shows zero open flags before locking.

**2. Cohort Overlap Check** -- `scripts/cohort_overlap_check.py`:

Clusters included studies by (a) shared public ICU/EHR database (MIMIC-IV, eICU, MIMIC-III, KNHIS, UK Biobank, Optum, MarketScan, TriNetX, IBM), (b) same institution + overlapping enrollment period, (c) shared first-author surname + ±2y year proximity. Flags HIGH / MEDIUM overlap confidence.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/cohort_overlap_check.py" \
  --input 2_Extraction/studies.csv \
  --enrich \
  --out 2_Extraction/qc/cohort_overlap.md
```

HIGH-confidence overlap pairs require Limitations acknowledgment + sensitivity analysis excluding one of the pair.

Cross-links: `/peer-review` Phase 2A P1 (cell integrity) + P2 (cohort overlap).
