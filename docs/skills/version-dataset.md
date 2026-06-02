<!-- AUTO-GENERATED from skills/version-dataset/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# version-dataset

> Dataset version control for research reproducibility. Builds a deterministic content-hash manifest of a dataset (file SHA-256 + tabular schema + per-column value hashes), verifies a later copy against it to detect drift (schema change, row-count change, value changes), and diffs two manifests. Use to prove an analysis ran on the intended data, lock a dataset version, or reproducibility-lock bundled demos.

**Invoke:** `/version-dataset` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`version-dataset` activates on requests such as: version dataset, dataset version, data manifest, data hash, dataset drift, reproducibility lock, verify dataset, data provenance, did my data change, manifest.lock.

## Bundled resources

**References** (`skills/version-dataset/references/`):

- `manifest_schema.md`

**Scripts** (`skills/version-dataset/scripts/`):

- `version_dataset.py`

## Source

Canonical definition: [`skills/version-dataset/SKILL.md`](../../skills/version-dataset/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
