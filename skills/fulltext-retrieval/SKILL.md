---
name: fulltext-retrieval
description: Use when you need full-text PDFs for a list of DOIs, such as a meta-analysis screening set. Batch-downloads open-access copies via Unpaywall, PMC, OpenAlex and Crossref, lists paywalled papers for manual access, and can convert PDFs to Markdown.
model: inherit
metadata:
  triggers: "PDF download, fulltext retrieval, open access PDF, batch download papers, meta-analysis PDF, PDF to markdown, convert PDF"
---

# Fulltext Retrieval Skill

Batch download open-access full-text PDFs from a DOI list using legitimate OA APIs only.
Paywalled articles fail by design and are listed in `manual_needed.txt` for institutional access
or ILL; never work around a paywall or publisher access control.

## Pipeline

```
DOI → arXiv (10.48550/arXiv.* DOIs) → Unpaywall → PMC (Europe PMC / OA FTP / web) → OpenAlex → Crossref → landing page
```

Each DOI goes through these sources in order until a valid PDF (≥10 KB, `%PDF-` header) is found.
arXiv DOIs (`10.48550/arXiv.2401.01234`, version suffixes, old-style `hep-th/9901001`, or a bare
`arXiv:` id) resolve directly to the arXiv PDF first.

## Run

Requires Python 3.10+ (stdlib only) and a contact email, which Unpaywall's Terms of Service
require. The script paces its requests (0.3–0.5 s delays) for the APIs' rate limits.

```bash
python "${CLAUDE_SKILL_DIR}/fetch_oa.py" dois.txt --output pdfs/ --email your@email.com

# Verbose mode for debugging (per-DOI source trace)
python "${CLAUDE_SKILL_DIR}/fetch_oa.py" dois.txt -o pdfs/ -e your@email.com --verbose
```

Input formats:

- **Plain text** — one DOI per line.
- **TSV / CSV with header**, or a **Markdown pipe table** — must contain a `DOI` column; optional
  `PMID`, `Title`, and `FirstAuthor` (surname or full name) columns.

A PMID makes the PMC lookup more reliable (PMID → PMCID conversion). Supply `Title` where
available: a DOI-only worklist can download a PDF but cannot establish title agreement.
`FirstAuthor` is optional additional evidence.

## Output

- PDFs saved as `{DOI_safe}.pdf` (slashes replaced with underscores).
- `pdfs/retrieval_report.json` — structured per-DOI report (below); override with `--report PATH`.
- `<output>/manual_needed.txt` — DOIs that could not be retrieved via OA; when a PMCID was
  resolved, the line also carries it and the PubMed Central article URL to open in a browser.
- Summary with arXiv/OA/PMC/fail/skip counts.

## Retrieval report (`--report`)

Every run writes the report (default `<output>/retrieval_report.json`), schema 2:

```json
{
  "schema_version": 2,
  "generated_by": "fetch_oa.py",
  "counts": {"total": 4, "retrieved": 3, "not_retrieved": 1, "title_mismatch": 1,
             "source_identity": {"consistent": 1, "conflict": 1, "unresolved": 1, "unavailable": 1}},
  "items": [
    {"doi": "10.1000/synthetic.example", "pmid": "", "title": "Example title",
     "first_author": "", "status": "oa", "source": "unpaywall",
     "file": "10.1000_synthetic.example.pdf", "size_bytes": 482113, "page_count": 9,
     "file_sha256": "<SHA-256 of the downloaded file>", "title_match": "match",
     "source_identity": {"status": "consistent", "reason": "title_and_identifier_agree",
                         "text_scope": "first_page_front_matter", "title_match": "match",
                         "doi_match": "match", "observed_identifiers": ["10.1000/synthetic.example"],
                         "first_author_match": "unavailable"}}
  ]
}
```

