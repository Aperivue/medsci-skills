# Reviewer Profiles

Canonical per-journal reviewer formatting profiles. Consumed by both the OSS `peer-review` skill (medsci-skills) and user-private peer-review skills (e.g., `~/.claude/skills/peer-review/`).

## Contents

| File | Journal | System | Scorecard |
|---|---|---|---|
| KJR.md | Korean Journal of Radiology | ScholarOne | 8 items, Excellent→Poor |
| RYAI.md | Radiology: Artificial Intelligence | ScholarOne | 5 items, 1–9 |
| INSI.md | Insights into Imaging | Editorial Manager | 4 items, H/M/L |
| AJR.md | American Journal of Roentgenology | Editorial Manager | Section-by-section |
| EURE.md | European Radiology | Editorial Manager | INSI-style base |

## Design Principles

1. **Single source of truth** — each journal's reviewer-form fields live in exactly one file here.
2. **Form fields, not opinions** — profiles describe what the editorial system expects (fields, scales, options); subjective calibration lives in the reviewer's own guideline.
3. **OSS-safe** — no PII, no specific reviewer identity, no manuscript content, **no manuscript IDs**, **no specific editor names**, no topic-level hints that could identify a past review. Under COPE reviewer confidentiality obligations, publishing the set of manuscripts a reviewer has handled can itself identify the reviewer. Keep personal precedent logs in a private store (e.g., `~/.claude/skills/peer-review/`) — never commit them here.
4. **Parallel to find-journal / write-paper profiles** — same directory-of-markdown pattern used elsewhere in medsci-skills.

## Adding a New Journal

1. Copy the closest existing profile as a template.
2. Record form fields from the first real review invitation (scorecard items, rating scales, required text boxes, recommendation options).
3. Commit under `{JOURNAL_SHORTNAME}.md` using established abbreviations (KJR, RYAI, INSI, AJR, EURE; full name if no common abbreviation).
4. Update this README table.

## Consumed By

- `medsci-skills/skills/peer-review/SKILL.md` — OSS public skill.
- `~/.claude/skills/peer-review/SKILL.md` — user's private overlay (reads same profiles, adds PII-specific guideline path).
