# Reverse-engineering progress ledger

One row per completed loop iteration. The loop appends here in Step E.
`Sources` lists `record_id`s (defined in `_corpus/manifest.json`, gitignored).

| # | Date | Batch (record_ids) | Improvement | Target skill | Codex (kept/total) | Branch | Status |
|---|------|--------------------|-------------|--------------|--------------------|--------|--------|
| 0 | 2026-06-11 | — | Infrastructure: PLAYBOOK, licensing firewall, manifest schema, helpers | reverse_engineer/ | — | feat/reverse-engineer-infra | infra only |

## Queue health

- Pending records in `doi_lists/queue.txt`: see that file (seeded by domain, license-checked at acquire time).
- Next priority item (per PLAYBOOK priority order): **#1 — peer-review / self-review probe + exemplar_reviews from published open reviews.**
