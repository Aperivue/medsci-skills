---
name: version-dataset
description: Dataset version control for research reproducibility. Builds a deterministic content-hash manifest of a dataset (file SHA-256 + tabular schema + per-column value hashes), verifies a later copy against it to detect drift (schema change, row-count change, value changes), and diffs two manifests. Use to prove an analysis ran on the intended data, lock a dataset version, or reproducibility-lock bundled demos.
triggers: version dataset, dataset version, data manifest, data hash, dataset drift, reproducibility lock, verify dataset, data provenance, did my data change, manifest.lock
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Version Dataset Skill

You help a medical researcher put a dataset under version control: fingerprint it,
detect when it changes, and lock a reproducible version. This guards the
data-integrity rule — an analysis must run on the data it claims to, with a fixed
seed — by making any drift between runs loud instead of silent.

## Communication Rules

- Communicate with the user in their preferred language.
- Manifest fields, drift reports, and provenance notes are in English.

## Philosophy

A dataset is an input to a result; if it changes silently, every downstream
number is suspect. This skill records a deterministic fingerprint (file SHA-256 +,
for tabular files, schema and per-column value hashes) so a later run can *prove*
the inputs are unchanged. It does not alter data, and it records nothing
non-deterministic (no timestamps unless explicitly passed), so the same data
always yields the same manifest.

## Reference Files

- **Manifest schema + workflow**: `${CLAUDE_SKILL_DIR}/references/manifest_schema.md` —
  the manifest.json structure, what each drift category means, and the non-
  deterministic-artifact policy (PPTX/DOCX timestamps). Read before interpreting drift.

## Deterministic Script

```bash
# Build a manifest (record the analysis seed + provenance)
python "${CLAUDE_SKILL_DIR}/scripts/version_dataset.py" manifest data.csv \
  --out manifest.json --seed 42 --provenance "KNHANES 2018 extract v1"

# Verify a later copy against it (CI / pre-analysis gate)
python "${CLAUDE_SKILL_DIR}/scripts/version_dataset.py" verify --manifest manifest.json --strict

# Compare two manifests (what changed between versions)
python "${CLAUDE_SKILL_DIR}/scripts/version_dataset.py" diff --old v1.json --new v2.json
```

File hashing is stdlib-only; tabular schema/column hashing uses pandas when present.
`--ignore-cols` excludes volatile columns; `--base` makes manifest keys relative.

## Workflow

### Step 1: Lock the version (gate)

Build the manifest at the moment the dataset is frozen for analysis. **Gate:**
confirm with the user the seed and provenance note are correct before locking —
the manifest is the record they will cite as "this is the data the results came from."

### Step 2: Verify before each run (gate)

Before re-running an analysis (or in CI), `verify --strict`. **Gate:** if drift is
reported, stop and show the user the drift report; do not proceed on changed data
without their explicit acknowledgement and a re-lock. Silent re-run on drifted data
is the failure this skill exists to prevent.

### Step 3: Diff across versions

When a dataset is intentionally updated, `diff` the old and new manifests and
present the change set (added/removed/changed columns, row-count delta) so the
user can record what changed and re-lock. **Gate:** the user approves the new
version before it replaces the locked one.

## Non-Deterministic Artifacts

Some outputs (PPTX/DOCX with embedded timestamps, figures with render metadata)
change byte-for-byte on every build even when the analysis is identical. Do not
put these under strict byte verification — manifest only the deterministic inputs
and tabular outputs (data files, result CSVs), or use `--ignore-cols` for volatile
columns. See references for the policy.

## Scope Limitations

### Supported
- Content-hash manifest of any file; schema + per-column hashes for tabular files
  (CSV/TSV/Parquet/Stata/SAS/Excel).
- Drift verification and manifest-to-manifest diff.

### NOT Supported
- Storing or transmitting the data itself (manifests hold hashes, not contents).
- Cleaning, profiling, or de-identifying — use `/clean-data`, `/generate-codebook`, `/deidentify`.
- Full pipeline-output reproducibility for non-deterministic binaries (see above).

## Cross-Skill Integration

- **/generate-codebook** documents *what* is in the data; version-dataset locks *which version*.
- **/deidentify** should run before a manifest is shared (example values are not stored, but provenance notes may carry context).
- Demo reproducibility: each bundled `demo/*/` carries a `manifest.lock.json` (input data + deterministic result tables) that `verify --strict` checks.

## Worked Example

Lock a freshly-frozen extract:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/version_dataset.py" manifest cohort.csv \
  --out manifest.json --seed 42 --provenance "KNHANES 2018 extract, frozen 2026-05"
# -> {"files": 1, "out": "manifest.json"}
```

Before re-running the analysis next month:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/version_dataset.py" verify --manifest manifest.json --strict
# OK: 1 file(s) match the manifest.   (exit 0 — safe to run)
```

If someone silently re-exported the data with three extra rows:

```text
========================================= 
 Dataset Manifest Verify
=========================================
DRIFT (3):
  ROW COUNT cohort.csv: 3457 -> 3460
  CHANGED column cohort.csv:bmi
  CHANGED column cohort.csv:hba1c
MANIFEST_DRIFT: dataset differs from manifest.   (exit 1 — STOP)
```

The analysis does **not** proceed: the result the manuscript will cite would no
longer match the locked data. The researcher reviews the drift, decides whether
the change is intended, and only then re-locks (`manifest` again) and records the
new provenance. A tabular file is compared on its **logical content** (schema +
per-column value hashes), not raw bytes — re-saving the same data, reordering
columns, or an `--ignore-cols` volatile timestamp column does not trip a false drift.

## Anti-Hallucination

- Never claim a dataset is unchanged without running `verify`.
- Manifests record only observed hashes/schema; no provenance is invented — the
  `provenance` note is user-supplied text.
- Report drift exactly as computed; do not downplay a changed column hash.
