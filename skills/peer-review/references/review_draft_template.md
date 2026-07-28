# `{manuscript_id}_review_draft.md` — the literal template

Load-on-demand companion to `/peer-review` Phase 3. SKILL.md keeps what governs the
*content* of a review — the request-type discipline (disclosure vs computation) and the
3-tier length targets. This file is the output skeleton.

Read it when you sit down to write the draft.

Both comment blocks below are load-bearing and **must not be transposed**: the
Confidential-to-Editor block carries the recommendation and must never reach the authors.
Verify the split on the rendered proof, not on this draft — the portal's two free-text
boxes are adjacent and unvalidated.

```markdown
# {manuscript_id} — Review Draft

**Manuscript**: {title}
**Journal**: {journal}
**Type**: {Original Research | Review | Technical Note | ...}
**Recommendation**: {Major Revision | Minor Revision}

---

## {Journal-specific scores section, if applicable}

---

## CONFIDENTIAL COMMENTS TO THE EDITOR

{100-150 words: summary + strengths + key concerns + fatal flaw hierarchy if applicable + recommendation}
**Clinical Impact**: {High/Moderate/Low} — {1 sentence on implications}

---

## COMMENTS TO THE AUTHORS

**Research Summary & General Comments**

{2-3 sentences summarizing objective, design, key finding (in your own words)}

Major strengths:
1. {Specific strength}
2. {Specific strength}
3. {Specific strength (optional)}

{Scope + feasibility: 1-2 sentences — "I have suggestions focused on [areas]. Achievable within existing data."}

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
