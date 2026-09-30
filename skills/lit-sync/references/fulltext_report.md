# Phase 2.7 report — `references/fulltext_retrieval.json`

Merge Route A's `pdfs/retrieval_report.json` (and the user-reported Route B summary) into
`references/fulltext_retrieval.json` (owner of this file is `/lit-sync`):

```json
{
  "schema_version": 2,
  "retrieved_oa_disk": [{"doi": "...", "source": "unpaywall", "file": "...",
                         "file_sha256": "...", "title_match": "match",
                         "source_identity": {"status": "unresolved", "reason": "identifier_not_found"}}],
  "retrieved_zotero_native": [{"doi": "...", "via": "addAvailablePDF"}],
  "not_retrieved": [{"doi": "...", "journal": "..."}],
  "institutional_fallback": ["<DOIs needing institutional access / ILL / author contact>"],
  "title_mismatch_flagged": ["<DOIs whose downloaded PDF title did not match>"],
  "identity_review_needed": ["<DOIs with conflict, unresolved, unavailable, or absent identity evidence>"]
}
```

Also append a short `fulltext` block (counts) to `references/zotero_collection.json`.

## Identity evidence

- Copy each Route A `source_identity` object in full (abbreviated above), its file hash, and the
  identity-status counts.
- `retrieved_oa_disk` counts file retrieval, not verified papers.
- A `consistent` status is advisory corroboration, not claim verification.
- A changed file hash needs re-assessment.
- Route B attachments and legacy reports without identity evidence remain unassessed and appear in
  `identity_review_needed` until reviewed.
- `not_retrieved` DOIs are candidates for institutional access, interlibrary loan, or author
  contact.
