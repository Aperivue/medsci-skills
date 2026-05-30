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
- 인용 포맷 예 (categorical): sheet = `{{dictionary_sheet}}`, row = `r{{N}}`, verbatim = `0={{meaning}}, 1={{meaning}}, ...` (codebook 원문 그대로 복사).
- Data dictionary 가 존재하는 관찰연구(예: NHIS, KNHANES, UK Biobank, 기관 EMR/검진 registry 등)에서 **필수** — 비워둘 수 없음. 프로젝트 단위 정책은 repo 내 `DICTIONARY_FIRST_POLICY.md` (또는 shared-config) 에 수록.
- Dictionary 에 명시 없는 코드값 → DB 담당자/data steward 문의 후 답변 수령 전까지 해당 행 작성 보류.
- BMI/SBP 등 자명한 continuous 변수는 `dict: n/a (continuous)` 로 표기 가능. Cutoff 는 여전히 canonical source 필요.

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
