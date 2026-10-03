---
name: revise
description: Use when a manuscript comes back with reviewer or editor comments. Numbers every comment, classifies it MAJOR/MINOR/REBUTTAL, drafts a point-by-point response with tracked manuscript changes, routes new analyses to /analyze-stats and writes the cover letter.
metadata:
  triggers: "revise paper, respond to reviewers, revision letter, reviewer comments, major revision, minor revision, resubmit, R1 revision, revision round, response letter, point-by-point response"
---

# Revision Skill -- Response to Peer Reviewers

## Activation

When the user provides reviewer comments (pasted text, PDF, or file path) or asks to revise a manuscript, confirm before proceeding:

1. The reviewer decision letter (pasted text or file path)
2. The current manuscript file (`manuscript/manuscript.md`)
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

### 5-Category Triage Strategy

Sort every comment into one of five categories; the category sets the response approach and informs (does not replace) the MAJ/MIN/REB classification.

| Category | Reviewer is... | Response | Typical class |
|---|---|---|---|
| 1. Simple Question (most common) | asking for description, clarification, or minor data | Add the requested text and point to its location; keep the reply short | MIN |
| 2. Misunderstanding | misreading the design, population, or analysis | Never say "you are wrong": apologise for the lack of clarity, re-explain, and revise the text so the next reader is not misled | MIN or REB |
| 3. Further Discussion | raising context (a different health system or clinical practice) | Acknowledge, explain your study context, add a brief Discussion note if appropriate; the full explanation can stay in the letter | MIN (text change) or REB (disagree) |
| 4. Additional Results | requesting a subgroup, sensitivity analysis, or additional metric | Run it (Step 2), add results to the Supplement (main text if important), and say what was done and found; never ignore these requests | MAJ |
| 5. Statistical Method Challenge | questioning or asking to change the statistical method | Justify the method with references; if the suggestion is valid, run both analyses and show the results agree | MAJ |

Say a statistician was consulted only if one was: a claim about who reviewed the work is a factual claim to the editor.

Answer careless or off-topic comments too, with the same professionalism. For an irrelevant comment, add a clarifying sentence to Methods or Discussion and say where; that shows effort without conceding a scientific point. For a factually incorrect comment, give referenced evidence framed as "We believe there may be a misunderstanding."

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

Before writing responses, flag the comments that need external work:

- **/analyze-stats:** any MAJOR comment that needs new statistical analysis, a re-run of an existing analysis, an additional metric (calibration, NRI, ICC), or a sample size recalculation. A `/self-review` finding carrying `requires_reanalysis: true` (power/MDE re-simulation under the full model, first-visit / one-record-per-subject dedup, an extended- or reduced-adjustment over-adjustment sensitivity, optimism correction of calibration) is always routed here: a prose edit cannot answer it, so it must produce a committed script + CSV whose numbers are then fed back here.
- **/make-figures:** any MAJOR comment that needs a new or revised figure (calibration plot, subgroup forest plot, Bland-Altman, new panel).

Output: "The following comments require statistical analysis before responses can be finalized: R1-1, R2-3. Run /analyze-stats with these tasks, then return to /revise."

**If `/analyze-stats` or `/make-figures` is not installed**, emit the same routing list as a checklist for the author to run manually (the named analysis or figure per comment) and hold those responses as `BLOCKED — pending analysis/figure` until the committed script + CSV (or figure file) returns. Reviewer-response numbers always trace to a produced artifact, never to a model estimate.

---

## Step 2.5: Revision Numerical Lineage Check (MANDATORY)

A script written to satisfy a reviewer (a comparative arm, a subgroup, a sensitivity check) often
hand-enters values copied by eye from the original paper's tables, bypassing the locked extraction
CSV; the numbers are then consistent everywhere and wrong at the source. In one R1 revision a
hand-typed Fisher matrix read an adjacent severity-grade column as the event count, and the script,
manuscript, and Table all carried the same direction-reversed result.

**When Step 2 flags any `/analyze-stats` re-run:**

1. **Tag every new numerical claim with `[VERIFY-CSV]`** as it is written into the revised
   manuscript, response letter, or new table. The tag comes off only at Step 7 (Final
   Verification), after an explicit CSV + primary-source back-check.

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
   rows** before the analysis script references them, so no new value skips the
   dual-extraction consensus layer.