`status` (`arxiv | oa | pmc | skip | fail`), `source`, and `counts.retrieved` describe the
resolver result, including existing files (`skip`). **They do not count identity-verified
papers.** No PDF is automatically deleted or rejected. `page_count` comes from Poppler's
`pdfinfo` (null without it) and is recorded, not judged — a 3-page "article" or a 4-page "book"
is worth opening.

| `source_identity.status` | Meaning / action |
|---|---|
| `consistent` | Complete normalized title and a compatible DOI/arXiv identifier occur in the bounded first-page front matter, with no supplement / preface / table-of-contents heading there; an optional supplied author must also match. Evidence agrees, but this is not independent source verification or claim validation. |
| `conflict` | Both the title and observed identifier differ. Inspect the PDF and requested record. |
| `unresolved` | Evidence is incomplete or ambiguous: title-only, DOI-only, missing author, multiple identifiers, a matching title with another DOI/version, or a supplement / preface / table-of-contents file that names the work without being it (`supplement_or_front_matter`). Inspect before using as evidence. |
| `unavailable` | No usable extracted text, Poppler unavailable, no output PDF, or the PDF changed during assessment. No current identity assessment was possible. |

Evidence is limited to the first page before a recognized abstract/body/reference heading (at
most 40 lines / 4,000 characters), so a title cited in the body or references does not count. A
`title_match` of `match` needs the complete normalized title on up to six consecutive lines;
partial overlap is `unavailable` and low overlap an advisory `mismatch`. Cover sheets, unusual
reading order, short or changed titles and DOI footers outside that area can stay unresolved.
PDF metadata and the filename alone are not identity evidence. Explicit arXiv versions must
agree; a preprint/published-version DOI difference needs review, not automatic rejection.

Downstream reports must preserve `source_identity` and `file_sha256`, keep unresolved items
visible, and check the hash still identifies the file being used. Older reports without identity
evidence remain **unassessed**; do not infer identity from `retrieved` or `title_match=match`.
Full-text conversion does not resolve an identity warning.

## Attach PDFs into Zotero ("Find Available PDF")

For paywalled-but-licensed papers the OA resolvers miss, `references/find_available_pdf.js` is a
user-run snippet for Zotero's *Tools → Developer → Run JavaScript* (no-code equivalent:
right-click → "Find Available PDF"). It triggers Zotero's own `addAvailablePDF` /
`addAvailablePDFs`, so it reuses **the user's** OpenURL resolver / institutional proxy config;
**no credentials, proxy hosts, or institutional identifiers are hard-coded or leave the Zotero
client**. It is user-initiated and depends on the live Zotero session, so record its results
manually — they are not reproducible CI evidence. `/lit-sync` Phase 2.7 orchestrates both routes
and reconciles them in a report.

## PDF → Markdown Conversion (Optional)

Convert downloaded PDFs to Markdown when the same papers will be read repeatedly (data extraction
from k≥5 studies, a meta-analysis pipeline); for one-pass screening, read the PDF directly.

```bash
# Install (one-time)
pip install pymupdf4llm

# Convert all PDFs in a directory (.md files land alongside the .pdf files)
python "${CLAUDE_SKILL_DIR}/pdf_to_md.py" pdfs/ -v

# Custom output directory
python "${CLAUDE_SKILL_DIR}/pdf_to_md.py" pdfs/ -o markdown/

# First 10 pages only (useful for long supplements)
python "${CLAUDE_SKILL_DIR}/pdf_to_md.py" pdfs/ --pages 0-9

# Overwrite existing conversions
python "${CLAUDE_SKILL_DIR}/pdf_to_md.py" pdfs/ --force
```

Images are skipped, so figures survive only as caption text. Scanned-only PDFs (no text layer)
convert poorly. `pdf_to_md.py` needs [pymupdf4llm](https://pypi.org/project/pymupdf4llm/)
(AGPL-3.0), an **optional** dependency; `fetch_oa.py` stays stdlib-only.
