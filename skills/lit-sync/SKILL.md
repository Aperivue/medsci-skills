---
name: lit-sync
description: Use when references (a .bib from /search-lit, a DOI/PMID list or a PDF folder) should land in Zotero and keep the manuscript refs.bib current. Adds items without duplicates, files them into the project collection and sets up the Better BibTeX auto-export. Obsidian notes are /obsidian-paper-vault.
metadata:
  triggers: "lit-sync, 문헌 동기화, 레퍼런스 정리, lit sync, Zotero 동기화, Zotero에 등록, PDF 폴더 Zotero, reference sync, refs.bib 갱신"
---

# Literature Sync: Zotero + refs.bib

Takes the `.bib` output of `/search-lit` (or any user-specified .bib file, a DOI/PMID list, or a
folder of PDFs), adds the papers to the Zotero library without duplicates, files them into the
project collection, and keeps `manuscript/_src/refs.bib` current through Better BibTeX.

This skill writes **no Obsidian notes**. Literature and concept notes are `/obsidian-paper-vault`,
which can start from the same collection or `refs.bib`. Keeping one writer per note type means one
template and one concept-extraction procedure, and no library sync that leaves a pile of empty
stub notes behind.

## Prerequisites

- **Project owner only.** Collaborators consume the committed `manuscript/_src/refs.bib` snapshot
  read-only. If the current user is a collaborator (no Zotero access per `SSOT.yaml`
  `reference_manager.required_for`), abort with instructions to flag `[@NEW:topic]` placeholders in
  the manuscript and notify the owner.
- Zotero desktop 7 or later + Better BibTeX plugin, with Better BibTeX "Keep updated" auto-export
  configured to `<project>/manuscript/_src/refs.bib`. Writing through Zotero's local API (no web
  API key, no cloud storage) needs Zotero 10 or later.
- Zotero MCP server, with Zotero running. Tool names change between server versions; this skill
  names the function and `${CLAUDE_SKILL_DIR}/references/zotero_mcp_tools.md` maps it to the
  current name. If Zotero cannot be reached, Phase 2 stops and asks (see Phase 2).

## Artifact Contract

`/lit-sync` is the **sole writer** of `manuscript/_src/refs.bib` (via the Better BibTeX auto-export
trigger), `references/zotero_collection.json`, and `references/fulltext_retrieval.json` (Phase 2.7).
**NEVER write `refs.bib` directly** — not even to compensate for a missing Zotero connection —
because only Better BibTeX's export keeps it in step with the library; if auto-export is broken, fix
the Zotero setup. Direct hand edits to `refs.bib` are drift — revert on sight.

---

## Phase 1: Parse BibTeX

Parse the user-specified `.bib` file, or the `references/library.bib` just produced by
`/search-lit`, with regex. Extract per entry: citekey, doi, pmid, title, authors (first + last
minimum), journal, year, and volume/number/pages if present. Log any parse failures and skip those
entries. All bibliographic data in later phases comes from these entries or from API responses.

A parsed citekey is not yet a library key: `/search-lit` candidate keys (`Kim_2024_Validation`) are
provisional, and Better BibTeX mints the real key when Phase 2 adds the item. Never compose a key;
Step 3.2 §Citekey provenance says where the note's key comes from.

---

## Phase 2: Zotero Sync

The Zotero MCP server must be connected. When it talks to Zotero's local API (no web API key
configured), the Zotero app must also be open, because every call fails while the app is closed.
A server set up with a web API key can still work with the app closed. Phase 2.5 needs the app
either way. If a call fails, do not go on without Zotero on your own. A silent skip is how a library can stop receiving papers for weeks without
anyone noticing. Stop and tell the user:

> Zotero is not reachable (`<the error>`). Open Zotero (and reconnect the Zotero MCP server if it
> is disconnected), then tell me to retry.

Retry when they answer. Only if the user says to go on without Zotero, write the Step 2.3 file with
`status: "pending"`, a `reason`, and a `pending` list of the entries not added (citekey, doi, pmid,
title), put the pending count in the final summary, skip Phase 2.5 (Step 2.5.3 JSON:
`refs_bib_refreshed: false`, `reason: "zotero_unreachable"`), and stop. Step 2.2 of the next
`/lit-sync` run picks the list up.

### Step 2.1: Determine project collection

