# Skill Script Maintenance — taxonomy & wiring rules

Every `.py`/`.sh` under `skills/*/scripts/` and `skills/*/tests/` falls into one of
four categories. Misclassifying one is how a detector goes "dormant" (counted in the
catalog but never invoked) or how a regression test gives false coverage (exists but
never runs in CI). This file is the source of truth for which is which and what each
category must satisfy.

## 1. Counted analysis-integrity detector

A script whose **filename** matches the catalog glob — `check_*.py`, `detect_*.py`,
`derive_*.py`, or `verify_refs.py` — under `skills/*/scripts/`. The glob is the SSOT:
`scripts/gen_detectors_catalog_json.py` and `scripts/validate_catalog_consistency.py`
both count these and they must agree with `metadata/catalog_counts.json`
(`integrity_detectors`).

A counted detector MUST:
- be registered in `scripts/gen_detectors_catalog_json.py` `FAMILY_BY_ID` (an unmapped id
  fails generation), and bump `metadata/catalog_counts.json` + `MEDSCI_AUDIT.md` when added;
- be **invoked** from its skill's `SKILL.md` (a named workflow step) — otherwise it is
  dormant (counted but never run on a real manuscript);
- have a **CI-wired** regression test (a `tests/test_*.sh` step in
  `.github/workflows/validate.yml`) with PII-free synthetic fixtures.

> Naming trap: a reusable helper must NOT be named `check_*`/`detect_*` or it inflates the
> detector count. Prefix helpers with `_` (see category 2).

## 2. Helper / library module

Shared logic imported by other scripts in the **same** skill (skills are self-contained —
no cross-skill imports). Name it with a leading underscore (`_yaml_frontmatter.py`) or a
plain verb (`fill_journal_abbrev.py`) so the detector glob never counts it. Helpers do not
need their own SKILL.md step, but if a user runs them directly they should be listed in the
skill's tool table (e.g. `manage-refs` documents `fill_journal_abbrev.py`).

## 3. Run-once authoring tool

A generator a maintainer runs by hand to (re)build a committed asset — NOT invoked at skill
invocation. These are intentionally not wired into any SKILL.md step. Keep them; document
their purpose in their own docstring. Current run-once tools:

- `skills/make-figures/scripts/build_jacc_template.py` — rebuilds the committed JACC Central
  Illustration PPTX template (`references/visual_abstract_templates/jacc_central_illustration.pptx`).
- `skills/make-figures/scripts/extract_exemplar_from_pdf.py` — extracts a figure region from a
  PDF page to grow the make-figures Critic-Loop exemplar reference set.

## 4. Test fixture / regression test

Lives under `skills/<skill>/tests/`. A `test_*.sh`/`test_*.py` is only real coverage if it
is wired into `.github/workflows/validate.yml` as a `run:` step. **Adding a test file is not
enough** — if it is not listed in `validate.yml` it never runs and gives false confidence.
When you add a detector and its test in the same PR, add the `validate.yml` step in that PR.

## When you touch a skill script — checklist

1. New `check_*`/`detect_*` detector → register in `gen_detectors_catalog_json.py`
   (`FAMILY_BY_ID`) + bump `catalog_counts.json` + `MEDSCI_AUDIT.md` + wire into the skill's
   `SKILL.md` + add a CI-wired test. Then run all three generators in `--check` mode.
2. New helper → underscore/plain name (never `check_*`), import only within the same skill.
3. New asset/fixture file → re-run `python3 scripts/gen_distribution_manifest.py` (it tracks
   payload files and hashes; tests are excluded from the distributed payload but the manifest
   `--check` still gates on edited payload scripts).
4. New/edited test → add its `run:` step to `.github/workflows/validate.yml`.

Run the full local CI-mirror before pushing (see the repo `CONTRIBUTING.md` / `validate.yml`
gates): `validate_skills.sh`, the three `gen_*.py --check`, `validate_catalog_consistency.py`,
`check_version_consistency.py`, `gen_skill_docs.py --check`, `check_locale_inventory.py`,
`validate_routing_assets.py --strict`, and the installer tests.
