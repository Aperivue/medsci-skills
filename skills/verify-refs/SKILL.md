---
name: verify-refs
description: Audit-only verification of manuscript references against PubMed and CrossRef. Detects fabricated or mismatched citations and writes qc/reference_audit.json. Does not modify references/ or refs.bib.
triggers: verify refs, verify references, citation audit, reference hallucination, fabricated references, bibliography check, PMID check, DOI check
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Verify References (Audit-Only)

You help a medical researcher prevent reference hallucinations before submission.
This skill audits an existing manuscript or bibliography. It **does not write**
to `references/` or `manuscript/_src/refs.bib`. It does not discover new
literature; use `/search-lit` for discovery and `/lit-sync` for bib management.

## When to Use

- Before journal submission, especially for `.docx` manuscripts inherited from
  coauthors or external editors.
- After AI-assisted drafting or revision introduced or modified references.
- When a reviewer or collaborator flags a possibly fabricated citation.
- Before `/sync-submission` freezes a journal package.

## Inputs

1. Manuscript or bibliography path: `.md`, `.docx`, `.bib`, `.txt`, or `.tsv`.
2. Optional project root. Default: current working directory.
3. Optional flags passed to the script:
   - `--offline`: extract and classify references without API verification.
   - `--timeout N`: HTTP timeout seconds.

## Companion: pandoc citation key check

For markdown manuscripts using pandoc `[@bibkey]` citations, run the citation-key
matcher first to catch undefined/unused keys before this audit:

```bash
python "${CLAUDE_SKILL_DIR}/../manage-refs/scripts/check_citation_keys.py" \
  manuscript.md references.bib
```

Then run `verify_refs.py` against the .bib to validate each entry against
PubMed/CrossRef. The two checks are complementary: `check_citation_keys.py`
catches mis-keyed cites; `verify_refs.py` catches fabricated metadata.

## Deterministic Script

Run the bundled script rather than verifying citations by memory:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/verify_refs.py" manuscript/manuscript.md --project-root .
```

For hooks or quick manual runs, use the wrapper:

```bash
"${CLAUDE_SKILL_DIR}/scripts/verify_cli.sh" manuscript/manuscript.md --offline
```

**Manual pre-submission strict run** (Phase 1A.5):

```bash
"${CLAUDE_SKILL_DIR}/scripts/verify_cli.sh" manuscript/index.qmd --strict
```

`--strict` forbids `--offline` and exits non-zero on any UNVERIFIED row.
Full checkpoint protocol: `references/manual_checkpoint_guide.md`.

The script uses DOI, PMID, CrossRef, and PubMed E-utilities where available. If
network verification fails, it records `UNVERIFIED` rather than silently passing.

## Output Contract (v1.3.0)

| Artifact | Path | Purpose |
|---|---|---|
| Audit JSON | `qc/reference_audit.json` | Sole output — row-level status (OK/MISMATCH/UNVERIFIED/FABRICATED), counts, `cited_authors[]`/`actual_authors[]`, `duplicate_findings[]`, submission-safe flag, full records |

**v1.2.0 (2026-05)** adds `duplicate_findings[]` to the audit JSON. Verbatim PMID or DOI duplicates within the reference list are flagged as MAJOR findings (resolves `/peer-review` Phase 2A P7). DOI normalization strips `https://doi.org/`, `http://dx.doi.org/`, `doi:` prefixes plus trailing slashes before comparison so `https://doi.org/10.x/abc/` and `10.x/abc` collapse to one key. Both `submission_safe` and `fully_verified` now require `duplicate_findings` to be empty.

**v1.3.0 (2026-05)** extends the author cross-check from first-author-only to the **full author list** and bumps `schema_version` to 4. For BibTeX inputs, every cited author family name is compared index-by-index against the authoritative source, and the cited-vs-source author counts are compared. PubMed `efetch.fcgi` (XML full record) is the truth source when a PMID is present — it is authoritative for given/family names where CrossRef is not (a documented case where CrossRef returned a wrong given name that PubMed efetch corrected). Records now carry `cited_authors[]`, `actual_authors[]`, `cited_author_count`, and `actual_author_count`. Motivation: a real AI-assisted manuscript registered a reference with a correct first author but seven of ten fabricated co-author names, and the first-author-only check passed it. Plain-text / TSV inputs, which cannot be parsed into a confident full list, degrade gracefully to the first-author check.

