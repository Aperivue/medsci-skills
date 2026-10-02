---
name: search-lit
description: Use when finding papers or building a reference list. Searches PubMed, Semantic Scholar and bioRxiv/medRxiv, includes only references verified through an API, and generates BibTeX. Auditing an existing reference list is /verify-refs.
metadata:
  triggers: "literature search, find papers, citation, references, bibliography, PubMed search, related work"
---

# Literature Search Skill

Every reference you produce must come from a live database result — never generate a citation from
memory alone, because a recalled citation can look real and not exist.

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

If any `mcp__claude_ai_PubMed__*` call returns an error containing "terminated", "not found",
"not available", or "not connected", switch ALL subsequent PubMed calls in this session to the
bundled E-utilities scripts. Do not retry MCP after a disconnect — it will not recover within the
same conversation.

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

The script sleeps 350 ms between calls (NCBI allows 3 requests/s without an API key, 10/s with
`NCBI_API_KEY`); keep batch calls sequential.

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

1. Get the research topic, question, or manuscript section that needs references.
2. Build the query from the key concepts (Population, Intervention/Exposure, Comparison, Outcome),
   with MeSH terms for PubMed: `(concept1 OR synonym1) AND (concept2 OR synonym2)`.
3. Set scope: date range (default: last 10 years unless the user specifies), article types, and
   language (default: English).
4. Present the Boolean query, databases, and filters to the user.

**Gate:** Wait for user approval before running searches.

### Phase 2: Execute Search

1. Search PubMed (`search_articles`, Boolean query), Semantic Scholar (`semanticSearch`, natural
   language query), and bioRxiv/medRxiv (`search_preprints`) when preprints are relevant.
2. Deduplicate across databases by DOI or title similarity.
3. Present the results in this table, and write the same rows to `references/search_results.tsv`:

```
| # | Title | Authors (first + last) | Year | Journal | PMID/DOI | Relevance |
|---|-------|----------------------|------|---------|----------|-----------|
| 1 | ...   | Kim J, ... Lee S     | 2024 | Radiology | 12345678 | High      |
```

4. Ask the user to select which papers to include.

#### Record what the source said existed, not only what you downloaded

A wrong haul raises no error, and a PRISMA flow built on a wrong number is fiction that nothing
downstream contradicts. Check both of these:

- **A count that equals a page cap exactly.** Every source reports a total:
  `esearchresult.count`, `opensearch:totalResults`, `meta.count`. **Record `api_total` beside
  `downloaded`, and fail loudly when `downloaded < api_total`, or when `downloaded` equals a page or
  loop cap exactly** (e.g. a loop's own `if start >= 2000: break` reporting 2,000 records). Print
  `TRUNCATED` and refuse to write the search record.
- **A boolean that was never applied.** OpenAlex's `search=` is a relevance-ranked free-text
  parameter that **silently ignores AND/OR**; `filter=title_and_abstract.search:` honours them. Run
  the query once more with one mandatory clause negated. **If the hit count does not drop, the
  boolean is being ignored** — the engine is ranking, not filtering.

PubMed via E-utilities is the one place where the naive pattern is safe. Everywhere else, do both.

#### A DOI in a screening row is not necessarily that row's DOI

When the pipeline **filled** a `doi` column (matched against Crossref by title similarity) rather
than receiving it with the record, a wrong match is a valid, resolvable DOI for a different paper.
Resolve it and read the title back before any decision rests on it:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_doi_record_match.py" --table 2_Screening/round3.tsv \
        --email <contact> --json qc/doi_record_match.json
```

`DOI_NOT_THIS_RECORD` is a DOI that resolves to another paper; `DOI_IS_CONTAINER` resolves to an
issue, supplement or proceedings rather than an article; `DOI_IS_UPDATE_NOTICE` resolves to a
correction, erratum or retraction notice (Crossref `update-to`) rather than to the article it
updates; `DOI_UNRESOLVED` is reported rather than dropped. This runs at screening, where a wrong DOI is still cheap; `/verify-refs` audits a finished
reference list.

### Phase 2.5: Citation Searching (Snowballing)

Optional; recommended for systematic reviews and thorough background work (PRISMA item 7,
"records identified through citation searching"). Expand a seed set along the citation graph with
the Semantic Scholar Graph API helper:

```bash
python3 "${CLAUDE_SKILL_DIR}/references/snowball.py" \
  --seed DOI:10.1000/synthetic.example,PMID:00000000 \
  --direction all \
  --pool references/library.bib \
  --out references/library.bib
```

- **Directions**: `backward` (references the seeds cite), `forward` (papers citing the seeds),
  `similar` (S2 recommendations), or `all` (default). Dedup is against the `--pool` and within the
  harvested set, by DOI and normalized title.
- **Trust flag**: candidates are written `verified=false` + `verified_by=semantic_scholar`. Run
  `/verify-refs` (or Phase 4 verification) on each before citing it.
- **Output contract**: appends to `references/library.bib` only; the script hard-refuses
  `manuscript/_src/refs.bib`.
- **PRISMA line**: the script prints `Records identified through citation searching (snowballing):
  N raw (backward=…, forward=…, similar=…); after dedup against existing pool: M new candidates.`
  Record M in the PRISMA flow's citation-searching box.
- **Incomplete runs**: when any seed/direction fetch fails, or the source says more records exist
  past `--limit` (a `next` page), the script prints a `FAILED` or `TRUNCATED` line per
  seed/direction, ends the PRISMA line with `INCOMPLETE`, and exits 1. Those counts are a lower
  bound. Do not record them; re-run (or raise `--limit`) until the run exits 0.

### Phase 3: Deep Read

For each selected paper, retrieve full metadata (`get_article_metadata` for PubMed, `get_preprint`
for bioRxiv) and extract the study design, sample size/dataset, key methods, primary findings (with
specific numbers), and the authors' stated limitations. For several papers, present a literature
matrix for review:

```
| Paper | Design | N | Key Finding | Limitation | Relevance to Our Study |
|-------|--------|---|-------------|------------|----------------------|
```

### Phase 4: Citation Management

#### Verification

1. **NEVER fabricate a DOI or PMID.** If you cannot find one, mark the reference
   `[UNVERIFIED - NEEDS MANUAL CHECK]`.
2. Cross-check every reference against the API result: first and last author, publication year,
   journal, article title (exact, not paraphrased), and volume/pages when available. Flag each
   field that does not match.
3. Confirm each DOI resolves with WebFetch `https://api.crossref.org/works/{DOI}` (on CrossRef
   errors, follow Error Handling).

