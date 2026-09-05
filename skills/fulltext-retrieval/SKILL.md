---
name: fulltext-retrieval
description: Batch download open-access PDFs by DOI using legitimate OA APIs (Unpaywall, PMC, OpenAlex, Crossref). Optional PDF→Markdown conversion for token-efficient LLM analysis.
triggers: PDF download, fulltext retrieval, open access PDF, batch download papers, meta-analysis PDF, PDF to markdown, convert PDF
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Fulltext Retrieval Skill

Batch download open-access full-text PDFs from a DOI list using legitimate OA APIs only.

## Pipeline

```
DOI → arXiv (10.48550/arXiv.* DOIs) → Unpaywall → PMC (Europe PMC / OA FTP / web) → OpenAlex → Crossref → landing page
```

Each DOI goes through these sources in order until a valid PDF (≥10 KB, `%PDF-` header) is found. arXiv DOIs (`10.48550/arXiv.2401.01234`, version suffixes, old-style `hep-th/9901001`, or a bare `arXiv:` id) resolve directly to the arXiv PDF first.

## Quick Start

```bash
# Prepare a DOI list (one per line)
cat > dois.txt << 'EOF'
10.1007/s00330-010-1783-x
10.1002/mp.12524
10.1148/radiol.13131265
EOF

# Run
python fetch_oa.py dois.txt --output pdfs/ --email your@email.com

# Verbose mode for debugging
python fetch_oa.py dois.txt -o pdfs/ -e your@email.com --verbose
```

## Input Formats

**Plain text** — one DOI per line:
```
10.1007/s00330-010-1783-x
10.1002/mp.12524
```

