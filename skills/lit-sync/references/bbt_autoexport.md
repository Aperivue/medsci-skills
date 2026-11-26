# Registering a Better BibTeX auto-export (Step 2.5.1c)

Better BibTeX (BBT) keeps `refs.bib` in step with a Zotero collection through an auto-export
("Keep updated"). It can be registered from the menu (File → Export Library / right-click the
collection → Export Collection → Better BibTeX → Keep updated) or through BBT's JSON-RPC endpoint.
This file covers the JSON-RPC route.

## Ask first

Show the user, and wait for their yes:

- the collection path (below),
- the translator (`Better BibTeX`, the format `docs/zotero_policy.md` uses for `refs.bib`),
- the absolute target path (`SSOT.yaml` → `truth.refs_bib`, default
  `<project>/manuscript/_src/refs.bib`).

BBT documents no call that lists or removes an auto-export. A wrong registration is removed in
Zotero → Settings → Better BibTeX → Automatic export. Deleting the collection it exports also
removed the registration in the one setup where this was tried (below).

## The call

```bash
curl -s -m 20 -X POST http://127.0.0.1:23119/better-bibtex/json-rpc \
  -H 'Content-Type: application/json' -H 'Accept: application/json' \
  --data-binary '{"jsonrpc":"2.0","id":1,"method":"autoexport.add",
                  "params":["//<Collection>/<Subcollection>","Better BibTeX","<absolute path>/refs.bib",{},false]}'
```

- **Collection** is a slash-separated **path of names, not a key**. The first segment is the
  library name, or empty (`//`) for the personal library. BBT **creates any collection on the path
  that does not exist**, so a typo makes a new empty collection instead of failing. Copy the names
  from the library (`zotero_get_collections` / `zotero_search_collections`) rather than typing
  them, and do not use this route when a collection name itself contains `/`.
- The fourth argument holds display options (`exportNotes`, `useJournalAbbreviation`, both false by
  default). The fifth is `replace`.
- The result is `{"id": …, "key": "<collection key>", "libraryID": …}`. Check that `key` is the
  project collection's key (`SSOT.yaml` → `reference_manager.collection_key`). A different key means
  BBT made a new collection: stop and tell the user.

## Confirm it writes

A registration on an empty collection may create an empty file or none. The export runs when the
collection changes: after Phase 2 has added or filed an item, poll the target for up to 60 s and
require a non-empty file whose entries include a key from the collection. Record the outcome in the
Step 2.5.3 JSON (`refs_bib_refreshed`). If nothing is written, fall back to the menu route above and
say that the JSON-RPC registration did not take effect.

## Where this was tried

Zotero 10.0.9 with Better BibTeX 9.0.77 on macOS (2026-11): the call created the collection,
returned the same `id` when repeated (with `replace` false or true), wrote the file within seconds
of an item being filed into the collection, and deleting the collection removed the registration.
Other BBT versions, Windows paths and group libraries were not tried; confirm the file is written
before relying on it.
