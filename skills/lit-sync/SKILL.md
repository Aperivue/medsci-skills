---
name: lit-sync
description: Use when references in a .bib file (often from /search-lit) should land in Zotero and Obsidian. Syncs them to the Zotero library, writes Obsidian literature notes and extracts cross-cutting concept notes once enough accumulate. A folder of PDFs is /obsidian-paper-vault.
triggers: lit-sync, 문헌 동기화, 레퍼런스 정리, 개념 노트 추출, lit sync, Zotero 동기화, reference sync, 참고문헌 옵시디언
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Literature Sync: Zotero + Obsidian Pipeline

Takes the `.bib` output of `/search-lit` (or any user-specified .bib file), synchronizes the
references into the Zotero library and Obsidian literature notes, and extracts cross-cutting
concept notes once enough literature notes accumulate.

## Prerequisites

- **Project owner only.** Collaborators consume the committed `manuscript/_src/refs.bib` snapshot
  read-only. If the current user is a collaborator (no Zotero access per `SSOT.yaml`
  `reference_manager.required_for`), abort with instructions to flag `[@NEW:topic]` placeholders in
  the manuscript and notify the owner.
- Zotero desktop 7.x + Better BibTeX plugin, with Better BibTeX "Keep updated" auto-export
  configured to `<project>/manuscript/_src/refs.bib`.
- Zotero MCP server (if not connected, skip Phase 2; auto-export still refreshes once Zotero is
  reopened).
- Obsidian CLI or direct file writing to the vault; vault path from the user's environment
  (e.g., `$OBSIDIAN_VAULT`).

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

If the Zotero MCP is not connected, skip this phase (still write the Step 2.3 file with
`status: "skipped"`) and proceed to Phase 3.

### Step 2.1: Determine project collection

Identify the project from the current working directory or an explicit user override. Reuse a
recorded collection key; otherwise check existing Zotero collections for the project and, if none
exists, create one with `zotero_create_collection`. Record the collection key, and report it to the
user when a new collection is created.

### Step 2.2: Dedupe + add

For each entry:

1. Use `zotero_search_items` to search by DOI or title — if already present, skip.
   This search-first step is what prevents duplicates; `zotero_add_by_doi` does **not**
   dedupe by itself (it fetches CrossRef and creates the item), so never skip the search.
