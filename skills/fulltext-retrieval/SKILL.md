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

**TSV / CSV with header** — must contain a `DOI` column; optional `PMID` and `Title` columns:
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

When a PMID is available, the PMC lookup is more reliable (PMID → PMCID conversion). When a `Title` column is present, downloaded PDFs get a best-effort title cross-check (see *Retrieval report* below).

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
  "schema_version": 1,
  "generated_by": "fetch_oa.py",
  "counts": {"total": 10, "retrieved": 6, "not_retrieved": 4, "title_mismatch": 1},
  "items": [
    {"doi": "10.1007/...", "pmid": "20628747", "title": "...",
     "status": "oa", "source": "unpaywall", "file": "10.1007_....pdf",
     "size_bytes": 482113, "title_match": "match"}
  ]
}
```

- `status` ∈ `arxiv | oa | pmc | skip | fail`; `source` names the resolver that succeeded.
- `title_match` ∈ `match | mismatch | unavailable` (tri-state). It is **best-effort**:
  it needs a `Title` column **and** `pdftotext` (poppler). When either is missing it is
  `unavailable`; a `mismatch` is **flagged** for review and **never** auto-rejects a PDF
  (guards against a publisher serving a wrong/redirect PDF that still passes the `%PDF-` check).

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
