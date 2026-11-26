---
name: obsidian-paper-vault
description: Use when turning research papers into Obsidian notes, even if Obsidian is not named, from a PDF folder or a Zotero collection or refs.bib whose PDFs are in Zotero. Writes one literature note per paper from its text and proposes concept notes, never overwriting. Adding papers to Zotero is /lit-sync.
metadata:
  triggers: "obsidian-paper-vault, paper vault, second brain, PDF를 Obsidian 노트로, 논문 요약 노트, 논문 노트 만들어줘, 이 폴더의 PDF 정리해줘, batch process papers, add papers to vault, extract concepts from papers, literature vault"
---

# Obsidian Paper Vault

Converts research papers into a two-layer Obsidian vault: **literature notes** (one per paper,
templated, written from the paper's text) and **atomic concept notes** (synthesized across papers).
The papers come from a folder of PDFs, or from a Zotero collection or `refs.bib` whose PDFs are
stored in Zotero. This is the only medsci skill that writes these notes, and it writes them only
when asked.

## Relationship to /lit-sync

`/lit-sync` owns the library: it adds papers to Zotero, files them into the project collection and
keeps `manuscript/_src/refs.bib` current. It writes no notes. This skill owns the notes.

| | `/lit-sync` | `obsidian-paper-vault` |
|---|---|---|
| Writes | Zotero items, `refs.bib` (through Better BibTeX) | literature and concept notes |
| Input | `.bib`, DOI/PMID list, PDF folder | PDF folder, or Zotero collection / `refs.bib` |
| Note name | — | title (PDF input) or citekey (Zotero input) |

To get a paper into Zotero, use `/lit-sync`; this skill never adds papers to the library. To check
that the citekeys in the vault exist in the library, use `/lit-sync`'s citekey audit.

**Never overwrite an existing note.** If a note for the paper already exists (by title, DOI,
or citekey), report it and skip.

## Step 0: Resolve the vault layout — ask, do not assume

Establish three paths before writing anything:

1. **Vault root** — from the user, or `$OBSIDIAN_VAULT`. Never guess a home-directory path.
2. **Literature notes folder** — default `Literature/`. If the vault already has a folder
   serving this role (`02_research/논문/`, `Papers/`, `文献/`), **honor the existing layout**
   rather than imposing the default.
3. **Concept notes folder** — default `Concepts/`, same honor-what-exists rule.
4. **Input** — a PDF folder, or a Zotero collection / `refs.bib`. For the Zotero input, read
   `references/zotero_input.md` before Step 1: it gathers the stored PDFs under their citekeys,
   and its notes carry `notetype`, `citekey` and `doi` and link to Zotero instead of embedding
   the PDF. Papers with no stored PDF get no note (a note with no text is an empty stub); list
   them instead.

For a vault whose structure is Korean, see `references/locale/ko/note_templates.md` — folder
names and note headings in Korean, opt-in.

Also confirm PyMuPDF is available: `python3 -c "import fitz; print(fitz.__version__)"`
(install with `pip install PyMuPDF`). Text extraction caches to
`~/.local/cache/paper-vault-texts/` unless the user names another location.

## Step 1: Pre-extract PDF text — always, for any batch

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/extract_pdfs.py" <pdf_folder> <text_cache_folder> [max_pages]
```

Defaults to 12 pages, which covers abstract through discussion for most papers. If notes come
out generic, the text file is abstract-only or its OCR is poor: re-extract with more pages or
check the source PDF. A PDF with no extractable text (an image-only scan) is reported as
`FAILED … (needs OCR)` and gets no `.txt`; OCR it or read it interactively, never batch it.

**Never hand a PDF path to a subagent.** A subagent that cannot open a file does not report
failure — it writes the note from training data, and the result is a plausible note with
invented numbers. Pass the `.txt` paths instead. Single-paper interactive work may read the
PDF directly (the Read tool handles PDFs); batches may not.

## Step 2: Write the notes — subagents in parallel

Split a batch across parallel subagents, a handful of papers each (per-agent note quality drops
when one agent carries too many), and group papers thematically per agent so each one can spot
recurring concepts.

Give each subagent: its assigned text-file paths with destination filenames, the template
from `references/templates.md` verbatim, the list of concept notes that already exist, and
the prohibition on inventing anything. `references/subagent-prompt.md` holds the full prompt.

Every note, batch or single, follows these rules:

1. **Numbers, authors, and dates come from the extracted text only** — never from model
   knowledge, however familiar the paper, because well-known papers drift between versions
   and that is exactly where invented values look most plausible.
2. **What the text does not state, the note does not claim.** Write "not stated in the
   extracted text" instead of filling the gap.
3. **Preserve the PDF filename exactly** in `![[filename.pdf]]`: take the text filename and
   swap `.txt` for `.pdf`, character for character (embeds are sensitive to case, spaces, and
   punctuation).
4. **Match the frontmatter field names** in `references/templates.md`. Dataview queries break
   on a renamed field, and they break by returning an empty table, not an error.
5. **Use the existing tag vocabulary** (`references/tag-vocabulary.md`) rather than inventing
   top-level tags.
6. **Name notes with 3–5 keyword concepts**, not the PDF's full title and not `paper_001`.

See `assets/example_paper_note.md` when unsure about literature-note formatting.

**Gate — before a batch is accepted**: spot-check two notes against their text files (one
sample size, one effect estimate). If either value is absent from the text, stop the batch
and report it rather than continuing. This gate is the user's call to waive, not the skill's.

## Step 3: Track progress in a queue file

Keep `PAPER_QUEUE.md` in the vault with per-paper status (done / pending / skipped / in
progress) so a 200-paper vault survives across sessions. Update it after each batch.

## Step 4: Concept notes — proposed, created on the user's yes

Run on request, or offer it once when the vault has 10 or more literature notes; never create
concept notes as a side effect of writing literature notes. List the candidates with the number of
notes each appears in, and create only the ones the user picks.

A phrase earns a concept note when it appears in 3+ notes, carries pedagogical value, and is
treated differently by different papers. Model names, datasets, and journals are entities,
not concepts. See `references/concept-extraction.md` for the full criteria, the frequency
scan, and the seedling/growing/mature lifecycle, and `assets/example_concept_note.md` for the
format.

Roughly one new concept note per 5–7 literature notes is healthy. Faster than that is concept
inflation, and it shows up as dozens of stub notes the user never edits.

**Gate — before concept notes are presented as done**: concept notes ship as 🌱Seedling with
the definition marked as a placeholder, and require user review before they count as the
reader's own. Say so explicitly when handing them over.

Read `references/workflow.md` when the user asks how the layers fit together or why the skill
will not write certain notes.
