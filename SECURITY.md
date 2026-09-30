# Security & Scope Boundary

MedSci Skills is open-source tooling for clinical-manuscript preparation. This page
covers how to report a vulnerability and — because this is medical-domain software —
the safety boundary and the data-hygiene rules for public issues.

## Reporting a vulnerability

If you find a security issue (for example, a script that could execute untrusted
input, a dependency vulnerability, or a path that could exfiltrate local data),
please report it privately rather than opening a public issue:

- Use GitHub's **"Report a vulnerability"** button (Security tab → Advisories) on the
  repository, or
- if that button is not shown, contact the maintainer through the contact details on their
  GitHub profile. Their GitHub handle is the owner listed in
  [`.github/CODEOWNERS`](.github/CODEOWNERS), and [`CITATION.cff`](CITATION.cff) gives their name.
  If you cannot reach them that way, a public issue that says only that you have a security
  report, with no details, is fine.

Please include reproduction steps and the affected version. We will acknowledge the
report and work on a fix; please allow reasonable time before public disclosure.

### Supported versions

| Version | Receives security fixes |
|---|---|
| Latest release (6.x) | Yes |
| Anything older, including 5.x | No. Fixes ship as a new release; update to it ([MIGRATION-v6.md](MIGRATION-v6.md) covers 5.x → 6.x) |

There are no maintenance branches: every fix goes to `main` and out in the next release.

### What is in scope for a skill collection

A skill is instructions that an agent follows, plus scripts it may run, so the risks differ from an
ordinary library. Report privately:

- **Instructions that overreach.** A `SKILL.md` or a file under a skill's `references/` that steers
  the agent toward something the user did not ask for: deleting or overwriting files, sending
  content to a network service, installing or running downloaded code, or skipping a confirmation
  step the skill promises.
- **Bundled scripts** (`skills/*/scripts/`) that execute untrusted input (shell or code injection),
  read credentials, write outside the folder they were pointed at, or make a network call their
  skill's instructions do not mention.
- **Untrusted text treated as instructions.** Skills read text that nobody in this project wrote:
  fetched abstracts and full texts, web pages, co-authors' manuscripts, reviewer comments. That
  text is data. A skill that lets such text direct the agent (indirect prompt injection), or acts
  on it without the user's confirmation, is a vulnerability.
- **Patient data leaving the machine**, for example `/deidentify` or a script it calls making a
  network request.
- **The installers and the self-updater**; see [Release integrity](#release-integrity--revocation).

Not a vulnerability here, but still worth an ordinary issue: an agent output that is wrong
(a fabricated reference, a miscounted checklist item). A vulnerability in the agent host itself
(Claude Code, Codex, Cursor, Copilot) belongs with that host's vendor.

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
- **Selected-source comparison** for both classroom ZIPs and the actual npm tarball:
  exact file sets and bytes must match the release checkout. The npm CLI must be executable.
  Recovery runs use verification tools from the workflow commit while recording the selected
  tag commit in ZIP provenance.
- **Payload privacy inspection** reuses the existing hashed-identifier, credential and asset
  metadata scanners. It includes packaged text, extracted PDF text and Office XML/relationships.
  Missing extraction tools or unreadable assets fail verification. It does not perform OCR or
  certify the absence of every possible personal identifier; public author attribution remains
  allowed in root READMEs and one exact synthetic credential fixture is hash-allowlisted.
- **Post-publication comparison** downloads both ZIPs and requires exact pre-upload bytes.
  The published npm version must have valid registry SHA-512 integrity and the same file contents
  and executable modes as the inspected tarball, including when publication is skipped because
  that version already exists. Only tar/gzip headers may differ. Successful runs retain hash and
  coverage reports for 30 days. A skipped npm job means that channel was not published or verified.

Post-publication failures require recovery; they do not roll back an already public release.
These checks apply to runs using the updated workflow, not retroactively to historical releases.

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
