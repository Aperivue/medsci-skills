<!--
Thanks for contributing to MedSci Skills. Keep PRs small and reviewable.
See CONTRIBUTING.md for the full workflow and PII/publication hygiene rules.
-->

## Summary

<!-- What does this PR change, and why? -->

## Type of change

- [ ] New skill
- [ ] Fix or improvement to an existing skill
- [ ] Deterministic script / validator
- [ ] Documentation
- [ ] Other (describe above)

## Validators

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
