# Codebook Schema & Role Inference

`generate_codebook.py` emits `codebook.json` (machine-readable) and `codebook.md`
(human review). This file documents the JSON schema, the role-inference rules,
and how the output threads into downstream skills.

## codebook.json schema (schema_version 1)

```jsonc
{
  "schema_version": 1,
  "source": "path/to/data.csv",
  "n_rows": 200,
  "n_columns": 9,
  "needs_dictionary_count": 2,
  "columns": [
    {
      "name": "fatty_liver_grade",
      "role": "categorical",          // id | continuous | categorical | binary | date | text
      "dtype": "int64",
      "n": 200,
      "n_missing": 0,
      "pct_missing": 0.0,
      "n_unique": 5,
      "label": null,                   // filled by researcher from the authoritative dictionary
      "units": null,                   // filled by researcher
      "needs_dictionary": true,        // true => level meanings are unknown; do NOT guess
      "notes": ["[NEEDS DICTIONARY] level codes are uninterpretable ..."],
      "levels": [{"value": 0, "count": 41}, {"value": 1, "count": 39}],  // categorical/binary
      "stats": {"min": 0, "q1": 1, "median": 2, "q3": 3, "max": 4},      // continuous/date
      "examples": ["0", "2", "1"]
    }
  ]
}
```

`label`, `units`, and per-level meanings are intentionally left `null` / unlabelled.
They are filled **only** from the authoritative data dictionary, never inferred.

## Role inference (heuristic — confirm with the user)

Decided in this order; dtype and column name dominate so that continuous
measurements are never misread as identifiers on small datasets:

1. **date** — datetime dtype, or >80% of a sample parses as dates.
2. **binary** — exactly 2 distinct non-null values.
3. **numeric dtype:**
   - **id** — integer-valued, id-like name (`*_id`, `uid`, `mrn`, `subject`, `patient`, `record`, `accession`), and unique count > `--max-levels`.
   - **categorical** — integer-valued and unique count ≤ `--max-levels` (coded scale).
   - **continuous** — otherwise (floats, or many distinct integers).
4. **object/string:**
   - **id** — id-like name with high cardinality, or all-unique on ≥50 rows.
   - **categorical** — unique count ≤ `--max-levels`.
   - **text** — otherwise.

`--max-levels` (default 20) is the categorical cutoff. Raise it for scales with
many levels; lower it to force more columns to `continuous`/`text`.

## needs_dictionary flag

A categorical/binary column is flagged `needs_dictionary: true` when its levels
are **bare codes** — integers, or short tokens like `Y`/`N`/`M`/`U`/`NA` — i.e.,
uninterpretable without the source dictionary. A column whose levels are already
human-readable (`never` / `former` / `current`) is **not** flagged. The flag is a
prompt for the researcher to fill meanings from the authoritative dictionary; it
is never resolved by guessing.

## Downstream integration

- **/define-variables** takes `codebook.json` as its data-dictionary input and
  operationalizes exposure/outcome/covariate definitions on top of it. Unresolved
  `needs_dictionary` flags should be cleared first.
- **dictionary-first QC** cites the codebook (file > variable) as the provenance
  for a coded value's meaning. The codebook is the artifact that citation points at.
- **/clean-data** and **/deidentify** operate on the raw data; run `/deidentify`
  before a codebook (which contains example values) is shared externally.
