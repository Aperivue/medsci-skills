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

Map each exposure, outcome, covariate, and eligibility variable to a canonical guideline/consensus
definition, cross-check it against prior operationalizations in comparable cohorts, then map it to
the available DB variables. Call after `/design-study` (and `/search-lit`), before
`/write-protocol`.

## Inputs

1. **Research question** (one sentence)
2. **Candidate variables** — exposure, outcome, key covariates, eligibility filters
3. **Data dictionary path** (xlsx / csv / markdown) OR explicit list of available DB columns
4. **Cohort type** (e.g., health-screening, NHANES-like, claims, registry) — informs which prior-art cohort to compare against

Missing inputs → ask once, then proceed.

## 4-Tier Pipeline (DB codebook + token-efficient literature)

### Tier 0 — DB codebook lookup (mandatory for DB-backed observational studies)

**Trigger**: project has a `project.yaml::db.dictionary_path` field pointing to a machine-readable codebook (xlsx/csv/markdown), OR the user supplied a dictionary path in inputs. If neither, skip to Tier 1.

For every candidate DB variable — **before** touching literature — open the dictionary and record, verbatim, the sheet name, row number, and code→meaning mapping. This prevents the most common observational-study error: assuming a column code (`status == 0`, `grade == 4`) means what it intuitively reads like, when the codebook says otherwise.

Per variable:

1. Locate the variable in the dictionary by exact column name.
2. Copy verbatim: the sheet title, row number, and full code→meaning mapping (or unit/range statement for continuous vars).
3. Paste into the `Dict. sheet & row` + `Dict. verbatim` columns of the operationalization table.
4. If the variable is not found, OR the codebook is silent on a specific code value, file a question to the DB owner / data steward. Do NOT infer from cross-tabs, do NOT guess, do NOT proceed with that variable until a verbatim answer exists.

Empirical checks (value distributions, cross-tabs with related columns) are useful for sanity testing **after** the verbatim codebook meaning is recorded — never as a substitute for it.

Recommend committing a `DICTIONARY_FIRST_POLICY.md` at the project root (or shared-config path) with the canonical dictionary path and the escalation contact.

**Exit gate**: before Tier 1, cross-check every row's `Dict. sheet & row` and `Dict. verbatim` against the source dictionary; no DB-backed row may be left blank.

### Tier 1 — Canonical index lookup (no API calls)

Look the variable up in `references/common_definitions.md` (hepatology, metabolic/endocrine, renal, pulmonary, cardiovascular, oncology/imaging incidentalomas, alcohol exposure). On a hit, record the guideline, year, canonical cutoff, and BibTeX key. Done — no `/search-lit` call.

### Tier 2 — Targeted `/search-lit` (focused queries only)

For variables NOT in Tier 1, OR when subgroup justification is needed (Asian-specific cutoff, pediatric, young-adult, pregnancy, etc.), call `/search-lit` with **one query per variable** — never a general sweep, which buries the signal. Query pattern:

```
"{construct} definition {cohort type} {subgroup qualifier}"
e.g., "obstructive sleep apnea prevalence Korean health screening cohort"
```

Cap: 5 queries per session. Stop early if the first 1-2 papers converge on the same definition.

### Tier 3 — Verification

Every definition, cutoff, and era anchor must come from a verified source — a clinical guideline, a peer-reviewed paper with DOI, or an established registry data dictionary. Never take a phenotype threshold from the model's prior or a reference from memory. Before finalizing, run `/verify-refs` on the accumulated BibTeX to confirm every citation exists in PubMed/CrossRef. A choice with no canonical source is flagged `Ad-hoc: yes`, justified in 1-2 sentences, and confirmed by the user before it propagates into `/write-protocol` or `/analyze-stats`.

## Output Template

Write `{project_root}/variable_operationalization.md` (or the path the user specifies) from `templates/variable_operationalization.md`. Required structure:

1. **Header**: research question, cohort type, date, author
2. **Operationalization table** — one row per variable:

   | Variable | Role | Dict. sheet & row | Dict. verbatim | Canonical source | Definition | Cutoff | DB vars | Implementation | Ad-hoc? |

   - `Role`: exposure / outcome / covariate / eligibility
   - `Dict. sheet & row`: e.g. `5-1.복부초음파 r12` — mandatory if a DB dictionary exists
   - `Dict. verbatim`: full code→meaning string copied from the dictionary — mandatory under the same condition
   - `Canonical source`: BibTeX key (e.g., `@rinella2023_aasld_masld`), so downstream skills can re-verify
   - `Definition`: one line, verbatim from the guideline where possible
   - `Cutoff`: numeric + units
   - `DB vars`: exact dictionary column names used
   - `Implementation`: SQL/pandas-style pseudocode (e.g., `bmi>=25 & (b_tg>=150 | b_hdl<40)`)
   - `Ad-hoc?`: yes/no. If yes, justification below the table

3. **Ad-hoc justifications** — for each yes row
4. **Mapping gaps** — variables in the protocol with no DB equivalent; list proxy / omit / request decisions
5. **References** — BibTeX block

Out of scope: statistical analysis → `/analyze-stats`; manuscript drafting → `/write-paper`; data cleaning / missingness → `/clean-data`; sample size → `/calc-sample-size`.

## Failure Modes to Avoid

1. **Column-first framing** — starting from what columns exist, then picking a definition that matches. Always flip: definition first, then map. Tier 0 still applies once a column is picked: quote its codebook entry verbatim before using its values.
2. **Cutoff drift** — using a different cutoff than the cited guideline without justification (e.g., BMI≥23 cited as WHO Asian while text says ≥25).
3. **Mixing eras** — 2020 MAFLD criteria with 2023 MASLD criteria in the same analysis. Pick one and note why.
4. **Dose/duration structural-missingness** — operationalizing a dose/duration covariate (pack-years, cessation-years, alcohol grams/week) anchored to a categorical exposure (smoking status, alcohol use) without specifying what the *reference level* (never-smoker, never-drinker) does to the dose. A never-smoker's pack-years is a structural zero, not a missing value; conflating the two collapses the analytic sample under complete-case modeling and lets MICE fabricate a non-zero dose for the unexposed. Operationalize it explicitly — add a row with `Role = covariate` and `Implementation = "IF status == 'never' THEN dose = 0 ELSE measured_value"` — and adjust on the categorical **status** variable, reserving the continuous **dose** for an exposed-only secondary analysis. `/clean-data` (categorical-implied-zero flag) and `/analyze-stats` ("Covariate Pitfalls") enforce this downstream.
