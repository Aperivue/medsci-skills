---
name: verify-refs
description: Use when checking whether a manuscript's references are real. Audits each citation against PubMed and CrossRef, flags fabricated or mismatched entries and writes qc/reference_audit.json. Audit-only; never edits references or refs.bib. Citation-key checks are /manage-refs.
metadata:
  triggers: "verify refs, verify references, citation audit, reference hallucination, fabricated references, bibliography check, PMID check, DOI check"
---

# Verify References (Audit-Only)

Audit an existing manuscript or bibliography for fabricated or mismatched references. This
skill **never writes** to `references/` or `manuscript/_src/refs.bib`: corrections flow through
`/lit-sync` (Zotero → Better BibTeX → `refs.bib`), and `/manage-project`'s
`scripts/validate_project_contract.py` flags any `references/*` file written here as drift. It
does not discover literature (`/search-lit`), and it never replaces a missing or bad citation
with a plausible alternative — replacements go through `/search-lit` or the user.

## Inputs

1. Manuscript or bibliography: `.md`, `.docx`, `.bib`, `.txt`, or `.tsv`.
2. Optional project root. Default: current working directory.
3. Optional flags: `--offline` (extract and classify without API calls), `--timeout N` (HTTP
   timeout seconds), `--strict`, `--no-openalex`.

For markdown manuscripts with pandoc `[@bibkey]` citations, run a citation-key check first
(`/manage-refs`'s `check_citation_keys.py`, or your reference manager's). It catches mis-keyed
cites; `verify_refs.py` catches fabricated metadata.

## Deterministic Script

