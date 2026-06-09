# Post-Submission Release Operations

**When**: between the end of Phase 9 (circulation) and journal submission. Separate from Phase 10 (recovery).

**Why it's hard**: during circulation (v7~v18 coexisting), the numbers keep shifting. Mint the DOI too early and a content mismatch forces a re-issue; too late and you are scrambling on submission day.

## Checklist

### Gate 1 — When to issue the release

- [ ] Internal circulation closed: every reviewer (internal PI, external peer) has signed off.
- [ ] `[VERIFY-CSV]` / `TODO` / `FIXME` / `(to be regenerated)` tags fully removed from manuscript / supplement / figures / code (`rg -n` → 0 hits).
- [ ] k (number of included studies) matches across the `4_Analysis/*.csv` row count, the manuscript prose, the PRISMA flow, and every figure caption.
- [ ] Author order / ICMJE COI finalized (just before reflecting it in the Zenodo author metadata).

### Gate 2 — GitHub repo

- [ ] Journal-target bundle regenerates successfully via `_build.sh`.
- [ ] Repo includes the raw analysis code, extraction_consensus_log.md, PROSPERO amendments tracker, and methodology.
- [ ] README has a DOI placeholder (replaced after the Zenodo DOI is issued).
- [ ] `.gitignore` confirmed to exclude raw PDFs / copyrighted material.
- [ ] LICENSE stated (CC-BY 4.0 or the journal-required license).

### Gate 3 — Zenodo DOI

- [ ] Zenodo record metadata: author order, affiliation, ORCID, keywords, related identifiers (PROSPERO registration number).
- [ ] Add the GitHub repo release tag URL to `related_identifiers` as `isSupplementTo`.
- [ ] The submission package (.tar.gz) is uploaded to Zenodo — the journal submission bundle, not the circulation package (vN).
- [ ] After the DOI is issued, reflect it in the "data availability" section of the manuscript / cover letter / submission portal.

### Gate 4 — Handling re-targeting after rejection

- [ ] Resubmission of identical content to another journal: **do NOT mint a new Zenodo version** (the DOI attaches to the content). Use `_build.sh --journal {new}` to create only a new SUBMISSION folder.
- [ ] Resubmission after revision: content changed → mint a new Zenodo version. The concept DOI is preserved.
- [ ] On author changes: redistribute the ICMJE COI + mint a new Zenodo version.

## Common failures

- **F1**: Zenodo DOI minted while `k` (included study count) is still oscillating between versions → content-DOI mismatch forces re-issue. **Blocked by**: Gate 1.
- **F2**: Journal-specific folders edited by hand without a `_build.sh` → the journal copies drift from master. **Blocked by**: see `submission_package_drift.md`.
- **F3**: `TODO` / `FIXME` tag left in an R analysis script surfaces only after the repo is pushed to GitHub. **Blocked by**: Gate 1 `rg` scope including code.
