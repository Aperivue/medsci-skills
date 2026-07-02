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
   - `CHANGELOG.md` — rename the `## [Unreleased]` header **in place** to `## [x.y.z] - <date>`
     so the accumulated items stay under it; do **not** insert a new `## [x.y.z]` header *above*
     `## [Unreleased]` (that orphans the items under a stale Unreleased heading). Verify with
     `grep '^## \[' CHANGELOG.md`.
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
   attests the ZIPs, verifies each is updater-consumable, publishes the GitHub Release, and
   then **publishes to npm** (idempotent, with npm provenance — needs the `NPM_TOKEN` repo
   secret; skips if that version is already on npm). **Approve** the run, then confirm the
   GitHub Release, npm (`npm view medsci-skills version`), and the Zenodo archive.
   - **One-time:** add an `NPM_TOKEN` repo secret — a granular/automation npm token scoped to
     `medsci-skills` with publish rights and **2FA bypass enabled** (a 2FA `auth-and-writes`
     account otherwise demands an OTP the CI cannot provide). Without the secret the npm step
     is skipped and you publish manually (`npm publish --otp=<code>`).
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

## Release cadence

Semver above says *what a bump means*; this says *how often to cut one*. The default
failure mode for an actively-developed toolkit — especially one worked on by an
autonomous agent — is **releasing per pull request**, which inflates the version number
until it no longer communicates anything. `[Unreleased]` racing several minors in a few
days is a credibility tell to an academic audience, the same way an unjustified major bump
is.

**Rules:**

1. **`[Unreleased]` is the staging area; a release drains it.** Merged PRs accumulate under
   `## [Unreleased]` in `CHANGELOG.md`. Do **not** cut a release for every 1–2 merged PRs.
   Let the section fill up, then release once.

2. **A minor release must be a coherent, user-noticeable batch** — not internal
   symmetry-completion. "The N-pillar set is now complete" or "the arc is finished" is an
   *aesthetic* trigger, not a release trigger. Release when `[Unreleased]` holds something a
   user would actually notice or act on.

3. **Cadence guardrail: at most ~one minor release per week** under normal additive work. If
   several minors would otherwise land in the same week, **bundle them into one**. More than
   one minor release in a single work session is almost always over-granular — accumulate
   instead.

4. **The only "release now" trigger is a patch for a broken install / CI / correctness or
   security fix.** Those ship immediately (see the Versioning policy for what counts as a
   patch). Everything else waits for the next batch.

5. **Content creation and releasing are decoupled.** New skills/detectors/guides should be
   **demand-driven** (a real reviewer comment, a user request, a desk-reject, or a
   review-harvest promotion), and *merged* whenever ready; *releasing* is **batch-driven** on
   the cadence above. Finishing a PR is a reason to merge, never by itself a reason to tag.

When in doubt, **do not release** — an extra week in `[Unreleased]` costs nothing, while an
extra version number spends credibility that is hard to earn back.
