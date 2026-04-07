---
name: search-lit
description: Literature search and citation management for medical research. Searches PubMed, Semantic Scholar, and bioRxiv/medRxiv with verified citations. Anti-hallucination — every reference verified via API before inclusion. Generates BibTeX entries.
triggers: literature search, find papers, citation, references, bibliography, PubMed search, related work
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Literature Search Skill

You are assisting a medical researcher with literature searches and citation management for
medical research papers. Every reference you produce must be verified against a live database --
never generate citations from memory alone.

## Communication Rules

- Communicate with the user in their preferred language.
- All citation content (titles, abstracts, BibTeX) in English.
- Medical terminology is always in English.

## Key Directories

- **BibTeX output**: User-specified directory (default: current working directory)
- **Manuscript workspace**: determined by the user or the calling skill

## Search Tools: MCP (Primary) + E-utilities (Fallback)

### Primary: MCP Tools (Claude.ai Remote)

| Database | MCP Tool | Purpose |
|----------|----------|---------|
| PubMed | `mcp__claude_ai_PubMed__search_articles` | Search by query, MeSH terms |
| PubMed | `mcp__claude_ai_PubMed__get_article_metadata` | Full metadata for a PMID |
| PubMed | `mcp__claude_ai_PubMed__find_related_articles` | Related articles for a PMID |
| PubMed | `mcp__claude_ai_PubMed__lookup_article_by_citation` | Verify a citation |
| PubMed | `mcp__claude_ai_PubMed__convert_article_ids` | Convert between PMID/DOI/PMCID |
| Semantic Scholar | `mcp__claude_ai_Scholar_Gateway__semanticSearch` | Semantic search across all fields |
| bioRxiv/medRxiv | `mcp__claude_ai_bioRxiv__search_preprints` | Search preprint servers |
| bioRxiv/medRxiv | `mcp__claude_ai_bioRxiv__get_preprint` | Full preprint metadata |
| CrossRef | WebFetch with `https://api.crossref.org/works/{DOI}` | DOI verification |

### Fallback: NCBI E-utilities (Direct API via Bash)

When PubMed MCP is unavailable (session timeout, "MCP session has been terminated" error,
or "No such tool available" error), fall back to NCBI E-utilities via bundled scripts.

**Detection**: If any `mcp__claude_ai_PubMed__*` call returns an error containing
"terminated", "not found", "not available", or "not connected", switch ALL subsequent
PubMed calls in this session to E-utilities. Do not retry MCP after a disconnect — it
will not recover within the same conversation.

**Scripts** (in `${CLAUDE_SKILL_DIR}/references/`):
- `pubmed_eutils.sh` — Bash wrapper for NCBI E-utilities API
- `parse_pubmed.py` — Python parser for E-utilities responses

**Usage patterns:**

```bash
EUTILS="${CLAUDE_SKILL_DIR}/references/pubmed_eutils.sh"
PARSER="${CLAUDE_SKILL_DIR}/references/parse_pubmed.py"

# Search PubMed (returns PMIDs)
bash "$EUTILS" search "diagnostic test accuracy meta-analysis radiology" 20 \
  | python3 "$PARSER" esearch

# Get article summaries as markdown table
bash "$EUTILS" fetch_json "16168343,16085191,31462531" \
  | python3 "$PARSER" esummary

# Get detailed metadata
bash "$EUTILS" fetch "16168343" \
  | python3 "$PARSER" efetch

# Generate BibTeX entries
bash "$EUTILS" fetch "16168343,16085191" \
  | python3 "$PARSER" bibtex

# Verify a citation by exact title
bash "$EUTILS" cite_lookup "Bivariate analysis of sensitivity and specificity" \
  | python3 "$PARSER" esearch

# Find related articles for a PMID
bash "$EUTILS" related "16168343" 10 \
  | python3 "$PARSER" esummary
```

**Rate limiting**: 3 requests/second without API key, 10/sec with NCBI_API_KEY.
The script auto-sleeps 350ms between calls. For batch operations, keep calls sequential.

