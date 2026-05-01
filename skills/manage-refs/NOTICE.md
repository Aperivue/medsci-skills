# NOTICE — Third-party components

## scripts/_vendor_citation_writer.py

- **Source**: alisoroushmd/zotero-mcp (https://github.com/alisoroushmd/zotero-mcp)
- **File**: `src/zotero_mcp/citation_writer.py`
- **Upstream SHA**: `ed5dfb718b78f355f300545eb375aec7a543e027` (fetched 2026-05-01)
- **License**: MIT, © 2026 Ali Soroush — full text in [`LICENSE.zotero-mcp`](./LICENSE.zotero-mcp)
- **Modifications**: None to the function bodies. The header comment was
  rewritten to point at this skill's NOTICE / LICENSE files.
- **Why vendored, not depended on**: the upstream module has no PyPI release
  and its repository ships an MCP server we do not need. The single file is
  self-contained (only `python-docx` required) and was validated against a
  21-reference RFA-Adjunct manuscript before being relocated here.

## CSL files (`citation_styles/*.csl`)

CSL files are author-licensed under CC BY-SA 3.0 (see individual file headers
or the README at the upstream Zotero / citation-style-language project).

## How `inject_zotero_cwyw.py` differs from upstream

The vendored `zotero_to_csl_json` walks an `_ITEM_TYPE_MAP` that does not
include `webpage`, `report`, `presentation`, etc. — those item types fall
back to `"article"` and silently lose `URL` / `accessDate` / `publisher`. The
wrapper in `inject_zotero_cwyw.py` monkey-patches that function at import
time so it instead fetches each item's CSL-JSON from Zotero's connector API
(`http://localhost:23119/api/users/<USER_ID>/items/<KEY>?format=csljson`),
which is Zotero's own serialization and handles every item type correctly.
