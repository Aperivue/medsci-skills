# Detector result convention

How a detector (`skills/*/scripts/check_*.py`, `detect_*.py`, `derive_*.py`, `verify_refs.py`)
reports its result, so that **"not checked" can never read as "no problem"**. New detectors follow
it; `scripts/check_detector_envelopes.py --strict` enforces the JSON part in CI. Detectors that
predate it are listed in that script's `GRANDFATHERED` table with what they emit today; the table
may only shrink.

## JSON envelope

```json
{"detector": "check_example", "claims": [...],
 "summary": {"n_claims": 2, "n_major": 0, "n_minor": 2, "verdict": "OK"}}
```

- `"detector"` is the script's own stem (the file name passed to `--out` cannot identify it).
- `summary.verdict` is exactly one of:

| verdict | means |
|---|---|
| `MAJOR_CANDIDATE` | at least one Major claim fired. Takes precedence over the two below. |
| `NOT_ASSESSED` | no Major claim, and the run could not check what it was asked to (no usable column, section or field was found). Never reported as `OK`. |
| `OK` | every check ran and none raised a Major claim. Minor claims may exist: they are counted in `summary.n_minor`, not hidden in the verdict. |

Do not add synonyms (`CLEAN`, `PASS`, `FLAG`, `REVIEW`, `MAJOR`, `INCOMPLETE`, ...). A consumer
reading many qc files should need three values, not a dictionary per detector.

- Write the verdict from string literals (`"MAJOR_CANDIDATE" if n_major else "OK"`, or a local
  variable assigned literals). The gate reads source, not output; a verdict it cannot resolve
  fails rather than counting as conforming.
- **One check that could not run** inside an otherwise assessed run is a claim of its own, named
  `<CHECK>_NOT_ASSESSED` (usually Minor), saying what was missing — not a silent skip.
- **Declared inputs** (a manifest, a config the author filled in, rather than the manuscript or
  data itself) add `"basis": "declared"` to the envelope: the result is only as true as the
  declaration.

## Exit codes

| code | when |
|---|---|
| 0 | run completed (report-only, or `--strict` with no Major claim) |
| 1 | `--strict` and `summary.n_major > 0` |
| 2 | input or usage error (missing file, bad flag); also `--strict` with `NOT_ASSESSED` |

`NOT_ASSESSED` under `--strict` exits 2, like an input error, because the input did not allow an
assessment (`meta-analysis/scripts/check_exclusion_code_validity.py`). Without `--strict` it
exits 0 and the verdict carries it. A run that is both Major and partly unassessed exits 1.

## Final stdout line

- `OK: ...` only when every check ran and nothing fired.
- `No Major issue: N Minor` when only Minor claims fired (they include `*_NOT_ASSESSED`).
- `NOT ASSESSED: <what was missing and how to supply it>` when nothing could be checked.
- `MAJOR candidate: ...` otherwise.
- Declared inputs append `(as declared)` to the line.

## What the gate does not cover

It checks the `"detector"` key and `summary.verdict` statically. It does not run detectors, so
the stdout line, the exit codes and `"basis"` above are convention, kept by review and by each
detector's own tests and `<feature>_challenge/verify.sh`.
