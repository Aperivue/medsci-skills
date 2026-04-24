# Manual Reference Verification Checkpoint Guide

**Scope**: medsci-skills v1.1.1 Phase 1A.5
**Audience**: Project owner before journal submission or before circulating a near-final draft to co-authors.

`/verify-refs` runs automatically inside `/write-paper` Step 7.3 and via the
pre-save hook `~/.claude/hooks/verify-refs-guard.sh` when a
`submission/*/manuscript/*.docx` or `revision/R*/*circulation*.docx` is saved.
This guide documents the **manual strict-mode run** the owner should perform
immediately before submitting or before the manuscript leaves the project
workspace.

## When to run manually

Run `verify-refs --strict` manually at every one of these checkpoints:

1. **Before first circulation to co-authors.** Catches hallucinations that
   slipped past Step 7.3 in earlier drafts.
2. **Before cover-letter + manuscript package freeze** (`/sync-submission`).
3. **Before each revision resubmission** (R1, R2, ...). Revisions are a common
   site of new citation drift because reviewer responses introduce new
   references.
4. **Before preprint posting** (medRxiv / arXiv). Preprints are public and hard
   to correct.
5. **After any external edit** (co-author returns a `.docx` with tracked
   changes, or an external editor touches references).

## Command

From the project root:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/verify_refs.py" \
  manuscript/index.qmd \
  --project-root . \
  --strict
```

Or via the wrapper:

```bash
"${CLAUDE_SKILL_DIR}/scripts/verify_cli.sh" manuscript/index.qmd --strict
```

Docx input is also accepted:

```bash
"${CLAUDE_SKILL_DIR}/scripts/verify_cli.sh" \
  submission/radiology_ai/manuscript_main.docx --strict
```

## What `--strict` changes

- Exit code is non-zero if `submission_safe: false` (any FABRICATED / MISMATCH).
- Exit code is non-zero if any UNVERIFIED row remains.
- Offline verification is not tolerated — the script requires live PubMed /
  CrossRef reachability.

## Reading the output

The only output file is `qc/reference_audit.json`. Inspect with:

```bash
python3 -c "import json; a=json.load(open('qc/reference_audit.json')); \
print('safe=', a['submission_safe'], 'counts=', a['counts'])"
```

Then jump to the records:

```bash
python3 -c "import json; a=json.load(open('qc/reference_audit.json')); \
[print(r['ref_id'], r['status'], r.get('note','')) \
  for r in a['records'] if r['status']!='OK']"
```

## Failure actions

| Status | Action |
|---|---|
| `FABRICATED` | STOP. Locate the citation in the manuscript. Either remove it or replace with a verified entry via `/search-lit` + `/lit-sync`. Never patch `refs.bib` by hand. |
| `MISMATCH` | STOP. Usually a copy-paste error (wrong DOI for the title). Confirm the author's intent and correct via Zotero. |
| `UNVERIFIED` | Review. If the reference genuinely lacks DOI/PMID (rare: old conference abstracts, grey literature), mark `verified: manual` in `refs.bib` via Zotero and re-run. Never keep UNVERIFIED rows in a submission package. |

## Relationship with `/lit-sync`

`/verify-refs` is audit-only. All bibliographic corrections flow through
`/lit-sync` (owner-only) → Zotero → Better BibTeX auto-export →
`manuscript/_src/refs.bib`. Never edit `refs.bib` to satisfy `/verify-refs`.

## Automation checkpoint (informational)

The pre-save hook `verify-refs-guard.sh` already runs on every `.docx` save
under `submission/` or `revision/R*/`. A `FABRICATED` status blocks the save.
The manual strict run is a belt-and-suspenders check at the checkpoints listed
above; it is NOT a substitute for the inline hook.

## Change log

- **2026-04-24 v1.1.1 Phase 1A.5** Initial manual checkpoint guide. Aligned to
  audit-only verify-refs contract (no `references/*` writes).
