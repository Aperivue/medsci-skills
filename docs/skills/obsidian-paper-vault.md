<!-- AUTO-GENERATED from skills/obsidian-paper-vault/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# obsidian-paper-vault

> Turn a folder of research PDFs into an Obsidian knowledge vault — consistently formatted literature notes with frontmatter, PDF embed links, and cross-referenced atomic concept notes. Use whenever the user wants PDFs converted to Obsidian notes, a batch of papers summarized into a common template, a research "second brain" built or extended, or concepts extracted across accumulated notes — even if they never say "Obsidian". Pairs with /lit-sync, which owns the same vault folders from the Zotero/BibTeX side.

**Invoke:** `/obsidian-paper-vault` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`obsidian-paper-vault` activates on requests such as: obsidian-paper-vault, paper vault, second brain, PDF를 Obsidian 노트로, 논문 요약 노트, 논문 노트 만들어줘, 이 폴더의 PDF 정리해줘, batch process papers, add papers to vault, extract concepts from papers, literature vault.

## Quality Card

**Purpose** — Convert a folder of research PDFs into templated Obsidian literature notes plus atomic concept notes synthesized across them.

**Safety boundaries**

- Every number, author, and date is transcribed from extracted PDF text; nothing is written from model knowledge.
- Existing notes are never overwritten.

**Known limitations**

- Requires PyMuPDF; scanned PDFs with poor OCR yield thin notes.
- Default extraction is the first 12 pages, so appendix-only content is missed unless max_pages is raised.
- Effects land in the user's Obsidian vault, so there is no self-contained demo.

**Validation**

- `python3 scripts/extract_pdfs.py <pdf_folder> <cache_folder>`
- `grep -c 'date_published' <vault>/<literature_folder>/*.md`

**Evidence** — `manual_workflow`

## Bundled resources

**References** (`skills/obsidian-paper-vault/references/`):

- `concept-extraction.md`
- `locale/` (1 file)
- `subagent-prompt.md`
- `tag-vocabulary.md`
- `templates.md`
- `workflow.md`

**Scripts** (`skills/obsidian-paper-vault/scripts/`):

- `extract_pdfs.py`

## Source

Canonical definition: [`skills/obsidian-paper-vault/SKILL.md`](../../skills/obsidian-paper-vault/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
