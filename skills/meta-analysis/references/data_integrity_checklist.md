# Data Integrity Checklist

**Applies to**: the full span of Phase 3 (Extraction) ~ Phase 6 (Statistical synthesis) ~ Phase 9 (Circulation). Blocks the numerical-consistency risks specific to meta-analysis.

## 1. Extraction stage

### DI-1. Formalize the extraction consensus log
- **Problem pattern**: Comparative extraction results kept only as inline comments inside the R analysis script — no standalone consensus log → arm-specific numbers become irretraceable once the script is edited.
- **Rule**: At the start of every MA project, create `2_Data/extraction_consensus_log.md` or `3_Extraction/extraction_consensus_log.md`. Columns: study_id, arm, numerator, denominator, source_page, source_type (text/table/figure/KM-reconstruction), extractor_initials, second_reviewer_initials, timestamp, notes. Comparative extractions must live only as formal rows, never as script comments.

### DI-2. Mandatory double-check of 2x2 cell counts
- **Problem pattern**: Hand-typed 2x2 cells with arm order swapped against the source paper, or with numerator/denominator misread from a KM-derived subgroup rather than the raw table. Both fail silently until a third reviewer back-calculates the proportion.
- **Rule**: Every 2x2 / comparative extraction requires (a) a first extraction + (b) an independent second re-extraction + (c) source re-check on any mismatch + a consensus-log row. Perform the Phase 6b "numerical safety gate".

### DI-3. Complete the KM-reconstruction audit trail
- **Problem pattern**: Subgroup cell counts reconstructed from a published KM curve without preserving the WebPlotDigitizer trace or the IPDfromKM reconstruction log → numbers cannot be re-derived if a reviewer challenges them.
- **Rule**: KM-reconstruction outputs must be kept as a set in `3_Extraction/km_reconstruction/{study_id}/`: (a) the WebPlotDigitizer JSON, (b) the IPDfromKM CSV, and (c) metadata for tool version + coordinate values + parameters + date. Link them in the consensus log as type "km-reconstruction".

### DI-4. Denominator change = source page citation + consensus-log row
- **Problem pattern**: Denominator correction (e.g., treatment-naive subset) entered only as an R-script comment without citing the source paper's page/table → the correction's rationale is lost at revision.
- **Rule**: Every denominator change requires (a) a source page/table citation, (b) a sentence stating the rationale, and (c) one consensus-log row. Reject the change if any of the three is missing.

### DI-5. Methodology mismatch random spot-check
- **Problem pattern**: A source paper reports per-protocol analysis while the SR framework is ITT/ITD (or vice versa). Without a methodology spot-check, the study's effect estimate is silently re-used under a different analysis framework.
- **Rule**: Include a "methodology flag" in the extraction spot-check scope — whether each study's source analysis unit (per-protocol / ITT / ITD) matches our SR framework. Re-extract on mismatch.

## 2. 3~5-way consistency

### DI-6. PRISMA flow 5-way consistency
- **Problem pattern**: PRISMA flow numbers drift across the search CSV, the screening log, the Methods prose, the Results prose, and the Figure 1 caption — five surfaces reach submission in three mutually inconsistent states (reversed database order, divergent full-text-assessed counts, stale caption numbers).
- **Rule**: Verify the PRISMA flow numbers as consistent across five places simultaneously:
  1. `1_Search/*.csv` original (source of truth, no edits)
  2. `2_Screening/prisma_flow_final.md`
  3. Manuscript Methods prose
  4. Manuscript Results prose (where mentioned again)
  5. Figure 1 caption (both `5_Figures/_captions.md` and the short DOCX caption)
- **ID-Set Gate Rule 5**: fix the prose first → then render the diagram. If the diagram is built first, editing the prose causes drift.
- **Automation candidate**: manage `k`, `n`, and the search numbers in a single YAML source and substitute them into the prose/diagram templates.

### DI-7. Single source for k = `4_Analysis/*.csv`
- **Problem pattern**: Included-study count `k` quoted as two different values across consecutive manuscript versions because it was hand-typed into prose rather than derived from the analysis CSV.
- **Rule**: Derive k only from the `4_Analysis/*.csv` row count. When entering k into the manuscript / MANIFEST / PROSPERO, also state the CSV path + row count.

## 3. Pre-submission cleanup

### DI-8. Remove every tag / TODO
- **Problem pattern**: `TODO`, `[VERIFY-CSV]`, "to be regenerated" strings survive into the submission package — found in R scripts, figure captions, and supplementary material banners.
- **Rule**: 0 hits for the following grep before submission day:
  ```bash
  rg -n "VERIFY-CSV|TODO|FIXME|XXX|to be regenerated|PH TODO|to-do" \
     7_Manuscript/ supplement/ 5_Figures/ 6_Tables/ 1_Code/
  ```
- **`[VERIFY-CSV]` lifecycle**: attach (v6) → verify (v7) → mark (v8+) → remove (submission). Record each stage in the MANIFEST.

### DI-9. State bias-driven homogeneity interpretation
- **Problem pattern**: In a DTA pool where every included study is retrospective with differential verification, Sp I²=0% reflects universalized bias compression rather than true between-study homogeneity — easy to over-interpret as robust agreement.
- **Rule**: When I²=0% and QUADAS-2 Domain 4 risk are both high/unclear → state "universalized bias compression" explicitly and frame as an "upper-bound estimate". Bias context is mandatory in the Discussion.
