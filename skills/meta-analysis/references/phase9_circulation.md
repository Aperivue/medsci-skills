# Phase 9 Reference — Co-author Circulation

Load this reference when Phase 9 is entered (after Phase 8 is complete and Phase 6b
source-fidelity audit has cleared). The SKILL.md body carries only the goal + summary
pointer; all procedural detail lives here.

## Goal

Standardized pre-submission circulation of the manuscript to co-authors and senior
methodologists / reviewers, with a bounded review window and a controlled attachment
scope.

## Trigger

Phase 8 is complete, and the draft has cleared Phase 6b source-fidelity audit.

## 9.1 Thread Continuity

- If a prior version (v1, v2, ...) of this manuscript was already circulated to the same
  author team, reply to the same email thread. Preserve `In-Reply-To` and `References`
  headers so the thread tracks v1 → v2 → v3 in one place.
- Open a new thread only for the first circulation, or when the author team / target
  journal has fundamentally changed.

## 9.2 Attachment Scope

**Include:**
- Manuscript body with figures embedded inline (single DOCX/PDF).
- Change summary — for v≥2, a delta table vs. the prior circulated version.

**Exclude (circulate separately later):**
- Graphical abstract — after the body is locked.
- Cover letter — after the target journal is confirmed.
- COI forms — after journal format is known.
- Supplementary appendices — share via a drive link, not attached.

Rationale: bundling all submission artifacts before the body is locked forces co-authors
to review multiple moving targets at once and telegraphs premature commitment to a
specific journal (especially when the GA carries journal-specific branding).

## 9.3 Attachment Method

| Total attachment size | Method |
|---|---|
| < 5 MB | Direct email attachment |
| 5 – 25 MB | Direct attachment (within the common 25 MB mailbox limit), but verify at the draft-API level — some clients fail well below the stated message limit |
| > 25 MB or grey-list formats | Shared drive link only |

A manuscript DOCX with inline figures is typically 0.5 – 1 MB — direct attach is safe.

## 9.4 Recipient Structure

- **TO**: Corresponding author + one senior methodologist reviewer (e.g., a protocol
  assessor or statistician external to the writing team).
- **CC**: All remaining co-authors. Include every alternate email address a co-author has
  used on the thread to avoid dropping them.

Ask the corresponding author explicitly for:
- target journal preference,
- 2 – 3 reviewer candidates,
- any framing adjustments to carry into the cover letter.

## 9.5 Journal-Undetermined Framing

If the target journal is not yet confirmed, state this explicitly:

> "The manuscript is currently formatted to [placeholder journal]'s guidelines. Please
> suggest an appropriate target journal and we will re-format accordingly."

Do not include the graphical abstract in this round if it carries journal-specific
branding that would require rework on re-targeting.

## 9.6 Deadline

- Set `(send date + 7 days)` = 5 business days + 1 weekend.
- Record the deadline in a task tracker with expected responses per recipient.
- Informal follow-up is acceptable after 4 – 5 days of silence. A formal second message
  before the 7-day window closes is not appropriate unless an external submission deadline
  forces it.

## 9.7 Response Tracking

For each recipient, log: date of response, issues raised, and whether the issues trigger
Phase 10 (Self-Audit Recovery) or are minor in-place revisions.
