# Manifest Schema & Drift Categories

`version_dataset.py` produces a deterministic `manifest.json`. This documents the
structure, the drift categories `verify`/`diff` report, and the non-deterministic
artifact policy.

## manifest.json schema (schema_version 1)

```jsonc
{
  "schema_version": 1,
  "seed": 42,                          // analysis seed, user-supplied (null if none)
  "provenance": "KNHANES 2018 v1",     // user-supplied note (null if none)
  "stamp": null,                       // omitted by default; set only via --stamp
  "files": {
    "data/cohort.csv": {
      "sha256": "…",                   // byte hash of the file
      "bytes": 12345,
      "tabular": {                     // present only for CSV/TSV/Parquet/Stata/SAS/Excel
        "n_rows": 200,
        "n_cols": 9,
        "column_hashes": {"age": "…", "bmi": "…"}   // sha256 of the column's literal
                                                    // cell strings (row order)
      }
    }
  }
}
```

Determinism: no timestamp is written unless `--stamp` is passed, so the same bytes
always yield the same manifest. `--base` stores file keys relative to a directory
(portable manifests); `--ignore-cols` omits volatile columns from `column_hashes`.

## Drift categories (verify / diff)

| Category | Meaning |
|---|---|
| `CHANGED bytes: F` | A **non-tabular** file's SHA-256 differs. Tabular files are compared on logical content (below), not raw bytes, since re-save / float formatting / an `--ignore-cols` column would otherwise produce spurious byte drift. |
| `MISSING file: F` | F was in the manifest but is absent now. |
| `UNEXPECTED file: F` | F is present now but not in the manifest. |
| `ROW COUNT F: a -> b` | Tabular row count changed. |
| `ADDED column F:c` / `REMOVED column F:c` | Schema change. |
| `CHANGED column F:c` | Column c's values (or dtype) changed, even if row count is stable. |

`verify --strict` exits non-zero if any drift is found; without `--strict` it
reports and exits 0 (for advisory runs).

## Non-deterministic artifact policy

Byte-for-byte hashing is correct for data files and result tables (CSV), but
**not** for artifacts that embed timestamps or render metadata:

- **PPTX / DOCX** embed creation/modification timestamps → hash changes every build.
- **PDF / PNG figures** may embed render metadata.

Policy: manifest only the **deterministic** surface — input data files and
tabular result outputs. Do not put PPTX/DOCX/figure binaries under `verify --strict`.
For tabular files with a volatile column (e.g. an export timestamp column), use
`--ignore-cols <name>` so the rest of the table is still verified.

## Demo reproducibility (codex Improvement E)

Each bundled `demo/<name>/manifest.lock.json` fingerprints the demo's input data
and deterministic result tables. Verify a demo reproduces with:

```bash
python skills/version-dataset/scripts/version_dataset.py verify \
  --manifest demo/01_wisconsin_bc/manifest.lock.json --base demo/01_wisconsin_bc --strict
```

The locks intentionally exclude the manuscript `.docx` and `.pptx` (timestamped)
and cover the input dataset plus the `analysis/tables/*.csv` outputs.
