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
3. **Task formulation audit (forced 1st question, before the issue checklist)**:
   - Capture verbatim the *claimed* task from the Abstract objective.
   - Capture verbatim the *measured* task from Methods (inputs → outputs).
   - Do the two match? Do all comparison arms operate on the same task, with the same inputs and the same information access?
   - Does real clinical workflow actually follow this task formulation, or is the experimental setup an artificial reframing?
   - If a mismatch exists, register it as the Major #1 candidate. Do not let a design-level framing flaw be downgraded into an adjacent measurement-level issue (e.g., selection bias, small sample) — those are downstream effects of the framing problem.
   - **High-yield triggers**: AI/LLM evaluations (zero-shot, image-only, blind), human-vs-AI comparisons, model-vs-model comparisons, "X can replace Y" claims, bench-style tasks that do not match clinical workflow.
   - **Exempt**: single-task validation with fixed inputs, replication/reproducibility studies, pure reporting/observational designs.
4. **Identify key issues** using this systematic checklist:
   - Task formulation (carry forward from step 3 if a candidate was found)
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
5. **Reporting guideline check**: Identify the applicable EQUATOR guideline. Flag MISSING items as candidate comments. If `/check-reporting` is available, delegate.
6. **Prioritize**: Rank issues by impact on validity. Select top 3-5 for Major, 3-4 for Minor. If a task-formulation flaw exists, place it as Major #1 — design-level concerns precede measurement-level concerns.
7. **Gate**: Present findings to user — "Here are the key issues I found — do you agree with this prioritization?"

### Phase 2A: Systematic Review / Meta-Analysis Extension

Apply this 8-probe checklist **only when manuscript type is "Systematic Review", "Meta-Analysis", or "Systematic Review and Meta-Analysis"**. These probes complement (do not replace) the generic Phase 2 issue checklist.

**SR-MA reviews almost always justify Tier 3 word budget** (1000-1400w) — apply ≥3 of P1-P5 triggering = Tier 3 default.

