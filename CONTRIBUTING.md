# Contributing to MedSci Skills

Thank you for helping make medical research workflows more reproducible and less brittle. Contributions are welcome through GitHub issues and pull requests.

## What to Contribute

- New skills for recurring medical research workflows.
- Improvements to existing skill routing, anti-hallucination checks, or quality gates.
- Deterministic scripts for checks that should not rely on language-model judgment.
- Public demo improvements using open or synthetic datasets.
- Documentation that helps clinicians install, test, or safely adapt the skills.

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

Until a repository-specific `CODE_OF_CONDUCT.md` is added, contributors are expected to follow the Contributor Covenant principles: https://www.contributor-covenant.org/