**Removed in Phase 1A.2** (per `docs/artifact_contract.md`):
- `references/verified_references.tsv` — record-level details now live inside `reference_audit.json` under `records[]`.
- `references/library.bib` — never this skill's concern. `/search-lit` produces candidates; `/lit-sync` (via Better BibTeX) writes `manuscript/_src/refs.bib`.

Sole-writer enforcement: `scripts/validate_project_contract.py` will flag any `references/*` file written by this skill as drift.

## Workflow

1. Identify the input file and project root.
2. Run `scripts/verify_refs.py`.
3. Read `qc/reference_audit.json`.
4. Report all `FABRICATED` and `MISMATCH` rows first (from `records[]`).
5. Report all `duplicate_findings[]` entries (verbatim PMID/DOI duplicates — cite renumbering required).
6. If `UNVERIFIED` rows remain, list them as manual checks and do not call the
   manuscript fully submission-safe.
7. If the user needs a human-readable table, summarize from `records[]` in chat — do not write a TSV.

## Quality Gates

- Gate 1: stop submission if any row is `FABRICATED`.
- Gate 2: require user confirmation before accepting `UNVERIFIED` references.
- Gate 3: rerun after any reference edits.
- Gate 4 (added 2026-04-26; extended to full-author in v1.3.0): the cited
  author list is cross-checked against the authoritative source (PubMed efetch
  preferred, then CrossRef, then PubMed esummary). A row whose DOI/PMID resolves
  but whose cited authors do not match — at any index, or in total count — is
  downgraded to `MISMATCH`. First-author mismatches get
  `note = "first-author hallucination suspected"`; #2..#N family or count
  mismatches get `note = "non-first-author hallucination or count mismatch"`.
  This catches the LLM failure mode where a real DOI is paired with invented
  author names anywhere in the list, not just the lead author. Intentional CSL
  et-al truncation (cited fewer than source) can be silenced per-entry with a
  BibTeX `_audit_truncated = <N>` field.
- Gate 5 (added 2026-05, v1.2.0): PMID/DOI duplicate detection within the
  reference list. Verbatim duplicates (same PMID or normalized DOI) — a common
  LLM citation-compilation artifact — are flagged as MAJOR findings in
  `duplicate_findings[]`. `submission_safe == true` requires the list to be
  empty. Resolves `/peer-review` Phase 2A P7.

## Author Cross-Check (Detail)

Driven by two actual incidents. First (Gate 4 origin): a manuscript had a
reference cited with a plausible lead author but the correct DOI for an entirely
different author's whitepaper. Pre-patch verify-refs marked it OK because the
DOI resolved; post-patch it is `MISMATCH`. Second (v1.3.0 extension): an
AI-assembled `.bib` registered a reference with the correct first author but
seven of ten fabricated co-author names — the first-author-only check passed it,
and it would have shipped to reviewers. The full-author cross-check catches it.

- The authoritative author list is taken from PubMed `efetch.fcgi` (XML) when a
  PMID is present, falling back to CrossRef (DOI) and then PubMed esummary.
  efetch is preferred because CrossRef is unreliable for given names.
- For BibTeX inputs, the full cited list is parsed (`cited_authors[]`,
  balanced-brace aware, LaTeX-accent tolerant) and compared family-by-family and
  by total count against `actual_authors[]`.
- Comparison is tolerant: case, diacritics (NFKD plus Turkish/Polish/Czech/
  German/Nordic special letters), hyphen vs space, and name particles
  ("von", "van", "de", ...) are normalized before matching.
- If the cited authors cannot be parsed confidently, the check degrades to the
  first-author surname comparison, and if even that is empty it is skipped
  silently — no false MISMATCH from formatting ambiguity.
- Title-only PubMed search does not return an authoritative author and is
  therefore excluded from this check.
- Intentional truncation (a bib that cites only the first author, or first five
  + et al., by design) would otherwise trip the count check; mark such entries
  with `_audit_truncated = <N>` to downgrade the count mismatch to a note.

## What This Skill Does NOT Do

- Does not generate new references from memory.
- Does not replace missing citations with plausible alternatives without
  `/search-lit` or user approval.
- Does not sync Zotero collections; use `/lit-sync` after this audit.

## Anti-Hallucination

- Never fabricate titles, DOIs, PMIDs, author lists, journal names, years,
  volumes, or pages.
- Every OK row must be backed by DOI, PMID, CrossRef, or PubMed title evidence.
- If evidence is unavailable, mark `UNVERIFIED` and keep it visible.
