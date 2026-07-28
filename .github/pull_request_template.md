<!--
Thanks for contributing to MedSci Skills. Keep PRs small and reviewable.
See CONTRIBUTING.md for the full workflow and PII/publication hygiene rules.

ADDING ONE FILE? (a journal profile, a CSL style, a reporting checklist, a
de-identification locale pack, a figure exemplar, a README translation)
Tick the first box under "Type of change" and stop. The rest of this template is
for larger changes. CI runs for you and a maintainer handles the bookkeeping
(catalog counts, changelog) in review — see CONTRIBUTING.md.
-->

## Summary

<!-- What does this PR change, and why? -->

## Type of change

- [ ] **One-file contribution** (journal profile, CSL, checklist, locale pack, figure exemplar, translation, typo) — **stop here.** A maintainer handles the bookkeeping below.
- [ ] New skill
- [ ] Fix or improvement to an existing skill
- [ ] Deterministic script / validator
- [ ] Documentation
- [ ] Other (describe above)

## Validators

<!--
CI runs every gate for you. To run them locally, `python3 scripts/run_ci_mirror.py`
executes the whole `validate` job in order — it parses the workflow, so it cannot
drift from CI. A red CI on a first contribution is normal and is NOT yours to fix
alone: say so in the PR and a maintainer will pick it up.
-->

- [ ] `bash scripts/validate_skills.sh`
- [ ] `python3 scripts/validate_skill_contracts.py`
- [ ] `python3 scripts/validate_catalog_consistency.py`
- [ ] `python3 scripts/validate_routing_assets.py --strict`

## Catalog consistency

- [ ] If this PR **adds or removes a skill, reporting checklist, or journal profile**, I updated `metadata/catalog_counts.json` to match the new disk count, and `validate_catalog_consistency.py` passes. (Counts are a single source of truth — the README badge, tagline, and skill docs must all agree.)
- [ ] If this PR **adds, removes, or renames a skill** (or changes a skill's `description`/`owner_domain`), I re-ran `python3 scripts/gen_skills_catalog_json.py` and committed the updated `metadata/skills_catalog.json` (the machine-readable catalog the public storefront consumes). A new `owner_domain` must be mapped in `gen_skills_catalog_json.py` or generation fails.

## PII and publication hygiene

- [ ] No private project identifiers, manuscript IDs, collaborator names, patient-level examples, or institution-specific hidden context.
- [ ] No personal absolute paths, private emails, or document metadata with author names.
- [ ] Examples use public or synthetic datasets.

## Documentation

- [ ] New scripts include a short usage example and deterministic expected behavior.
- [ ] The skill documentation states when the skill should **not** be used.
- [ ] Public-facing copy is suitable for an open-source repository.

## Medical claims & classification

- [ ] No unsupported medical claims. If this PR changes a medical/research claim, it needs founder / Clinical-Lead review (see `MAINTAINERS.md`), and the change only makes the claim **more** cautious/accurate/scoped.
- [ ] Classification: this is an **official** / **experimental** / **community** change (delete as appropriate).
