# Research connectors

The external research APIs MedSci Skills calls, what uses them, and — importantly —
**what you have to set up (almost nothing).** This is the clinical-manuscript analogue of a
curated connector registry: it is intentionally small, keyless where possible, and limited
to **metadata and legitimate open-access** sources. It never scrapes paywalled publisher
full text.

## What actually gets called

Every connector below is a **free, public API — no account, no API key** for the core
workflow. The only per-user input is a **contact email** (etiquette for the OA services,
not a credential) and, optionally, authorising the domains so your agent stops asking on
each fetch.

| Connector | Endpoint | Purpose | Used by | Auth |
|---|---|---|---|---|
| **PubMed / NCBI E-utilities** | `eutils.ncbi.nlm.nih.gov` | authoritative author/title/PMID verification (esummary / efetch / esearch) | verify-refs, search-lit, manage-refs, lit-sync, meta-analysis | keyless (optional `NCBI_API_KEY` for higher rate limit) |
| **CrossRef** | `api.crossref.org` | DOI ↔ publisher metadata (title, authors, journal) | verify-refs, search-lit | keyless |
| **OpenAlex** | `api.openalex.org` | conference / non-DOI recovery, tertiary author cross-check | verify-refs | keyless |
| **Unpaywall** | `api.unpaywall.org` | legal open-access location for a DOI | fulltext-retrieval, lit-sync | keyless; **requires a contact `email`** |
| **Europe PMC** | `europepmc.org` | open-access full-text render | fulltext-retrieval | keyless |
| **PMC (NCBI)** | `www.ncbi.nlm.nih.gov/pmc` | open-access PDF via idconv / OA service | fulltext-retrieval | keyless |

**"Publisher connection" in practice** = CrossRef (the publisher DOI/metadata registry) +
Unpaywall / OpenAlex / PMC / Europe PMC (open-access full text). That is the entire,
legitimate publisher surface — there is no login to Elsevier/Springer/Wiley, and no
paywall bypass.

Separately, the `find-journal` / `write-paper` journal **profiles** cite publisher
homepages and author-guideline pages (thelancet.com, sciencedirect.com, …). Those are
**documentation references a human reads**, not live API connectors — the toolkit does not
call them programmatically.

## How you "enter an API" — three tiers

### Tier 0 — nothing (the default)

PubMed, CrossRef, OpenAlex, Europe PMC, and PMC are keyless. Install the skills and they
work. There is no key to paste, no account to create.

### Tier 1 — authorise the domains (so your agent stops asking every fetch)

MedSci Skills runs inside your coding agent (Claude Code / Codex / Cursor), so the analogue
of a hosted "Allowed domains" panel is your agent's **tool-permission allowlist**. Either
approve each fetch when prompted, or pre-authorise once. In Claude Code, add to
`.claude/settings.json` (or use the `/update-config` skill):

```jsonc
{
  "permissions": {
    "allow": [
      "WebFetch(domain:eutils.ncbi.nlm.nih.gov)",
      "WebFetch(domain:api.crossref.org)",
      "WebFetch(domain:api.openalex.org)",
      "WebFetch(domain:api.unpaywall.org)",
      "WebFetch(domain:europepmc.org)",
      "WebFetch(domain:www.ncbi.nlm.nih.gov)",
      "Bash(curl:*)"
    ]
  }
}
```

That is the whole "input" for most users: paste this once. (Exact matcher syntax is
host-specific; the intent — allow these research domains — is the same across hosts.)

### Tier 2 — optional environment variables (never required)

Set these only if you want them; every one has a working default or fallback.

| Variable | Effect | Default if unset |
|---|---|---|
| `MEDSCI_CONTACT_EMAIL` | polite contact email sent to Unpaywall / PMC / NCBI (a courtesy, not a credential) | falls back to `fetch_oa.py --email`, then a generic UA |
| `NCBI_API_KEY` | raises the PubMed rate limit from 3 → 10 requests/s | keyless (3 req/s) |
| `GEMINI_API_KEY` | only for `make-figures` optional AI-image generation | AI images off (non-AI illustration is the default) |

`fulltext-retrieval` also accepts the contact email directly: `fetch_oa.py … --email you@lab.org`
(Unpaywall rejects `example.com`). If `--email` is omitted it falls back to
`MEDSCI_CONTACT_EMAIL`.

## Reference manager (separate mechanism)

Zotero is **not** one of the connectors above — it is a local reference manager reached
through an MCP server, configured with `ZOTERO_API_KEY` / `ZOTERO_LIBRARY_ID` in your MCP
settings, not through these research APIs. See
[`docs/setup/mcp-setup.md`](setup/mcp-setup.md).

## Boundaries (what is deliberately not a connector)

- **No paywalled-publisher full-text scraping.** `fulltext-retrieval` is open-access only
  (Unpaywall / OpenAlex / PMC / Europe PMC); it does not, and will not, bypass paywalls.
- **No institution-authenticated connectors** (EZproxy, licensed databases) are bundled —
  those stay on the user's own infrastructure.
- **No omics / cheminformatics databases** (UniProt, PDB, Ensembl, ChEMBL, …). That is the
  domain of a bench-science workbench; see
  [`competitive_positioning.md`](competitive_positioning.md).

---

*Part of [MedSci Skills](../README.md). Reference integrity policy lives in
[`docs/citations.md`](citations.md).*