**P1 — DTA 2×2 cell extraction integrity (spot-check)**:
- For SR-MA with diagnostic accuracy outcomes, select ≥2 outlier studies (k=1 subgroup studies, extreme sens/spec, single-study outliers driving subgroup p-values).
- For each, retrieve source paper sensitivity / specificity (PubMed abstract or full-text).
- Compare manuscript forest plot cells (TP/TP+FN, TN/TN+FP) against source values.
- Common error: **sens/spec swap** at cell level. If a study has source sens=A% / spec=B% but manuscript forest reports sens=B% / spec=A%, this is a cell-assignment error.
- If found, register as MAJOR (#1 if it drives a reported subgroup p-value).

**P2 — Cohort overlap probe**:
- Identify clusters in included studies sharing: (a) institution name, (b) author surname + year proximity, (c) public ICU/EHR database (MIMIC-IV, eICU, MIMIC-III, KNHIS, UK Biobank, Optum, MarketScan, IBM).
- For each cluster, fetch PubMed efetch affiliation + abstract Methods database source.
- Flag pairs sharing same data source + overlapping enrollment period as "high-confidence overlap".
- Manuscript should acknowledge in Limitations + perform sensitivity analysis. If absent → MAJOR.

**P3 — Diagnostic subset N transparency (mixed DTA + prognostic MA)**:
- Compute bivariate pool denominator (TP+FP+TN+FN) from Table 2 or forest plot.
- Compare to total N reported in Abstract.
- If diagnostic subset is <50% of total without explicit "diagnostic subset N = X / Y" in Results → MAJOR transparency gap.

**P4 — k=1 subgroup flag**:
- Inspect subgroup analyses for strata with k=1 (single included study).
- If a reported subgroup p-value is driven by k=1 stratum → flag MAJOR.
- Recommend reframing as exploratory or removing from formal subgroup test.

**P5 — Supplementary completeness check**:
- SR-MA supplementary must contain at minimum:
  - PRISMA / PRISMA-DTA checklist with page refs
  - Full-text exclusion list with reasons (per PRISMA 2020 item 16b)
  - Per-study data extraction table
  - Per-study × per-domain risk-of-bias table (QUADAS-2 / QUADAS-AI / PROBAST / PROBAST-AI)
  - Full search strategy verbatim per database
- If supplementary contains only figure captions or is missing 3+ of these → MAJOR.

**P6 — PROSPERO ID format + live URL request**:
- Standard PROSPERO format: `CRD42` + 4-digit YYYY + 6-digit sequential = 13 chars total. Some pre-2020 IDs are 12 chars (5-digit sequential).
- IDs with >13 chars or non-numeric tail → FORMAT_ANOMALY (MAJOR).
- Always request authors provide live registration URL in cover letter for protocol cross-check.

**P7 — Reference duplicate detection** (extends `/verify-refs`):
- Run `/verify-refs` (PubMed + CrossRef). In addition to standard checks, detect duplicate PMID or DOI within reference list.
- Verbatim duplicates indicate LLM-assisted reference compilation error → MAJOR (cite renumbering required).

**P8 — AI Disclosure presence**:
- `grep -iE "chatgpt|gpt-|llm|generative ai|ai was used|ai-assisted|copilot|claude|gemini|chatbot|large language model"` on manuscript body.
- If 0 matches AND journal requires AI Disclosure (RYAI / Radiology / RSNA family / Lancet family / JAMA family / most BMJ family / Nature family) → flag MINOR-to-MAJOR.

**Output template (P1 example)**:
> "I spot-checked [Author Year] (PMID [...]) against the source paper and found that the values in Figure X are swapped. The source paper reports external-test sensitivity A% / specificity B% (n=N); the manuscript forest entries place [num1/denom1] in the sensitivity slot (which is the source's specificity numerator/denominator) and [num2/denom2] in the specificity slot (which is the source's sensitivity)."

**Output template (P2 example)**:
> "[Author1 Year1] uses [Database] (N=...). [Author2 Year2] uses [Database] (N=...). These are nearly certainly overlapping patient pools, and statistical independence assumption for MA pooling is violated. I'd suggest a sensitivity analysis excluding one of the two studies, plus an explicit cohort-source column in Table 1."

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

**Length targets (3-tier, data-grounded)**:

> **Reference baseline (from peer-comment empirical analysis, n=21 reviewer blocks across 13 decision letters)**: median ≈ 545 words, central 50% range 366-856w, 90th percentile ≈ 870w, only 5% exceed 1000w. Most peer reviewers cluster below 900w.

- **Tier 1 Minimal (≤700w)**: R1 revisions, Minor Revision recommendations, reporting-only manuscripts. Major 1-3, Minor 3-5.
- **Tier 2 Standard (700-1000w) ★ default — most reviews should land here**: typical first-round reviews with 1-2 design-level concerns. Major 3-5, Minor 4-6. Sweet spot 800-950w — sits just above the 90th percentile of peer reviewers, expressing design-level rigor without overwhelming editor parsimony.
- **Tier 3 Extended (1000-1400w)**: justified only when (a) fatal-flaw hierarchy required (≥2 design-level limitations), (b) cross-domain methodology (medical AI × radiology × biostatistics), (c) task-formulation misframing critique, or (d) AI/LLM evaluation requiring model-spec + prompt + selection-bias + framing 4-layer audit. Major 3-5, Minor 5-7. Frequency cap: ≤20% of reviews rolling — if every review trends Tier 3, the niche signal dilutes.
- **Hard cap 1400 words**. Measure with `awk + wc` (no estimation) — at Phase 3 mid-checkpoint and Phase 6 final.
- Each Major: 5-8 lines (Tier 1-2) or 8-12 lines (Tier 3, with Why it matters + alternative framings).
- **Reference-baseline ratio** (self-QC metric): compute `your_wc / 545` and report. Ratio > 2.0 (above 1090w) flags trim candidate. Ratio < 1.0 may indicate insufficient design-level rigor for AI/methodology critique reviews.

### Phase 4: Self-QC

After drafting, verify mechanically:

1. **Numerical accuracy**: All cited numbers (sample size, p-value, AUC) match the manuscript.
2. **Citation accuracy**: Section/Table/Figure references match manuscript.
3. **Feasibility**: All suggested revisions achievable with existing data.
4. **Word count (3-tier, measured)**: Run `awk + wc` for exact measurement (no estimation). Identify which tier the Author section falls in (Tier 1 ≤700w / Tier 2 700-1000w ★ default / Tier 3 1000-1400w). Most reviews should land in Tier 2. If Tier 3, justify with a one-line rationale (which design-level concern warrants the extra length) and verify Tier 3 frequency stays ≤20% rolling. Hard cap 1400w. Also measure at Phase 3 mid-checkpoint, not only at final. Report **reference-baseline ratio** (`wc / 545w`) — ratio > 2.0 flags trim candidate.
5. **Forbidden words**: No recommendation words (accept/reject/minor/major revision) in Comments to Authors.
6. **Major #1 = task formulation flaw** (if present): if §3C-1 audit found framing mismatch, place it as Major #1. Do not let it be downgraded into adjacent measurement-level issues (selection bias, sample size).
7. **AI pattern density (quantified threshold)**: em-dash ≤2 per 1000 words, structural rule-of-three ≤2 per Major comment, significance inflation ("genuinely", "truly", "indeed") 0 per Major, hedged Minor proportion ≥50% ("could", "would help", "I'd suggest" vs bare "Please [verb]").
8. **Aczel tone audit** (`references/aczel_2021_reviewer2_patterns.md`):
   - 0 attitude markers (reject/absurd/ridiculous/naive/oblivious/fail)
   - 0 personal attacks ("the authors seem...", "the authors do not understand")
   - ≥2 first-person rapport instances in General Comments / Closing Remark
   - ≥50% of Minor requests use hedged forms ("I'd suggest," "could," "would help") rather than imperative ("must," bare "Please [verb]")
   - General Comments names ≥2 specific strengths before listing concerns
   - At most 1 typo/grammar Minor Comment, only if in formal section or systematic
9. **SR-MA-specific QC** (if Phase 2A applied): For each P1–P8 probe used, verify the corresponding Major comment cites source PMID + source page/table reference + verbatim quote. Reviews citing extraction errors without source-page reference are not actionable for authors.

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
- [ ] Major comments ranked by impact (Task formulation flaw, if present, as Major #1)
- [ ] All suggestions feasible with existing data
- [ ] Author section word count measured (awk + wc), tier identified (Tier 1 ≤700w / Tier 2 700-1000w ★ default / Tier 3 1000-1400w); Tier 3 justified + ≤20% rolling frequency
- [ ] Reference-baseline ratio (`wc / 545w`) reported; ratio > 2.0 trimmed
- [ ] Hard cap 1400 words not exceeded
- [ ] AI pattern density within thresholds (em-dash ≤2/1000w; structural rule-of-three ≤2/Major; significance inflation 0/Major; hedged Minor ≥50%)
- [ ] Fatal flaw hierarchy stated in Confidential Comments (if applicable)
- [ ] Reject recommendations (if used): §1C condition checklist (design-level flaw + speculative practical value 3-trigger + novelty gap) explicitly verified — at least 2 of 3 conditions met

## Tone and Calibration

- **Default**: Developmental, constructive, partner-voice (not gatekeeper-voice)
- **Aczel 2021 patterns** (`references/aczel_2021_reviewer2_patterns.md`): avoid attitude markers ("reject," "absurd," "oblivious"), boosters, personal attacks on authors, vague dismissals, and typo nitpicking; prefer first-person rapport ("I appreciate," "I stumbled over"), hedged suggestions ("I'd suggest," "could," "would help"), and critique aimed at the work rather than the people. Apply throughout drafting, not just QC.
- **Escalate tone** only when: clinical validity threatened, patient safety concern, severe data leakage, or reference standard fundamentally flawed
- **Default recommendation**: Major Revision (unless issues are purely reporting/clarity → Minor Revision)
- **Fatal flaw signal**: State in Confidential Comments which issue(s) represent fundamental design limitations, rather than recommending Reject directly
- **Length proportionality**: Minor Revision ≤ 600 words; Major Revision ≤ 1000 words. Length signals difficulty — a Minor Revision review longer than the manuscript itself reads as Reviewer 2.

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
