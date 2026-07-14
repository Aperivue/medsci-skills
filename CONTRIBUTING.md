# Contributing to MedSci Skills

Thank you for helping make medical research workflows more reproducible and less brittle. Contributions are welcome through GitHub issues and pull requests.

## Quickstart: your first PR (5 minutes)

Most contributions are **one small, self-contained file** (a CSL style, a de-identification locale, a figure exemplar, a journal profile, a README translation). You do **not** need to read the rest of this document, understand the whole pipeline, or run the full validator suite locally for one of these.

### You do not need git

Most of the people who use this toolkit are clinicians, and the single most common reason a good
contribution never arrives is that step one used to be *"fork the repo and clone your fork."* For a
one-file contribution, **you can do the whole thing in your browser** — no git, no clone, no terminal:

1. Open the folder the issue points to (e.g. [`skills/manage-refs/citation_styles/`](skills/manage-refs/citation_styles/)).
2. Click **Add file → Create new file** (or open an existing file and click the **pencil** to edit it).
   Open the nearest existing file in another tab and copy its shape.
3. Write the file, then click **Propose changes** at the bottom. GitHub forks the repository for you,
   makes the branch, and offers to open the pull request. Click **Create pull request**.
4. That is the whole thing. **CI runs for you.** If something needs fixing, a maintainer will say so in
   plain language on that page — you will not be asked to rebase anything.

If you would rather work locally, the git path is: fork → clone → `git checkout -b add-<thing>` → add
the file → push → open a PR. Either way, you do **not** need the worktree discipline, the release
process, or any catalog-count bump. The catalog-consistency check auto-derives journal-profile counts
from disk, so adding a profile will not flag you; a maintainer handles the bookkeeping in review.

**One check may go red, and it is not your fault.** If your change *adds* a file that ships to users
(a journal profile, a reference doc), the `Distribution manifests in sync` check fails: we keep a
hashed list of every shipped file so the self-updater can verify a download, and your new file is not
in it yet. If you are working locally, refresh it with `python3 scripts/gen_distribution_manifest.py`
and commit the `metadata/` files it writes. **If you contributed through the browser, you cannot run
that — and you are not expected to.** Leave it red, say so in the PR, and a maintainer will refresh
the manifest before merging. A red mark on that one check is bookkeeping, not a rejection.

### Already changed something on your own machine?

If you have adapted an installed skill — added your journal, fixed something that was wrong for your
specialty — run **`/contribute`**. It finds what you changed, **scans it for patient data, hospital
names, IRB numbers and manuscript IDs** (that scan blocks), shows you every line, and opens the pull
request for you. You never type a git command.

**Claiming an issue:** you don't need to. **No assignment is required — just open a PR.** The first PR that passes CI and review wins. If you want to signal intent, comment on the issue; that soft-claim lapses after **7 days** so an issue never sits blocked on someone who moved on.

The heavier **Pull Request Checklist**, **Skill Addition Workflow**, and validator steps below apply to **maintainers and larger PRs** (new skills, detectors, or anything touching a medical/research claim) — not to a one-file drive-by contribution.

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

### Registry consistency (`capabilities.yml` ⇄ `skill.yml`)

`capabilities.yml` adjudicates the *overlapping* domains (each with an `owner`
and `overlaps` list); every skill's `skill.yml` declares its `owner_domain`.
`scripts/validate_capabilities.py --strict` (CI-enforced) asserts four
invariants — run it after adding or moving a skill:

1. **Valid contract** — every `skills/*/skill.yml` is valid YAML with `name`
   equal to its directory and a non-empty `owner_domain`.
2. **Owner agreement** — each declared domain's `owner` is a real skill whose
   `owner_domain` is that domain.
3. **No silent claimant** — a skill whose `owner_domain` is a *declared* domain
   must be that domain's owner or listed in its `overlaps`.
4. **Resolvable references** — every `overlaps` entry and every umbrella member
   resolves to an existing skill / declared domain.

A single-skill domain that needs no adjudication is *not* declared in
`capabilities.yml` — that is intentional, not drift.

## Running the tests

MedSci Skills is guarded by a deterministic test suite that runs in CI on every
push and pull request. The authoritative list of every check is
[`.github/workflows/validate.yml`](.github/workflows/validate.yml); the whole
suite uses synthetic fixtures and needs no private data or network access.