#### BibTeX Generation

Generate an entry for every reference, verified or not, with an explicit `verified` flag:

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
  verified  = {true},
  verified_by = {pubmed+crossref},
  verified_on = {2026-04-24},
}
```

| `verified` (required on every entry) | Meaning |
|---|---|
| `true` | DOI or PMID confirmed via PubMed/CrossRef; title, authors, year all match |
| `false` | Parsed from text, but the API lookup failed or returned a mismatch; the manuscript MUST show `[UNVERIFIED - NEEDS MANUAL CHECK]` |
| `manual` | User explicitly added it despite the lookup failure; still unverified |

`verified_by` lists the confirming sources (`pubmed`, `crossref`, `semantic_scholar`, or a
combination); `verified_on` is the ISO date of the most recent successful verification. No
downstream script reads these fields — `/verify-refs` re-checks every entry — so they record trust
rather than grant it.

**BibTeX key convention**: `FirstAuthorLastName_Year_OneWord` (e.g., `Kim_2024_Validation`). The key
is provisional: Better BibTeX assigns the citable key when `/lit-sync` imports the entry into Zotero.

#### Output

1. Append the entries to `references/library.bib` (do not overwrite) — the candidate pool
   `/lit-sync` imports into Zotero. NEVER write to `manuscript/_src/refs.bib`, because `/lit-sync`
   (via Better BibTeX) is its sole writer.
2. Print a summary with verification status:

```
Verified:    12 references (verified=true)
Unverified:   1 reference  (verified=false) [NEEDS MANUAL CHECK]
Total:       13 references
```

### Phase 4b: Zotero Library Integration

Importing into Zotero belongs to `/lit-sync`, which owns Zotero writes and
`references/zotero_collection.json`: hand it `references/library.bib`. If a Zotero MCP server is
connected, you may read from it here — `zotero_search_items` (by DOI) to mark candidates already in
the library, `zotero_get_annotations` to reference the user's prior reading notes.

### Phase 5: Full-Text Retrieval

Delegate to `/fulltext-retrieval`, the single home of the open-access cascade; do **not**
re-implement OA fetching here. Pass the verified candidate DOIs from `references/library.bib`:

```bash
ENGINE="${CLAUDE_SKILL_DIR}/../fulltext-retrieval/fetch_oa.py"
# extract DOI + Title (and PMID/FirstAuthor when available) → worklist.tsv
python3 "$ENGINE" worklist.tsv -o pdfs/ -e <contact-email> --report pdfs/retrieval_report.json
```

Put the verified bibliographic title in the worklist rather than a DOI-only list. Keep
`source_identity` and `file_sha256` from the retrieval report with the record. Download success and
title agreement alone do not verify the PDF: inspect conflicts, unresolved/unavailable evidence, and
files whose hashes have changed before citing them. Missing identity fields in older reports mean
unassessed; even `consistent` is advisory front-matter corroboration, not verification of the
paper's claims.

For Zotero-resident PDFs and proxy-aware retrieval, use `/lit-sync` Phase 2.7. For DOIs in
`pdfs/manual_needed.txt`, use only institutional access (your library's own subscriptions, proxy or
VPN), interlibrary loan, or the corresponding author. Never bypass paywalls or publisher access
controls, and do not configure unauthorized PDF mirrors.

### Phase 6: Gap Analysis

When called during manuscript writing, extract the manuscript's inline citations, compare them with
the search results, and report specific gaps: key papers not cited, outdated references with newer
versions, and missing methodological references (statistical methods, reporting guidelines).

---

## Specialized Search Modes

### Mode: Manuscript Paper Reference Pool

Supplies a manuscript's reference pool — typically invoked by `/write-paper` Step 7.3c (or
`/self-review` Phase 2.5c-2) when the reference-adequacy gate finds the draft under target or a
named method uncited; usable directly for an original-research bibliography.

For an original-research article, return **25–40** verified candidates, not the ~10 a quick search
settles on. If the field is genuinely sparse, say so explicitly rather than returning a thin list
silently. Respect a narrower journal reference cap or user scope when one is given.

Cover **six candidate categories**:

1. **Background / disease burden / clinical context** — why the question matters.
2. **Gap-defining prior studies** — the work the manuscript extends or contradicts.
3. **Comparator / comparable-design cohorts** — studies the Results will be measured against.
4. **Methods / statistical canonical sources** — the originating reference for every named method,
   model, score, equation, or diagnostic criterion (e.g. competing-risk model, multiple
   imputation, E-value, eGFR equation, concordance statistic). This category clears Methods
   named-method gaps.
5. **Reporting-guideline sources** — STROBE, TRIPOD(+AI), CONSORT, PRISMA(-DTA), STARD, etc.
6. **Interpretation / mechanism / limitation support** — grounds Discussion claims.

For each candidate, report **PMID/DOI**, **verification status**, **candidate category**, the
**target manuscript section**, and a one-line **why it is needed**. Entries go through Phase 4 into
`references/library.bib` only. This mode produces candidates: the user decides inclusion, and it
does not insert references into the manuscript bib.

### Mode: Crowding Check

Run **before a study is designed**. A background search ("what has been written about this topic")
leaves the trap open; ask four narrower questions instead:

| Ask of | Verdict |
|---|---|
| the **research question** | taken / partly taken / open |
| the **sampling frame** (what population, which records, which years) | taken / partly taken / open |
| the **measurement axis** (what is being coded or measured, and at what granularity) | taken / partly taken / open |
| the **target journal** | already published there / adjacent / open |

Give each its own verdict: a design can be original on one axis and fully occupied on another, and
collapsing the four into one answer hides that. The journal row is not vanity: a design once matched
an existing paper on frame, coding axis **and** journal — its own first choice. Most of the time
this mode **narrows a claim rather than ending a project** (e.g. from "nobody has looked at this" to
"nobody has decomposed it by provenance"), and the narrowed claim survives review.

Search the way a competitor would: the exact frame, the exact measure, and the journal's own site,
not only the topic. Report the four verdicts and the papers behind each, then let the user decide.

### Mode: Systematic Search

For systematic reviews or comprehensive literature sections:

1. Document the full search strategy (PRISMA-compliant).
2. Record: database, date of search, query string, number of results.
3. Track inclusion/exclusion at each screening step.
4. Output a PRISMA flow diagram data summary.

### Mode: Quick Cite

For a single reference the user describes ("that 2023 paper by Smith about AI in chest X-ray"):
search PubMed and Semantic Scholar with the details, present the top 3 candidates, and generate the
BibTeX entry for the one the user confirms.

### Mode: Related Papers

From a PMID or DOI, get related papers with `find_related_articles` plus Semantic Scholar
citation-based recommendations, ranked by relevance. For a structured, dedup-aware,
PRISMA-countable expansion (backward + forward + similar), use **Phase 2.5: Citation Searching**
with `references/snowball.py` instead.

### Mode: Embase Browser Automation

Embase has no public API. Read `${CLAUDE_SKILL_DIR}/references/embase_browser.md` when the search
must include Embase — it has the Chrome-automation export steps, the CSV row format, and the
PubMed → Embase query translation.

---

## Error Handling

- If a search returns 0 results, broaden the query (remove one concept or use broader MeSH terms)
  and retry.
- **CrossRef HTTP errors (token-saving rules):**
  - **403 (rate-limited):** Do NOT retry. Skip CrossRef → verify via PubMed title search instead.
  - **303 (redirect):** Follow the redirect if possible. If not, skip CrossRef → PubMed fallback.
  - After the first CrossRef 403/303 in a session, skip CrossRef for ALL remaining references and
    go directly to PubMed title verification, to avoid N×retry token waste.
  - Do not print raw error messages ("Request failed with status code 403."). Report one summary
    line at the end: `CrossRef unavailable for {N} references (rate-limited). Verified via PubMed instead.`
- If a DOI does not resolve via CrossRef (after the rules above), search PubMed by title to confirm
  the reference exists.
- If a reference cannot be verified by any method, state: "This reference could not be verified.
  Please check manually before submission." Never silently include an unverified reference.

## Known limits

- `check_doi_record_match.py` compares titles at a similarity threshold and reads structured
  Crossref fields (`type`, `update-to`). A study protocol, or part 2 of a multi-part paper, whose
  title differs from the row's by a word or a number is not separated from the paper the row
  describes; no structured field marks it. Treat a silent run as "no mismatch detected", not as
  proof that every DOI is right.
