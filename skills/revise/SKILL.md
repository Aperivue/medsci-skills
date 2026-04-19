---
name: revise
description: Parse peer reviewer comments and generate a structured Response to Reviewers document with tracked manuscript changes. Classifies comments as MAJOR/MINOR/REBUTTAL, coordinates new analyses with /analyze-stats and /make-figures, and produces cover letter for editor.
triggers: revise paper, respond to reviewers, revision letter, reviewer comments, major revision, minor revision, resubmit, R1 revision, revision round, response letter, point-by-point response
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Revision Skill -- Response to Peer Reviewers

## Purpose

Parse reviewer decision letters, classify each comment by type, generate a formal Response to Reviewers document, track required manuscript changes, and coordinate with /analyze-stats or /make-figures when new analyses or visuals are needed.

---

## Activation

When the user provides reviewer comments (pasted text, PDF, or file path), or requests revision of a manuscript, this skill activates. Before proceeding, confirm:

1. The reviewer decision letter (pasted text or file path)
2. The current manuscript file (`paper/main.tex` or `paper/main.qmd`)
3. The revision round number (default: R1)
4. The journal name (affects cover letter format)

---

## Step 1: Parse and Number All Comments

Read the full decision letter. Extract every discrete comment from every reviewer and the editor.

### Numbering Convention

```
E-1, E-2, ...       <- Editor comments
R1-1, R1-2, ...     <- Reviewer 1 comments
R2-1, R2-2, ...     <- Reviewer 2 comments
R3-1, R3-2, ...     <- Reviewer 3 (if present)
```

If a reviewer groups multiple requests in one paragraph, split them into sub-items: `R1-3a, R1-3b, R1-3c`

### Classification

| Type | Symbol | Definition |
|------|--------|------------|
| **MAJOR** | `[MAJ]` | Requires new experiment, re-analysis, new figure/table, or substantial structural rewrite |
| **MINOR** | `[MIN]` | Requires text revision, clarification, formatting change, or additional citation |
| **REBUTTAL** | `[REB]` | Reviewer is factually incorrect, misunderstood the study, or requests something scientifically unjustified |

Output a classified comment list before generating responses:

```
E-1   [MIN]  Request to shorten abstract
R1-1  [MAJ]  Requires subgroup analysis by scanner type
R1-2  [MIN]  Clarify exclusion criteria rationale
R1-3  [REB]  Claims our sample size is underpowered (we disagree)
R2-1  [MAJ]  Requires additional figure showing calibration curve
R2-2  [MIN]  Add reference to [Author Year]
```

**Gate:** Present the classified comment list to the user. Confirm classifications
(especially REBUTTAL vs MAJOR) before generating responses. A misclassified REBUTTAL
generates a response that argues with a valid reviewer point.

---

## Step 2: Triage -- Flag External Actions Needed

Before writing responses, identify which comments require external action:

**Comments requiring /analyze-stats:** Flag any MAJOR comment that requires new statistical analysis, re-run of existing analysis, additional metric (calibration, NRI, ICC), or sample size recalculation.

**Comments requiring /make-figures:** Flag any MAJOR comment that requires a new figure or revised figure (calibration plot, subgroup forest plot, Bland-Altman, new panel).

Output: "The following comments require statistical analysis before responses can be finalized: R1-1, R2-3. Run /analyze-stats with these tasks, then return to /revise."

---

## Step 2.5: Revision Numerical Lineage Check (MANDATORY)

Revision-time is the highest-risk moment for numerical hallucinations. A new analysis script
written to satisfy a reviewer — typically a comparative arm, a subgroup, or a sensitivity
check — frequently hand-enters values copied by eye from the original paper's tables, bypassing
the locked extraction CSV. The resulting numbers then flow into the response letter, the
revised manuscript, and regenerated figures, and they can be internally consistent everywhere
while still being wrong at the source.

