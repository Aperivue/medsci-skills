---
name: verify-refs
description: Verify manuscript references against PubMed and CrossRef, detect fabricated or mismatched citations, and write auditable reference artifacts.
triggers: verify refs, verify references, citation audit, reference hallucination, fabricated references, bibliography check, PMID check, DOI check
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Verify References

You help a medical researcher prevent reference hallucinations before submission.
This skill audits an existing manuscript or bibliography. It does not discover
new literature; use `/search-lit` for literature discovery.

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

## Deterministic Script

Run the bundled script rather than verifying citations by memory:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/verify_refs.py" manuscript/manuscript.md --project-root .
```

For hooks or quick manual runs, use the wrapper:

```bash
"${CLAUDE_SKILL_DIR}/scripts/verify_cli.sh" manuscript/manuscript.md --offline
```

The script uses DOI, PMID, CrossRef, and PubMed E-utilities where available. If
network verification fails, it records `UNVERIFIED` rather than silently passing.

## Output Contract

| Artifact | Path | Purpose |
|---|---|---|
| Reference table | `references/verified_references.tsv` | Row-level OK/MISMATCH/UNVERIFIED/FABRICATED status |
| BibTeX library | `references/library.bib` | Verified or explicitly marked bibliography entries |
| Audit JSON | `qc/reference_audit.json` | Machine-readable summary for `/orchestrate` and `/sync-submission` |

## Workflow

1. Identify the input file and project root.
2. Run `scripts/verify_refs.py`.
3. Read `qc/reference_audit.json`.
4. Report all `FABRICATED` and `MISMATCH` rows first.
5. If `UNVERIFIED` rows remain, list them as manual checks and do not call the
   manuscript fully submission-safe.

## Quality Gates

- Gate 1: stop submission if any row is `FABRICATED`.
- Gate 2: require user confirmation before accepting `UNVERIFIED` references.
- Gate 3: rerun after any reference edits.

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
