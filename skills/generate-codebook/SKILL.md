---
name: generate-codebook
description: Generate a citable data dictionary / codebook from a tabular dataset (CSV/TSV/Excel/Parquet/Stata/SAS). Profiles every variable — role, type, units placeholder, level frequencies, range/quantiles, missingness — and emits codebook.md + codebook.json. Flags coded variables whose level meanings are unknown as [NEEDS DICTIONARY] rather than guessing them, feeding /define-variables and the dictionary-first workflow.
triggers: generate codebook, data dictionary, codebook, profile variables, variable dictionary, describe dataset, what variables, column dictionary, build codebook
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Generate Codebook Skill

You help a medical researcher turn a raw tabular dataset into a structured,
**citable** data dictionary (codebook). This is the *generator* side of the
dictionary-first workflow: it produces the artifact that `/define-variables` and
dictionary-first QC later consume. You generate code and review output — you do
**not** invent the meaning of coded values.

## Communication Rules

- Communicate with the user in their preferred language.
- Variable names, codebook fields, and report output are in English.
- Medical terminology is always in English.

## Philosophy

A codebook describes *what is in the data*, not *what the codes mean*. Column
distributions, types, and missingness are observable and safe to profile. The
**meaning** of a coded value (`fatty_liver_grade = 0`) is NOT observable from the
data — it lives in the authoritative data dictionary. This skill profiles the
former deterministically and explicitly flags the latter as `[NEEDS DICTIONARY]`
so a human fills it from the source. This is the generator counterpart to the
dictionary-first rule that `/define-variables` enforces on consumption.

## Reference Files

- **Schema + role rules**: `${CLAUDE_SKILL_DIR}/references/codebook_schema.md` — the
  codebook.json schema, the role-inference heuristics, and how the output threads
  into `/define-variables` and dictionary-first QC. Read this before interpreting output.

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

Present `codebook.md` and walk the user through it. **Gate:** the user confirms
the inferred roles (e.g., an integer-coded scale mis-read as continuous, or an id
column). Do not proceed to definition work until the user approves the role
assignments.

### Step 3: Resolve [NEEDS DICTIONARY] items (gate)

For every variable flagged `needs_dictionary: true`, the level codes are
uninterpretable without the authoritative source. **Gate:** ask the user to
supply the meaning of each code from the real data dictionary (file/sheet/row),
or to confirm none exists. Fill `label`, `units`, and per-level meanings into the
codebook **only** from that source — never from inference. If the user cannot
supply it, leave the `[NEEDS DICTIONARY]` marker in place; do not erase it.

### Step 4: Hand off

The completed `codebook.json` becomes the input dictionary for `/define-variables`
(operationalization) and the citation source for dictionary-first QC. **Gate:**
confirm with the user that no `needs_dictionary` flags remain unresolved before
the codebook is treated as authoritative for downstream analysis.

## Scope Limitations

### Supported
- Tabular files: CSV, TSV, Excel, Parquet, Stata (`.dta`), SAS (`.sas7bdat`).
- Per-variable profiling, role inference, missingness, level/range summaries.

### NOT Supported
- Inventing or guessing the meaning of coded values (that is `[NEEDS DICTIONARY]`).
- Cleaning or transforming data — use `/clean-data`.
- De-identification — use `/deidentify` before sharing.
- Operationalizing exposure/outcome definitions — use `/define-variables` (this skill feeds it).

## Cross-Skill Integration

- **/define-variables** consumes `codebook.json` as its data dictionary input.
- **/clean-data** profiles + cleans; this skill produces a durable dictionary artifact instead.
- **/deidentify** should run on the raw data before a codebook is shared externally.

## Output Format

`codebook.json` (schema in references) and `codebook.md` (review table with a
"Columns requiring dictionary lookup" section). Summarize the counts
(rows, columns, `needs_dictionary_count`) in chat; do not paste the full JSON.

## Worked Example

Input `cohort.csv`:

```text
patient_id,age,sex,fatty_liver_grade,smoking_status,visit_date
1001,54,1,0,never,2023-01-15
1002,61,2,2,former,2023-02-03
```

Run:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/generate_codebook.py" cohort.csv --out-dir .
# -> {"n_rows": ..., "n_columns": 6, "needs_dictionary_count": 2, "outputs": [...]}
```

`codebook.md` (excerpt):

```text
| Variable            | Role        | Missing % | Unique | Needs dictionary |
| `patient_id`        | id          | 0.0       | N      |                  |
| `age`               | continuous  | 0.0       | ...    |                  |
| `sex`               | binary      | 0.0       | 2      | ⚠️ YES           |
| `fatty_liver_grade` | categorical | 0.0       | 5      | ⚠️ YES           |
| `smoking_status`    | categorical | 0.0       | 3      |                  |
| `visit_date`        | date        | 0.0       | ...    |                  |
```

`sex` and `fatty_liver_grade` are flagged because their levels are bare codes
(`1/2`, `0..4`). `smoking_status` is **not** flagged — its levels are already
human-readable. The reviewer then:

1. Opens the project's authoritative data dictionary.
2. Fills `sex`: `1 = male, 2 = female` and `fatty_liver_grade`: `0 = none … 4 = suspected`
   into the codebook **from that source** (citing file > sheet > row).
3. Confirms no `[NEEDS DICTIONARY]` flags remain, then hands `codebook.json` to
   `/define-variables`.

What the skill must **never** do: write `sex: 1 = male` because "that is the
usual coding." If the dictionary is unavailable, the flag stays.

## Anti-Hallucination

- Never invent a variable's label, units, or the meaning of any coded level.
- Coded categorical/binary columns with bare codes are flagged `[NEEDS DICTIONARY]`;
  the meaning is filled only from the authoritative data dictionary, then cited.
- Role inference is a heuristic — surface it for user confirmation, do not assert it as ground truth.
- The profiler reads values locally; no data is sent to any model or network.
