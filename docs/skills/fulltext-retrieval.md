<!-- AUTO-GENERATED from skills/fulltext-retrieval/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# fulltext-retrieval

> Batch download open-access PDFs by DOI using legitimate OA APIs (Unpaywall, PMC, OpenAlex, Crossref). Optional PDF→Markdown conversion for token-efficient LLM analysis.

**Invoke:** `/fulltext-retrieval` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`fulltext-retrieval` activates on requests such as: PDF download, fulltext retrieval, open access PDF, batch download papers, meta-analysis PDF, PDF to markdown, convert PDF.

## Quality Card

**Purpose** — Resolve a DOI list to open-access full-text PDFs via legitimate OA APIs, with optional Markdown conversion.

**Safety boundaries**

- Uses legitimate open-access sources only (Unpaywall, PMC / Europe PMC, OpenAlex, Crossref); never circumvents paywalls or access controls.
- Validates each download (>=10 KB and a %PDF- header) before accepting it.

**Known limitations**

- Only open-access content is retrievable; non-OA DOIs fail by design rather than fetching from unauthorized sources.
- Higher-yield in-library retrieval (find_available_pdf.js) is user-initiated inside Zotero and uses the user's own proxy/OpenURL config; it is not reproducible CI evidence.
- Title cross-check is best-effort: it needs a Title column plus pdftotext (poppler); otherwise title_match is 'unavailable'. A mismatch is flagged, never auto-rejected.
- PDF-to-Markdown conversion requires the optional pymupdf4llm dependency (AGPL-3.0 or commercial license).

**Validation**

- `bash fetch_oa_report_challenge/verify.sh   # offline report-builder + title tri-state (CI-wired)`
- `python fetch_oa.py dois.txt -o pdfs/ -e <email> --report pdfs/retrieval_report.json --verbose   # per-DOI source trace`
- `verify each output begins with %PDF- and is at least 10 KB`

**Evidence** — `bundled_script`

## Bundled resources

**References** (`skills/fulltext-retrieval/references/`):

- `find_available_pdf.js`

## Source

Canonical definition: [`skills/fulltext-retrieval/SKILL.md`](../../skills/fulltext-retrieval/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
