# Reviewer Profiles

Per-journal notes for `/peer-review`. Each profile carries only what the journal publishes, and
links the public page every item comes from.

## Contents

| File | Journal | System | Review model |
|---|---|---|---|
| KJR.md | Korean Journal of Radiology | ScholarOne | Double-blind |
| RYAI.md | Radiology: Artificial Intelligence | ScholarOne | Double-anonymized |
| INSI.md | Insights into Imaging | Editorial Manager | Single-blind |
| AJR.md | American Journal of Roentgenology | Editorial Manager | Double-blind |
| EURE.md | European Radiology | Editorial Manager | Single-blind |

## What a profile holds

1. Journal name, submission system, and review model (single- or double-blind).
2. The comment structure from the journal's public reviewer guide, if it publishes one.
3. The journal's reviewer-AI policy: a short summary and the link.

## What a profile does not hold

Recommendation options and scorecard fields differ by journal and change without notice. Read
them from the live review form, keep any notes in a private store, and do not commit form-level
details to a public repository.

Nothing here identifies a reviewer, a manuscript or a review: no names, no manuscript IDs, no
manuscript content, no editor names.

## Adding a journal

1. Copy the closest existing profile.
2. Fill it only from the journal's public pages (reviewer guide, author instructions, AI policy),
   and link each one. If a page cannot be opened, link it without summarising it, or leave the item
   out.
3. Name the file `{JOURNAL_SHORTNAME}.md` with the established abbreviation (KJR, RYAI, INSI, AJR,
   EURE), or the full name when there is none.
4. Add a row to the table above and to the Journal-Specific Formatting table in
   `skills/peer-review/SKILL.md`.

## Consumed by

- `skills/peer-review/SKILL.md` — Journal-Specific Formatting.
