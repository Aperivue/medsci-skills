---
name: version-dataset
description: Use when you must prove an analysis ran on the intended data or lock a dataset version. Builds a deterministic content-hash manifest (file SHA-256, schema, per-column value hashes), verifies later copies against it for drift, and diffs two manifests.
metadata:
  triggers: "version dataset, dataset version, data manifest, data hash, dataset drift, reproducibility lock, verify dataset, data provenance, did my data change, manifest.lock"
---

# Version Dataset Skill

An analysis must run on the data it claims to, with a fixed seed. This skill makes drift between
runs loud instead of silent: it records a deterministic fingerprint (file SHA-256 plus, for
tabular files, schema and per-column value hashes; no timestamp unless explicitly passed) so a
later run can *prove* the inputs are unchanged. It never alters data, and manifests hold hashes,
not the data itself. Provenance notes are in English.

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
The provenance note is the user's text; never invent it.

### Step 2: Verify before each run (gate)

Before re-running an analysis (or in CI), `verify --strict`. Never say a dataset is unchanged
without running `verify`. **Gate:** if drift is reported (`MANIFEST_DRIFT`, exit 1), stop and
show the user the drift report exactly as computed — never downplay a changed column hash. Do not
proceed on changed data without their explicit acknowledgement and a re-lock. Silent re-run on
drifted data is the failure this skill exists to prevent.

Read `${CLAUDE_SKILL_DIR}/references/manifest_schema.md` before interpreting drift — it defines
each drift category. A CSV/TSV file is compared on its logical content (schema + per-column
value hashes), not raw bytes, so re-quoting, reordering columns, or an `--ignore-cols` volatile
column does not trip a false drift. Binary tabular files (Parquet/Stata/SAS/Excel) are also
checked at the byte level, since labels, metadata and other sheets are not in the column hashes.

### Step 3: Diff across versions

When a dataset is intentionally updated, `diff` the old and new manifests and
present the change set (added/removed/changed columns, row-count delta) so the
user can record what changed and re-lock. **Gate:** the user approves the new
version before it replaces the locked one.

## Non-Deterministic Artifacts

Do not put PPTX/DOCX or figure binaries under strict byte verification — they embed timestamps
or render metadata and change on every build. Manifest only the deterministic inputs and tabular
outputs (data files, result CSVs), or use `--ignore-cols` for volatile columns; the policy is in
`references/manifest_schema.md`. Each bundled `demo/*/` carries a `manifest.lock.json` (input data
+ deterministic result tables) that `verify --strict` checks; the reference gives the demo
command.

## Scope

- Run `/deidentify` before a manifest is shared: example values are not stored, but provenance
  notes may carry context.
- Cleaning, profiling or de-identifying the data → `/clean-data`, `/generate-codebook`,
  `/deidentify`. `/generate-codebook` documents *what* is in the data; this skill locks *which
  version*.
