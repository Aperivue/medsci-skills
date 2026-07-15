---
name: lit-sync
description: Sync research references from .bib files to Zotero library + Obsidian literature notes. Extract cross-cutting concept notes when enough literature accumulates. Works after /search-lit or standalone.
triggers: lit-sync, 문헌 동기화, 레퍼런스 정리, 개념 노트 추출, lit sync, Zotero 동기화, reference sync, 참고문헌 옵시디언
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Literature Sync: Zotero + Obsidian Pipeline

Takes the `.bib` output of `/search-lit` (or any user-specified .bib file) and
synchronizes the references into the Zotero library and Obsidian literature notes.
When enough literature notes accumulate, extracts cross-cutting concept notes.

## Communication Rules

- Communicate with the user in their preferred language.
- **Vault layout — honor what exists, default to English.** Before creating notes, detect the
  vault's existing layout: if the vault already uses a particular folder structure (including a
  Korean one such as `02 연구/문헌/` and `02 연구/개념노트/`), **honor it — never silently
  rename a user's folders**. For a new or unclear vault, default to the English folders
  `Literature/` and `Concepts/` with the English note templates below.
- A Korean opt-in variant (Korean folder layout + Korean-heading templates) lives in
  `references/locale/ko/note_templates.md` — use it when the vault is Korean-structured or the
  user prefers Korean notes.

## When to Use

- After `/search-lit` completes — sync the produced .bib into Zotero + Obsidian.
- Bulk-register references from an existing .bib into Zotero + Obsidian.
- Tidy the `references/` folder inside a project workspace.
- On explicit concept-extraction request → extract cross-cutting concepts from existing literature notes.

## Prerequisites

- **Project owner only** — `/lit-sync` is an owner-scoped operation per `docs/zotero_policy.md`. Collaborators consume the committed `manuscript/_src/refs.bib` snapshot read-only.
- Zotero desktop 7.x + Better BibTeX plugin installed.
- Better BibTeX "Keep updated" auto-export configured to `<project>/manuscript/_src/refs.bib` (owner setup checklist in `docs/zotero_policy.md` §Setup).
- Zotero MCP server available (skip the Zotero phase if not connected; auto-export refresh still fires once Zotero is reopened).
- Obsidian CLI or direct file writing to the Obsidian vault.
- Obsidian vault path: configured in user's environment (e.g., `$OBSIDIAN_VAULT`).

## Artifact Contract

Per `docs/artifact_contract.md`, `/lit-sync` is the **sole writer** of:

| Artifact | Writer | Readers |
|---|---|---|
| `manuscript/_src/refs.bib` | `/lit-sync` (via Better BibTeX auto-export trigger) | `/write-paper`, `/verify-refs`, `/manage-refs` |
| `references/zotero_collection.json` | `/lit-sync` | `/verify-refs`, `/sync-submission` |

Direct hand edits to `refs.bib` are drift — revert on sight.

## Pipeline Overview

```
.bib file (or /search-lit output)
    │
    ▼ Phase 1: Parse
    Extract DOI, PMID, title, authors, journal, year
    │
    ▼ Phase 2: Zotero Sync (owner)
    Dedupe → zotero_add_by_doi → place in collection → pin citekey
    │
    ▼ Phase 2.5: refs.bib snapshot refresh
    Trigger Better BibTeX auto-export → verify manuscript/_src/refs.bib mtime updated
    │
    ▼ Phase 2.7: Fulltext Retrieval (opt-in)
    Disk OA PDFs via /fulltext-retrieval + in-library via find_available_pdf.js → reconcile report
    │
    ▼ Phase 3: Obsidian Literature Notes
    Create Literature/{citekey}.md (empty note OK — fill later with highlights)
    │
    ▼ Phase 4: Concept Extraction (conditional)
    ≥10 literature notes → scan for cross-cutting concepts → propose concept notes
```

---

## Phase 1: Parse BibTeX

### Input

The user-specified .bib file path, or the .bib just produced by `/search-lit`.

### Process

```python
# Parse .bib entries with regex.
# Extract per entry:
#   - citekey (e.g., Kim_2024_Validation)
#   - doi
#   - pmid
#   - title
#   - authors (first + last minimum)
#   - journal
#   - year
#   - volume, number, pages (if present)
```

Log any parse failures and skip those entries.

---

## Phase 2: Zotero Sync

### Step 2.1: Determine project collection

Identify the project from the current working directory or from an explicit user
override. Reuse an existing collection key if one is recorded; otherwise create a
new collection.

**Collection mapping**: Check existing Zotero collections for the current project.
If no collection exists, create one with `zotero_create_collection`. Record the
collection key for future use.

### Step 2.2: Dedupe + add

For each entry:

