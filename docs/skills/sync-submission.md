<!-- AUTO-GENERATED from skills/sync-submission/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# sync-submission

> Audit SSOT-to-submission drift and create journal submission manifests from canonical manuscript artifacts.

**Invoke:** `/sync-submission` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`sync-submission` activates on requests such as: sync submission, build submission, submission drift, SSOT sync, journal package, retarget journal, freeze submission.

## Quality Card

**Purpose** — Audit SSOT-to-submission drift and build journal submission manifests from canonical manuscript artifacts.

**Safety boundaries**

- Never silently edits the canonical manuscript; a drifted submission is not frozen until reconciled.
- Submission packages are derived from canonical sources, not hand-assembled.

**Known limitations**

- Detects drift it is configured to scan (counts, cover-letter fields, scope); portal free-text fields still need a human check.
- A clean audit is necessary, not sufficient, for acceptance.
- Building a marked (tracked-changes) manuscript drives Microsoft Word and therefore needs macOS + Word; the round-trip verification of a marked file is portable and runs anywhere.

**Validation**

- `python3 scripts/sync_submission.py`
- `python3 scripts/cross_document_n_check.py`
- `bash tests/test_marked_manuscript.sh`
- `bash tests/test_wordcount_cap.sh`
- `bash tests/test_assemble_supplement.sh`
- `bash tests/test_disclosure_availability.sh`
- `bash scripts/check_portal_field_residue_challenge/verify.sh  # deterministic, network-free`

**Evidence** — `bundled_script`

## Bundled resources

**References** (`skills/sync-submission/references/`):

- `journal_availability_policy.json`

**Scripts** (`skills/sync-submission/scripts/`):

- `_yaml_frontmatter.py`
- `assemble_supplement.py`
- `author_registry_example.yaml`
- `blind_sweep.py`
- `build_marked_manuscript.py`
- `check_asset_anonymization.py`
- `check_checklist_dump_leak.py`
- `check_cross_artifact_stale.py`
- `check_disclosure_availability.py`
- `check_marked_manuscript.py`
- `check_portal_field_residue.py`
- `check_portal_field_residue_challenge/` (6 files)
- `check_wordcount_cap.py`
- `cover_letter_drift_check.py`
- `cross_document_n_check.py`
- `detect_copy_divergence.py`
- `figure_portal_readiness_challenge/` (2 files)
- `figure_portal_readiness_check.py`
- `preflight_gate.py`
- `scope_drift_check.py`
- `sync_submission.py`

## Source

Canonical definition: [`skills/sync-submission/SKILL.md`](../../skills/sync-submission/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