2. Otherwise call `zotero_add_by_doi` (when a DOI is available) or `zotero_add_by_url` (the PubMed
   URL, when only a PMID is available). An entry with neither DOI nor PMID is not added: count it
   as failed and ask the user to add it manually.
   - `zotero_add_by_doi` accepts an `attach_mode` argument that governs the **OA child-PDF
     attach attempt at add time** (the installed server treats `linked_url` as "bookmark the
     PDF URL"; other values download/import). Exact accepted values are server-version-specific —
     verify against the connected server. Do **not** use `zotero_add_from_file` to attach a PDF to
     an item added here: it has no parent-item argument and would create a duplicate parent item.
3. Use `zotero_manage_collections` to place the item in the project collection.

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

If Zotero is unavailable, write the same file with `status: "skipped"` and a
human-readable `reason`.

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

   > Phase 2.5 skipped: target snapshot `<path>` not found. Configure BBT auto-export with "On Change" to the SSOT path, then re-run.

In either early-exit, set `refs_bib_refreshed: false` + `reason: "precondition:<which>"` in the
Step 2.5.3 JSON, tell the user, and return control to the caller. Nothing downstream enforces this
flag, so telling the user is what stands between a stale `refs.bib` and a manuscript.

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
and the snapshot is verified (Phase 2.5), before Obsidian notes (Phase 3).

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

## Phase 3: Obsidian Literature Notes

Detect the vault's existing layout before creating notes. If the vault already uses a folder
structure (including a Korean one), **honor it — never silently rename a user's folders**. For a new
or unclear vault, default to the English folders `Literature/` and `Concepts/` with the English
templates (Step 3.2, Step 4.3). For a Korean-structured vault, or a user who prefers Korean notes, use the Korean
folder layout and Korean-heading templates in
`${CLAUDE_SKILL_DIR}/references/locale/ko/note_templates.md` (and the vault's own hub-note names).

### Step 3.1: Check existing literature notes

```bash
# Default English layout; substitute the vault's existing folder if one is present
# (e.g. "02 연구/문헌/" for a Korean-structured vault — see references/locale/ko/note_templates.md).
ls "$VAULT/Literature/" | grep -v "📊" | wc -l
```

### Step 3.2: Create literature notes

For each .bib entry, create `Literature/{citekey}.md` (or the vault's existing literature folder).
**Skip if the file already exists — never overwrite**, because the user may have added highlights
or personal notes.

#### Citekey provenance — the note filename is a claim about the library

A note's filename and `citekey:` field assert that Zotero has an entry with that key. `[@key]` in a
manuscript, `[[key]]` between notes, and the Zotero Integration plugin's `{{citekey}}.md` all depend
on it, and a key that resolves to nothing still looks correct. So the key is **read, never
composed**:

1. Take it from the Better BibTeX-exported `refs.bib` entry, or ask Better BibTeX
   (`item.search` over json-rpc — see `${CLAUDE_SKILL_DIR}/references/bbt_lookup.md`).
2. If the paper is not in Zotero, **add it first** (`zotero_add_by_doi`) and let BBT mint
   the key. Phase 2 owns that step for a reason: a note written ahead of its library entry
   has no key to be right about.
3. If it cannot be added (no DOI, offline), write the note with `citekey: ""` and the tag
   `_needs-citekey`. An empty field is recoverable; an invented one is not, because nothing
   downstream can tell it apart from a real key.

Verify before finishing:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_citekey_provenance.py" --vault "$VAULT" --bib "$REFS_BIB"
```

`INVENTED` means the note's key is absent but its DOI resolves to a real key; fix it here. Match
notes to papers by DOI, never by key (`AMBIGUOUS`, `UNUSABLE`, `NO_IDENTIFIER`: see the script's
`--help`), and search the full library (`--live`) before importing anything it reports missing.

#### Template

```markdown
---
notetype: literature
citekey: "{citekey}"
title: "{title}"
authors: "{authors}"
journal: "{journal}"
year: {year}
doi: "{doi}"
pmid: "{pmid}"
created: "{today}"
tags:
  - type/literature
  - _unread
---

# {title}

## Bibliographic info
- **Authors**: {authors}
- **Journal**: {journal}{volume_issue_pages}
- **Year**: {year}
- **DOI**: [{doi}](https://doi.org/{doi})
{pmid_line}

## Key points (in my own words)

## My thoughts

## Related notes
- [[Research Hub]]
- [[Papers & Reviews]]
-
-
```

**Rules:**
- `notetype: literature` — compatible with the Zotero Integration template.
- `_unread` tag — change to `_read` later after the user reads the PDF in Zotero and adds highlights.
- Leave `## Key points` and `## My thoughts` blank — the user fills these in personally.
- `## Related notes` contains 2 hub links + 2 empty slots (reserved for later concept-note linking).
- If a PMID is available, add a PubMed link.

### Step 3.3: Result report

```
Obsidian Literature Notes:
  Created:   8 notes (new)
  Skipped:   3 notes (already exist)
  Location:  Literature/
  Total in vault: 12 literature notes
```

---

## Phase 4: Concept Extraction (conditional)

### Trigger condition

Run this phase only when there are **≥10** literature notes in the vault. If fewer exist, print a
status message like "N literature notes — concept extraction unlocks at ≥10" and stop.

### Step 4.1: Cross-cutting concept scan

Read all files under `Literature/*.md` (or the vault's existing literature folder), extract
keywords from each paper's title, journal, and tags and major concepts from the .bib entry titles,
and identify **concepts that co-occur across ≥3 literature notes**.

### Step 4.2: Filtering (5 exclusion rules)

Exclude from concept candidates: model names (GPT-4, Claude, etc.), dataset names (MedQA,
ImageNet, etc.), journal names, institution names, and generic technique names (too unspecific).
Whatever remains becomes a concept-note candidate.

### Step 4.3: Draft concept note

Create `Concepts/{concept name}.md` (or the vault's existing concept-note folder) from the
template in `${CLAUDE_SKILL_DIR}/references/concept_note_template.md` (Korean-structured vault:
the concept template in `references/locale/ko/note_templates.md`).

**Key rules:**
- **Never auto-fill `## Definition`** — keep the `> TODO` marker; the 2nd-layer note only becomes
  meaningful once the user writes the definition in their own words.
- `status` always starts at `🌱Seedling`.
- At least 4 wikilinks under `## Related notes` (vault convention).

### Step 4.4: Propose to the user

```
Concept-note candidates (≥3 papers cross-referenced):
  1. {Concept A} (4 papers)
  2. {Concept B} (3 papers)
  3. {Concept C} (5 papers)

Create? (all / selected / skip)
```

Auto-draft, but create only after user confirmation.

---

## Standalone Modes

This skill can run without a fresh .bib file.

### Concept extraction only
On an explicit concept-extraction request, scan existing `Literature/*.md` (or the vault's existing
literature folder) and run only Phase 4.

### References tidy
On a "tidy this project's references" request, locate `.bib` files inside the workspace and run
Phase 1–3.

### Zotero sync only
On a "sync Zotero" request, diff the Zotero collection against the `.bib` file and add whatever is
missing.

### PMID-list ingestion (no .bib)
When the user supplies a list of PMIDs (e.g., from a HANDOFF or a colleague), resolve PMIDs to DOIs
via PubMed esummary first, then enter Phase 2 with the DOIs:

```bash
PMIDS="12345,67890,..."
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=${PMIDS}&retmode=json" \
  | jq -r '.result | to_entries[] | select(.key != "uids") | "\(.value.uid)\t\(.value.elocationid)\t\(.value.title)"'
```

For items already in the library (found by the Step 2.2 search), use `zotero_manage_collections` to
attach them to the project collection **without re-adding** — re-adding by URL/PubMed-URL would
bypass the search dedup and create duplicates. Record both `added` and `existing` items in
`references/zotero_collection.json`. If a PMID has no DOI in PubMed (older or non-indexed papers),
fall back to `zotero_add_by_url` with the PubMed URL and mark the entry `no_doi: true`.

### Worklist ingestion (DOI/PMID/Title; no .bib)
When the user supplies a worklist file (a `.tsv`/`.csv`/`.md` table with a `DOI` column,
optional `PMID`/`Title`, or a plain DOI-per-line list — e.g. an SR include set), enter
Phase 2 directly from it: resolve any PMID-only rows to DOIs (esummary above), then run the
search-first dedupe + add loop. The same worklist file feeds Phase 2.7 Route A
(`fetch_oa.py` reads `.tsv`/`.csv`/`.md`/plain natively), so no reformatting is needed.
