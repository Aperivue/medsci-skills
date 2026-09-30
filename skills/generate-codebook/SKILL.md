---
name: generate-codebook
description: Use when a tabular dataset (CSV, Excel, Parquet, Stata, SAS) needs a data dictionary. Profiles every variable (type, levels, range, missingness) into codebook.md and codebook.json and flags coded values of unknown meaning as [NEEDS DICTIONARY] instead of guessing.
model: inherit
metadata:
  triggers: "generate codebook, data dictionary, codebook, profile variables, variable dictionary, describe dataset, what variables, column dictionary, build codebook"
---

# Generate Codebook Skill

Turn a raw tabular dataset into a structured, **citable** data dictionary (codebook). This is the
*generator* side of the dictionary-first workflow: it produces the artifact that `/define-variables`
and dictionary-first QC later consume. Distributions, types, and missingness are observable and the
bundled script profiles them; the **meaning** of a coded value (`fatty_liver_grade = 0`) is not
observable from the data and lives only in the authoritative data dictionary. You generate code and
review output — you do **not** invent the meaning of coded values.

## Deterministic Script

Run the bundled profiler rather than describing columns from memory:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/generate_codebook.py" data.csv --out-dir .
```

Supports `.csv/.tsv/.xlsx/.parquet/.dta/.sas7bdat`. Flags: `--max-levels N`
(categorical cutoff, default 20), `--json-only`, `--md-only`. The script is
pandas-only, runs locally, and never sends data anywhere.

## Workflow

### Step 1: Profile (deterministic)

Run `generate_codebook.py` on the dataset. It writes `codebook.json` (machine-
readable) and `codebook.md` (review table), reporting per variable: role
(id / continuous / categorical / binary / date / text), dtype, missingness,
unique count, level frequencies or quantile summary, and a `needs_dictionary` flag.

### Step 2: Review with the researcher (gate)

Read `${CLAUDE_SKILL_DIR}/references/codebook_schema.md` (the codebook.json schema, the
role-inference heuristics, the `needs_dictionary` rule) before interpreting the output. Present
`codebook.md` and walk the user through it. **Gate:** role inference is a heuristic, so the user
confirms the inferred roles (e.g., an integer-coded scale mis-read as continuous, or an id column).
Do not proceed to definition work until the user approves the role assignments.

### Step 3: Resolve [NEEDS DICTIONARY] items (gate)

For every variable flagged `needs_dictionary: true`, the level codes are
uninterpretable without the authoritative source. **Gate:** ask the user to
supply the meaning of each code from the real data dictionary (file/sheet/row),
or to confirm none exists. Fill `label`, `units`, and per-level meanings into the
codebook **only** from that source, citing file > sheet > row — never from inference. If the user
cannot supply it, leave the `[NEEDS DICTIONARY]` marker in place; do not erase it.

Example: in a cohort file, `sex` (levels `1/2`) and `fatty_liver_grade` (`0..4`) are flagged because
their levels are bare codes; `smoking_status` (`never/former/current`) is not. Never write
`sex: 1 = male` because "that is the usual coding" — if the dictionary is unavailable, the flag stays.

### Step 4: Hand off

The completed `codebook.json` becomes the input dictionary for `/define-variables`
(operationalization) and the citation source for dictionary-first QC. **Gate:**
confirm with the user that no `needs_dictionary` flags remain unresolved before
the codebook is treated as authoritative for downstream analysis.

Run `/deidentify` on the raw data before a codebook is shared externally. Cleaning or transforming
data is `/clean-data`.

## Output Format

`codebook.json` (schema in references) and `codebook.md` (review table with a
"Columns requiring dictionary lookup" section). Summarize the counts
(rows, columns, `needs_dictionary_count`) in chat; do not paste the full JSON.
