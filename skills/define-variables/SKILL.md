---
name: define-variables
description: >
  Literature-grounded variable operationalization for observational research. Turns a data dictionary +
  research question into a citation-backed table of exposure/outcome/covariate definitions, cutoffs, and
  DB variable mappings. Prevents ad-hoc phenotype definitions that invite reviewer rejection. Bridges
  /search-lit output into /write-protocol Methods.
triggers: variable definition, phenotype definition, operationalization, cutoff justification, inclusion criteria, case definition, grouping criteria, literature-grounded definition, canonical definition, 변수 정의, 정의 근거
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Define-Variables Skill

## Purpose

Every observational study operationalizes abstract constructs (MASLD, CKD, emphysema, obesity, incidentaloma) into concrete rules against the available data dictionary. When that operationalization is invented ad-hoc from the dictionary alone, reviewers reject on construct validity regardless of downstream statistics.

This skill forces a **literature-first** pass: each variable is mapped to a canonical guideline/consensus definition, cross-checked against prior operationalizations in comparable cohorts, then mapped to available DB variables. Ad-hoc deviations are flagged explicitly and justified, not hidden.

Use it when:
- a study question is known and variables are being selected
- inclusion/exclusion criteria or phenotype definitions need citation backing
- a data dictionary has ambiguous or derived variables (eGFR formula, BMI class, liver steatosis criteria, etc.)
- a reviewer asked "why this cutoff?"
- a retrospective audit reveals drifted definitions across projects in the same cohort

Call after `/design-study`, before `/write-protocol`.

## Communication Rules

- Communicate in the user's preferred language.
- All variable names, guideline names, cutoffs in English.
- Produce one artifact: `variable_operationalization.md` in the project root (or path the user specifies).

## Inputs

1. **Research question** (one sentence)
2. **Candidate variables** — exposure, outcome, key covariates, eligibility filters
3. **Data dictionary path** (xlsx / csv / markdown) OR explicit list of available DB columns
4. **Cohort type** (e.g., health-screening, NHANES-like, claims, registry) — informs which prior-art cohort to compare against

Missing inputs → ask once, then proceed.

## 4-Tier Pipeline (DB codebook + token-efficient literature)

### Tier 0 — DB codebook lookup (mandatory for DB-backed observational studies)

**Trigger**: project has a `project.yaml::db.dictionary_path` field pointing to a machine-readable codebook (xlsx/csv/markdown), OR user supplied a dictionary path in inputs. If neither, skip to Tier 1.

For every candidate DB variable — **before** touching literature — open the dictionary and record, verbatim, the sheet name, row number, and code→meaning mapping. This prevents the single most common observational-study error: assuming a column code (`status == 0`, `grade == 4`) means what it intuitively reads like, when the codebook says otherwise.

Concrete procedure per variable:

1. Locate the variable in the dictionary by exact column name.
2. Copy verbatim: the sheet title, row number, and full code→meaning mapping (or unit/range statement for continuous vars).
3. Paste into the `Dict. sheet & row` + `Dict. verbatim` columns of the operationalization table.
4. If the variable is not found, OR the codebook is silent on a specific code value, file a question to the DB owner / data steward. Do NOT infer from cross-tabs, do NOT guess, do NOT proceed with that variable until a verbatim answer exists.

Empirical checks (value distributions, cross-tabs with related columns) are useful for sanity testing **after** the verbatim codebook meaning is recorded — never as a substitute for it.

Project-level binding (recommended): commit a `DICTIONARY_FIRST_POLICY.md` at the project root (or shared-config path) capturing the canonical dictionary path + escalation contact. Cross-project rule template: `~/.claude/rules/dictionary-first.md`.

**Exit gate**: `check_dictionary_citations.py` (or equivalent) PASS on the operationalization table before running Tier 1.

### Tier 1 — Canonical index lookup (no API calls)

Check `references/common_definitions.md` (shipped with skill) for the variable. Covers high-frequency constructs:

- Liver: MASLD (AASLD 2023), MetALD (AASLD 2023), MAFLD (2020), NAFLD (legacy), ALD, viral hepatitis (AASLD 2022/2024 HBV, AASLD-IDSA HCV)
- Metabolic: T2DM (ADA 2024), prediabetes (ADA 2024), metabolic syndrome (IDF 2009 / NCEP ATP III / K-NCEP), obesity/BMI (WHO Asian 2004 + WHO global), HTN (ACC/AHA 2017 + JNC-8), dyslipidemia (NCEP ATP III, 2023 AHA/ACC)
- Renal: CKD (KDIGO 2024), eGFR formulas (CKD-EPI 2021 race-free, MDRD legacy), incidental renal mass (ACR 2018 white paper, Bosniak 2019)
- Pulmonary: COPD (GOLD 2024), emphysema imaging (Fleischner 2015)
- CV: CAC scoring (Agatston 1990, MESA percentiles), CAD risk (2018 ACC/AHA cholesterol, PREVENT 2023)
- Cancer: gastric cancer H. pylori (Maastricht VI 2022), thyroid nodule (ACR TI-RADS 2017), gallbladder polyp (European 2022 joint guideline)
- Imaging incidentalomas: adrenal (ACR 2023), pancreas (ACR 2017), renal (ACR 2018), thyroid (ACR 2017)

