# Maintainer workflow & release checklist

How a maintainer reviews PRs and prepares a release, and how a future part-time
technical maintainer can be onboarded safely. Roles are defined in
[`MAINTAINERS.md`](../MAINTAINERS.md).

## Permission ramp (onboarding a part-time technical maintainer)

Merge rights expand with demonstrated trust, never all at once. The founder retains
final release approval at every stage.

| Stage | What they can do |
|-------|------------------|
| **Month 1** | Triage and comment only — label issues, request changes, review PRs. No merge. |
| **Months 2–3** | Merge **docs-only** PRs and simple CI/docs fixes. |
| **After trust is established** | Merge **non-medical** PRs (refactors, tests, packaging, CI). Prepare release drafts. |
| **Always** | **Final release approval stays with the founder.** Anything touching clinical/research scope or a medical claim needs Clinical-Lead sign-off. |

## Reviewing a PR

1. CI is green (`.github/workflows/validate.yml`).
2. The PR states its **type** (skill / detector / docs / CI / release) and whether
   it changes a **medical/research claim** (if yes → founder review).
3. Catalog consistency: if a skill / checklist / journal profile / detector was
   added or removed, `metadata/catalog_counts.json` and the generated catalogs were
   updated and `python3 scripts/validate_catalog_consistency.py` passes.
4. No PHI, private paths, manuscript IDs, or unsupported medical claims
   (see [`CONTRIBUTING.md`](../CONTRIBUTING.md) and [`SECURITY.md`](../SECURITY.md)).
5. New deterministic scripts ship a challenge/regression test wired into CI.

## Release checklist

A release is cut from `main` by pushing a version tag; `release.yml` builds the
ZIPs (with an injected, verified `provenance.json`), attests their build provenance,
verifies they are consumable by the self-updater, creates the GitHub Release, and
Zenodo archives it.

**One-time setup:** in repo **Settings → Environments**, create a `release` environment
and add yourself as a **required reviewer**. The release job then pauses for your approval
before publishing. (The workflow names the environment unconditionally; without the setting
it simply does not gate.)

1. **Decide the version** honestly (see "Versioning" below).
2. **Sync versions in one commit:**
   - `CHANGELOG.md` — move `[Unreleased]` to `[x.y.z]` with today's date.
   - `CITATION.cff` — `version` + `date-released`.
   - `package.json` — `version` (npm).
   - `README.md` — "What's New" entry.
3. **Regenerate the distribution manifest + catalogs:**
   - `python3 scripts/gen_distribution_manifest.py` — refreshes `distribution_manifest.json`
     (version, from `CITATION.cff`) + the `distribution_files.json` inventory. Run
     `check_version_consistency.py` to confirm CITATION == package.json == manifest.
   - If skill/detector counts changed: `gen_skills_catalog_json.py`,
     `gen_detectors_catalog_json.py`, `gen_marketplace_json.py` (then `--check` each) and
     `validate_catalog_consistency.py`.
4. **Tag** `vX.Y.Z` and push → `release.yml` runs. It gates on the version-consistency
   check (tag must equal the manifest version), pauses for `release`-environment approval,
   attests the ZIPs, and verifies each is updater-consumable before publishing. **Approve**
   the run, then confirm the GitHub Release and Zenodo archive.
5. **Sync downstream surfaces** that live outside this repo's CI: the homepage
   `skills.json` counts and any hero-skill mirrors (`sync_hero_skill.py`).
6. **Record evidence** — refresh [`IMPACT.md`](../IMPACT.md) (run the metrics
   snapshot *before* the release commit so the bot commit is in place) and log any
   new citations / named use.

A compromised-release revocation procedure is in [`SECURITY.md`](../SECURITY.md)
("Release integrity & revocation").

## Versioning policy

Semantic versioning, read honestly:

- **Patch (x.y.Z)** — critical install / CI / broken-workflow fixes.
- **Minor (x.Y.z)** — new skills, detectors, checklists, or docs; additive,
  backward-compatible changes (the common case here).
- **Major (X.y.z)** — a **structural or breaking** change: an install-layout
  change, a skill removal/merge/rename, or an output-path change. A major bump is
  reserved for a real break, not for a large additive release — version inflation
  reads as a credibility tell to an academic audience.

Release notes distinguish: **Added / Changed / Fixed / Deprecated /
Validation-Evidence / Breaking changes / Documentation.**
