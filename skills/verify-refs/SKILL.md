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
python "${CLAUDE_SKILL_DIR}/../write-paper/scripts/check_citation_keys.py" \
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

## Output Contract (v1.1.1)

| Artifact | Path | Purpose |
|---|---|---|
| Audit JSON | `qc/reference_audit.json` | Sole output — row-level status (OK/MISMATCH/UNVERIFIED/FABRICATED), counts, submission-safe flag, full records |

**Removed in Phase 1A.2** (per `docs/artifact_contract.md`):
- `references/verified_references.tsv` — record-level details now live inside `reference_audit.json` under `records[]`.
- `references/library.bib` — never this skill's concern. `/search-lit` produces candidates; `/lit-sync` (via Better BibTeX) writes `manuscript/_src/refs.bib`.

Sole-writer enforcement: `scripts/validate_project_contract.py` will flag any `references/*` file written by this skill as drift.

## Workflow

1. Identify the input file and project root.
2. Run `scripts/verify_refs.py`.
3. Read `qc/reference_audit.json`.
4. Report all `FABRICATED` and `MISMATCH` rows first (from `records[]`).
5. If `UNVERIFIED` rows remain, list them as manual checks and do not call the
   manuscript fully submission-safe.
6. If the user needs a human-readable table, summarize from `records[]` in chat — do not write a TSV.

## Quality Gates

- Gate 1: stop submission if any row is `FABRICATED`.
- Gate 2: require user confirmation before accepting `UNVERIFIED` references.
- Gate 3: rerun after any reference edits.
- Gate 4 (added 2026-04-26): first-author surname is cross-checked against
  CrossRef/PubMed. A row whose DOI resolves but whose cited first author does
  not match the authoritative source is downgraded to `MISMATCH` with
  `note = "first-author hallucination suspected"`. This catches the common
  LLM failure mode where a real DOI is paired with an invented author name.

## First-Author Cross-Check (Detail)

Driven by an actual incident: Paper 3 submitted to BMC Medical Education had
ref 8 cited as "Ebrahimi S, et al." with the correct DOI for a Ballard et al.
task force whitepaper. Pre-patch verify-refs marked it OK because DOI resolved.
Post-patch it is correctly flagged as `MISMATCH`.

- Comparison is tolerant: case, diacritics, hyphen vs space, and name
  particles ("von", "van", "de", ...) are normalized before matching.
- If the cited surname cannot be parsed confidently (`first_author_guess`
  empty), the check is skipped silently — no false MISMATCH from formatting
  ambiguity.
- Title-only PubMed search does not return an authoritative author and is
  therefore excluded from this check.

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