**Precedent incident — treat as a lived failure, not hypothetical:**
> CBCT Ablation MA-2 R1 revision introduced a new `ma2_comparative_arm.R` script to respond
> to a reviewer's comparative-analysis request. The Fisher exact matrix was hand-typed from
> Du 2023 Table 3, with the CTCAE-Grade column misread as the event count. The script, the
> revised manuscript, and Table 4 all converged on "3/45 vs 0/56, p=0.085" — direction
> reversed from the actual "0/45 vs 1/56, p=0.37."

**Non-negotiable actions when Step 2 flags any `/analyze-stats` re-run:**

1. **Tag every new numerical claim with `[VERIFY-CSV]`** as it is written into the revised
   manuscript, response letter, or new table. The tag is a tripwire — it only comes off at
   Step 7 (Final Verification) after explicit CSV + primary-source back-check.

2. **New analysis scripts must read from the locked extraction CSV.** Hand-typed `matrix()`,
   `c(...)`, or `data.frame(...)` numerical inputs are PROHIBITED when a CSV row exists. If
   hand entry is truly unavoidable (e.g., comparative-arm subset not present in the CSV), the
   line MUST carry a comment citing the CSV coordinate AND the primary-source Table/Figure:
   ```r
   # source: data_extraction_final.csv row 23 (Du 2023 CBCT arm),
   #         verified against Du 2023 Table 3 (Quant Imaging Med Surg 2023;13(9)), p.6
   fisher.test(matrix(c(0, 45, 1, 55), nrow = 2, byrow = FALSE))
   ```

3. **Comparative / arm-specific values must enter `extraction_consensus_log.md` as separate
   rows** before the analysis script references them. Do not let a new script invent values
   that never passed through the dual-extraction consensus layer.

4. **Revision-time numerical audit table** — maintain this inside the response document draft
   and copy into the final change log:

   | New claim (response + manuscript location) | Source script:line | CSV row/col | Primary source (Table/Fig, page) | Match? |
   |---|---|---|---|---|

5. **Gate before Step 3** — do not generate response prose for a MAJOR comment whose new
   numbers have not yet cleared this check. Prose written around un-audited numbers is very
   hard to unwind cleanly after a mismatch is found.

**Why this matters for reviewer politics:** a numerical reversal caught by the reviewer in R2
is far more damaging than the same error caught internally in R1 — it implies extraction
integrity problems to the editor and licenses deeper scrutiny of the rest of the data. Treat
Step 2.5 as a reputation-preservation gate, not just a QC step.

---

## Step 3: Generate Response to Reviewers Document

**Output location:** `revision/R[N]/response_to_reviewers_R[N].md`

### Document Header

```
Response to Reviewers

Manuscript ID: [JOURNAL-XXXXX]
Manuscript Title: [Full title]
Authors: [Last name of first author] et al.
Revision Round: [R1 / R2 / R3]
Date: [YYYY-MM-DD]

We thank the Editor and reviewers for their careful reading of our manuscript
and their constructive comments. We have revised the manuscript accordingly
and provide a point-by-point response below. All changes are shown in the
revised manuscript with tracked changes (or highlighted in yellow).
```

### Per-Comment Response Block

```
---

**Comment R[X]-[Y]** [MAJ/MIN/REB]

*Reviewer's comment:*
> [Exact text of the comment, quoted verbatim]

**Response:**

[Response text -- format by type below]

**Manuscript change:**
- Section: [Methods / Results / Discussion / etc.]
- Page [X], Line [Y] (in the revised manuscript)
- [Quote the new or changed sentence if short]
```

---

## Step 4: Response Formats by Comment Type

### MINOR Comment

Keep concise (3-8 sentences). Acknowledge, explain the change.

```
We thank the reviewer for this observation. We have [describe change] in
the [section] section. The revised text now reads: "[new sentence]."
```

### MAJOR Comment

Structured response with four parts: acknowledgment -> new analysis -> key result -> location of changes.