Identify the project from the current working directory or an explicit user override. Reuse a
recorded collection key; otherwise check existing Zotero collections for the project and, if none
exists, create one (*create collection*, see `references/zotero_mcp_tools.md`). Record the collection key, and report it to the
user when a new collection is created.

### Step 2.2: Dedupe + add

For each entry, plus any entries left in the `pending` list of an earlier
`references/zotero_collection.json` (Phase 2 opening; drop each from the list once it is added or
found):

1. *Search items* by DOI, then by title — if already present, file the existing item into the
   project collection (*file into collection*) and count it as skipped. Search first even where the
   server dedupes on add: its match is by DOI/URL, so a title-only entry or an item stored without
   its DOI would be created twice.
2. Otherwise *add item* by DOI. With only a PMID, resolve it to a DOI first (§PMID batch import
   below) and add by DOI; if PubMed has no DOI for it, add by PMID as the identifier
   (`source_type: "pmid"`, a journal article from PubMed's record) and mark the entry
   `no_doi: true`. **Never add a PubMed URL**: a URL becomes a bare webpage item that later DOI
   lookups do not match. Pass the project collection in the add call. An entry with neither DOI
   nor PMID is not added: count it as failed and ask the user to add it manually.
   - The add call's attach mode governs the **OA child-PDF attempt at add time** (link the PDF
     URL, import a copy, or none). Accepted values are server-version-specific: check the
     connected server's tool description. To attach a local PDF to an item added here, use
     *attach file* with that item's key; *add item* with a file path creates a new parent item
     and would duplicate it.
3. Confirm the item is in the project collection (*file into collection* if the add call did not
   place it).

### Step 2.3: Result report

```
Zotero Sync:
  Added:     8 papers (new)
  Skipped:   3 papers (already in library)
  Failed:    1 paper (no DOI/PMID)
  Collection: RFA-Meta (TZQEP4NH)
```

Always write `references/zotero_collection.json` in the project workspace:

```json
{
  "schema_version": 1,
  "status": "synced",
  "collection": "RFA-Meta",
  "collection_key": "TZQEP4NH",
  "added": 8,
  "skipped": 3,
  "failed": 1
}
```

If the user chose to go on without Zotero (Phase 2 opening), write the same file with
`status: "pending"`, a human-readable `reason` and the `pending` entry list.

---

## Phase 2.5: refs.bib snapshot refresh

Better BibTeX "Keep updated" auto-export normally refreshes `manuscript/_src/refs.bib` within
seconds of a Zotero change. This phase **verifies** the snapshot actually updated before downstream
skills consume it.

### Step 2.5.1: Resolve path

Read `SSOT.yaml` → `truth.refs_bib`. Default: `manuscript/_src/refs.bib`. If absent (legacy project), fall back to `manuscript/_src/refs.bib` and emit a WARN recommending SSOT migration.

### Step 2.5.1b: Precondition assertion (early-exit, do NOT poll)

Before entering the 10s polling loop in Step 2.5.2, verify both preconditions. If **either** fails, abort Phase 2.5 with setup instructions instead of waiting for a timeout that will never resolve.

1. **Better BibTeX is answering.** Probe the running plugin, not a file on disk:

   ```bash
   curl -s -m 5 -o /dev/null -w "%{http_code}" \
     http://127.0.0.1:23119/better-bibtex/json-rpc    # expect 200
   ```

   A non-200 means Zotero is closed or BBT has not finished starting. Retry once after Zotero's
   window is up; BBT registers its endpoint a few seconds after the app does.

   ⚠️ **Do not gate on `~/Zotero/better-bibtex/read-only.json`.** Current BBT releases keep
   auto-export registrations in their own store, so that file is routinely `[]` on a healthy
   install; treating it as "not configured" skips this phase on working setups, which is how a
   stale `refs.bib` and an invented citekey reach a manuscript.

   On failure print:

   > Phase 2.5 skipped: Better BibTeX did not answer on `127.0.0.1:23119` (HTTP `<code>`). Open Zotero, wait for it to finish loading, then re-run `/lit-sync`.

2. **Target refs.bib exists.** The resolved `truth.refs_bib` path from Step 2.5.1 must exist on disk (even empty is OK — BBT will overwrite). On failure print:

   > Phase 2.5 skipped: target snapshot `<path>` not found.

   Then offer to register the auto-export for the user (Step 2.5.1c) instead of only pointing at
   the menu.

