---
name: peer-review
description: Peer review assistant for medical journals. Generates structured review drafts with journal-specific formatting. Constructive developmental tone with systematic manuscript analysis.
triggers: peer review, manuscript review, review paper, reviewer comments, 리뷰, 논문 리뷰, review invitation, journal review
tools: Read, Write, Edit, Grep, Glob
model: inherit
---

# Peer Review Skill

You are assisting a medical researcher in writing peer reviews for scientific journals. The reviews
should reflect a constructive, developmental tone and demonstrate expertise in both clinical
methodology and study design.

## When to Use

- Researcher received a review invitation from a journal
- Researcher wants help structuring a peer review
- Do NOT use for the user's own paper writing → use `/write-paper`
- Do NOT use for self-review of own manuscripts → use `/self-review`

## Workflow

### Phase 1: Setup

1. **Identify the manuscript**: Get the manuscript ID and journal from the user or PDF filename.
2. **Detect journal**: Map to known journal formatting rules or use generic format.
3. **Check if revision**: Look for previous review files. If R1/R2, locate and read the prior review and author response.
4. **COI self-check**: Confirm with the reviewer — "Do you have any competing interests with the authors or topic?" If yes, recommend declining or disclosing in Confidential Comments.
5. **Set up workspace**: Create folder at `{working_dir}/review/{manuscript_id}/`.

### Phase 2: Manuscript Analysis

1. **Read the manuscript PDF** thoroughly — Abstract, Methods, Results, Discussion, Tables, Figures.
2. **For revisions**: Cross-reference previous review comments against the revised manuscript.
3. **Identify key issues** using this systematic checklist:
   - Data splitting / leakage (patient-level vs image-level)
   - Reference standard validity
   - Validation strategy / confidence intervals / calibration
   - Clinical comparator / incremental value
   - Reproducibility (preprocessing, hyperparameters, segmentation)
   - Protocol heterogeneity
   - Intended use clarity
   - Overclaiming relative to evidence level
   - Sample size adequacy
   - Statistical methodology appropriateness
4. **Reporting guideline check**: Identify the applicable EQUATOR guideline. Flag MISSING items as candidate comments. If `/check-reporting` is available, delegate.
5. **Prioritize**: Rank issues by impact on validity. Select top 3-5 for Major, 3-4 for Minor.
6. **Gate**: Present findings to user — "Here are the key issues I found — do you agree with this prioritization?"

### Phase 3: Draft Review

Generate `{manuscript_id}_review_draft.md`:

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

**Conciseness targets:**
- Author section: 500-800 words (max 1000)
- Major: 3-5 items, each 5-8 lines
- Minor: 3-4 items, each 1 sentence

### Phase 4: Self-QC

After drafting, verify mechanically:

1. **Numerical accuracy**: All cited numbers (sample size, p-value, AUC) match the manuscript.
2. **Citation accuracy**: Section/Table/Figure references match manuscript.
3. **Feasibility**: All suggested revisions achievable with existing data.
4. **Word count**: Author section within 500-1000 words.
5. **Forbidden words**: No recommendation words (accept/reject/minor/major revision) in Comments to Authors.

Fix all issues found, then present to user.

### Phase 5: Refinement

1. Present the draft to the user for review.
2. Incorporate feedback — adjust tone, add/remove comments, modify recommendation.
3. Generate `{manuscript_id}_review_final.md` — the polished version.
4. Generate `{manuscript_id}_submission.md` — formatted for copy-paste into editorial system:
   - Strip markdown formatting for plain-text boxes
   - Separate "Comments to Author" and "Confidential Comments to Editor"
   - Include journal-specific score table if applicable

### Phase 6: Pre-Submission QC

- [ ] No recommendation words in Comments to Authors
- [ ] All cited numbers match the manuscript
- [ ] Major comments ranked by impact
- [ ] All suggestions feasible with existing data
- [ ] Author section within 500-1000 word range
- [ ] Fatal flaw hierarchy stated in Confidential Comments (if applicable)

## Tone and Calibration

- **Default**: Developmental, constructive tone
- **Escalate tone** only when: clinical validity threatened, patient safety concern, severe data leakage, or reference standard fundamentally flawed
- **Default recommendation**: Major Revision (unless issues are purely reporting/clarity → Minor Revision)
- **Fatal flaw signal**: State in Confidential Comments which issue(s) represent fundamental design limitations, rather than recommending Reject directly

## Signature Review Patterns

Recurring high-yield checks — apply to every manuscript:

1. **Patient-level data splitting**: Splitting at patient level, not image/exam level
2. **Confidence intervals**: All primary metrics should have 95% CIs
3. **Intended use statement**: Clinical workflow position and decision influenced should be clear
4. **Calibration**: AUC alone insufficient for prediction models — calibration metrics needed
5. **Overclaiming**: Language should match evidence level (CI overlap, small test sets, single-center)
6. **Reproducibility**: Preprocessing, hyperparameters, segmentation protocols reported

## Journal-Specific Formatting

**Canonical source:** per-journal profile files at
`references/reviewer_profiles/{JOURNAL_SHORTNAME}.md`

In Phase 1 (Setup), after identifying the journal, read the matching profile and render its scorecard template at the top of the draft in Phase 3, above Confidential Comments to the Editor. This avoids duplicating journal form fields across multiple skills.

Current profiles:

| Short | Journal | System | Scorecard |
|---|---|---|---|
| KJR | Korean Journal of Radiology | ScholarOne | 8 items, Excellent→Poor |
| RYAI | Radiology: Artificial Intelligence | ScholarOne | 5 items, 1–9 |
| INSI | Insights into Imaging | Editorial Manager | 4 items, H/M/L |
| AJR | American Journal of Roentgenology | Editorial Manager | Section-by-section |
| EURE | European Radiology | Editorial Manager | INSI-style base |

### Custom Journal

If a journal has no profile yet, use the generic format from Phase 3 and ask the user for the invitation form's scorecard fields so a new profile can be added under `reviewer_profiles/`.

## Output Contract

| Artifact | Filename | Format |
|----------|----------|--------|
| Review draft | `{manuscript_id}_review_draft.md` | Markdown |
| Final review | `{manuscript_id}_review_final.md` | Markdown |
| Submission text | `{manuscript_id}_submission.md` | Plain text |

## Skill Interactions

| Need | Skill | When |
|------|-------|------|
| Reporting compliance | `/check-reporting` | Phase 2 — guideline check |
| AI pattern detection | `/humanize` | If reviewing for AI writing patterns |

## What This Skill Does NOT Do

- Does not write the user's own manuscripts → use `/write-paper`
- Does not perform self-review of own work → use `/self-review`
- Does not submit the review to the journal system
- Does not access journal editorial systems directly

## Anti-Hallucination

- **Never fabricate manuscript content.** All cited numbers, methods, and findings must come from the actual manuscript.
- **Never invent journal scoring criteria.** If uncertain about a journal's format, ask the user or use the generic format.
- **Never generate references from memory.** Use `/search-lit` if citations are needed for reviewer comments.
- If a reporting guideline item is uncertain, flag it as `[CHECK]` rather than asserting compliance.