4. **Revision-time numerical audit table** — maintain it inside the response document draft
   and copy it into the final change log:

   | New claim (response + manuscript location) | Source script:line | CSV row/col | Primary source (Table/Fig, page) | Match? |
   |---|---|---|---|---|

5. **Gate before Step 3** — do not generate response prose for a MAJOR comment whose new
   numbers have not yet cleared this check, because prose written around un-audited numbers
   is very hard to unwind after a mismatch is found.

---

## Step 3: Generate Response to Reviewers Document

**Output location:** `revision/R[N]/response_to_reviewers_R[N].md`

Read `${CLAUDE_SKILL_DIR}/references/r2r_voice.md` before drafting: before/after examples, three response skeletons (accept / partial-accept / polite-rebuttal), and a meta-phrase-to-natural conversion table.

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

- **MINOR:** acknowledge, describe the change, and quote it: "The revised text now reads: '[new sentence].'"
- **MAJOR:** acknowledgment -> new analysis -> key result -> location of changes. All new results MUST include the 95% CI and exact p-value. New text added to the Results section states findings only; interpretation belongs in the response letter or the Discussion.

  ```
  [Acknowledge; state the concern.]
  To address this, we [describe new analysis/experiment/rewrite].
  [Key result: metric = value (95% CI, lower-upper; P = exact value)]
  This finding [supports / strengthens / does not change] our original
  conclusion because [brief interpretation].
  We have added: [Table X / Figure X / Supplementary Table X] showing [content];
  Methods revised: Page X, Lines Y-Z; Results revised: Page X, Lines Y-Z.
  ```

- **REBUTTAL:** polite but firm; open with acknowledgment, restate the reviewer's claim fairly, then give your position with evidence. Do not capitulate without scientific justification. Where it helps, add a clarifying sentence to the manuscript and quote it.

Cite only references verified via `/search-lit` with a confirmed DOI or PMID; mark any other as `[UNVERIFIED - NEEDS MANUAL CHECK]`. Never invent a clinical definition, diagnostic criterion, or guideline recommendation: flag an unconfirmed one with `[VERIFY]` and ask the user.

The acknowledgment lines in the skeletons are placeholders. Repeating one opener ("We thank the reviewer for this important suggestion.") down the letter is itself an AI-tell, so vary them.

---

## Response-Letter Voice & AI-Tell Avoidance

A response letter is a reviewer-facing scientific argument, not an internal change log. The
AI-tell patterns are defined once in humanize `references/ai_patterns.md` (patterns 22-24);
`references/r2r_voice.md` carries the authoring guidance. The rules:

1. **Write the change and the science, not the editing mechanism.** State what changed and why,
   and quote the new sentence. No version prefixes ("v2 adds..."), no "softened N phrases", no
   grep/verification language, no internal FIX codes, no bare "No further manuscript change"
   stubs. Describing a *new analysis you ran* ("we performed a sensitivity analysis and found X")
   is the science, not a tell.
2. **No `§` symbols, no internal draft line numbers.** A revised-manuscript page/line, stated once
   as referring to the revised manuscript, is fine.
3. **Succinct and non-defensive, especially on R2+.** A satisfied reviewer gets one sentence. No
   cross-reviewer lobbying ("Reviewers 2 and 3 also accepted this") and no defensive meta-comments
   ("we confirm this statement is unchanged and not softened"). Fold methodology disclosure
   (multiplicity, a SAP deviation) into the response to the comment it answers, never a separate
   front section, and never drop it. Split a multi-point reviewer paragraph into separate comments,
   each with its reviewer sentence quoted.

### Mandatory pre-submission scan

Before circulating or uploading, run `/humanize` on **both** the response letter and the cover
letter. The response-letter scan is patterns 22-24 plus 13 (em dash), 16 (filler), and 19 (`§`) in
humanize `references/ai_patterns.md`. Hold the letter to the manuscript's classical-style bar
(`/write-paper` `references/section_guides/step7_1_classical_qc.md`): zero `§` symbols, no
`(Methods §X)` self-references, em dashes kept low, and the heading style the target journal
actually publishes.

### Response-claim verification gate (MANDATORY, deterministic)

