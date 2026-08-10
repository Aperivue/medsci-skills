# Asking Better BibTeX for a citekey

Better BibTeX mints the citekey; nothing else is entitled to guess it. When a `.bib`
snapshot is stale or absent, ask the running plugin instead of composing a key from the
author and year.

## Is BBT answering?

```bash
curl -s -m 5 -o /dev/null -w "%{http_code}\n" \
  http://127.0.0.1:23119/better-bibtex/json-rpc      # 200 = ready
```

A non-200 means Zotero is closed, or BBT has not finished starting — it registers the
endpoint a few seconds after the app window appears. Do not read
`~/Zotero/better-bibtex/read-only.json` to decide this: current releases keep their
auto-export registrations elsewhere, so that file is routinely `[]` on a healthy install.

## Look up one paper

```bash
curl -s -m 20 -X POST http://127.0.0.1:23119/better-bibtex/json-rpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"item.search","params":["<title words or first author>"],"id":1}' \
  | python3 -c 'import json,sys
for i in json.load(sys.stdin)["result"]:
    print(i["citation-key"], "|", i.get("DOI", ""), "|", i.get("title", "")[:70])'
```

Match on DOI when the search returns more than one hit. Author-and-year alone will
happily match the wrong paper in a library that holds several from the same group.

## Dump the whole library

Useful for auditing an existing vault, where per-note lookups would take hours:

```bash
curl -s -m 120 "http://127.0.0.1:23119/better-bibtex/export/library?/1/library.bibtex" \
  -o library.bib
```

The `?/1/` is the library id, and the extension picks the translator. Other URL shapes
(`?libraryID=1&translator=…`, a `.csljson` extension) return an error page of a few
dozen bytes rather than an export — check the byte count before trusting the file.

Feed that dump straight to the provenance gate:

```bash
python3 scripts/check_citekey_provenance.py --vault "$VAULT" --bib library.bib --strict
```

## What the keys look like

BBT's default pattern is author + title words + year: `smithDeepLearningRadiology2024`.
Keys shaped like `Smith_2024_Validation`, `smith2024validation`, or `Smith_2024_38471102`
do not come from BBT. They come from something that needed a key and made one up — and
they resolve against nothing.