Run the bundled script rather than verifying citations by memory:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/verify_refs.py" manuscript/manuscript.md --project-root .
```

For hooks or quick manual runs, use the wrapper:

```bash
"${CLAUDE_SKILL_DIR}/scripts/verify_cli.sh" manuscript/manuscript.md --offline
```

Manual pre-submission strict run:

```bash
"${CLAUDE_SKILL_DIR}/scripts/verify_cli.sh" manuscript/index.qmd --strict
```

`--strict` forbids `--offline` and exits non-zero on any UNVERIFIED row. Read
`references/manual_checkpoint_guide.md` for when to run it and what to do per status.

Lookups run PubMed (PMID) → CrossRef (DOI; doi.org's handle registry when CrossRef answers
404) → OpenAlex, with a PubMed title search last. Every
`OK` row rests on DOI, PMID, CrossRef, or PubMed title evidence; a failed lookup is recorded as
`UNVERIFIED`, never silently passed. A title search, in either index, counts only when a returned
title matches the cited one (the same token-similarity guard), so a made-up title cannot earn `OK`
from a search that merely returned something.

**OpenAlex tier.** It recovers conference and non-DOI citations (NeurIPS / ICLR / ACL, common
in medical-AI manuscripts) that PubMed and CrossRef miss, and is called only when no author list
was obtained yet. It resolves by DOI, otherwise by a title search behind a token-similarity
guard so a fabricated title cannot earn `OK`. OpenAlex names have no family/given split, so they
support only an existence check and a tolerant first-author membership check — never the strict
positional or author-count MISMATCH, which stays with PubMed efetch / CrossRef. An OpenAlex miss
is `UNVERIFIED`, never `FABRICATED`. `--no-openalex` restricts verification to PubMed + CrossRef.

## Output Contract (v1.3.0)

`qc/reference_audit.json` (`schema_version` 4) is the only output; this skill is its sole writer
and writes no TSV and no `library.bib`.

- `records[]`: per reference, `status`, `note`, `evidence`, `cited_authors[]` /
  `actual_authors[]`, `cited_author_count` / `actual_author_count`. `status` is one of:
  - `OK`: a lookup confirmed the work (DOI, PMID, or a title search passing the similarity
    guard) and the authors agree.
  - `MISMATCH`: the work exists but the citation is wrong: its authors differ (Gate 4), or its
    DOI/PMID does not exist while a lookup still found the work (`note = "wrong identifier…"`).
  - `FABRICATED`: the cited identifier does not exist and nothing else found the work (details
    below).
  - `UNVERIFIED`: nothing confirmed or refuted it (a failed lookup, a DOI held only by another
    registration agency that no index confirmed, no identifier and no title match, a PubMed
    title-only match whose authors could not be compared or differ (`note = "title_only: …"`), or
    `--offline`).
- `counts` and `duplicate_findings[]` (Gate 5).
- `submission_safe`: no `FABRICATED`, no `MISMATCH`, and `duplicate_findings` empty.
  `fully_verified` additionally requires no `UNVERIFIED`.
- `submission_safe` tolerates `UNVERIFIED` rows because offline runs produce them; before a
  submission, resolve each one (confirm it by hand and say how, or remove the citation) — do not
  ship an `UNVERIFIED` reference as if it were checked.
- `source_sha256` and `audited_ref_ids`: what was audited. A later reader compares them with the
  current bib; a changed bib makes the audit stale.

## Workflow

1. Identify the input file and project root.
2. Run `scripts/verify_refs.py`.
3. Read `qc/reference_audit.json`. Every verdict comes from it; never mark a row `OK` yourself.
4. Report all `FABRICATED` and `MISMATCH` rows first (from `records[]`).
5. Report all `duplicate_findings[]` entries (verbatim PMID/DOI duplicates — cite renumbering
   required).
6. If `UNVERIFIED` rows remain, list them as manual checks and do not call the manuscript fully
   submission-safe. Check `note` on every row, whatever its status: `pagination_placeholder`
   (`e000–e000` / `in press` / `TBD` / `forthcoming`) needs the citation resolved before
   submission; `/self-review` Phase 2.5c decides whether any is a P0 blocker.
7. If the user needs a human-readable table, summarize from `records[]` in chat — do not write a
   TSV.

## Quality Gates

- Gate 1: stop submission if any row is `FABRICATED`.
- Gate 2: require user confirmation before accepting `UNVERIFIED` references.
- Gate 3: rerun after any reference edits.
- Gate 4 (full-author cross-check): the authoritative author list comes from PubMed
  `efetch.fcgi` (XML) when a PMID is present — preferred because CrossRef is unreliable for
  given names — with CrossRef and PubMed esummary as fallbacks. For BibTeX inputs every cited family name is
  compared index-by-index, and the cited and source author counts are compared, after
  normalizing case, diacritics, hyphen vs space, and name particles ("von", "van", "de"); one
  name may be a whole word of the other ("Garcia" / "Garcia-Lopez"), never a mere substring
  ("Li" / "Williams"). A row
  whose DOI/PMID resolves but whose authors differ at any index or in count becomes `MISMATCH`:
  `note = "first-author hallucination suspected"` for the first author,
  `note = "non-first-author hallucination or count mismatch"` for #2..#N or the count. A correct
  first author does not establish the rest of the list. Plain-text / TSV inputs, and lists that
  cannot be parsed confidently, degrade to the first-author check (skipped if even that is
  empty). A PubMed title-only match is `OK` only when the matched record's esummary authors were
  compared with the cited ones and agree; otherwise it stays `UNVERIFIED`. A declared
  truncation — BibTeX `and others`, or a `_audit_truncated = <N>` field — turns a
  shorter-than-source count into a note; citing more authors than the source is always flagged.
- Gate 5: verbatim PMID or normalized-DOI duplicates in the reference list are MAJOR findings in
  `duplicate_findings[]`; `submission_safe == true` requires the list to be empty.
- Gate 6: a reference whose raw entry still carries `e000–e000`, `in press`, `TBD`, or
  `forthcoming` is marked `UNVERIFIED` with `note = "pagination_placeholder"`. verify-refs is
  manuscript-agnostic and only flags; `/self-review` Phase 2.5c, with the manuscript in hand,
  decides whether the citation is method- or headline-load-bearing and hence a P0 blocker.

**Citation-metadata confusion is not fabrication.** DOI-suffix digits that look like, but differ
from, the article number (a DOI tail "77196" against article 26068) are cosmetic. When the
identifier resolves and the authors match, do not report the row as fabricated: the script
returns `FABRICATED` only for an identifier that does not exist — a PMID PubMed has no record of,
or a DOI that CrossRef answers 404 for and that doi.org's handle registry (which spans every
registration agency: CrossRef, DataCite, mEDRA, JaLC) reports as not found — and only when no
lookup found the work some other way. After a CrossRef 404 the DOI verdict is:

| doi.org handle registry | another lookup finds the work | status |
|---|---|---|
| not found | no | `FABRICATED` |
| not found | yes (a title search passing the similarity guard) | `MISMATCH` — a real paper cited with a wrong DOI |
| found (registered with another agency) | no / yes | `UNVERIFIED` / `OK` |
| lookup failed (network, 5xx, unexpected reply) | no / yes | `UNVERIFIED` / `OK` |

A DOI field that is not a well-formed DOI (a placeholder such as `n/a`) is not sent to doi.org and
stays `UNVERIFIED`, and so does a legacy SICI DOI (`10.1002/(SICI)…`) that doi.org does not find,
since its punctuation is easily cut in extraction. A real identifier with wrong authors is
`MISMATCH` (Gate 4).

## Claim Fidelity — does the source say what you say it says?

`verify_refs.py` answers whether a reference is real and whose it is, not whether the sentence
citing it is true of it. `scripts/check_claim_fidelity.py` checks the claims that have a
checkable answer against full texts already downloaded and converted (`/fulltext-retrieval`
produces exactly that layout; this script never fetches anything):

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_claim_fidelity.py" \
  --manuscript manuscript/manuscript.md \
  --fulltext-dir fulltext/ --bib manuscript/_src/refs.bib \
  --out qc/claim_fidelity.json --strict
```

