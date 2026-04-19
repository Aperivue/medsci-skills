# Phase 10 Reference — Self-Audit Recovery (v{N} → v{N+1} Sprint)

Load this reference when any Phase 10 trigger fires during `/meta-analysis`. The SKILL.md
body carries only the trigger table and summary pointer; all procedural detail lives here.

## Goal

When an audit — internal, or triggered by an incoming co-author comment — uncovers a
structural data or protocol-application error, withdraw the current version, rebuild, and
re-circulate with a transparent audit trail. Catching the error yourself before a journal
reviewer does is the principal trust-building move in this phase.

## Trigger Conditions (any one)

- Extraction CSV disagrees with the primary source for a cell that materially feeds a
  pooled estimate, subgroup estimate, or a reported proportion.
- A study that was excluded (or included) by the pre-specified criteria is found to
  violate those criteria on re-read.
- A hand-typed numerical literal in the analysis script traces to a wrong value (see the
  Phase 6b precedent failure pattern).
- The PROSPERO (or equivalent) protocol and the delivered analysis disagree on a
  pre-specified outcome, subgroup, or eligibility rule.
- A dual-reviewer consensus record shows a study was supposed to be excluded, but the
  locked dataset still contains it (or vice versa).

## Non-Negotiable Rule

If the trigger fires after Phase 9 circulation but before journal submission, withdraw
the current version within 24 hours. Reviewer discovery is a strictly worse failure mode
than self-withdrawal.

## 10.1 Audit Log

Create `qc/audit_vN_to_vNplus1.md`. For each flagged item, record:
- Affected study (first author, year).
- Cell or claim (e.g., TP/FP/FN/TN, k, pooled estimate, CI, subgroup count).
- Source of the error (extraction, application of criteria, script literal, protocol
  mismatch, reviewer-consensus mismatch).
- Proposed resolution (exclude study, re-extract cell, correct script literal, amend
  protocol, reinstate study).

## 10.2 CSV Re-Verification

For every flagged cell, re-verify against the primary source (paper Table/Figure, page
number). Any revision-introduced value must carry the `[VERIFY-CSV]` tag until the
Phase 6b audit clears it.

## 10.3 Re-Run the Analysis Script

Re-execute the full synthesis pipeline with a fixed random seed. Save complete output to
`analysis/vNplus1_run.log`. Do not re-use partial v{N} output even for subsections that
"should be unchanged" — prove it with a fresh run.

## 10.4 Manuscript Auto-Sync

Every number the manuscript reports — k, pooled estimate, 95% CI, τ², I², subgroup
counts, sensitivity-analysis rows, GRADE levels — must be pulled from the fresh output.
Grep the manuscript for old v{N} numerical values to confirm no residue survives.

## 10.5 Supplementary Regeneration

Re-emit (do not patch):
- Extraction consensus log.
- RoB tables.
- GRADE / Summary of Findings table.
- PRISMA flow diagram (counts shift when studies are excluded/reinstated).

## 10.6 Figure Regeneration

Regenerate forest plots, funnel plots, subgroup plots, and the PRISMA flow via
`/make-figures`. Re-embed at the original manuscript positions. Confirm figure captions
match the new values (captions often contain pooled estimates).

## 10.7 Change Summary

Produce `v{N+1}_change_summary.md` with an explicit delta table:

| Item | v{N} | v{N+1} | Reason |
|------|------|--------|--------|
| k | | | |
| Primary pooled estimate (95% CI) | | | |
| Heterogeneity (I², τ²) | | | |
| Studies added | | | |
| Studies removed | | | |
| Subgroup re-stratification | | | |

This file is the external audit trail. It must be circulated with the v{N+1} manuscript.

## 10.8 PROSPERO (or Equivalent) Amendment

If eligibility, analysis population, or outcome definitions changed, file an amendment
to the registered protocol in parallel with the re-build:
- Keep revision notes within the registry's word limit (often 250 words).
- Frame the amendment as application correction, not criteria change:
  > "The pre-specified inclusion criteria are unchanged. The amended application excludes
  > {N} study(ies) whose characteristics were confirmed on independent re-review to fall
  > outside the pre-specified criteria."
- Submit the amendment before — or simultaneously with — re-circulation, so co-authors
  see an amendment already in flight rather than only a draft change.

## 10.9 Re-Circulation Framing

Use the Phase 9 thread. State the situation plainly in the first paragraph:

> "On re-review of v{N}, we identified {N} study(ies) whose data did not meet the
> pre-specified inclusion criteria. These were excluded and the analysis regenerated.
> The manuscript body, supplementary, and all figures have been re-rendered. A change
> summary is attached."

Tonal anchors worth preserving:
- "On re-review" — signals internal audit, not external pressure.
- "Pre-specified criteria" — the protocol itself is unchanged; application is corrected.
- "Change summary" — an external audit trail is available for scrutiny.

## 10.10 Anti-Patterns (do not)

- Hide the error and submit v{N} as-is. This converts a recoverable finding into a
  retraction-class incident if the reviewer catches it.
- Reframe the fix as a "minor revision" with no audit trail. Senior reviewers read audit
  trails; absence of one signals concealment.
- Disclose only in the cover letter while leaving Methods silent. Methods and the cover
  letter must agree.

## 10.11 When the Trigger Fires Post-Submission

If the audit trigger is detected after the journal submission but before an editorial
decision, notify the editorial office immediately and submit a corrected manuscript
alongside the disclosure. Do not wait for the reviewer to surface it; editors prefer
author-initiated correction.

## 10.12 Post-Recovery Loop

After v{N+1} is circulated, Phase 9 restarts. If a further audit trigger emerges during
the new review window, a second recovery sprint (v{N+1} → v{N+2}) is acceptable — but
each recovery costs co-author goodwill, so the incoming audit in Phase 6b should be
tightened each cycle rather than relying on Phase 10 as a routine catch.
