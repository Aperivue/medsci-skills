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

## Reference Files

- **Response-letter voice gallery**: `${CLAUDE_SKILL_DIR}/references/r2r_voice.md` -- before/after examples, three response skeletons (accept / partial-accept / polite-rebuttal), and a meta-phrase-to-natural conversion table. Read it before drafting the Response to Reviewers document.

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

**Comments requiring /analyze-stats:** Flag any MAJOR comment that requires new statistical analysis, re-run of existing analysis, additional metric (calibration, NRI, ICC), or sample size recalculation. When the source is a `/self-review` finding, any issue carrying `requires_reanalysis: true` (power/MDE re-simulation under the full model, first-visit / one-record-per-subject dedup, an extended- or reduced-adjustment over-adjustment sensitivity, optimism correction of calibration) is automatically a `/analyze-stats` routing item — it cannot be answered by a prose edit, so it must produce a committed script + CSV whose numbers are then fed back here.

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

**Precedent failure pattern — treat as a lived failure, not hypothetical:**
> An R1 revision introduced a new comparative-arm analysis script to answer a reviewer
> request. The Fisher exact matrix was hand-typed from the primary source Table, with an
> adjacent severity-grade column misread as the event count. The script, the revised
> manuscript, and an accompanying Table all converged on the same direction-reversed
> numbers relative to what the primary source actually reported.

**Non-negotiable actions when Step 2 flags any `/analyze-stats` re-run:**

1. **Tag every new numerical claim with `[VERIFY-CSV]`** as it is written into the revised
   manuscript, response letter, or new table. The tag is a tripwire — it only comes off at
   Step 7 (Final Verification) after explicit CSV + primary-source back-check.

2. **New analysis scripts must read from the locked extraction CSV.** Hand-typed `matrix()`,
   `c(...)`, or `data.frame(...)` numerical inputs are PROHIBITED when a CSV row exists. If
   hand entry is truly unavoidable (e.g., comparative-arm subset not present in the CSV), the
   line MUST carry a comment citing the CSV coordinate AND the primary-source Table/Figure:
   ```r
   # source: data_extraction_final.csv row <N> (<first-author> <year>, <arm> only),
   #         verified against <primary source> Table <X>, page <P>
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

**Voice caution:** The acknowledgment lines in these templates are schematic placeholders, not literal text to paste under every comment. Repeating the same opener ("We thank the reviewer for this important suggestion.") across a dozen responses is itself an AI-tell that careful reviewers notice. Vary the openers and apply the **Response-Letter Voice & AI-Tell Avoidance** section below before finalizing any response.

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

## Response-Letter Voice & AI-Tell Avoidance

A response-to-reviewers letter is a reviewer-facing scientific argument, not an internal
change-log. The dominant AI-tell in machine-drafted letters is the **editing-mechanism
register**: prose that narrates *how the text was edited* ("the revised Methods adds one
sentence at line 88", "a grep-and-soften pass replaced six phrases", "no further manuscript
change") instead of stating, in plain language, what changed and why.

Three principles when drafting (the AI-tell patterns themselves are defined once in humanize
`references/ai_patterns.md`, patterns 22-24 — this section is the authoring guidance):

1. **Write the change and the science, not the editing mechanism.** Describe what changed and
   why, and quote the new sentence. Never narrate the diff: no version prefixes ("v2 adds..."),
   no "softened N phrases", no grep/verification language, no internal FIX codes, no bare "No
   further manuscript change" stubs. Describing a *new analysis you ran* ("we performed a
   sensitivity analysis and found X") is the science, not a tell — that is welcome.
2. **No `§` symbols, no internal draft line numbers.** A revised-manuscript page/line
   ("page 7, lines 177-178", stated once as referring to the revised manuscript) is fine;
   only internal draft line numbers that will not match the reviewer's view are banned.
3. **Format is free.** Free prose, a structured `Response:` / `Changes made:` block, an
   `Original → Revised` pair, or a left-comment/right-response table are all standard human
   conventions. Pick any; strip only the mechanism narration.

### Reviewer-facing tone

- **Vary openers.** "We thank the reviewer for this point." / "We agree." / "This is an important concern." / "We have addressed this as follows." Do not repeat one acknowledgment sentence down the whole letter.
- **Calibrate the stance**: full agreement, partial agreement with a bounded clarification, or a polite, evidence-backed rebuttal. Match the register to the substance.
- **Admit error plainly** when the reviewer is right ("The reviewer is correct; we have corrected this.") — natural humility reads as human and builds editor trust.
- **Quote the new manuscript text** verbatim in quotation marks, then name its section — what experienced authors do, and the single strongest human signal across real letters.

### Succinctness & non-defensiveness (especially R2+)

Let the point-by-point prove the work; strip the pre-emptive defence. This matters most on **R2+ rounds**, where over-explaining reads as anxiety rather than rigor.

- **No pre-emptive hand-holding.** Drop "Reviewers 2 and 3 also accepted this," "we left it unchanged because the other reviewers were satisfied," and similar cross-reviewer lobbying. Answer the comment in front of you.
- **A satisfied reviewer gets one sentence.** If a reviewer is content or offers only praise, "We thank the reviewer." or a single sentence is the whole response. Do not manufacture paragraphs.
- **Cut defensive meta-comments.** Remove "We confirm this statement is unchanged and not softened," "These passages already make the point, so no further text was added." State plainly where the matter is handled and move on.
- **Fold methodology disclosure into the comment it answers.** Multiplicity, a SAP deviation, or an analysis caveat goes inside the relevant response — not into a separate "Statistical note" front section. Keep the disclosure (never hide a deviation), but keep it in place.
- **Split, do not bundle.** When a reviewer packs several points into one paragraph, answer each as its own comment with that reviewer sentence quoted, not one block reply to the whole paragraph. Succinct means short *answers*, not fewer *comments*.

See `${CLAUDE_SKILL_DIR}/references/r2r_voice.md` for the before/after gallery, response
skeletons, and the meta-phrase conversion table.

### Mandatory pre-submission scan

Before circulating or uploading the response letter and cover letter, run `/humanize` on
**both documents**. The R2R AI-tell patterns (22-24) are defined in humanize
`references/ai_patterns.md`; together with 13 (em dash), 16 (filler), and 19 (`§`) they form
the response-letter scan. Also apply `~/.claude/rules/manuscript-style-classical.md` (`§`,
em-dash, heading discipline) — the same senior-reviewer red flags apply to the letter.

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

### R1 vs R2+ cover-letter protocol

The template above is the **R1** convention: a standalone editor cover letter (200-400 words).

On an **R2+ round (second revision onward), do not write a separate cover letter.** Whatever you would say to the editor — the greeting and the brief change summary — belongs in the **head of the response-to-reviewers letter**, not in a second document. A standalone cover letter that merely restates the response letter's summary reads as redundant and, on later rounds, as boilerplate. If an earlier round already produced a `cover_letter_R1.md`, move it to `_superseded/`, exclude it from the R2+ package, and reuse the response-letter head verbatim in any portal "cover letter" field. (Exception: a journal that explicitly requires a separate cover letter at every round — then keep the head summary and the cover letter from duplicating each other.)

**Response-letter head (R2+)** — placed at the top of `response_to_reviewers_R[N].md`, before the point-by-point:

```
Dear Dr. [Editor Name / "Editor-in-Chief"],

