# Input from a Zotero collection or refs.bib

Use this when the papers are already in Zotero (usually added by `/lit-sync`) and the user wants
notes for a collection or for the entries of a project's `refs.bib`.

## 1. Gather the papers

For each entry, collect:

- **citekey** — read from the Better BibTeX-exported `refs.bib`, or from Better BibTeX's JSON-RPC
  (`item.citationkey` for item keys, `item.search` for a title or DOI) on
  `http://127.0.0.1:23119/better-bibtex/json-rpc`. **Never compose a key** from author and year:
  a note named after a key that does not exist still looks right, and `[@key]`, `[[key]]` and the
  Zotero Integration plugin all break on it. If no key can be read, leave `citekey: ""`, add the
  tag `_needs-citekey`, and name the note by title.
- **DOI** and **Zotero item key**.
- **Stored PDF path** — from the Zotero MCP server (`zotero_get_attachment_path`) or Better
  BibTeX (`item.attachments` with the citekey). Use only a stored or linked PDF that exists on
  disk.

Entries without a PDF on disk get **no note**. List them for the user ("no PDF in Zotero: N"); the
library side can fetch them (`/lit-sync` Phase 2.7). A note written from metadata alone is an empty
stub with nothing for the reader to start from.

## 2. Extract text

`extract_pdfs.py` reads a folder. Put a symbolic link to each stored PDF into a fresh folder under
the text cache, named `<citekey>.pdf` (or a short title when there is no key), and run Step 1 on
that folder. Do not copy or move the PDFs out of Zotero's storage.

## 3. Write the notes

Same rules as SKILL.md Step 2 (text only, no invented values, subagents get `.txt` paths), with
these differences:

- **Name**: `{citekey}.md`, so it matches `[[citekey]]`, `[@citekey]` and the Zotero Integration
  plugin's `{{citekey}}.md`. Put the short descriptive title in `aliases`.
- **Frontmatter**: the template's fields plus

  ```yaml
  notetype: literature
  citekey: "{citekey}"
  doi: "{doi}"
  ```

  `/lit-sync`'s citekey audit reads notes by `notetype: literature` and checks `citekey` and `doi`
  against the library.
- **PDF line**: the PDF is not in the vault, so instead of `![[file.pdf]]` link to the item:
  `[Open in Zotero](zotero://select/library/items/{item key})` for the personal library, or
  `zotero://select/groups/{group ID}/items/{item key}` for an item in a group library.

Skip an entry when a note with the same citekey or DOI already exists, and report it.