**E-utilities → MCP equivalence:**

| MCP Tool | E-utilities Command | Parser Mode |
|----------|-------------------|-------------|
| `search_articles` | `search <query> [retmax]` | `esearch` |
| `get_article_metadata` | `fetch <pmids>` | `efetch` or `bibtex` |
| `find_related_articles` | `related <pmid> [retmax]` | `esummary` |
| `lookup_article_by_citation` | `cite_lookup <title>` | `esearch` → `fetch` |
| `convert_article_ids` | Not available (use CrossRef DOI lookup) | — |

---

## Workflow

### Phase 1: Search Strategy

1. **Understand the need**: Get the research topic, specific question, or manuscript section
   that needs references.
2. **Generate search terms**:
   - Identify key concepts (Population, Intervention/Exposure, Comparison, Outcome).
   - Generate MeSH terms for PubMed queries.
   - Build Boolean queries: `(concept1 OR synonym1) AND (concept2 OR synonym2)`.
3. **Define scope**:
   - Date range (default: last 10 years unless user specifies).
   - Article types (original research, review, meta-analysis, etc.).
   - Language filter (default: English).
4. **Present the search plan** to the user before executing. Include the Boolean query,
   databases to search, and filters.

**Gate:** Wait for user approval before running searches.

### Phase 2: Execute Search

1. **Search PubMed** using `search_articles` with the Boolean query.
2. **Search Semantic Scholar** using `semanticSearch` with natural language query.
3. **Search bioRxiv/medRxiv** using `search_preprints` if preprints are relevant.
4. **Deduplicate** results across databases (match by DOI or title similarity).
5. **Present results** in a structured table:

```
| # | Title | Authors (first + last) | Year | Journal | PMID/DOI | Relevance |
|---|-------|----------------------|------|---------|----------|-----------|
| 1 | ...   | Kim J, ... Lee S     | 2024 | Radiology | 12345678 | High      |
```

6. Ask the user to select which papers to include.

### Phase 3: Deep Read

For each selected paper:

1. **Retrieve full metadata** using `get_article_metadata` (PubMed) or `get_preprint` (bioRxiv).
2. **Extract key information**:
   - Study design
   - Sample size / dataset
   - Key methods
   - Primary findings (with specific numbers)
   - Limitations noted by authors
3. **Build a literature matrix** if multiple papers selected:

```
| Paper | Design | N | Key Finding | Limitation | Relevance to Our Study |
|-------|--------|---|-------------|------------|----------------------|
```

4. Present the matrix to the user for review.

### Phase 4: Citation Management

#### Anti-Hallucination Protocol

This is the most critical part of the skill. Follow these rules without exception:

1. **NEVER generate a reference from memory alone.** Every reference must come from an API search result.
2. **NEVER fabricate DOIs or PMIDs.** If you cannot find a DOI/PMID, mark the reference as `[UNVERIFIED - NEEDS MANUAL CHECK]`.
3. **Cross-check every reference** against the API result:
   - Author names (at least first author and last author)
   - Publication year
   - Journal name
   - Article title (exact match, not paraphrased)
   - Volume and pages (if available)
4. **If any field does not match**, flag the specific mismatch.
5. **For DOI verification**, use WebFetch with `https://api.crossref.org/works/{DOI}` to confirm the DOI resolves correctly.

#### BibTeX Generation

For each verified reference, generate a BibTeX entry:

```bibtex
@article{FirstAuthorLastName_Year_ShortKey,
  author    = {Last1, First1 and Last2, First2 and Last3, First3},
  title     = {Full Title As Retrieved From Database},
  journal   = {Journal Name},
  year      = {2024},
  volume    = {310},
  number    = {2},
  pages     = {e234567},
  doi       = {10.1001/jama.2024.12345},
  pmid      = {12345678},
}
```