**TSV / CSV with header** — must contain a `DOI` column; optional `PMID`, `Title`, and
`FirstAuthor` columns (first author's surname or full name for corroboration):
```tsv
ID	Title	DOI	PMID	Year
1	Some paper	10.1007/s00330-010-1783-x	20628747	2010
```

**Markdown table** — a pipe table with a `DOI` column also works:
```markdown
| DOI | PMID | Title |
|-----|------|-------|
| 10.1007/s00330-010-1783-x | 20628747 | Some paper |
```

When a PMID is available, the PMC lookup is more reliable (PMID → PMCID conversion).
Supply `Title` where available: a DOI-only worklist can download a PDF but cannot
establish title agreement. `FirstAuthor` is optional additional evidence.

## PMC Download (JS-Challenge Resistant)

PMC web pages may block automated downloads with JavaScript proof-of-work challenges. This tool uses three fallback methods:

### Method A: Europe PMC REST API (most reliable)

```bash
PMCID="PMC9733600"
curl -sLo output.pdf \
  "https://europepmc.org/backend/ptpmcrender.fcgi?accid=${PMCID}&blobtype=pdf"
```

### Method B: PMC OA FTP Service

```bash
curl -s "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=${PMCID}" | \
    grep -oE 'href="[^"]*\.pdf"' | head -1 | \
    sed 's/href="//;s/"//' | xargs curl -sLo output.pdf
```

### DOI/PMID → PMCID Conversion

```bash
# Works with both DOI and PMID
curl -s "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids=${DOI}&format=json" | \
    python3 -c "import sys,json; print(json.load(sys.stdin)['records'][0].get('pmcid',''))"
```

## Output

- PDFs saved as `{DOI_safe}.pdf` (slashes replaced with underscores)
- `pdfs/retrieval_report.json` — structured per-DOI report (see below)
- `manual_needed.txt` — DOIs that could not be retrieved via OA
- Summary with arXiv/OA/PMC/fail/skip counts

## Retrieval report (`--report`)

Every run writes a structured report (default `<output>/retrieval_report.json`,
override with `--report PATH`):

```json
{
  "schema_version": 2,
  "generated_by": "fetch_oa.py",
  "counts": {"total": 4, "retrieved": 3, "not_retrieved": 1, "title_mismatch": 1,
             "source_identity": {"consistent": 1, "conflict": 1, "unresolved": 1, "unavailable": 1}},
  "items": [
    {"doi": "10.1000/synthetic.example", "pmid": "", "title": "Example title",
     "first_author": "", "status": "oa", "source": "unpaywall",
     "file": "10.1000_synthetic.example.pdf", "size_bytes": 482113,
     "file_sha256": "<SHA-256 of the downloaded file>", "title_match": "match",
     "source_identity": {"status": "consistent", "reason": "title_and_identifier_agree",
                         "text_scope": "first_page_front_matter", "title_match": "match",
                         "doi_match": "match", "observed_identifiers": ["10.1000/synthetic.example"],
                         "first_author_match": "unavailable"}}
  ]
}
```

The example abbreviates `items`. Legacy `status` (`arxiv | oa | pmc | skip | fail`),
`source`, and `counts.retrieved` retain their resolver-result meaning, including existing
files (`skip`). **They do not count identity-verified papers.** Report schema 2 adds the
file hash and separate identity evidence; no PDF is automatically deleted or rejected.

| `source_identity.status` | Meaning / action |
|---|---|
| `consistent` | Complete normalized title and a compatible DOI/arXiv identifier occur in the bounded first-page front matter; an optional supplied author must also match. Evidence agrees, but this is not independent source verification or claim validation. |
| `conflict` | Both the title and observed identifier differ. Inspect the PDF and requested record. |
| `unresolved` | Evidence is incomplete or ambiguous: title-only, DOI-only, missing author, multiple identifiers, or a matching title with another DOI/version. Inspect before using as evidence. |
| `unavailable` | No usable extracted text, Poppler unavailable, no output PDF, or the PDF changed during assessment. No current identity assessment was possible. |

`title_match` keeps its tri-state shape. A `match` now requires the complete normalized
title on up to six consecutive front-matter lines. Case, punctuation and line wrapping
are normalized. Scattered matching words cannot establish a match; partial overlap is
`unavailable`, and low overlap is an advisory `mismatch`.

Evidence is limited to the first page, before a recognized abstract/body/reference
heading, at most 40 lines / 4,000 characters. Thus a title cited in the body or references
does not establish a title match. These are conservative layout heuristics: cover sheets,
unrecognized headings, short or changed titles, unusual reading order and DOI footers
outside that area can remain unresolved. PDF metadata and the filename alone are not
identity evidence. The CLI compares hashes before extraction and when reporting;
changed files cannot inherit the previous text's assessment. Explicit arXiv versions
must agree; preprint/published-version DOI
differences require review rather than automatic rejection.

Downstream reports must preserve `source_identity` and `file_sha256`, keep unresolved
items visible, and check the hash still identifies the file being used. Older reports
without identity evidence remain **unassessed**; do not infer identity from `retrieved`
or `title_match=match`. Full-text conversion does not resolve an identity warning.

## Attach PDFs into Zotero ("Find Available PDF")

OA-only resolvers miss paywalled-but-licensed papers. To attach full text **inside
Zotero** at a much higher yield, use `references/find_available_pdf.js` — a user-run
snippet for Zotero's *Tools → Developer → Run JavaScript*. It triggers Zotero's own
`addAvailablePDF` / `addAvailablePDFs` and therefore reuses **your** OpenURL resolver /
institutional proxy config; **no credentials, proxy hosts, or institutional identifiers
are hard-coded or leave your Zotero client**. The no-code equivalent is right-click →
"Find Available PDF".

This path is **user-initiated** and depends on your live Zotero session, so its results
are recorded manually (not reproducible CI evidence). `/lit-sync` Phase 2.7 orchestrates
both routes (disk OA via this script + in-library via the snippet) and reconciles them in
a report.

## Requirements

- Python 3.10+ (stdlib only, no pip dependencies)
- Contact email (required by Unpaywall Terms of Service)

## API Policies

| Source | Rate Limit | Notes |
|--------|-----------|-------|
| Unpaywall | 100 req/sec | Email required |
| NCBI PMC | 3 req/sec without API key | Add `&api_key=` for higher limits |
| OpenAlex | 100k req/day | Polite pool with email in User-Agent |
| Crossref | 50 req/sec with email | Plus service with `mailto:` in UA |
| Europe PMC | No documented limit | Be polite, ≤1 req/sec recommended |

The script uses 0.3–0.5 second delays between requests.

## PDF → Markdown Conversion (Optional)

After downloading PDFs, convert them to LLM-friendly Markdown for token-efficient repeated analysis. Uses [pymupdf4llm](https://github.com/pymupdf/RAG) — optimized for academic papers with two-column layout handling and table preservation.

### Quick Start

```bash
# Install (one-time)
pip install pymupdf4llm

# Convert all PDFs in a directory
python pdf_to_md.py pdfs/

# Convert with verbose output
python pdf_to_md.py pdfs/ -v

# Custom output directory
python pdf_to_md.py pdfs/ -o markdown/

# First 10 pages only (useful for long supplements)
python pdf_to_md.py pdfs/ --pages 0-9

# Overwrite existing conversions
python pdf_to_md.py pdfs/ --force
```

### Combined Workflow

```bash
# Step 1: Download PDFs
python fetch_oa.py dois.txt -o pdfs/ -e your@email.com

# Step 2: Convert to Markdown (only successful downloads)
python pdf_to_md.py pdfs/ -v
```

After conversion, `.md` files sit alongside `.pdf` files. Claude Code can then use `Read` for full content or `Grep` for targeted extraction — significantly more token-efficient than re-reading PDFs.

### When to Convert

| Scenario | Recommendation |
|----------|---------------|
| Screening/triage (read once) | Skip — read PDF directly |
| Data extraction from k≥5 studies | Convert — repeated reads save tokens |
| Meta-analysis full pipeline | Convert — papers referenced across multiple phases |
| Single paper deep review | Optional — marginal benefit |

### Academic Paper Defaults

- **Images**: Skipped (saves tokens; figures referenced by caption text)
- **Tables**: `lines_strict` strategy (preserves grid-line tables accurately)
- **Layout**: Two-column academic layout handled automatically
- **Headers/footers**: Removed by pymupdf4llm

### Dependency Note

`pdf_to_md.py` requires [pymupdf4llm](https://pypi.org/project/pymupdf4llm/) (AGPL-3.0). This is an **optional** dependency — `fetch_oa.py` remains stdlib-only with zero external dependencies. The AGPL license applies to pymupdf4llm itself, not to this skill.

## Limitations

- Only retrieves **open-access** articles. Paywalled articles require institutional access.
- Landing page scraping may fail on publisher-specific JavaScript-heavy pages.
- Some recent articles may not yet be indexed by OA sources.
- PDF→Markdown quality depends on the PDF's text layer. Scanned-only PDFs may produce poor output.

## Anti-Hallucination

- **Never fabricate file paths, URLs, DOIs, or package names.** Verify existence before recommending.
- **Never invent journal metadata, impact factors, or submission policies** without verification at the journal's website.
- If a tool, package, or resource does not exist or you are unsure, say so explicitly rather than guessing.