```
We thank the reviewer for this important suggestion. [State the concern.]

To address this, we [describe new analysis/experiment/rewrite].
[Key result: metric = value (95% CI, lower-upper; P = exact value)]
(All new results MUST include 95% CI and exact p-value.)

This finding [supports / strengthens / does not change] our original
conclusion because [brief interpretation].

Note: New text added to the Results section must contain only factual
findings. Interpretation belongs in the response letter text or Discussion.

We have added:
- New [Table X / Figure X / Supplementary Table X] showing [content]
- Methods revised: Page X, Lines Y-Z
- Results revised: Page X, Lines Y-Z
```

### REBUTTAL Comment

Polite but firm. Do not capitulate without scientific justification.

```
We thank the reviewer for raising this point. We respectfully suggest
that [restate reviewer's claim], while we [state your position].

[Explanation with supporting evidence. Cite literature if available:
"This is consistent with [Author et al., Year; PMID XXXXXX], who
demonstrated that..."]

[If applicable: "We have added the following clarifying sentence to
[section] (Page X, Line Y): '[new sentence].'"]

We believe this issue does not warrant [the specific change requested]
because [reason]. We hope the reviewer finds this explanation satisfactory.
```

---

## 5-Category Triage Strategy

Before writing individual responses, classify every comment into one of five categories.
This classification determines the response template and effort level. Process Category 1
(Simple) comments first — they are the most numerous and clearing them early reduces the
perceived workload.

### Category 1: Simple Question (most common)

Reviewer asks for additional description, clarification, or minor data.
**Response**: Add the requested text and point to the location. Keep the response short.
**Example**: "Please specify the study period" → add dates, reply "Done. See page X, line Y."

### Category 2: Misunderstanding

Reviewer misinterpreted the study design, population, or analysis.
**Response**: Never say "you are wrong." Instead: "We apologize for the lack of clarity"
→ re-explain the intended meaning → revise the manuscript text to prevent future confusion.

### Category 3: Further Discussion

Reviewer raises a contextual concern (different healthcare system, different clinical practice).
**Response**: Acknowledge the valid perspective → explain your study context → add a brief
note in Discussion if appropriate. The full explanation can stay in the response letter
without bloating the manuscript.

### Category 4: Additional Results

Reviewer requests new analysis (subgroup, sensitivity, additional metric).
**Response**: Perform the analysis → add results to Supplementary (or main text if important)
→ describe what was done and what was found. Treat this as a constructive contribution,
not an attack. **Never ignore these requests** — reviewer engagement is a positive signal.

### Category 5: Statistical Method Challenge

Reviewer questions or requests changes to statistical methods.
**Response**: Consult a biostatistician if unfamiliar → provide a reasoned justification
for your method choice with references → if the reviewer's suggestion is valid, perform
both analyses and show results are consistent. "This analysis was reviewed in consultation
with our biostatistician" adds credibility.

### Mapping to MAJ/MIN/REB

| Category | Typical Classification |
|----------|----------------------|
| 1. Simple Question | MIN |
| 2. Misunderstanding | MIN or REB |
| 3. Further Discussion | MIN (if text change) or REB (if disagree) |
| 4. Additional Results | MAJ |
| 5. Statistical Challenge | MAJ |

Use the 5-category triage to inform the MAJ/MIN/REB classification in Step 1, not replace it.

---

## Handling Low-Quality Reviews

Reviewer quality varies widely. When facing comments that suggest the reviewer did not
carefully read the manuscript:

1. **Do not get combative.** Respond with the same professionalism regardless of review quality.
2. **Address every point**, even trivial or off-topic ones. Skipping a comment signals
   disrespect to the editor.
3. **For irrelevant comments**: Add a clarifying sentence to Discussion or Methods, and
   reply: "We have added clarification in [section] to address this concern." This shows
   effort without conceding a scientific point.
4. **For factually incorrect comments**: Provide evidence (with references) politely.
   Frame as "We believe there may be a misunderstanding" rather than "The reviewer is wrong."
5. **Remember the audience**: The response letter is read by the editor, not just the
   reviewer. A measured, thorough response demonstrates manuscript quality even when
   the review does not.

