# `{manuscript_id}_review_draft.md` — the literal template

Load-on-demand companion to `/peer-review` Phase 3. SKILL.md keeps what governs the
*content* of a review — the request-type discipline (disclosure vs computation) and the
3-tier length targets. This file is the output skeleton.

Read it when you sit down to write the draft.

Both comment blocks below are load-bearing and **must not be transposed**: the
Confidential-to-Editor block carries the recommendation and must never reach the authors.
Verify the split on the rendered proof, not on this draft — the portal's two free-text
boxes are adjacent and unvalidated.

**Provisional editor record** (Phase 2 step 1 sends you here before the detailed checks). After
the first full read, write elements (1), (2) and (4) of the editor block below as a provisional record in
`work/` (a fixability call may be "unclear" at this point). Finalize the block after
verification. If the final recommendation differs from the provisional one, in either direction,
add one line to the record naming the new fact or the corrected reasoning. Keep both versions:
together they are the reviewer's calibration record.

```markdown
# {manuscript_id} — Review Draft

**Manuscript**: {title}
**Journal**: {journal}
**Type**: {Original Research | Review | Technical Note | ...}
**Recommendation**: {the journal's own options, e.g. Accept | Minor Revision | Major Revision | Reject & resubmit | Reject}

---

## {Journal-specific scores section, if applicable}

---

## CONFIDENTIAL COMMENTS TO THE EDITOR

{100-150 words, in this order:
 (1) the manuscript's main claim, in one sentence;
 (2) the major issues ranked by their effect on that claim, each graded as in
     `reviewer_calibration/recommendation_calibration.md`: fixable with existing data / fixable
     with additional work on the existing material (state the scope) / not fixable in this
     submission / unclear;
 (3) the balance of contribution against limitations, including strengths;
 (4) the recommendation, consistent with (2): an unfixable issue that undercuts the main claim
     governs it, unless a narrower contribution still stands on its own.}
**Clinical Impact**: {High/Moderate/Low} — {1 sentence on implications}

---

## COMMENTS TO THE AUTHORS

**Research Summary & General Comments**

{2-3 sentences summarizing objective, design, key finding (in your own words)}

Major strengths:
1. {Specific strength}
2. {Specific strength}
3. {Specific strength (optional)}

{Scope + feasibility: 1-2 sentences — "I have suggestions focused on [areas]." Describe feasibility from the fixability grades in the editor block (for example, "most can be addressed with the existing data; point 2 would need [additional work]"), not as a stock phrase.}

(80-150 words total)

**Major Comments**

1) **{Issue title}**

{Problem 1-2 sentences. Location cited.}

Suggested revisions:
- {Fix 1}
- {Fix 2}

2) **{Issue title}**
...

**Minor Comments**

1) {One sentence, location cited.}
2) ...

**Closing Remark**

{2-3 sentences, constructive.}
```
