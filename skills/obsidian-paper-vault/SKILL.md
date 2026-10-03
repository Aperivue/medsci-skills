---
name: obsidian-paper-vault
description: Use when turning a folder of research PDFs into Obsidian notes, even if Obsidian is not named. Writes one templated literature note per paper and extracts cross-linked atomic concept notes, never overwriting existing ones. A .bib or Zotero library is /lit-sync.
metadata:
  triggers: "obsidian-paper-vault, paper vault, second brain, PDF를 Obsidian 노트로, 논문 요약 노트, 논문 노트 만들어줘, 이 폴더의 PDF 정리해줘, batch process papers, add papers to vault, extract concepts from papers, literature vault"
---

# Obsidian Paper Vault

Converts a folder of research PDFs into a two-layer Obsidian vault: **literature notes**
(one per paper, templated) and **atomic concept notes** (synthesized across papers).

## Relationship to /lit-sync

Both skills write literature and concept notes into the same vault folders. They enter from
opposite ends and must not overwrite each other.

| | `/lit-sync` | `obsidian-paper-vault` |
|---|---|---|
| Input | Zotero collection / `refs.bib` | a folder of PDFs |
| Note key | citekey | short descriptive title |
| Owns | `manuscript/_src/refs.bib` | extracted-text cache |

**Never overwrite an existing note.** If a note for the paper already exists (by title, DOI,
or citekey), report it and skip. When both skills are in play, `/lit-sync` notes are the
bibliographic spine; this skill's notes are the read-through summaries.

## Step 0: Resolve the vault layout — ask, do not assume

Establish three paths before writing anything:

1. **Vault root** — from the user, or `$OBSIDIAN_VAULT`. Never guess a home-directory path.
2. **Literature notes folder** — default `Literature/`. If the vault already has a folder
   serving this role (`02_research/논문/`, `Papers/`, `文献/`), **honor the existing layout**
   rather than imposing the default.
3. **Concept notes folder** — default `Concepts/`, same honor-what-exists rule.

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

Five subagents × 5–6 papers is the working batch size: enough parallelism to clear 25 papers
in one pass, small enough that per-agent quality holds. Group papers thematically per agent
so each one can spot recurring concepts.

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

## Step 4: Extract concept notes once 10+ literature notes exist

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