In either early-exit, set `refs_bib_refreshed: false` + `reason: "precondition:<which>"` in the
Step 2.5.3 JSON, tell the user, and return control to the caller. Nothing downstream enforces this
flag, so telling the user is what stands between a stale `refs.bib` and a manuscript.

### Step 2.5.1c: Register the auto-export (asks first)

When the target `refs.bib` is missing, or it does not refresh after a library change, offer to
register the Better BibTeX auto-export through its JSON-RPC `autoexport.add`. Show the user the
collection path, the translator and the target path, and call it only after they agree: Better
BibTeX has no call that lists or removes an auto-export, so a wrong registration has to be removed
by hand. Read `${CLAUDE_SKILL_DIR}/references/bbt_autoexport.md` first: it has the call, how to
confirm the file is written, the versions it was tried on, and the manual fallback.

### Step 2.5.2: Verify refresh

After Phase 2 adds items:

1. Capture `stat -f "%m" manuscript/_src/refs.bib` before Zotero writes.
2. Wait up to 10s (Better BibTeX debounce). Poll mtime.
3. If mtime unchanged after 10s:
   - Prompt user to check Zotero is running and BBT export is "Keep updated".
   - If BBT auto-export path is wrong, print the expected path (`<project>/manuscript/_src/refs.bib`).
   - As last resort, offer manual export: `File → Export Library → Better BibTeX → target path`.
4. Once mtime advances, grep for the newly added citekeys. All must be present; if any is missing, report as failure (do NOT fabricate entries).

### Step 2.5.3: Record in zotero_collection.json

Append to the JSON written in Step 2.3:

```json
{
  "refs_bib_path": "manuscript/_src/refs.bib",
  "refs_bib_mtime": "2026-04-24T14:32:11Z",
  "refs_bib_refreshed": true,
  "citekeys_verified": ["smithDeepLearningRadiology2024", "..."]
}
```

If refresh failed, set `refs_bib_refreshed: false` and include `reason`.

---

## Phase 2.7: Fulltext Retrieval (opt-in, owner-only)

