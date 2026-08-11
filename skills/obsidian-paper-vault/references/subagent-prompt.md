# Subagent Prompt for Batch Note Writing

Reusable prompt for converting extracted PDF text into literature notes. Five subagents ×
5–6 papers each is the working batch; launch them in one message so they run concurrently.

## Filling it in

| Placeholder | Value |
|---|---|
| `{DOMAIN}` | the field, e.g. "medical AI", "interventional radiology" |
| `{TEXT_DIR}` | the extracted-text cache from `scripts/extract_pdfs.py` |
| `{LIT_DIR}` | `<vault>/Literature/` or the vault's existing equivalent |
| `{ASSIGNMENTS}` | this agent's table of text file → destination note filename |
| `{EXISTING_CONCEPTS}` | concept notes already in the vault, so links point somewhere real |

## Prompt

```
You are writing Obsidian literature notes for {DOMAIN} papers. Each note is written from a
text file extracted from the source PDF, which you read with the Read tool.

INPUT   {TEXT_DIR}   (one .txt per paper, first 12 pages)
OUTPUT  {LIT_DIR}    (one new .md per paper, created with the Write tool)

Assigned papers:
{ASSIGNMENTS}

Concept notes that already exist — link to these by exact name, and propose new ones only
when a paper genuinely introduces something absent from this list:
{EXISTING_CONCEPTS}

For each paper:

1. Read the whole text file.

2. Take from the text, and only from the text: the exact title including any subtitle; up to
   five authors as written; the journal or arXiv id; the publication date as YYYY-MM-DD; the
   design, results, comparisons, and stated limitations.

   Numbers, authors, and dates that are not in the text file do not go in the note. Do not
   supply them from memory, even for a paper you recognise. If the text does not state
   something, write "not stated in the extracted text" rather than filling the gap.

3. Write the note to {LIT_DIR} using the template below. The PDF embed link must reproduce
   the source filename exactly — take the .txt filename and change the extension to .pdf,
   character for character, preserving case, spaces, and punctuation.

4. If a note of that name already exists, skip it and report it. Do not overwrite.

Template — follow it exactly, including frontmatter field names:

---
title: "exact title from the text"
authors: [Family1, Family2]
journal: "journal or arXiv id"
date_published: YYYY-MM-DD
tags:
  - 📝Paper
  - 🤖AI/LLM
  - {domain tag}
status: 🟢Completed
aliases:
  - ShortAlias
---

# Paper title

📎 **Open the PDF inside Obsidian**: ![[exact_source_filename.pdf]]

## 📌 One-line summary

## 🎯 Background and aim
*
*

## 🔑 Methods and results
1. **Design**:
2. **Main results** (figures exactly as the text gives them):
3. **Comparison**:
4. **Limitations**:

## 💡 My reading
*
*

---
## Related notes
* [[existing concept note]]
* [[proposed new concept]]

Report back: notes written, notes skipped as existing, and any paper whose text file was too
short or too garbled to write from.
```

## Why the text-file constraint is absolute

A subagent handed a PDF path it cannot open does not stop and report the failure. It writes
the note anyway, from whatever it knows about a paper with that name — and the output is
fluent, correctly formatted, and wrong in the numbers. Sample counts, IQRs, author lists, and
p-values have all been produced this way. The `.txt` indirection is the only reliable guard.
