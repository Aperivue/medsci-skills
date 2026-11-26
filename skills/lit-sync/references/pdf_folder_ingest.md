# PDF folder ingestion

Adds the PDFs in a folder to Zotero, each as a stored copy attached to its own item. Items are found
by DOI, so a PDF whose first pages carry another paper's DOI would be filed under the wrong paper.
That is why nothing is added before the dry run below has been shown to the user.

## 1. Build the dry-run table

One row per PDF:

| file | DOI found | CrossRef title | title on page 1–2? | in library? | plan |
|---|---|---|---|---|---|

**PDFs from a `/fulltext-retrieval` report.** For a row whose `source_identity.status` is
`consistent` and whose file still has the recorded `file_sha256` (`shasum -a 256`), take the DOI
and title from the report and mark the title column `consistent (report)`. Rows with any other
status, a hash that no longer matches, or a report without `source_identity` are treated like any
other PDF below.

**Every other PDF:**

- **DOI found**: from the first two pages' text. The `zotero-cli` command installed with zotero-mcp
  has `zotero-cli add folder --dry-run <folder>` (checked in 0.17.4), which lists the DOI it would
  use per PDF; any PDF text extractor works too. Strip zero-width characters (U+200B and the like)
  inside a DOI before using it.
- **CrossRef title**: `https://api.crossref.org/works/<DOI>`.
- **Title on page 1–2?**: the CrossRef title, normalised (case, punctuation, whitespace), found in
  the text of the first two pages. Page 1 can be an advertisement, a cover sheet or a journal
  spread that carries two DOIs, so a DOI on page 1 alone is not enough.

For every row:

- **In library?**: *search items* by DOI.
- **Plan**: `add` (DOI and title confirmed, not in library), `attach` (in library without this
  PDF), `skip` (in library with a PDF), or `review` (no DOI, two DOIs, title not found, or a
  supplementary-material / erratum page). `review` rows are never added automatically.

## 2. Show it, then act on the user's go-ahead

Show the table. After the user approves (all, or the rows they pick):

- `add`: *add item* by DOI into the project collection (attach mode `none`), then *attach file*
  with the PDF's absolute path, stored as a copy (`link_mode` `import`). Keep `if_exists` at
  `file`, which files an existing match instead of duplicating it. (*add item* with the PDF path as
  the source also works, but it guesses metadata when it finds no DOI, so use it only for rows
  whose DOI is confirmed.)
- `attach`: *attach file* to the found item. Attaching to an existing item does not create a
  second parent.
- `attach` and `skip`: the item may sit only in another collection. *File it into the project
  collection* as well, or the project's `refs.bib` export leaves it out.
- `review`: list them for the user to add by hand.

## 3. Check and report

After adding, confirm each item has exactly one PDF attachment and that its stored file has the
same SHA-256 as the source PDF (`zotero_get_attachment_path`, then `shasum -a 256`). Report counts
as added / attached / already / review / failed. Write them into `references/zotero_collection.json`
under a `pdf_folder` block (folder path, counts, and the `review` file names).