| Verdict | Severity | Fires when |
|---|---|---|
| `CITED_QUOTE_ABSENT` | major | Quoted text attributed to a source is not in it in any reading order. |
| `CITED_QUOTE_UNRESOLVED` | prompt | The quote matched with a word or two missing — the signature of a dirty extraction, not of a fabrication. Look; do not assume. |
| `ATTRIBUTION_UNSUPPORTED` | prompt | Not one content word of the attributed claim appears in the source, in any form. Paraphrase normally keeps at least one of the source's own terms. |
| `ORDINAL_CLAIM_UNSUPPORTED` | prompt | "reports three strategies [12]" where the source discusses that noun but never that count near it. |

Only the quote verdict can fail `--strict`; the others are prompts to go read the source,
because paraphrase is legitimate. Read the "not checked" lines: a citation with no full text on
disk is reported unresolved, and a source whose extracted text is an abstract is reported as too
short to judge. Silence means "nothing checkable was wrong", not "everything is right".

Known limits: a quote whose words all appear in order with source tokens between them
(`INTERLEAVED`) is treated as verified, so a quotation that drops a source word such as "not"
produces no finding; reread every quotation that changes a negation or qualifier.

### Sentence-level source evidence table

`qc/claim_fidelity.json` also carries `evidence_rows`: one per recognized prose
sentence/citation pair, with manuscript coordinates, source-text and PDF hashes, advisory
retrieval identity, and an assessor-entered comparison that starts `not_assessed` even when the
bibliographic status is OK and no probe fires.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_claim_fidelity.py" \
  --manuscript manuscript/manuscript.md --bib manuscript/_src/refs.bib \
  --fulltext-dir fulltext/ --retrieval-report pdfs/retrieval_report.json \
  --reference-audit qc/reference_audit.json \
  --out qc/claim_fidelity.json --evidence-table qc/claim_fidelity.md
```

Enter pages, excerpts, metric/unit/denominator, population, direction, and a named assessment
only after inspecting the actual source; equal numbers or matching words do not establish
support. Record whether the assessor used AI assistance, and never describe an AI-generated
assessment as human approval. Rerun with `--reviewed-report qc/claim_fidelity.json` to retain
annotations; changed inputs leave old assessments unresolved. The Markdown table is a derived
view, not a second editable evidence store. Read `references/claim_evidence_workflow.md` before
entering or carrying forward an assessment.