**BibTeX key convention**: `FirstAuthorLastName_Year_OneWord` (e.g., `Kim_2024_Validation`).

#### Output

1. Save BibTeX entries to the specified .bib file (append, do not overwrite).
2. Print a summary of all references with verification status:

```
Verified:    12 references (DOI confirmed)
Unverified:   1 reference [NEEDS MANUAL CHECK]
Total:       13 references
```

### Phase 4b: Zotero Library Integration

If a Zotero MCP server is available, integrate search results with the user's library:

1. **Add papers to Zotero**: Use `zotero_add_by_doi` for DOI-based import (auto-downloads OA PDFs).
2. **Organize into collections**: Use `zotero_manage_collections` to file into the relevant project collection.
3. **Check for duplicates**: Use `zotero_search_items` to avoid adding papers already in the library.
4. **Leverage annotations**: Use `zotero_get_annotations` to reference the user's prior reading notes.

> Requires Zotero Desktop running with MCP server. Skip this phase if unavailable.

### Phase 5: Full-Text Retrieval

After identifying relevant papers, retrieve full-text PDFs for detailed review.
This is especially important for meta-analyses where data extraction requires full text.

#### Phase 5a: Open Access Auto-Retrieval

Try sources in order of reliability:

1. **Unpaywall API** (highest quality OA links):
   ```python
   import os, requests
   email = os.environ.get("UNPAYWALL_EMAIL", "user@example.com")
   url = f"https://api.unpaywall.org/v2/{doi}?email={email}"
   r = requests.get(url).json()
   if r.get("best_oa_location", {}).get("url_for_pdf"):
       pdf_url = r["best_oa_location"]["url_for_pdf"]
   ```

2. **PubMed Central (PMC)**:
   - Convert PMID to PMCID via NCBI ID Converter
   - Download from PMC OA service: `https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{id}/pdf/`

3. **OpenAlex API** (additional OA discovery):
   ```python
   url = f"https://api.openalex.org/works/https://doi.org/{doi}"
   # Requires polite pool: add email in User-Agent header or mailto= param
   r = requests.get(url, headers={"User-Agent": f"MyApp/1.0 (mailto:{email})"}).json()
   oa_url = r.get("open_access", {}).get("oa_url")
   ```

4. **CrossRef landing page**: Follow `https://api.crossref.org/works/{doi}` → publisher link
   → scrape `<meta name="citation_pdf_url">` tag

#### Phase 5b: Alternative Sources

Some researchers use alternative access methods for paywalled content.
**Users are responsible for ensuring compliance with their institutional access policies.**

If an environment variable (e.g., `SCIHUB_BASE`) is set, the skill may use it as an
alternative PDF source. No specific URLs are provided here — users configure this themselves.

Other options:
- **Institutional proxy/VPN**: Access publisher sites through institutional EZproxy or VPN
- **Interlibrary loan (ILL)**: Request through library services for papers not otherwise available
- **Author contact**: Email corresponding authors for preprints

#### PDF Validation

Always validate downloaded files before use:

```python
def is_valid_pdf(filepath):
    """Check that a downloaded file is actually a PDF, not an HTML redirect."""
    import os
    if os.path.getsize(filepath) < 10240:  # < 10KB is likely a stub/redirect
        return False
    with open(filepath, 'rb') as f:
        header = f.read(5)
    return header == b'%PDF-'
```

Additional checks:
- Verify HTTP `Content-Type: application/pdf` header before saving
- Files under 10KB are almost always HTML login/redirect pages, not real PDFs
- Some publishers return CAPTCHA pages — these fail the `%PDF-` check

#### Rate Limiting

- Unpaywall: Polite pool (no hard limit with email parameter)
- OpenAlex: Include email in User-Agent for polite pool access
- NCBI/PMC: 3 requests/sec without API key, 10/sec with `NCBI_API_KEY`
- General: 2-second minimum interval between requests to any single host

### Phase 6: Gap Analysis

When called during manuscript writing (especially by `/write-paper` Phase 7):

