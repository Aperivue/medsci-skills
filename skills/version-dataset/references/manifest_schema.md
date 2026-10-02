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
        "column_hashes": {"age": "…", "bmi": "…"},  // sha256 of the column's literal
                                                    // cell strings (row order) joined by
                                                    // \x1e; only in a column where some
                                                    // cell itself holds \x1e, every \x1e
                                                    // or \x1b inside a cell is escaped
                                                    // with \x1b
        "escaped_cols": ["note"],      // only when some column was hashed in the
                                       // escaped form; absent = all columns use the
                                       // plain join, as every older manifest does
        "header": ["a", "a"],          // CSV/TSV only, and only when the raw header
                                       // differs from the parsed names (duplicates);
                                       // absent = not recorded, so not compared
        "ignored_cols": ["ts"]         // binary formats only, and only when an
                                       // --ignore-cols column is present in the file
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
| `CHANGED bytes: F` | A **non-tabular** file's SHA-256 differs. CSV/TSV files are compared on logical content (below), not raw bytes, so re-quoting, line endings or an `--ignore-cols` column do not produce spurious byte drift. |
| `CHANGED bytes: F (column hashes match; …)` | A **binary tabular** file (Parquet/Stata/SAS/Excel) has identical column hashes but a different SHA-256. These formats hold content the column hashes do not cover (variable labels, other Excel sheets, file metadata), so the byte change is reported, not cleared. A binary re-save also trips it. Not emitted when an `--ignore-cols` column is present in the file (`ignored_cols`), since that column's changes alter the bytes; label/metadata changes in such a file are then not detected. |
| `CHANGED header F: [...] -> [...]` | The raw CSV/TSV header changed in a way the parsed column names hide (e.g. duplicate `a,a` vs `a,a.1`, which pandas reads identically). Checked only when the lock recorded a header; a lock built before headers were recorded is not compared on it. |
| `MISSING file: F` | F was in the manifest but is absent now. |
| `UNEXPECTED file: F` | F is present now but not in the manifest. |
| `ROW COUNT F: a -> b` | Tabular row count changed. |
| `ADDED column F:c` / `REMOVED column F:c` | Schema change. |
| `CHANGED column F:c` | Column c's values (or dtype) changed, even if row count is stable. `verify` checks a column that the lock does not list in `escaped_cols` (this includes every lock written before escaping existed) with the plain join, so such a lock still verifies an unchanged file clean; in it, a `\x1e` moved across a cell boundary is not detected until the file is re-locked. `diff` has no file to re-hash, so comparing an older manifest with a newer one of the same data reports a column that holds `\x1e` in a cell as changed. |

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
