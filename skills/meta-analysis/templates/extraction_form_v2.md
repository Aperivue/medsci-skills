# SR-MA Data Extraction Form v2

**Version**: v2.0
**Motivation**: Recent SR-MA peer-review cycles surfaced three recurring extraction-stage failure modes — diagnostic 2×2 cell sens/spec swap, undisclosed cohort overlap via shared public databases, and undocumented diagnostic vs prognostic subset N. v2 adds three column families to prevent recurrence.

## Coverage

Use this form for any SR-MA with diagnostic accuracy and/or prognostic prediction outcomes. Compatible with QUADAS-AI / PROBAST-AI / METRICS frameworks.

## Column schema (CSV / Google Sheets)

### Identity (always required)

| Column | Description | Example |
|---|---|---|
| `study_id` | Internal ID (`<Surname>_<Year>_<seq>`) | `StudyA_2021_1` |
| `pmid` | PubMed ID | `00000000` |
| `doi` | DOI | `10.xxxx/example.YYYY.NNNNNN` |
| `first_author_lastname` | LastName from PubMed | `Surname` |
| `first_author_forename` | ForeName from PubMed | `Forename` |
| `year` | Publication year | `2021` |
| `country` | Per affiliation (use country of cohort, not publisher) | `[Country]` |
| `journal` | Full journal name | `[Journal Full Title]` |
| `study_design` | retrospective / prospective / case-control / cross-sectional | `retrospective` |

### Cohort source (NEW in v2 — prevents undisclosed overlap)

| Column | Description | Example |
|---|---|---|
| `cohort_source` | One of: `institutional` / `multi-center prospective` / `MIMIC-IV` / `eICU` / `MIMIC-III` / `KNHIS` / `UK Biobank` / `TriNetX` / `Optum` / `MarketScan` / `SEER` / etc. | `MIMIC-IV` |
| `institution_primary` | Verbatim institution name from corresponding-author affiliation | `Tertiary Academic Medical Center, [City]` |
| `institutions_additional` | Pipe-separated additional centers | `Other Affiliated Hospital` |
| `enrollment_period_start` | YYYY-MM | `2017-01` |
| `enrollment_period_end` | YYYY-MM | `2019-12` |
| `data_sharing_statement` | Yes / No / NotReported | `NotReported` |
| `overlap_flag_reviewer1` | Reviewer 1 suspects cohort overlap with which study_id (or empty) | `StudyB_YYYY` |
| `overlap_flag_reviewer2` | Reviewer 2's overlap flag | `StudyB_YYYY` |

### Sample sizes (diagnostic subset N transparency)

| Column | Description | Example |
|---|---|---|
| `sample_n_total` | Total study N | `452` |
| `sample_n_train` | Training set N | `273` |
| `sample_n_internal_test` | Internal test N | `68` |
| `sample_n_external_test` | External test N | `111` |
| `sample_n_dta_pool` | N contributing to DTA bivariate (sens/spec extraction) | `111` |
| `sample_n_prognostic_pool` | N contributing to prognostic AUC pool | `0` |
| `prevalence_in_dta_pool` | (TP+FN) / sample_n_dta_pool | `0.414` |

### DTA outcome extraction (2×2 cell integrity)

For each cohort that contributes to bivariate pool, extract:

| Column | Description | Example |
|---|---|---|
| `dta_cohort_label` | Which cohort the values come from (must match `sample_n_external_test` or similar) | `external_test` |
| `tp` | True positive count | `45` |
| `fn` | False negative count | `1` |
| `tn` | True negative count | `36` |
| `fp` | False positive count | `29` |
| `extracted_sens` | TP / (TP+FN), decimal | `0.978` |
| `extracted_spec` | TN / (TN+FP), decimal | `0.554` |
| **`source_sens_reported`** | Sensitivity as reported in source paper (decimal) | `0.978` |
| **`source_spec_reported`** | Specificity as reported in source paper (decimal) | `0.554` |
| **`source_page_ref`** | Page + Table/Figure number in source paper | `Table 3, p.7` |
| **`source_verbatim_quote`** | Verbatim sentence containing the sens/spec values | `"The deep-integrated model achieved a sensitivity of 0.978..."` |
| `extractor1_initials` | First extractor | `R1` |
| `extractor2_initials` | Second extractor | `R2` |
| `extraction_consensus_status` | Resolved / DiscussNeeded / Conflict | `Resolved` |

**QC**: Run `scripts/dta_extraction_qc.py` with `--tolerance 0.02` after dual-extractor entry. Any FLAG_SWAP or FLAG_MISMATCH requires third-reviewer adjudication.

### Prognostic outcome extraction (PROBAST-AI compatible)

| Column | Description | Example |
|---|---|---|
| `prognostic_outcome_type` | mortality / AKI / disease_progression / readmission / etc. | `mortality` |
| `prognostic_endpoint_definition` | Verbatim definition | `In-hospital all-cause death within index admission` |
| `auc_point` | Reported AUC, decimal | `0.87` |
| `auc_ci_lower` | 95% CI lower | `0.83` |
| `auc_ci_upper` | 95% CI upper | `0.90` |
| `validation_type` | internal / external / leave-one-out / k-fold | `external` |
| `calibration_reported` | Yes / No | `No` |
| `dca_reported` | Decision curve analysis Yes/No | `No` |

### Risk of bias (per-study × per-domain)

QUADAS-AI (for DTA studies):

| Column | Description |
|---|---|
| `quadasai_d1_patient_selection` | Low / High / Unclear |
| `quadasai_d2_index_test` | Low / High / Unclear |
| `quadasai_d3_reference_standard` | Low / High / Unclear |
| `quadasai_d4_flow_timing` | Low / High / Unclear |
| `quadasai_d1_justification` | Verbatim short reason |
| `quadasai_d2_justification` | ... |
| ... | (same for D3, D4) |
| `quadasai_overall` | Low / High / Unclear (consensus) |

PROBAST-AI (for prognostic studies): D1 Participants / D2 Predictors / D3 Outcome / D4 Analysis — same Low/High/Unclear + justification.

METRICS: 4 domains (data, model dev, validation, reporting) per study.

### Authors of extraction record

| Column | Description |
|---|---|
| `extraction_date_initial` | YYYY-MM-DD |
| `extraction_date_consensus` | YYYY-MM-DD |
| `cohens_kappa_d1` | Pre-adjudication inter-rater κ for domain D1 |
| ... | (record κ for each pre-adjudication discrepancy domain) |

## Workflow (dual-extractor consensus)

1. Extractor 1 + Extractor 2 independently fill all cells, source_page_ref, source_verbatim_quote
2. Run `dta_extraction_qc.py --tolerance 0.02` → flag mismatches
3. Pre-adjudication κ recorded for D1-D4
4. Discrepancies → third-reviewer adjudication, consensus_status updated
5. Run `cohort_overlap_check.py --enrich` → populate database_source via PubMed if missing
6. Manual review of HIGH/MEDIUM clusters → confirm or override
7. Lock extraction (read-only) before statistical analysis

## Related

- `scripts/dta_extraction_qc.py`
- `scripts/cohort_overlap_check.py`
- `templates/supplementary_8file_checklist.md`
