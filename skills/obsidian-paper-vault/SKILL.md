---
name: obsidian-paper-vault
description: Turn a folder of research PDFs into an Obsidian knowledge vault — consistently formatted literature notes with frontmatter, PDF embed links, and cross-referenced atomic concept notes. Use whenever the user wants PDFs converted to Obsidian notes, a batch of papers summarized into a common template, a research "second brain" built or extended, or concepts extracted across accumulated notes — even if they never say "Obsidian". Pairs with /lit-sync, which owns the same vault folders from the Zotero/BibTeX side.
triggers: obsidian-paper-vault, paper vault, second brain, PDF를 Obsidian 노트로, 논문 요약 노트, 논문 노트 만들어줘, 이 폴더의 PDF 정리해줘, batch process papers, add papers to vault, extract concepts from papers, literature vault
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Obsidian Paper Vault

Converts a folder of research PDFs into a two-layer Obsidian vault: **literature notes**
(one per paper, templated) and **atomic concept notes** (synthesized across papers).

The rules below are not style preferences. Each one is here because its absence produced a
specific, silent failure — a fabricated patient count, a broken PDF link, an empty Dataview
table — in a vault of 100+ papers.

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
python3 scripts/extract_pdfs.py <pdf_folder> <text_cache_folder> [max_pages]
```

Defaults to 12 pages, which covers abstract through discussion for most papers.

**Never hand a PDF path to a subagent.** A subagent that cannot open a file does not report
failure — it writes the note from training data, and the result is a plausible note with
invented numbers. Pass the `.txt` paths instead. Single-paper interactive work may read the
PDF directly (the Read tool handles PDFs); batches may not.

## Step 2: Launch subagents in parallel

Five subagents × 5–6 papers is the working batch size: enough parallelism to clear 25 papers
in one pass, small enough that per-agent quality holds. Group papers thematically per agent
so each one can spot recurring concepts.

Give each subagent: its assigned text-file paths with destination filenames, the template
from `references/templates.md` verbatim, the list of concept notes that already exist, and
the prohibition on inventing anything. `references/subagent-prompt.md` holds the full prompt.

## Step 3: Track progress in a queue file

Keep `PAPER_QUEUE.md` in the vault with per-paper status (done / pending / skipped / in
progress) so a 200-paper vault survives across sessions. Update it after each batch.

## Step 4: Extract concept notes once 10+ literature notes exist

A phrase earns a concept note when it appears in 3+ notes, carries pedagogical value, and is
treated differently by different papers. Model names, datasets, and journals are entities,
not concepts. See `references/concept-extraction.md` for the full criteria, the frequency
scan, and the seedling/growing/mature lifecycle.

Roughly one new concept note per 5–7 literature notes is healthy. Faster than that is concept
inflation, and it shows up as dozens of stub notes the user never edits.

## Anti-Hallucination rules (non-negotiable)

A note that is fluent, correctly formatted, and wrong in its numbers is worse than no note:
the user cites it. These three rules exist to make that failure impossible rather than
unlikely.

1. **Numbers, authors, and dates come from the extracted text only** — never from model
   knowledge, however familiar the paper. Well-known papers drift between versions, and that
   is exactly where invented values look most plausible.
2. **Subagents receive `.txt` paths, never PDF paths.** A subagent that cannot open a file
   does not report the failure; it writes from training data. The text indirection is the
   only reliable guard.
3. **What the text does not state, the note does not claim.** Write "not stated in the
   extracted text" instead of filling the gap.

**Gate — before a batch is accepted**: spot-check two notes against their text files (one
sample size, one effect estimate). If either value is absent from the text, stop the batch
and report it rather than continuing. This gate is the user's call to waive, not the skill's.

## Structural rules

4. **Preserve the PDF filename exactly** in `![[filename.pdf]]`. Obsidian embeds are
   sensitive to case, spaces, and punctuation — take the text filename and swap `.txt` for
   `.pdf`, character for character.
5. **Match the frontmatter field names** in `references/templates.md`. Dataview queries break
   on a renamed field, and they break by returning an empty table, not an error.
6. **Use the existing tag vocabulary** (`references/tag-vocabulary.md`) rather than inventing
   top-level tags.
7. **Name notes with 3–5 keyword concepts**, not the PDF's full title and not `paper_001`.
8. **Never overwrite an existing note** — see the `/lit-sync` boundary above.

**Gate — before concept notes are presented as done**: concept notes ship as 🌱Seedling with
the definition marked as a placeholder, and require user review before they count as the
reader's own. Say so explicitly when handing them over.

## Reference files

| File | Read it when |
|---|---|
| `references/templates.md` | writing any literature or concept note |
| `references/subagent-prompt.md` | launching a batch |
| `references/concept-extraction.md` | extracting concepts across notes |
| `references/tag-vocabulary.md` | choosing tags |
| `references/workflow.md` | the user asks how the layers fit together |
| `references/locale/ko/note_templates.md` | the vault is Korean-structured |
| `assets/example_paper_note.md` | unsure about literature-note formatting |
| `assets/example_concept_note.md` | unsure about concept-note formatting |

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Subagent says it could not read the PDF | it was given a PDF path | run `extract_pdfs.py`, pass `.txt` paths |
| Note reads plausibly but numbers are wrong | subagent wrote from training data | re-run against the text file; verify n, CI, p-values |
| Dataview table is empty | frontmatter field renamed | match `references/templates.md` exactly |
| PDF embed shows a broken tile | filename mismatch | compare character by character, including case |
| Note content is generic | text file is abstract-only or OCR is poor | re-extract with more pages, or check the source PDF |
