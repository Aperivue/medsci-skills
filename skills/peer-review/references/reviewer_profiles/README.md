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

## A form field is a claim until you say what you read it off

These profiles are trusted precisely because they are specific: a reviewer reads the recommendation
options here and picks one without opening the portal first. That is what makes a wrong entry
expensive, and it has now happened twice on two different journals.

- A profile listed **"Accept with Minor Revision"** as a recommendation option. The live form does
  not have that label, and its minor-revision tier is **two** options — final approval *by Editor*
  versus *by this reviewer*, a real decision about whether the paper returns to the reviewer. The
  reviewer was told to pick the non-existent option and had to report back from the portal. Filed,
  then observed a second time two weeks later, still uncorrected.
- Another profile listed **ORCID Reviewer Credit** under *Confirmed Form Fields*. It is not a
  scorecard field at all — zero occurrences in either round's confirmation PDF; it is an
  account-level setting. It reached a submission checklist as a field to answer.

Both entries came from the same place: **a review invitation, or the author guidelines.** An
invitation advertises the review. The form is what you fill in. They are not the same document, and
nothing in this directory used to say so.

**Rules:**

1. **Source of truth is a completed form or its confirmation PDF** — never the invitation, never the
   author guidelines. Guidelines describe the journal's policy; the form is the journal's software.
2. **Every form-field list carries an evidence pointer**, or it may not be called *confirmed*:
   `Verified against {R1/R2/…} confirmation PDF, {YYYY-MM-DD}`. **Date and round only — never the
   manuscript ID** (Design Principle 3: the set of manuscripts a reviewer has handled can identify
   the reviewer).
3. **A confirmation PDF cannot verify a dropdown.** It carries no form widgets, so the *contents* of
   a recommendation or rating menu are not recoverable from it. Verifying an option list means
   rendering the live page as an image. Until that is done, mark the list partially verified and
   **leave the unread labels blank rather than filling them in** — a plausible guess in a confident
   file is worse than an admitted gap.
4. **When a profile is wrong, correct the profile.** Reading it and working around it in one session
   leaves the next reader to hit the same wall.

## Adding a New Journal

1. Copy the closest existing profile as a template.
2. Record form fields from a **completed submission form or its confirmation PDF** (scorecard items,
   rating scales, required text boxes, recommendation options) — see the rules above. If you have
   only an invitation so far, write what you have and mark it unverified.
3. Add the evidence pointer (round + date, no manuscript ID).
4. Commit under `{JOURNAL_SHORTNAME}.md` using established abbreviations (KJR, RYAI, INSI, AJR, EURE; full name if no common abbreviation).
5. Update this README table.

## Consumed By

- `medsci-skills/skills/peer-review/SKILL.md` — OSS public skill.
- `~/.claude/skills/peer-review/SKILL.md` — user's private overlay (reads same profiles, adds PII-specific guideline path).
