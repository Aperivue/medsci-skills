# Security & Scope Boundary

MedSci Skills is open-source tooling for clinical-manuscript preparation. This page
covers how to report a vulnerability and — because this is medical-domain software —
the safety boundary and the data-hygiene rules for public issues.

## Reporting a vulnerability

If you find a security issue (for example, a script that could execute untrusted
input, a dependency vulnerability, or a path that could exfiltrate local data),
please report it privately rather than opening a public issue:

- Use GitHub's **"Report a vulnerability"** (Security → Advisories) on the
  repository, or
- contact the maintainer listed in [`CITATION.cff`](CITATION.cff).

Please include reproduction steps and the affected version. We will acknowledge the
report and work on a fix; please allow reasonable time before public disclosure.

## Medical scope boundary

MedSci Skills supports **manuscript preparation and research workflow**. It is
**not** a clinical tool. Specifically, it:

- does **not** provide patient-specific medical advice;
- does **not** make diagnoses or recommend treatment;
- does **not** replace authors, statisticians, reviewers, IRBs, or journal
  requirements;
- **requires human-expert verification** of every output — it can produce
  incomplete or incorrect results if used without review.

The deterministic detectors are designed to **reduce common manuscript-preparation
errors** before review; they do not guarantee correctness and are not a substitute
for expert judgment.

## Data hygiene — keep PHI and private content out of public issues

This is a public repository. When filing issues, PRs, or examples, do **not**
include:

- protected health information (PHI) or any patient-level data;
- unredacted local file paths, private emails, or institution-only context;
- unpublished manuscript content, private manuscript IDs, or project codes;
- confidential reviewer comments (unless fully anonymized and you have the right to
  share them).

Use synthetic or public datasets in examples. The repository's validators include a
PII/precedent scan, but the first line of defense is not pasting sensitive content
in the first place. If you need to share a failing case that involves sensitive
data, reduce it to a synthetic minimal reproduction.

## Release integrity & revocation

The classroom self-updater downloads a release ZIP and runs its bundled installer. This
**is remote code execution within the GitHub trust boundary**. Be precise about what is and
is not defended:

- The updater verifies each download's **SHA-256 against the digest the github.com API reports
  for that release asset**, and re-checks the asset name, the release tag, a single ZIP root,
  and that every payload entry matches the bundled `metadata/distribution_files.json` inventory
  (path + size + sha256). This detects a **corrupted or tampered-in-transit download**.
- It does **not** defend against a **compromised maintainer account or a malicious official
  release** served from the same boundary. Treat an update with the same trust you place in
  this repository.

What the release pipeline adds to make a published release trustworthy:

- A **protected `release` environment** with a required reviewer (configured in repo Settings →
  Environments) so a human approves before any release is published.
- A **version-consistency gate**: a tag is only releasable when `CITATION.cff` ==
  `package.json` == `metadata/distribution_manifest.json` (the version-consistency check) **and**
  that shared version equals the pushed tag (the release-workflow tag gate).
- **Build-provenance attestation** of the ZIP artifacts (`actions/attest-build-provenance`);
  anyone can verify a downloaded asset with `gh attestation verify <zip> --repo Aperivue/medsci-skills`.
- A **pre-publish round-trip check** (`scripts/check_release_zip.py`) that runs the updater's own
  safe-extract + provenance validation, so a release cannot ship a ZIP the updater would reject.

### If a release is compromised

If a published release is believed to be malicious or tampered:

1. **Report privately** via GitHub Security Advisories (see "Reporting a vulnerability") — do not
   open a public issue with exploit detail first.
2. Maintainers **delete or mark the affected release** on GitHub and **delete the tag**, then
   publish a new patched release with a higher version. Because the updater compares **semver**,
   users move forward to the patched version and never back to the revoked one.
3. Maintainers **rotate any credentials** that could have been used to publish the bad release
   and review the attestation log for the affected artifacts.
4. The incident and the fixed version are noted in `CHANGELOG.md` and the GitHub Security Advisory.

Users who are concerned can always re-install from a known-good GitHub release — download that
release's classroom ZIP and run its bundled installer — or verify an asset's attestation with
`gh attestation verify <zip> --repo Aperivue/medsci-skills` before installing.