The single source of truth is the **revised manuscript**, not the response prose. A letter that
says *"we added the sentence '…'"* or *"we now cite Tariq et al. [15]"* must be verifiable in the
body. Run the gate before sending:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_response_claims.py \
  --response revision/response_to_reviewers.md \
  --manuscript manuscript/manuscript.md --strict
```

Add `--out qc/response_claims.json` to write the verdicts to `qc/response_claims.json`.

`RESPONSE_QUOTE_UNVERIFIED` (a quoted added sentence absent from the body) and
`RESPONSE_CITATION_UNVERIFIED` (an added citation whose token is nowhere in the body) are real
discrepancies, since the gate ignores vague, paraphrased claims: either insert the promised edit or
correct the response wording. `RESPONSE_QUOTE_UNRESOLVED` is **minor** and does not fail `--strict`:
the quoted words are all present in order but separated by extraction debris (a reference column
bled in from a two-column PDF, proof line numbers, a footnote marker, a hyphen split across a line).
Look at it by eye; do not delete a quote because of this verdict — accurate quotes have nearly been
deleted that way. A numeric citation counts only as a whole bracket element or inside a range
(',' or ';' separated, spaces inside the bracket allowed, a range written with a hyphen or any dash):
a claimed [5] is not satisfied by [15]. A bracket that mixes numbers and words ("[5, see also 8]")
is not read as a citation list, so a claim citing it is flagged; check it by eye.

Known limits: quote CONTENT is not compared. A quote that differs from the body's sentence by a
number (the letter says 0.92, the body 0.87) or by a negator ("not", added or dropped) is graded
like extraction debris, minor `RESPONSE_QUOTE_UNRESOLVED`, and `--strict` passes. A number
comparison was tried and withdrawn: the same value written in two formats (mid-dot decimals,
space-grouped thousands, a plain-text "10^9" against a superscript that extraction glues onto the
base) read as a changed number and flagged accurate quotes. Read every UNRESOLVED quote by eye for a
changed number or a flipped finding. A citation claim passes when ANY of its cited tokens is in the
body, so "we now cite [15] and [16]" passes with only [15] inserted; check multi-citation claims by
eye.
A claim is read as a citation claim only when its verb says so ("cite", "reference"): "We added
the citation [15]" or "We have added a reference to X [15]" is not checked. Read any added citation
by eye; reading past the verb was withdrawn ("reference standard" fired).

**If a reviewer called the manuscript too long or too dense, prove the body got shorter.**
Answering a density comment point-by-point adds a sentence per point, so the revision that responds
to "shorten this" comes back longer. This gate is arithmetic:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_density_complaint.py \
  --comments revision/decision_letter.md \
  --previous manuscript/manuscript_R0.md \
  --revised manuscript/manuscript.md --strict
```

`DENSITY_COMPLAINT_UNADDRESSED` fires only when the decision letter contains a density/length
complaint AND the body word count (Introduction through Discussion, citation markers excluded) did
not fall; with no complaint it stays silent. When it fires, cut or move detail to the supplement; do
not defend the length by adding a paragraph that explains it.

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

On an **R2+ round (second revision onward), do not write a separate cover letter.** The greeting and the brief change summary go in the **head of the response-to-reviewers letter**; a standalone letter restating that summary reads as redundant boilerplate. If an earlier round produced a `cover_letter_R1.md`, move it to `_superseded/`, exclude it from the R2+ package, and reuse the response-letter head verbatim in any portal "cover letter" field. (Exception: a journal that requires a separate cover letter at every round — then keep the head summary and the cover letter from duplicating each other.)

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

Keep the head to these parts; everything else is point-by-point.

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

- [ ] Every reviewer comment has a response (none skipped, even trivial ones or ones addressed elsewhere)
- [ ] Every MAJOR comment has the actual new data or analysis and a manuscript change with location, not just agreement
- [ ] Every change the letter promises was actually made in the manuscript
- [ ] Every REBUTTAL is backed by cited evidence or clear scientific reasoning
- [ ] All new statistics include 95% CI and exact p-values
- [ ] Page/line number references match the revised manuscript (not the original)
- [ ] Figures and tables renumbered if new items were inserted; all new figures/tables are referenced in the response letter
- [ ] Voice rules hold: no `§`, no internal draft line numbers ("(line 43)"), no editing-mechanism narration, varied openers; (R2+) satisfied reviewers get ≤1-2 sentences, no cross-reviewer lobbying; multi-point paragraphs split; methodology disclosure folded into the relevant response
- [ ] Response letter AND cover letter ran through `/humanize` (patterns 22-24 triage hits reviewed; confirmed instances = 0; `§` = 0 hard)
- [ ] (R2+) No separate cover letter — the editor greeting and "in brief" summary are folded into the response-letter head
- [ ] Cover letter is addressed to the correct editor
- [ ] Response letter length within the Word Count Guidance below
- [ ] The marked manuscript passed the round-trip gate (below) — not merely "tracked changes are on"

