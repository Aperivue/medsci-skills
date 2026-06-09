# Variable Operationalization — {{PROJECT_SHORT_TITLE}}

- **Research question**: {{ONE_SENTENCE_Q}}
- **Cohort**: {{COHORT_NAME_TYPE}} (e.g., Institutional Health Screening Cohort, retrospective)
- **Author**: {{AUTHOR_NAME}}
- **Last updated**: {{YYYY-MM-DD}}
- **Upstream artifacts**: `design_study.md`, `search_lit_results.md` (if present)

## Operationalization table

| # | Variable | Role | Dict. sheet & row | Dict. verbatim | Canonical source | Definition | Cutoff | DB vars | Implementation | Ad-hoc? |
|---|----------|------|-------------------|----------------|------------------|------------|--------|---------|----------------|---------|
| 1 | {{var}} | exposure | `{{sheet}} r{{N}}` | `{{code→meaning verbatim from dictionary}}` | @bibkey | verbatim from guideline | value + units | `col_a, col_b` | `col_a>=X & col_b==Y` | no |
| 2 | {{var}} | outcome | `{{sheet}} r{{N}}` | `{{verbatim}}` | @bibkey | ... | ... | ... | ... | no |
| 3 | {{var}} | covariate | `{{sheet}} r{{N}}` | `{{verbatim}}` | @bibkey | ... | ... | ... | ... | yes |
| 4 | {{var}} | eligibility | `{{sheet}} r{{N}}` | `{{verbatim}}` | @bibkey | ... | ... | ... | ... | no |

Roles: `exposure` / `outcome` / `covariate` / `eligibility`

**Dict. sheet & row / Dict. verbatim (mandatory for DB-backed projects)**:
- Citation format example (categorical): sheet = `{{dictionary_sheet}}`, row = `r{{N}}`, verbatim = `0={{meaning}}, 1={{meaning}}, ...` (copied exactly from the codebook).
- **Mandatory** for observational studies that have a data dictionary (e.g., NHIS, KNHANES, UK Biobank, institutional EMR / health-screening registries) — it cannot be left blank. Record the project-level policy in `DICTIONARY_FIRST_POLICY.md` (or a shared config) in the repo.
- For a code value not specified in the dictionary → hold off filling that row until you have asked the DB owner / data steward and received an answer.
- Self-evident continuous variables such as BMI/SBP may be marked `dict: n/a (continuous)`. The cutoff still requires a canonical source.

## Ad-hoc justifications

For each row flagged `Ad-hoc: yes`, document:

### {{variable_name}}

- **Why no canonical source**: e.g., no guideline for this subgroup; novel combination of existing criteria
- **Chosen rule**: precise cutoff / logic
- **Sensitivity plan**: alternative cutoff to test in sensitivity analysis
- **Reviewer-facing justification**: 1-2 sentences that will appear in Methods

## Mapping gaps

Variables defined in the protocol but NOT directly available in the DB:

| Protocol variable | DB status | Decision |
|-------------------|-----------|----------|
| {{name}} | not available | proxy with `...` / request from DB owner / drop |

## References

```bibtex
@article{rinella2023_aasld_masld,
  author  = {Rinella, Mary E and others},
  title   = {A multisociety {Delphi} consensus statement on new fatty liver disease nomenclature},
  journal = {Hepatology},
  year    = {2023},
  doi     = {10.1097/HEP.0000000000000520}
}

% add one entry per cited canonical source
```

## Verification log

- [ ] Tier 1 lookups documented (guideline year, cutoff quoted)
- [ ] Tier 2 `/search-lit` queries logged (query string + papers retained)
- [ ] Tier 3 `/verify-refs` passed (0 unverified citations)
- [ ] No silent ad-hoc — every deviation flagged and justified
