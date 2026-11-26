# PDF folder ingestion

Adds the PDFs in a folder to Zotero, each as a stored copy attached to its own item. Items are found
by DOI, so a PDF whose first pages carry another paper's DOI would be filed under the wrong paper.
That is why nothing is added before the dry run below has been shown to the user.

## 1. PDFs that come with an identity check

If the folder came from `/fulltext-retrieval`, read its `retrieval_report.json`. For rows whose
`source_identity.status` is `consistent`, first confirm the file still has the recorded
`file_sha256` (`shasum -a 256`), then:

1. *search items* by the row's DOI; if there is no item, *add item* by DOI (no PDF yet, attach mode
   `none`) into the project collection;
2. *attach file* to that item with the PDF's absolute path, stored as a copy (`link_mode`
   `import`). Attaching to an existing item does not create a second parent.

Rows with any other status (`conflict`, `unresolved`, `unavailable`) and rows whose hash no longer
matches go to step 2 like any other PDF. A report without `source_identity` is unassessed: treat
all its rows as step 2.

## 2. Every other PDF: dry run, then the user's go-ahead

For each remaining PDF, build one row:

| file | DOI found | CrossRef title | title on page 1–2? | in library? | plan |
|---|---|---|---|---|---|

- **DOI found**: from the first two pages' text. `zotero-cli add folder --dry-run <folder>`
  (bundled with zotero-mcp 0.17.2 and later) lists the DOI it would use per PDF; any PDF text
  extractor works too. Strip zero-width characters (U+200B and the like) inside a DOI before
  using it.
- **CrossRef title**: `https://api.crossref.org/works/<DOI>`.
- **Title on page 1–2?**: the CrossRef title, normalised (case, punctuation, whitespace), found in
  the text of the first two pages. Page 1 can be an advertisement, a cover sheet or a journal
  spread that carries two DOIs, so a DOI on page 1 alone is not enough.
- **In library?**: *search items* by DOI.
- **Plan**: `add` (DOI found, title found, not in library), `attach` (already in library without
  this PDF), `skip` (already in library with a PDF), or `review` (no DOI, two DOIs, title not
  found, or a supplementary-material / erratum page). `review` rows are never added automatically.

Show the table. After the user approves (all, or the rows they pick):

- `add`: *add item* with the PDF's absolute path as the source and the project collection (the
  server reads the DOI, imports the metadata and stores the PDF), or add by DOI and then *attach
  file*. Keep `if_exists` at `file`, which files an existing match instead of duplicating it.
- `attach`: *attach file* to the found item.
- `review`: list them for the user to add by hand.

## 3. Check and report

After adding, confirm each item has exactly one PDF attachment and that its stored file has the
same SHA-256 as the source PDF (`zotero_get_attachment_path`, then `shasum -a 256`). Report counts
as added / attached / already / review / failed. Write them into `references/zotero_collection.json`
under a `pdf_folder` block (folder path, counts, and the `review` file names).