**Run only when the user asks for full text** (e.g. "download the PDFs", "fetch full
text", or a worklist supplied with that intent). Default `/lit-sync` stays metadata-only
and network-light — do not auto-run this phase. Runs after items are in Zotero (Phase 2)
and the snapshot is verified (Phase 2.5).

Offer both routes below and reconcile them in one report. Retrieve full text only through them:
never automate authenticated browser sessions, never bypass paywalls or access controls, and never
hard-code institutional proxies, credentials, or hosts into this skill. Route what neither reaches
to institutional access, interlibrary loan, or author contact.

### Route A — disk OA PDFs (for downstream skills)

Delegate to the `/fulltext-retrieval` engine (do **not** re-implement the OA cascade or
import its code; invoke it by path):

```bash
ENGINE="${CLAUDE_SKILL_DIR}/../fulltext-retrieval/fetch_oa.py"
python3 "$ENGINE" <worklist> -o pdfs/ -e <contact-email> --report pdfs/retrieval_report.json
```

`<worklist>` is the DOI/PMID(/Title) list — the Phase-1 `.bib` DOIs, a worklist supplied in
Standalone Modes, or the project collection's DOIs. Output: `pdfs/*.pdf` for `/meta-analysis` and
`pdf_to_md.py`, plus `pdfs/retrieval_report.json` (schema 2: retrieval `status`/`source`,
`source_identity`, and `file_sha256`). Keep the distinction between having a file and assessing its
identity.

### Route B — in-library PDFs (Zotero-native, higher yield, proxy-aware)

Emit `${CLAUDE_SKILL_DIR}/../fulltext-retrieval/references/find_available_pdf.js`
for the user to paste into Zotero (*Tools → Developer → Run JavaScript*) with the project
collection selected. It triggers Zotero's own `addAvailablePDF`/`addAvailablePDFs`, which
reuse the **user's** OpenURL resolver / institutional proxy — so it typically retrieves more
than OA-only, while **no credentials or institutional identifiers enter this skill**. The
no-code equivalent is right-click → "Find Available PDF". Record its `{attached, missing}` summary
from the printed JSON.

### Report

Merge Route A's `pdfs/retrieval_report.json` (and the user-reported Route B summary) into
`references/fulltext_retrieval.json`, and append a short `fulltext` counts block to
`references/zotero_collection.json`. Read `${CLAUDE_SKILL_DIR}/references/fulltext_report.md`
before writing them — it has the schema and the identity-evidence rules (a retrieved file is not
a verified paper; a `consistent` status is advisory; unassessed items go to
`identity_review_needed`).

---

## Phase 3: Hand off — notes and citekey audit

`/lit-sync` ends here: its outputs are the Zotero items, `references/zotero_collection.json` and a
refreshed `refs.bib`. If the user wants Obsidian notes for these papers, hand the project collection
(or `refs.bib`) to `/obsidian-paper-vault`. Notes are written there, from each paper's text, only
when asked.

### Citekey audit (vault ↔ library)

Notes that carry a citekey (written by `/obsidian-paper-vault`, the Zotero Integration plugin, or
by hand) claim that Zotero has an entry with that key. `[@key]`, `[[key]]` and `{{citekey}}.md` all
depend on it, and a key that resolves to nothing still looks correct. On request, or before a
manuscript build that cites from the vault, run:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_citekey_provenance.py" --vault "$VAULT" --bib "$REFS_BIB"
```

`INVENTED` means the note's key is absent but its DOI resolves to a real key. `MISMATCH` means the
key is real but the note's DOI is the library's DOI for another key, so it cites another paper;
rename to the suggested key (known limit: a note DOI spelled differently from the library's, e.g.
quoted or braced, never raises it). `UNPARSED` means a literature note's frontmatter never closes,
so its key was not read. With `--strict` these three exit 1, and a scan that finds no literature
note exits 2. Match notes to papers by DOI, never by key (`AMBIGUOUS`, `UNUSABLE`, `NO_IDENTIFIER`:
see the script's `--help`), and search the full library (`--live`) before importing anything it
reports missing. A key is read from Better BibTeX (`refs.bib`, or `item.search` over json-rpc —
see `${CLAUDE_SKILL_DIR}/references/bbt_lookup.md`), never composed.

---

## Standalone Modes

This skill can run without a fresh .bib file.

### References tidy
On a "tidy this project's references" request, locate `.bib` files inside the workspace and run
Phase 1–2.5.

### Zotero sync only
On a "sync Zotero" request, diff the Zotero collection against the `.bib` file and add whatever is
missing.

### PDF folder ingestion
When the user supplies a folder of PDFs (lecture, study or downloaded papers), add them to Zotero
with each PDF stored as the item's attachment. Nothing is added before the user has seen a dry-run
list, because a PDF's first-page DOI can belong to another paper (a journal spread, a supplement,
an advertisement page). Read `${CLAUDE_SKILL_DIR}/references/pdf_folder_ingest.md` for the steps:
a `/fulltext-retrieval` report's `consistent` rows are attached to their items directly; every
other PDF goes through the dry-run list first.

### PMID-list ingestion (no .bib)
When the user supplies a list of PMIDs (e.g., from a HANDOFF or a colleague), resolve PMIDs to DOIs
via PubMed esummary first, then enter Phase 2 with the DOIs:

```bash
PMIDS="12345,67890,..."
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=${PMIDS}&retmode=json" \
  | jq -r '.result | to_entries[] | select(.key != "uids") | "\(.value.uid)\t\(.value.elocationid)\t\(.value.title)"'
```

For items already in the library (found by the Step 2.2 search), *file* them into the project
collection **without re-adding**. Record both `added` and `existing` items in
`references/zotero_collection.json`. If a PMID has no DOI in PubMed (older or non-indexed papers),
add it by PMID (`source_type: "pmid"`), never by its PubMed URL, and mark the entry
`no_doi: true`.

### Worklist ingestion (DOI/PMID/Title; no .bib)
When the user supplies a worklist file (a `.tsv`/`.csv`/`.md` table with a `DOI` column,
optional `PMID`/`Title`, or a plain DOI-per-line list — e.g. an SR include set), enter
Phase 2 directly from it: resolve any PMID-only rows to DOIs (esummary above), then run the
search-first dedupe + add loop. The same worklist file feeds Phase 2.7 Route A
(`fetch_oa.py` reads `.tsv`/`.csv`/`.md`/plain natively), so no reformatting is needed.
