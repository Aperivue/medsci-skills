# Detector result convention

How a detector (`skills/*/scripts/check_*.py`, `detect_*.py`, `derive_*.py`, `verify_refs.py`)
reports its result, so that **"not checked" can never read as "no problem"**. Part 1 is enforced in
CI by `scripts/check_detector_envelopes.py --strict`. Part 2 is the target for new or modified
detectors; nothing checks it mechanically and most existing detectors do not follow it yet.

## 1. Enforced by CI

- The JSON envelope carries `"detector": "<script stem>"` (the `--out` file name cannot identify it).
- `summary.verdict` is exactly one of the three values below, unless the detector is listed in the
  gate's `GRANDFATHERED` table. That table records what each listed detector emits today, fails
  on any new value, and fails on a stale entry, so it can only shrink.

| verdict | means |
|---|---|
| `MAJOR_CANDIDATE` | at least one Major claim fired. Takes precedence over the two below. |
| `NOT_ASSESSED` | no Major claim, and the run could not check what it was asked to (no usable column, section or field was found). Never reported as `OK`. |
| `OK` | every check ran and none raised a Major claim. Minor claims may exist; they are counted in the summary, not hidden. |

Do not add synonyms (`CLEAN`, `PASS`, `FLAG`, `REVIEW`, `MAJOR`, `INCOMPLETE`, ...). Write the
verdict from string literals (`"MAJOR_CANDIDATE" if n_major else "OK"`, or a local variable
assigned literals): the gate reads source, not output, and a verdict it cannot resolve fails.

The gate does not see a verdict outside `summary`, a value chosen at run time for the wrong
reason (an `OK` written for a run that skipped a check), or scripts outside the four name
patterns. Its docstring lists these limits.

## 2. Target for new or modified detectors

**Summary counts.** `summary.n_major` and `summary.n_minor`. Most existing detectors write
`n_flag` for the Minor count; it is accepted as an existing alias, not to be copied.

**Partial coverage.** One check that could not run inside an otherwise assessed run is a claim of
its own, `<CHECK>_NOT_ASSESSED` (usually Minor), saying what was missing, not a silent skip.

**Declared inputs.** When the input is a declaration (a manifest or config the author filled in)
rather than the manuscript or data, add `"basis": "declared"` to the envelope.

**Final stdout line.**

- `OK: ...` only when every check ran and nothing fired.
- `No Major issue: N Minor ...` when only Minor claims fired (including `*_NOT_ASSESSED`).
- `NOT ASSESSED: <what was missing and how to supply it>` when nothing could be checked.
- `MAJOR candidate: ...` otherwise.
- Declared inputs put `(as declared)` right after the label: `OK (as declared): ...`,
  `No Major issue (as declared): N Minor ...`.

Existing detectors still print `MINOR flag: N ...`, `MINOR: N ...`, `OK: ... (N minor flag(s))`,
or a plain `OK:` while Minor claims exist. Move them to the forms above when you next touch them.

**Exit codes.**

| code | when |
|---|---|
| 0 | run completed (report-only, or `--strict` with no Major claim) |
| 1 | `--strict` and at least one Major claim |
| 2 | input or usage error (missing file, bad flag); also `--strict` with `NOT_ASSESSED` |

`NOT_ASSESSED` under `--strict` exits 2 because the input did not allow an assessment, as in
`meta-analysis/scripts/check_exclusion_code_validity.py`. Without `--strict` it exits 0 and the
verdict carries it; Major takes precedence (exit 1). Older gates outside the `check_*.py` pattern
use other conventions (`meta-analysis/scripts/prisma_5way_consistency.py` exits 3 under
`--strict`; `make-figures/scripts/_strobe_cascade.py` prints a `NOT_ASSESSED:` line per unevaluated link
and still exits 0 when the evaluated links close). New
detectors follow exit 2.