1. Use `zotero_search_items` to search by DOI or title — if already present, skip.
   This search-first step is what prevents duplicates; `zotero_add_by_doi` does **not**
   dedupe by itself (it fetches CrossRef and creates the item), so never skip the search.
2. Otherwise call `zotero_add_by_doi` (when a DOI is available) or
   `zotero_add_by_url` (falling back to the PubMed URL when no DOI is available).
   - `zotero_add_by_doi` accepts an `attach_mode` argument that governs the **OA child-PDF
     attach attempt at add time** (the installed server treats `linked_url` as "bookmark the
     PDF URL"; other values download/import). Set it when you want a PDF attached during the
     add. Exact accepted values are server-version-specific — verify against the connected
     server. Do **not** use `zotero_add_from_file` to attach a PDF to an item added here: it
     has no parent-item argument and would create a duplicate parent item.
3. Use `zotero_manage_collections` to place the item in the project collection.

### Step 2.3: Result report

```
Zotero Sync:
  Added:     8 papers (new)
  Skipped:   3 papers (already in library)
  Failed:    1 paper (no DOI/PMID)
  Collection: RFA-Meta (TZQEP4NH)
```

If the Zotero MCP is not connected, skip this entire phase and proceed to Phase 3.

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

Better BibTeX "Keep updated" auto-export normally refreshes `manuscript/_src/refs.bib` within seconds of a Zotero change. This phase **verifies** the snapshot actually updated before downstream skills consume it.

### Step 2.5.1: Resolve path

Read `SSOT.yaml` → `truth.refs_bib`. Default: `manuscript/_src/refs.bib`. If absent (legacy project), fall back to `manuscript/_src/refs.bib` and emit a WARN recommending SSOT migration.

### Step 2.5.1b: Precondition assertion (early-exit, do NOT poll)

Before entering the 10s polling loop in Step 2.5.2, verify both preconditions. If **either** fails, abort Phase 2.5 with setup instructions instead of waiting for a timeout that will never resolve.

1. **BBT auto-export registered.** `~/Zotero/better-bibtex/read-only.json` must be a non-empty JSON list. Check with:

   ```bash
   python3 -c 'import json,sys,pathlib; p=pathlib.Path.home()/".zotero"/"zotero"/"Profiles"; \
     f=pathlib.Path.home()/"Zotero"/"better-bibtex"/"read-only.json"; \
     sys.exit(0 if f.exists() and json.loads(f.read_text() or "[]") else 1)'
   ```

   Or equivalent shell: `[ -s ~/Zotero/better-bibtex/read-only.json ] && [ "$(jq 'length' ~/Zotero/better-bibtex/read-only.json)" -gt 0 ]`.

   On failure print:

   > Phase 2.5 skipped: BBT auto-export not configured (`~/Zotero/better-bibtex/read-only.json` is empty or missing). Set up "Keep updated" auto-export per `docs/zotero_policy.md` §Setup, then re-run `/lit-sync`.

2. **Target refs.bib exists.** The resolved `truth.refs_bib` path from Step 2.5.1 must exist on disk (even empty is OK — BBT will overwrite). On failure print:

   > Phase 2.5 skipped: target snapshot `<path>` not found. Configure BBT auto-export with "On Change" to the SSOT path, then re-run.

In either early-exit, set `refs_bib_refreshed: false` + `reason: "precondition:<which>"` in the Step 2.5.3 JSON and return control to the caller. Record it and tell the user; nothing downstream enforces it. `verify_refs.py` has never read this flag, and the sentence that said it did was the only thing standing between a stale `refs.bib` and a manuscript.

### Step 2.5.2: Verify refresh

After Phase 2 adds items:

1. Capture `stat -f "%m" manuscript/_src/refs.bib` before Zotero writes.
2. Wait up to 10s (Better BibTeX debounce). Poll mtime.
3. If mtime unchanged after 10s:
   - Prompt user to check Zotero is running and BBT export is "Keep updated".
   - If BBT auto-export path is wrong, print the expected path (`<project>/manuscript/_src/refs.bib`) and refer to `docs/zotero_policy.md` §Setup.
   - As last resort, offer manual export: `File → Export Library → Better BibTeX → target path`.
4. Once mtime advances, grep for the newly added citekeys. All must be present; if any is missing, report as failure (do NOT fabricate entries).

### Step 2.5.3: Record in zotero_collection.json

Append to the JSON written in Step 2.3:

```json
{
  "refs_bib_path": "manuscript/_src/refs.bib",
  "refs_bib_mtime": "2026-04-24T14:32:11Z",
  "refs_bib_refreshed": true,
  "citekeys_verified": ["Kim_2024_Validation", "..."]
}
```

If refresh failed, set `refs_bib_refreshed: false` and include `reason`. The flag records whether the export ran. It is a note to the reader, not a gate.

---

## Phase 2.7: Fulltext Retrieval (opt-in, owner-only)

**Run only when the user asks for full text** (e.g. "download the PDFs", "fetch full
text", or a worklist supplied with that intent). Default `/lit-sync` stays metadata-only
and network-light — do not auto-run this phase. Runs after items are in Zotero (Phase 2)
and the snapshot is verified (Phase 2.5), before Obsidian notes (Phase 3).

There are two complementary retrieval routes; offer both and reconcile them in one report:

### Route A — disk OA PDFs (for downstream skills)

Delegate to the `/fulltext-retrieval` engine (do **not** re-implement the OA cascade or
import its code; invoke it by path). Resolve the engine as:

```bash
ENGINE="${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}/skills/fulltext-retrieval/fetch_oa.py"
python3 "$ENGINE" <worklist> -o pdfs/ -e <contact-email> --report pdfs/retrieval_report.json
```

`<worklist>` is the DOI/PMID(/Title) list — the Phase-1 `.bib` DOIs, the worklist supplied
in the standalone mode below, or the project collection's DOIs. Output: `pdfs/*.pdf` for
`/meta-analysis` and `pdf_to_md.py`, plus
`pdfs/retrieval_report.json` (per-DOI `status`/`source`/`title_match`).

### Route B — in-library PDFs (Zotero-native, higher yield, proxy-aware)

Emit `${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}/skills/fulltext-retrieval/references/find_available_pdf.js`
for the user to paste into Zotero (*Tools → Developer → Run JavaScript*) with the project
collection selected. It triggers Zotero's own `addAvailablePDF`/`addAvailablePDFs`, which
reuse the **user's** OpenURL resolver / institutional proxy — so it typically retrieves more
than OA-only, while **no credentials or institutional identifiers enter this skill**. The
no-code equivalent is right-click → "Find Available PDF". This route is user-initiated and
session-dependent; record its `{attached, missing}` summary from the printed JSON.

### Report

Merge Route A's `pdfs/retrieval_report.json` (and the user-reported Route B summary) into
`references/fulltext_retrieval.json` (owner of this file is `/lit-sync`):

```json
{
  "schema_version": 1,
  "retrieved_oa_disk": [{"doi": "...", "source": "unpaywall", "file": "...", "title_match": "match"}],
  "retrieved_zotero_native": [{"doi": "...", "via": "addAvailablePDF"}],
  "not_retrieved": [{"doi": "...", "journal": "..."}],
  "institutional_fallback": ["<DOIs needing institutional access / ILL / author contact>"],
  "title_mismatch_flagged": ["<DOIs whose downloaded PDF title did not match>"]
}
```

Also append a short `fulltext` block (counts) to `references/zotero_collection.json`.
`not_retrieved` DOIs are candidates for institutional access, interlibrary loan, or author
contact — never bypass paywalls or access controls from this skill.

---

## Phase 3: Obsidian Literature Notes

### Step 3.1: Check existing literature notes

```bash
# Default English layout; substitute the vault's existing folder if one is present
# (e.g. "02 연구/문헌/" for a Korean-structured vault — see references/locale/ko/note_templates.md).
ls "$VAULT/Literature/" | grep -v "📊" | wc -l
```

### Step 3.2: Create literature notes

For each .bib entry, create `Literature/{citekey}.md` (or the vault's existing literature folder).
**Skip if the file already exists** (never overwrite).

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

(For a Korean-structured vault, use the Korean-heading template in `references/locale/ko/note_templates.md` and the vault's own hub-note names.)

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

Run this phase only when there are **≥10** literature notes in the vault.
If fewer exist, print a status message like "N literature notes — concept extraction
unlocks at ≥10" and stop.

### Step 4.1: Cross-cutting concept scan

Read all files under `Literature/*.md` (or the vault's existing literature folder):
1. Extract keywords from each paper's title, journal, and tags.
2. Extract major concepts from the .bib entry titles.
3. Identify **concepts that co-occur across ≥3 literature notes**.

### Step 4.2: Filtering (5 exclusion rules)

Exclude from concept candidates:
- Model names (GPT-4, Claude, etc.).
- Dataset names (MedQA, ImageNet, etc.).
- Journal names.
- Institution names.
- Generic technique names (too unspecific).

Whatever remains becomes a concept-note candidate.

### Step 4.3: Draft concept note

Create `Concepts/{concept name}.md` (or the vault's existing concept-note folder):

```markdown
---
title: "{concept name}"
type: concept
tags:
  - concept
  - {domain tag}
aliases:
  - {alternative name}
related_papers:
  - "[[{lit-note-1}]]"
  - "[[{lit-note-2}]]"
  - "[[{lit-note-3}]]"
status: 🌱Seedling
---

# {concept name}

## Definition (My Understanding)
> TODO: write in your own words

## Why it matters
{why the concept matters in this domain — AI supplies a draft}

## Per-paper perspectives
- **[[{lit-note-1}]]**: {this paper's angle}
- **[[{lit-note-2}]]**: {a different angle}
- **[[{lit-note-3}]]**: {comparison / complement}

## Related concepts
- [[{another concept}]]

## Open questions
- {open question 1}
- {open question 2}

## Related notes
- [[Research Hub]]
- [[{related project hub}]]
- [[{lit-note-1}]]
- [[{lit-note-2}]]
```

(For a Korean-structured vault, use the Korean-heading concept template in `references/locale/ko/note_templates.md`.)

**Key rules:**
- Keep the `## Definition` section as a `> TODO` marker — the 2nd-layer note only becomes
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

Create only after user confirmation. **Auto-draft but always confirm.**

---

## Standalone Modes

This skill can run without a fresh .bib file.

### Concept extraction only
On an explicit concept-extraction request, scan existing
`Literature/*.md` (or the vault's existing literature folder) and run only Phase 4.

### References tidy
On a "tidy this project's references" request, locate `.bib` files inside the
workspace and run Phase 1–3.

### Zotero sync only
On a "sync Zotero" request, diff the Zotero collection against the `.bib` file
and add whatever is missing.

### PMID-list ingestion (no .bib)
When the user supplies a list of PMIDs (e.g., from a HANDOFF or a colleague), resolve
PMIDs to DOIs via PubMed esummary first, then enter Phase 2 with the DOIs:

```bash
PMIDS="12345,67890,..."
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=${PMIDS}&retmode=json" \
  | jq -r '.result | to_entries[] | select(.key != "uids") | "\(.value.uid)\t\(.value.elocationid)\t\(.value.title)"'
```

For each resolved DOI, search-first with `zotero_search_items`, then call
`zotero_add_by_doi` — the search is what dedupes (add-by-doi alone does not). For items
already in the library (detected via `zotero_search_items` by DOI), use
`zotero_manage_collections` to attach them to the project collection **without re-adding** —
re-adding by URL/PubMed-URL would bypass the search dedup and create duplicates. Record both
`added` and `existing` items in `references/zotero_collection.json`.

If a PMID has no DOI in PubMed (rare; older papers, non-indexed), fall back to
`zotero_add_by_url` with the PubMed URL and mark the entry as `no_doi: true`.

### Worklist ingestion (DOI/PMID/Title; no .bib)
When the user supplies a worklist file (a `.tsv`/`.csv`/`.md` table with a `DOI` column,
optional `PMID`/`Title`, or a plain DOI-per-line list — e.g. an SR include set), enter
Phase 2 directly from it: resolve any PMID-only rows to DOIs (esummary above), then run the
search-first dedupe + add loop. The same worklist file feeds Phase 2.7 Route A
(`fetch_oa.py` reads `.tsv`/`.csv`/`.md`/plain natively), so no reformatting is needed.

---

## Safety Rules

1. **Never overwrite literature notes** — the user may have added highlights or
   personal notes.
2. **Never auto-fill `## Definition` of a concept note** — keep the TODO marker; the
   essence of the 2nd-layer note is the user's own wording.
3. **Skip Zotero for entries without a DOI** — ask the user to add those manually.
4. **Gracefully skip Zotero when the MCP is not connected** — Obsidian notes are
   created independently; but do NOT hand-edit `refs.bib` to compensate (violates artifact contract).
5. **Always record the collection key** — report the key to the user when a new
   collection is created.
6. **Never write `refs.bib` directly.** Only Better BibTeX auto-export may write that file. If auto-export is broken, fix the Zotero setup rather than writing the file from this skill.
7. **Owner-only execution.** If the current user is a collaborator (no Zotero access per `SSOT.yaml` `reference_manager.required_for`), abort with instructions to flag `[@NEW:topic]` placeholders in the manuscript and notify the owner.
8. **Fulltext boundary (Phase 2.7).** Retrieve full text only via OA APIs (the
   `/fulltext-retrieval` engine) and the user-run Zotero "Find Available PDF" snippet
   (which uses the user's own proxy config). Never automate authenticated browser sessions,
   never bypass paywalls/access controls, and never hard-code institutional proxies,
   credentials, or hosts into this skill. `not_retrieved` items are routed to institutional
   access / ILL / author contact, not worked around.

## Anti-Hallucination

- **Never fabricate DOIs, PMIDs, or citation metadata.** All bibliographic data must come from the .bib file or API responses.
- **Never auto-fill the "Definition (My Understanding)" section** of concept notes. This must be written by the user.
- **Never overwrite existing literature notes.** User highlights and annotations may be present.
- If a DOI lookup fails, report the failure rather than guessing the metadata.
