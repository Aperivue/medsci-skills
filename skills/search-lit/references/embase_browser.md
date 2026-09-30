# Embase search via browser automation

Embase has no public API. Search and export it through Chrome browser automation (MCP):

1. Navigate to `embase.com` — institutional SSO authenticates automatically.
   If cookie error (`login?error#`), clear Elsevier/Embase cookies and retry.
2. Go to the **Advanced Search** tab.
3. Enter an Embase-syntax query (Emtree `/exp` + `:ab,ti` field tags).
   Uncheck "Map to preferred term in Emtree" when using explicit `/exp` terms.
4. After results appear, use the "Select number of items" dropdown → select the total count.
5. Click **Export** (in the Results section) → choose **CSV** format → check fields:
   Title, Author names, Source, Publication year, Publication type, DOI, Abstract,
   Language of article, Medline PMID.
6. Click Export → the Download tab opens → click Download.
7. The CSV is in **row format** (records separated by blank rows). Parse it as:
   ```python
   # Each record = consecutive rows until blank row
   # Row format: [FIELD_NAME, value1, value2, ...]
   # AUTHOR NAMES row has multiple values (one per author)
   ```

## PubMed → Embase query translation

- MeSH `[Mesh]` → Emtree `/exp`
- `[tiab]` → `:ab,ti`
- `[Title/Abstract]` → `:ab,ti`
- Boolean operators stay the same (AND, OR)
- Phrase search: use single quotes in Embase (`'artificial ascites'`)
