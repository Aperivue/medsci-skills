# Zotero MCP tool names

`/lit-sync` names Zotero operations by what they do (*search items*, *add item*, ...). This table
maps each one to the tool name of the Zotero MCP server (`zotero-mcp`, 54yyyu). Names have changed
between server versions, so check the connected server's tool list before calling; if a name below
is missing there, find the tool whose description does the same job.

| Function in SKILL.md | 0.17.x name | Notes | Older names (gone by 0.17) |
|---|---|---|---|
| search items | `zotero_search_items` | by DOI, title, or `tag=` | `zotero_search_by_tag` |
| add item | `zotero_add_item` | `source` = DOI, PMID, URL, ISBN, BibTeX, CSL JSON or an absolute file path; `source_type` (default `auto`); `collections`; `if_exists` (`file` reuses an item with the same DOI/arXiv ID/ISBN/URL and adds the missing collections and tags, `skip`, `duplicate`); `attach_mode` (`auto`, `linked_url`, `none`, `required`) | `zotero_add_by_doi`, `zotero_add_by_url`, `zotero_add_from_file` |
| attach file | `zotero_attach_file` | attaches to an **existing** item key; `link_mode` `import` (stored copy, default) or `linked` | — |
| file into collection | `zotero_set_item_collections` | `item_keys` plus `add_to` / `remove_from` | `zotero_manage_collections` |
| create collection | `zotero_manage_collection` | `action='create'`, `name`, optional `parent_collection` | `zotero_create_collection` |
| find collection | `zotero_search_collections`, `zotero_get_collections` | | — |
| attachment path | `zotero_get_attachment_path` | where a stored PDF sits on disk | — |

Prefer a DOI for *add item*: a URL other than doi.org or arxiv.org becomes a bare webpage item,
which a later DOI lookup does not match. A PMID is accepted directly and yields a journal article
from PubMed's record, which is the fallback when PubMed lists no DOI.

Writing through Zotero's local API (no web API key) needs Zotero 10 or later (zotero-mcp 0.17.4
source: "Local API write access (Zotero 10+)") and a one-time local authorization in the server
(`zotero-mcp authorize-local`). With the local API, every call
fails while the Zotero app is closed.

Checked against zotero-mcp 0.17.4 (2026-11).