If the variable hits Tier 1, record: guideline, year, canonical cutoff, BibTeX key. Done — no `/search-lit` call.

### Tier 2 — Targeted `/search-lit` (focused queries only)

For variables NOT in Tier 1, OR when subgroup justification is needed (Asian-specific cutoff, pediatric, young-adult, pregnancy, etc.), call `/search-lit` with **one query per variable** — not a general sweep. Query pattern:

```
"{construct} definition {cohort type} {subgroup qualifier}"
e.g., "obstructive sleep apnea prevalence Korean health screening cohort"
```

Cap: 5 queries per session. Stop early if first 1-2 papers converge on the same definition.

### Tier 3 — Verification

Before finalizing, run `/verify-refs` on the accumulated BibTeX to confirm every citation exists in PubMed/CrossRef. Ad-hoc choices (no canonical source found) must be flagged `Ad-hoc: yes` and justified with 1-2 sentences — never hidden.

## Output Template

Write to `{project_root}/variable_operationalization.md` using `templates/variable_operationalization.md`. Required structure:

1. **Header**: research question, cohort type, date, author
2. **Operationalization table** — one row per variable:

   | Variable | Role | Dict. sheet & row | Dict. verbatim | Canonical source | Definition | Cutoff | DB vars | Implementation | Ad-hoc? |

   - `Role`: exposure / outcome / covariate / eligibility
   - `Dict. sheet & row`: e.g. `5-1.복부초음파 r12` — mandatory if a DB dictionary exists
   - `Dict. verbatim`: full code→meaning string copied from the dictionary — mandatory same condition
   - `Canonical source`: BibTeX key (e.g., `@rinella2023_aasld_masld`)
   - `Definition`: one line, verbatim from guideline where possible
   - `Cutoff`: numeric + units
   - `DB vars`: exact dictionary column names used
   - `Implementation`: SQL/pandas-style pseudocode (e.g., `bmi>=25 & (b_tg>=150 | b_hdl<40)`)
   - `Ad-hoc?`: yes/no. If yes, justification below table

3. **Ad-hoc justifications** — for each yes row
4. **Mapping gaps** — variables in the protocol with no DB equivalent; list proxy / omit / request decisions
5. **References** — BibTeX block

## Non-Goals

- Statistical analysis → `/analyze-stats`
- Manuscript drafting → `/write-paper`
- Data cleaning / missingness → `/clean-data`
- Sample size → `/calc-sample-size`

## Pipeline Position

```
intake-project → design-study → search-lit → define-variables → write-protocol → analyze-stats → write-paper
                                              ^^^^^^^^^^^^^^^
```

`/orchestrate` should insert this skill between `/search-lit` and `/write-protocol` for any observational cohort or registry study.

## Anti-Hallucination

Every variable definition, cutoff, and era anchor must be grounded in a verified source — a clinical guideline, a peer-reviewed paper with DOI, or an established registry data dictionary. Never invent a phenotype threshold from the model's prior; if the source is unknown, mark the row `Ad-hoc: yes` and require user confirmation before it propagates into `/write-protocol` or `/analyze-stats`. When citing papers to justify a cutoff, verify the citation via `/search-lit` or `/verify-refs` — do not carry references from memory alone. The output table must carry explicit `source`, `year`, and `guideline_version` columns so downstream skills can re-verify.

## Failure Modes to Avoid

0. **Ad-hoc DB code interpretation** (the single most costly observational-study error). Interpreting a column value (`status == 0`, `grade == 4`) by its surface reading without consulting the codebook. Tier 0 exists specifically to prevent this. Distinguish from Failure #1: Tier 0 says "once you've picked the DB column, quote the codebook verbatim before using its values." Failure #1 says "don't pick DB columns before picking definitions from literature." Both rules co-exist.
1. **Dictionary-first framing** — starting from what columns exist, then picking a definition that matches. Always flip: definition first, then map.
2. **Cutoff drift** — using a different cutoff than the cited guideline without justification (e.g., BMI≥23 cited as WHO Asian while text says ≥25).
3. **Mixing eras** — 2020 MAFLD criteria with 2023 MASLD criteria in the same analysis. Pick one and note why.
4. **Silent ad-hoc** — introducing a novel cutoff without the `Ad-hoc: yes` flag.
5. **Sweep-style /search-lit** — running a generic lit search instead of one focused query per gap variable. Wastes tokens and buries the signal.
6. **Dose/duration structural-missingness** — operationalizing a dose/duration covariate (pack-years, cessation-years, alcohol grams/week) anchored to a categorical exposure (smoking status, alcohol use) without specifying what the *reference level* (never-smoker, never-drinker) does to the dose. A never-smoker's pack-years is a structural zero, not a missing value; conflating the two collapses the analytic sample under complete-case modeling and lets MICE fabricate a non-zero dose for the unexposed. Operationalize it explicitly — add a row with `Role = covariate` and `Implementation = "IF status == 'never' THEN dose = 0 ELSE measured_value"` — and adjust on the categorical **status** variable, reserving the continuous **dose** for an exposed-only secondary analysis. `/clean-data` (categorical-implied-zero flag) and `/analyze-stats` ("Covariate Pitfalls") enforce this downstream.