### The marked manuscript is gated, not eyeballed

The journal wants the revised paper with tracked changes against **the version the reviewers saw** (R0 — not the previous round). Produce it with Word's Compare, which `/sync-submission` drives from the command line, and verify it by round trip: accepting every revision must reproduce the revised manuscript exactly, and rejecting every revision must reproduce the original. A spot-check that "sentence X appears as an insertion" passes even when Compare has dropped a paragraph or attributed half the changes to another author.

```bash
python3 <medsci-skills>/skills/sync-submission/scripts/check_marked_manuscript.py \
  --marked revision/R1/manuscript_marked.docx \
  --original submission/R0/manuscript.docx \
  --revised revision/R1/manuscript_clean.docx \
  --author "Submitting Author" --strict
```

See `/sync-submission` Phase 10 for the build step and for why the check must be move-aware (`w:moveFrom` / `w:moveTo` are not `w:ins` / `w:del`).

---

## Revision Round File Structure

| Round | Folder | Files |
|-------|--------|-------|
| R1 | `revision/R1/` | `response_to_reviewers_R1.md`, `cover_letter_R1.md`, `change_log_R1.md` |
| R2 | `revision/R2/` | `response_to_reviewers_R2.md`, `cover_letter_R2.md`, `change_log_R2.md` |

Also write the current round's letter and change log to `revision/response_to_reviewers.md` and `revision/change_log.md`, the paths the claim gate and `/sync-submission` read.

Revised manuscript: `manuscript/manuscript.md`; keep the version the reviewers saw as `manuscript/manuscript_R0.md` (the density gate compares the two).

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

## Gates

| Gate | Severity | Trigger | Action on fail |
|---|---|---|---|
| Comment classification (MAJOR / MINOR / REBUTTAL) | ENFORCED | comment unclassified or classification disputed | ask user; do not silently default |
| Step 2.5 `[VERIFY-CSV]` tagging on revision-introduced numbers | ENFORCED | new numerical claim added without `[VERIFY-CSV]` tag | tag automatically; HALT until CSV cross-check completes |
| Reference re-render after revisions touching citations | ENFORCED | any new `[@bibkey]` added in R1+ | route to `/manage-refs` for a re-render before R1 submission |
| `/verify-refs --strict` post-revision | ENFORCED | FABRICATED / HIGH_MISMATCH_FIRST_AUTHOR > 0 | HALT R1 submission |
| New analysis coordination | ENFORCED | reviewer asks for new analysis | route to `/analyze-stats` (and `/make-figures` if figure changes); never hand-write new numbers |
| Body word count vs journal cap (revision-inflation trap) | ENFORCED after every revise pass | resolving majors pushes the body over the target journal's word limit | run `python3 "${CLAUDE_SKILL_DIR}/../sync-submission/scripts/check_wordcount_cap.py"` (`--journal-profile` or `--limit`; prefer the rendered DOCX count); `WORDCOUNT_OVER_CAP` blocks submission — relocate methods/sensitivity detail to the Supplement, do not silently exceed |
| Cover letter to editor | ENFORCED at R1 submission | R1 missing editor cover letter | block submission |
| R2+ cover-letter handling | ENFORCED at R2+ submission | standalone cover letter present on an R2+ round (not folded into the response-letter head) | move it to `_superseded/`; fold the summary into the head |
| Response-letter voice / AI-tell | ENFORCED before submission | editing-mechanism narration, internal draft line refs, `§`, tooling leak, or repeated openers in response/cover letter | run `/humanize` (patterns 22-24 as triage; `§` = 0 hard); resolve confirmed tells before submission |