To run it locally, install the test dependencies and execute the checks:

```bash
pip install pyyaml pandas numpy python-pptx python-docx

# Structure, PII, and skill-contract validation
bash scripts/validate_skills.sh

# Version + distribution manifest + installer round-trip
python3 scripts/check_version_consistency.py
python3 scripts/gen_distribution_manifest.py --check
python3 installers/install.py --self-test
bash installers/tests/test_release_zip.sh

# Skill-registry, /orchestrate routing, and catalog consistency
python3 scripts/validate_capabilities.py --strict
python3 scripts/check_orchestrate_reachability.py --strict
python3 scripts/validate_catalog_consistency.py

# Deterministic-detector self-tests (drift fixtures must fail, live repo clean)
for t in skills/self-review/tests/*.sh; do bash "$t"; done
```

Each deterministic detector additionally ships a self-contained
`<detector>_challenge/` directory — a positive case, a negative control, and a
`verify.sh` — so any single detector can be exercised offline in isolation, for
example:

```bash
bash skills/self-review/scripts/check_reported_p_from_counts_challenge/verify.sh
```

A green run of `.github/workflows/validate.yml` is required before any release is
cut.

## Pull Request Checklist

- [ ] `bash scripts/validate_skills.sh`
- [ ] `python3 scripts/validate_skill_contracts.py`
- [ ] `python3 scripts/validate_capabilities.py --strict` (skill-registry consistency)
- [ ] `python3 scripts/check_locale_inventory.py` (any new non-English text is justified in `docs/locale_inventory.md`).
- [ ] No private project identifiers, manuscript IDs, collaborator names, patient-level examples, or institution-specific hidden context.
- [ ] No personal absolute paths.
- [ ] New scripts have a short usage example and deterministic expected behavior.
- [ ] Documentation states when the skill should not be used.
- [ ] Public-facing copy is suitable for an open-source repository.
- [ ] **Does this PR change a medical/research claim?** If yes, it needs founder / Clinical-Lead review (see [`MAINTAINERS.md`](MAINTAINERS.md)). Only make such claims **more** cautious, accurate, or clearly scoped — never broader.
- [ ] **Status declared** — is this an *official* (founder-approved, documented, tested), *experimental* (useful but not fully tested), or *community* (external, not founder-validated) contribution?

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

## Releasing (maintainers)

**A release is an event, not a commit.** Merge to `main` continuously — that is what `main` is for —
and let the work accumulate into something a person would actually want to read about.

The rule is enforced by `scripts/check_release_cadence.py` (CI):

- **At least 14 days since the last release.**
- **The release must carry something a user would notice.** Docs, CI and internal changes are fine
  to merge and a poor reason to make a hundred people update; they ride along with the next release
  that has a reason of its own.
- **Exception — a hotfix.** Something already shipped is broken: it will not install, it loses data,
  it is a security problem, or it produced a wrong result that a user may have believed. Those go out
  immediately. Say so, and the gate stands aside:

  ```markdown
  ## [5.20.1] - 2026-07-11

  **Hotfix:** `/orchestrate --e2e` halted at step 3 requiring a DOCX only rendered at step 7,
  so an end-to-end run could not complete.
  ```

### Why this is a gate and not a preference

In the 37 days to 2026-07-13 this repository cut **42 releases** — a median gap of **zero days**,
three of them on one afternoon. That was not merely untidy:

1. **The release stopped meaning anything.** Someone who sees forty-nine releases does not read a
   changelog; they wonder whether the project is stable. A version number that changes daily is a
   commit log with extra ceremony, and it stops being usable as a coordinate — *"which version were
   you on?"* has no answer when there were four that week.

2. **It destroyed our own adoption signal.** Every release attracts a handful of automated asset
   downloads (mirrors, scanners, crawlers), so `release_downloads` grows with the number of
   **releases**, not the number of **users**. Across that window the cumulative total doubled while
   per-release downloads collapsed from **32 to 5** — and the cumulative total was about to be cited
   as evidence of adoption. **Cadence is a measurement decision, not only a shipping one.**

## Code of Conduct

This project follows its [Code of Conduct](CODE_OF_CONDUCT.md), which adopts the Contributor Covenant. By participating, you agree to uphold it.