Thank you for the opportunity to revise our manuscript once more. In brief, this
revision [1-2 sentence summary of the principal changes — e.g., "adds the requested
subgroup analysis and tempers the three comparisons the reviewers flagged as
over-stated"].

[If applicable: one sentence on a companion paper, a re-analysis, or a verification
the editor requested.]

All quotations below are from the revised manuscript. A point-by-point response to each
comment follows.

Sincerely,
[First Author Name], on behalf of all authors
```

Keep the head to a short greeting, a one-paragraph "in brief," an optional companion/verification note, the single line stating quotations are from the revised manuscript, and the signature. Everything else is point-by-point.

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
- [ ] No internal draft line numbers ("(line 43)"); locations point to section names or revised-manuscript page/line
- [ ] No `§` symbols and no editing-mechanism narration ("v2 adds one sentence", "grep verification", "No further manuscript change")
- [ ] Acknowledgment openers varied (not one sentence repeated across responses)
- [ ] Response letter AND cover letter ran through `/humanize` (patterns 22-24 triage hits reviewed; confirmed instances = 0; `§` = 0 hard)
- [ ] (R2+) No separate cover letter — the editor greeting and "in brief" summary are folded into the response-letter head
- [ ] (R2+) Satisfied reviewers get ≤1-2 sentences; no pre-emptive hand-holding or cross-reviewer lobbying
- [ ] Multi-point reviewer paragraphs are split into discrete comments (reviewer sentence quoted + Response N), not answered as a block
- [ ] Methodology disclosure (multiplicity, SAP deviation) is folded into the relevant response, not a separate front section
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
- Cover letter: 200-400 words (R1 only; on R2+ there is no separate cover letter — see Step 5)
- MINOR response: 50-150 words
- MAJOR response: 150-400 words
- REBUTTAL response: 200-500 words
- **R2+ rounds run leaner.** Most R1 concerns are already resolved, so the letter is shorter and a satisfied reviewer's response is 1-2 sentences. Do not pad an R2+ reply to reach the R1 range.

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

---

## Gates

| Gate | Severity | Trigger | Action on fail |
|---|---|---|---|
| Comment classification (MAJOR / MINOR / REBUTTAL) | ENFORCED | comment unclassified or classification disputed | ask user; do not silently default |
| Step 2.5 `[VERIFY-CSV]` tagging on revision-introduced numbers | ENFORCED | new numerical claim added without `[VERIFY-CSV]` tag | tag automatically; HALT until CSV cross-check completes |
| Reference re-render after revisions touching citations | ENFORCED | any new `[@bibkey]` added in R1+ | route to `/manage-refs` Phase 7.6 re-render before R1 submission |
| `/verify-refs --strict` post-revision | ENFORCED | FABRICATED / HIGH_MISMATCH_FIRST_AUTHOR > 0 | HALT R1 submission |
| New analysis coordination | ENFORCED | reviewer asks for new analysis | route to `/analyze-stats` (and `/make-figures` if figure changes); never hand-write new numbers |
| Body word count vs journal cap (revision-inflation trap) | ENFORCED after every revise pass | resolving majors pushes the body over the target journal's word limit | run `/sync-submission` `scripts/check_wordcount_cap.py` (`--journal-profile` or `--limit`; prefer the rendered DOCX count); `WORDCOUNT_OVER_CAP` blocks submission — relocate methods/sensitivity detail to the Supplement, do not silently exceed |
| Cover letter to editor | ENFORCED at R1 submission | R1 missing editor cover letter | block submission |
| R2+ cover-letter handling | ENFORCED at R2+ submission | standalone cover letter present on an R2+ round (not folded into the response-letter head) | move it to `_superseded/`; fold the summary into the head |
| Response-letter voice / AI-tell | ENFORCED before submission | editing-mechanism narration, internal draft line refs, `§`, tooling leak, or repeated openers in response/cover letter | run `/humanize` (patterns 22-24 as triage; `§` = 0 hard); resolve confirmed tells before submission |