---

## Step 5: Cover Letter to Editor

**Output location:** `revision/R[N]/cover_letter_R[N].md`

```
[Date]

Dear Dr. [Editor Name / "Editor-in-Chief"],

Thank you for the opportunity to revise our manuscript, "[Full title]"
(Manuscript ID: XXXX), submitted to [Journal Name]. We have carefully
reviewed the comments from the Editor and reviewers and have revised
the manuscript accordingly.

In brief, the principal changes in this revision are: [1) ..., 2) ...,
3) ...]. A point-by-point response to each comment is provided in the
accompanying Response to Reviewers document. Revised sections are
highlighted in yellow in the manuscript.

We believe the revised manuscript addresses all concerns raised in the
review and is now suitable for publication in [Journal Name].

Sincerely,

[First Author Name], MD/PhD
[Institution]
[Email]
On behalf of all authors
```

---

## Step 6: Change Log

**Output location:** `revision/R[N]/change_log_R[N].md`

| Comment | Type | Change Made | Section | Page | Lines |
|---------|------|-------------|---------|------|-------|
| R1-1 | MAJ | Added subgroup analysis by scanner type | Results 4.3, Table 3 | 12 | 234-251 |
| R1-2 | MIN | Clarified exclusion criteria for motion artifact | Methods 2.2 | 6 | 112-115 |

---

## Step 7: Final Verification

After all responses are drafted, check:

- [ ] Every reviewer comment has a response (none skipped)
- [ ] Every MAJOR comment has a corresponding manuscript change with location
- [ ] Every REBUTTAL is backed by cited evidence or clear scientific reasoning
- [ ] All new statistics include 95% CI and exact p-values
- [ ] Page/line number references match the revised manuscript (not the original)
- [ ] Cover letter is addressed to the correct editor
- [ ] Response letter is 5000-8000 words
- [ ] Tracked changes are enabled in the revised manuscript
- [ ] All new figures/tables are referenced in the response letter

---

## Revision Round File Structure

| Round | Folder | Files |
|-------|--------|-------|
| R1 | `revision/R1/` | `response_to_reviewers_R1.md`, `cover_letter_R1.md`, `change_log_R1.md` |
| R2 | `revision/R2/` | `response_to_reviewers_R2.md`, `cover_letter_R2.md`, `change_log_R2.md` |

Revised manuscript: `paper/main_revised_R[N].tex` (or `.qmd`)

For R2+, acknowledge whether R1 concerns were fully resolved. If a reviewer raises a new concern at R2, note: "This comment was not raised in the first review round; we address it as follows."

---

## Word Count Guidance

- Response letter total: 5000-8000 words (including quoted reviewer comments)
- Cover letter: 200-400 words
- MINOR response: 50-150 words
- MAJOR response: 150-400 words
- REBUTTAL response: 200-500 words

---

## Common Mistakes to Avoid

1. Do not agree with every MAJOR comment without providing the actual new data or analysis.
2. Do not write vague responses ("We have revised the text accordingly") without specifying what changed and where.
3. Do not skip any comment, even if trivial or addressed elsewhere.
4. Do not reference page/line numbers from the original manuscript; use the revised version.
5. Do not begin a rebuttal aggressively; always open with acknowledgment.
6. Do not promise changes that were not actually made.
7. Do not forget to renumber figures and tables if new items were inserted.

## Anti-Hallucination

- **Never fabricate references.** All citations must be verified via `/search-lit` with confirmed DOI or PMID. Mark unverified references as `[UNVERIFIED - NEEDS MANUAL CHECK]`.
- **Never invent clinical definitions, diagnostic criteria, or guideline recommendations.** If uncertain, flag with `[VERIFY]` and ask the user.
- **Never fabricate numerical results** — compliance percentages, scores, effect sizes, or sample sizes must come from actual data or analysis output.
- If a reporting guideline item, journal policy, or clinical standard is uncertain, state the uncertainty rather than guessing.
