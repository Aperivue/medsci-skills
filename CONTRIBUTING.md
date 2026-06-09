# Contributing to MedSci Skills

Thank you for helping make medical research workflows more reproducible and less brittle. Contributions are welcome through GitHub issues and pull requests.

## What to Contribute

- New skills for recurring medical research workflows.
- Improvements to existing skill routing, anti-hallucination checks, or quality gates.
- Deterministic scripts for checks that should not rely on language-model judgment.
- Public demo improvements using open or synthetic datasets.
- Documentation that helps clinicians install, test, or safely adapt the skills.

Per-skill documentation under `docs/skills/` is **generated** from each `skills/<skill-name>/SKILL.md` by `scripts/gen_skill_docs.py` — do not hand-edit those pages (a parallel copy drifts). Improve the `SKILL.md` itself, then run `python3 scripts/gen_skill_docs.py` and commit the regenerated `docs/skills/`. CI runs `gen_skill_docs.py --check` and fails the build if the pages are out of sync.

## Skill Addition Workflow

1. Open an issue describing the workflow, target users, expected artifacts, and safety boundaries.
2. Add a skill under `skills/<skill-name>/` with a `SKILL.md` file.
3. Include `skill.yml` when the skill has stable inputs, outputs, downstream consumers, or deterministic scripts.
4. Keep examples public and anonymized. Use synthetic or public datasets whenever possible.
5. Add focused tests or validation scripts for deterministic behavior.
6. Run the repository validators before opening a pull request.

## Pull Request Checklist

- [ ] `bash scripts/validate_skills.sh`
- [ ] `python3 scripts/validate_skill_contracts.py`
- [ ] `python3 scripts/check_locale_inventory.py` (any new non-English text is justified in `docs/locale_inventory.md`).
- [ ] No private project identifiers, manuscript IDs, collaborator names, patient-level examples, or institution-specific hidden context.
- [ ] No personal absolute paths.
- [ ] New scripts have a short usage example and deterministic expected behavior.
- [ ] Documentation states when the skill should not be used.
- [ ] Public-facing copy is suitable for an open-source repository.

## PII and Publication Hygiene

MedSci Skills is public. Do not include:

- Private manuscript IDs or study-folder names.
- Unpublished project codes.
- Real collaborator names in examples.
- Patient-level clinical vignettes.
- Screenshots or document metadata with hidden author names.
- Private emails, home-directory paths, or local institution-only paths.

The validator blocklist is intentionally conservative. If it catches a false positive, explain the case in the pull request rather than bypassing the check silently.

## Language Policy

MedSci Skills is **English-canonical**. Write skill mechanics and prose in English so that any
international reader or contributor can understand and adapt them:

- `SKILL.md` body prose, `skill.yml`, code comments, and general reference/template files: **English**.
- Default user-facing prompts and default output templates: **English**, with Korean (or any other
  language) offered as an opt-in `*_ko` variant or via a "communicate in the user's preferred
  language" instruction — not hardcoded as the default.

Non-English text is allowed **only** when it is functional, and then it must be **labeled and
justified**. Permitted categories:

- **Locale data / features** — e.g. the Korean PHI pack in `deidentify`, KNHANES variable labels,
  Korean-PDF rendering references, Korean PII-detection patterns.
- **Locale-jurisdiction modes** — e.g. `grant-builder`'s "Korean Government Grant Mode", where the
  prose is English but real Korean program/artifact terms are preserved.
- **Bilingual `triggers:`** — additive recognition aliases in SKILL.md frontmatter.
- **Opt-in `*_ko` variants** — a Korean sibling of an English-default file.

Every file containing non-English text must appear in
[`docs/locale_inventory.md`](docs/locale_inventory.md) with a one-line reason. The deterministic
gate `python3 scripts/check_locale_inventory.py` (run in CI) fails if a Korean-bearing file under
`skills/` is missing from that inventory. Note that `validate_skills.sh`'s Korean-prose check is
WARN-only and scans only SKILL.md (skipping code blocks, tables, and blockquotes), so the inventory
— not that warning — is the authoritative allowlist.

## Code Style

- Prefer small, reviewable changes.
- Use deterministic scripts for count checks, citation checks, file manifests, and package audits.
- Keep skill prose procedural and testable.
- Avoid adding broad orchestration behavior when a narrow skill-level check is enough.

## Review Process

Maintainers may ask for:

- A smaller PR split.
- More explicit safety boundaries.
- A public demo or synthetic test case.
- Stronger validator coverage before merge.

For JOSS readiness, contributions should strengthen open-source practice signals: public issues, pull requests, tests, CI, documentation, release notes, and clear contribution pathways.

## Code of Conduct

This project follows its [Code of Conduct](CODE_OF_CONDUCT.md), which adopts the Contributor Covenant. By participating, you agree to uphold it.