1. **Read the manuscript** to extract all inline citations.
2. **Compare** cited references against the search results.
3. **Identify gaps**:
   - Key papers in the field that are not cited.
   - Outdated references when newer versions exist.
   - Missing methodological references (e.g., statistical methods, reporting guidelines).
4. **Report** findings to the user with specific suggestions.

---

## Specialized Search Modes

### Mode: Systematic Search

For systematic reviews or comprehensive literature sections:

1. Document the full search strategy (PRISMA-compliant).
2. Record: database, date of search, query string, number of results.
3. Track inclusion/exclusion at each screening step.
4. Output a PRISMA flow diagram data summary.

### Mode: Quick Cite

For quickly finding a single reference the user describes:

1. User says something like "that 2023 paper by Smith about AI in chest X-ray."
2. Search PubMed and Semantic Scholar with the described details.
3. Present top 3 candidates.
4. User confirms which one.
5. Generate BibTeX entry.

### Mode: Related Papers

For expanding from a known paper:

1. User provides a PMID or DOI.
2. Use `find_related_articles` to get related papers.
3. Use Semantic Scholar for citation-based recommendations.
4. Present results ranked by relevance.

### Mode: Embase Browser Automation

Embase has no public API. Use Chrome browser automation (MCP) to search and export:

1. Navigate to `embase.com` — institutional SSO authenticates automatically.
   If cookie error (`login?error#`), clear Elsevier/Embase cookies and retry.
2. Go to **Advanced Search** tab.
3. Enter Embase-syntax query (Emtree `/exp` + `:ab,ti` field tags).
   Uncheck "Map to preferred term in Emtree" when using explicit `/exp` terms.
4. After results appear, use "Select number of items" dropdown → select total count.
5. Click **Export** (in Results section) → choose **CSV** format → check fields:
   Title, Author names, Source, Publication year, Publication type, DOI, Abstract,
   Language of article, Medline PMID.
6. Click Export → Download tab opens → click Download.
7. CSV is in **row format** (records separated by blank rows) — parse with:
   ```python
   # Each record = consecutive rows until blank row
   # Row format: [FIELD_NAME, value1, value2, ...]
   # AUTHOR NAMES row has multiple values (one per author)
   ```

**PubMed → Embase query translation:**
- MeSH `[Mesh]` → Emtree `/exp`
- `[tiab]` → `:ab,ti`
- `[Title/Abstract]` → `:ab,ti`
- Boolean operators stay the same (AND, OR)
- Phrase search: use single quotes in Embase (`'artificial ascites'`)

---

## Error Handling

- If a search returns 0 results, broaden the query (remove one concept or use broader MeSH terms) and retry.
- **CrossRef HTTP errors (token-saving rules):**
  - **403 (rate-limited):** Do NOT retry. Skip CrossRef silently → verify via PubMed title search instead.
  - **303 (redirect):** Follow the redirect if possible. If not, skip CrossRef → PubMed fallback.
  - **Any repeated failure:** After the first CrossRef 403/303 in a session, assume CrossRef is
    rate-limiting and skip CrossRef for ALL remaining references. Go directly to PubMed title
    verification. This avoids N×retry token waste.
  - **Never print raw error messages** like "Request failed with status code 403." Collect
    failures silently and report a single summary line at the end:
    `CrossRef unavailable for {N} references (rate-limited). Verified via PubMed instead.`
- If a DOI does not resolve via CrossRef (after applying the rules above), try searching PubMed by title to confirm the reference exists.
- If the user provides a reference that cannot be verified by any method, clearly state: "This reference could not be verified. Please check manually before submission."
- Never silently include an unverified reference.

## What This Skill Does NOT Do

- Does not download from paywalled journals without user-provided credentials or institutional access.
- Does not assess the quality of evidence (use `/analyze-stats` or `/check-reporting` for that).
- Does not write the literature review text (use `/write-paper` for that).
- Does not fabricate any part of a citation.
