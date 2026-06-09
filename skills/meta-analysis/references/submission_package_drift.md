# Submission Package Drift Control

**Applies to**: situations with multiple coexisting journal targets (academic radiology / DIR / BJR / MDPI Diagnostics, etc.).

## The problem

When 4~5 per-journal `SUBMISSION/{journal}/` folders coexist and each holds the full body/supplement/figures, there is a drift risk after rebuilds: it becomes unclear which folder is the master, and a typo fixed in only one folder gets re-propagated to the other targets.

## Rules

### SPD-1. Single master + build script
- **Rule**: There is exactly one `7_Manuscript/` master. Per-journal conversion is handled by `SUBMISSION/_build.sh`.
- **Build output**: `SUBMISSION/{journal}/{manuscript.docx, supplement.docx, figures/, tables/}` — these are **build artifacts; do not edit by hand**.

### SPD-2. `DO_NOT_EDIT_HERE.md` gate
- **Rule**: Place a `DO_NOT_EDIT_HERE.md` file in each per-journal folder. When this file is present, the body/supplement/figure in that directory must not be edited. Allowed exception files:
  - `cover_letter.docx`
  - `title_page.docx`
  - `highlights.txt`
  - `checklist.md` (journal-specific reporting checklist)
  - `response_to_reviewers.docx` (during revision)
- These exception files are needed per-journal, so direct editing is allowed.

### SPD-3. Record build time in `MANIFEST.md`
- **Rule**: Four lines in each `SUBMISSION/{journal}/MANIFEST.md`:
  1. `_build.sh` run timestamp
  2. Source: master manuscript commit / `v{N}`
  3. List of files allowed to be edited in the journal folder
  4. Confirmation that all `[VERIFY-CSV]` tags were removed (timestamp of `rg` → 0 hits)

### SPD-4. Handling re-targeting after rejection
- **Same content → different journal**: `_build.sh --journal {new}` for a new folder. No Zenodo DOI re-issue needed. Move the old journal folder to `_archive/`.
- **After revision, same journal**: `_build.sh --journal {same} --revision {n}`. Build the Response matrix + the changed manuscript together.
- **Major revision → different journal**: new folder + new Zenodo version (content changed).

## Templates

### `_build.sh` base structure
```bash
#!/bin/bash
# SUBMISSION/_build.sh
# Usage: ./_build.sh --journal {academic_radiology|dir|bjr|mdpi_diagnostics|...} [--revision N]

set -euo pipefail
JOURNAL="$1"
# Per-journal config: word limit, figure limit, reference style, supplement rules
source "configs/${JOURNAL}.sh"

# Build manuscript
pandoc "../7_Manuscript/master.md" \
    --reference-doc "configs/${JOURNAL}_template.docx" \
    --citeproc --csl "configs/${JOURNAL}.csl" \
    -o "${JOURNAL}/manuscript.docx"

# Build supplement
# ... figures, tables, DO_NOT_EDIT_HERE.md touch, MANIFEST.md update
```

### `DO_NOT_EDIT_HERE.md` contents
```
This directory holds build artifacts from SUBMISSION/_build.sh.

Do not edit the body/supplement/figures here. The master is /7_Manuscript/.

Files allowed to be edited:
- cover_letter.docx
- title_page.docx
- highlights.txt
- checklist.md
- response_to_reviewers.docx (during revision)
```
