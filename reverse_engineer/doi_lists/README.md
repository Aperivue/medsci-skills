# DOI / source lists

The loop pulls work from `queue.txt`. This directory defines **where** to source from
(by domain) and the rules for adding a record. Specific DOIs/URLs are added to
`queue.txt` only when verified at acquire time — never fabricated here.

## Curation rules

- **Open access or open review only.** Verify the license per record at acquire time and
  record it in `_corpus/manifest.json`. Unknown license → learn-only (never committed).
- **Spread across domains.** Don't over-fit to one field; rotate through the domains in
  `sources_by_domain.md` so the distilled probes/exemplars generalize.
- **Prefer published open reviews for review-skill work** — they are real reviewer
  language, and venues like F1000Research publish them under CC-BY.
- **No fabricated identifiers.** A DOI/PMID enters `queue.txt` only after it resolves.
  Use the `verify-refs` / `search-lit` skills to confirm before queueing.

## queue.txt format

One record per line: `record_id<TAB>doi_or_url<TAB>domain`. Lines starting with `#`
are comments. `record_id` must match the manifest schema pattern
(`^[a-z0-9][a-z0-9_]{2,79}$`). Example (illustrative — replace with verified entries):

```
# record_id                         doi_or_url                              domain
f1000_review_dta_calibration_2024   https://doi.org/10.12688/...            radiology_ai
```

`acquire.py` reads the next N uncommented lines, scaffolds `_corpus/` directories, and
creates a manifest stub per record for you to complete.
