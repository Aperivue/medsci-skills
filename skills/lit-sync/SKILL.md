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

- Communicate with the user in their preferred language (typically Korean).
- Note template headings (`서지 정보`, `핵심 내용`, `내 생각`, `관련 노트`), vault
  folder paths (`02 연구/문헌/`, `02 연구/개념노트/`), and Obsidian-side conventions
  are preserved as literal template content because they match the user's existing vault.

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
| `manuscript/_src/refs.bib` | `/lit-sync` (via Better BibTeX auto-export trigger) | `/write-paper`, `/verify-refs`, `/render` |
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
    ▼ Phase 3: Obsidian Literature Notes
    Create 02 연구/문헌/{citekey}.md (empty note OK — fill later with highlights)
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
2. Otherwise call `zotero_add_by_doi` (when a DOI is available) or
   `zotero_add_by_url` (falling back to the PubMed URL when no DOI is available).
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

If refresh failed, set `refs_bib_refreshed: false` and include `reason`. `/verify-refs` uses this flag to decide whether the snapshot is trustworthy.

---

## Phase 3: Obsidian Literature Notes

### Step 3.1: Check existing literature notes

```bash
ls "$VAULT/02 연구/문헌/" | grep -v "📊" | wc -l
```

### Step 3.2: Create literature notes

For each .bib entry, create `02 연구/문헌/{citekey}.md`.
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

## 서지 정보
- **저자**: {authors}
- **저널**: {journal}{volume_issue_pages}
- **연도**: {year}
- **DOI**: [{doi}](https://doi.org/{doi})
{pmid_line}

## 핵심 내용 (내 언어로)



## 내 생각



## 관련 노트
- [[🗺️ 연구 종합]]
- [[🗺️ 논문과 리뷰]]
-
-
```

**Rules:**
- `notetype: literature` — compatible with the Zotero Integration template.
- `_unread` tag — change to `_read` later after the user reads the PDF in Zotero and adds highlights.
- Leave `## 핵심 내용` and `## 내 생각` blank — the user fills these in personally.
- `## 관련 노트` contains 2 hub links + 2 empty slots (reserved for later concept-note linking).
- If a PMID is available, add a PubMed link.

### Step 3.3: Result report

```
Obsidian Literature Notes:
  Created:   8 notes (new)
  Skipped:   3 notes (already exist)
  Location:  02 연구/문헌/
  Total in vault: 12 literature notes
```

---

## Phase 4: Concept Extraction (conditional)

### Trigger condition

Run this phase only when there are **≥10** literature notes in the vault.
If fewer exist, print a status message like "N literature notes — concept extraction
unlocks at ≥10" and stop.

### Step 4.1: Cross-cutting concept scan

Read all files under `02 연구/문헌/*.md`:
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

Create `02 연구/개념노트/{concept name}.md`:

```markdown
---
title: "{concept name}"
type: concept
tags:
  - 🧠개념
  - {domain tag}
aliases:
  - {English/Korean alternative name}
related_papers:
  - "[[{lit-note-1}]]"
  - "[[{lit-note-2}]]"
  - "[[{lit-note-3}]]"
status: 🌱Seedling
---

# {concept name}

## 정의 (My Understanding)
> TODO: write in your own words

## 왜 중요한가
{why the concept matters in this domain — AI supplies a draft}

## 논문별 관점
- **[[{lit-note-1}]]**: {this paper's angle}
- **[[{lit-note-2}]]**: {a different angle}
- **[[{lit-note-3}]]**: {comparison / complement}

## 관련 개념
- [[{another concept}]]

## 열린 질문
- {open question 1}
- {open question 2}

## 관련 노트
- [[🗺️ 연구 종합]]
- [[{related project hub}]]
- [[{lit-note-1}]]
- [[{lit-note-2}]]
```

**Key rules:**
- Keep the `## 정의` section as a `> TODO` marker — the 2nd-layer note only becomes
  meaningful once the user writes the definition in their own words.
- `status` always starts at `🌱Seedling`.
- At least 4 wikilinks under `## 관련 노트` (vault convention).

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
`02 연구/문헌/*.md` and run only Phase 4.

### References tidy
On a "tidy this project's references" request, locate `.bib` files inside the
workspace and run Phase 1–3.

### Zotero sync only
On a "sync Zotero" request, diff the Zotero collection against the `.bib` file
and add whatever is missing.

---

## Safety Rules

1. **Never overwrite literature notes** — the user may have added highlights or
   personal notes.
2. **Never auto-fill `## 정의` of a concept note** — keep the TODO marker; the
   essence of the 2nd-layer note is the user's own wording.
3. **Skip Zotero for entries without a DOI** — ask the user to add those manually.
4. **Gracefully skip Zotero when the MCP is not connected** — Obsidian notes are
   created independently; but do NOT hand-edit `refs.bib` to compensate (violates artifact contract).
5. **Always record the collection key** — report the key to the user when a new
   collection is created.
6. **Never write `refs.bib` directly.** Only Better BibTeX auto-export may write that file. If auto-export is broken, fix the Zotero setup rather than writing the file from this skill.
7. **Owner-only execution.** If the current user is a collaborator (no Zotero access per `SSOT.yaml` `reference_manager.required_for`), abort with instructions to flag `[@NEW:topic]` placeholders in the manuscript and notify the owner.

## Anti-Hallucination

- **Never fabricate DOIs, PMIDs, or citation metadata.** All bibliographic data must come from the .bib file or API responses.
- **Never auto-fill the "정의 (My Understanding)" section** of concept notes. This must be written by the user.
- **Never overwrite existing literature notes.** User highlights and annotations may be present.
- If a DOI lookup fails, report the failure rather than guessing the metadata.
