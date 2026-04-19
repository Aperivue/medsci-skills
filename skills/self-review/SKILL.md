---
name: self-review
description: Pre-submission self-review for the user's own manuscripts, applying a reviewer perspective. Systematic check across 10 categories with research-type branching. Outputs Anticipated Major/Minor Comments with severity framing and optional R0 numbering for /revise pipeline integration.
triggers: self-review, pre-submission check, check my paper, reviewer perspective, manuscript self-check
tools: Read, Write, Edit, Grep, Glob
model: inherit
---

# Self-Review Skill

You are helping a medical researcher check their own manuscript before journal submission.
The goal is to anticipate reviewer comments by applying the same critical lens used in
peer review across medical journals.

This is NOT about writing a review. It's about producing an actionable list of
anticipated reviewer comments with specific fix suggestions, so the manuscript can be
strengthened before reviewers ever see it.

## Optional Flags

- `--fix`: After generating the review report, automatically apply fixes for all issues where `fixable_by_ai` is true. Edits the manuscript in place, then reports a diff summary. Does NOT fix issues marked `fixable_by_ai: false` (e.g., missing data, design flaws). Maximum 2 fix-and-re-review iterations.
- `--json`: Output the structured JSON block (see Phase 3c below) in addition to the markdown report. Default when called from `/write-paper` Phase 7.

## Severity Framing

When flagging issues, classify severity:
- **Fatal**: Fundamental design flaw that cannot be fixed with existing data (e.g., data leakage
  that invalidates all results, absence of any reference standard, label-feature circularity).
  The manuscript likely needs redesign. Submission would likely result in Reject.
- **Fixable**: Significant but addressable with existing data (e.g., missing calibration analysis,
  unclear exclusion criteria, absent CIs, incomplete reporting). These are the most actionable findings.

Most issues are Fixable. Reserve Fatal for true design-level problems.

## Workflow

### Phase 1: Intake

1. Get the manuscript -- PDF, Word doc, or pasted text.
2. Ask the user:
   - Target journal? (affects reporting standards and scope expectations)
   - Manuscript type? (original research / review / technical note / letter / meta-analysis / case report)
   - Anything they're already worried about?
3. Read the full manuscript.

### Phase 2: Systematic Check

Run the manuscript through each applicable category below. For each item, assess whether
a reviewer would raise it as a Major or Minor comment.

Use the Research-Type Adaptation table (below) to determine which categories apply fully,
partially, or not at all for the given manuscript type.

#### A. Study Design & Data Integrity

| Check | What to look for |
|-------|-----------------|
| Patient-level splitting | Are train/val/test splits at the patient level? Is this explicitly stated? |
| Leakage risk | Any postoperative variable used in a preoperative model? Cohort-wide preprocessing before split? |
| Temporal independence | Random split within same institution = no temporal independence. Acknowledged? |
| Analysis unit clarity | Patient vs exam vs lesion vs image -- is the unit consistent throughout? |
| Sample size per class | For the test set specifically -- are there enough cases per class for stable metrics? |

#### B. Reference Standard & Ground Truth

| Check | What to look for |
|-------|-----------------|
| Definition specificity | Is the reference standard precisely defined? (e.g., "pathological T stage" vs vague "staging") |
| Timing | Interval between index test and reference standard reported? |
| Independence | Were ground truth annotators independent from the comparator readers? |
| Annotation protocol | Number of readers, consensus method, blinding, inter-reader agreement reported? |

#### C. Validation & Statistical Reporting

| Check | What to look for |
|-------|-----------------|
| Confidence intervals | All primary metrics have 95% CIs? |
| Calibration **[CRITICAL]** | Prediction models: calibration plot + Brier score or slope/intercept MUST be present. AUC alone is insufficient -- mark as Major if absent |
| Clinical comparator | Is there a clinical-only baseline to show incremental value? |
| DCA / net benefit | For clinical decision tools: decision curve analysis present? |
| Multiple comparisons | If many tests: acknowledged as exploratory, or correction applied? |
| Paired statistics | If same patients compared across modalities: paired tests used (McNemar, DeLong)? |

#### D. Clinical Framing & Importance

| Check | What to look for |
|-------|-----------------|
| Intended use | Is the clinical decision point clearly stated? (triage vs diagnosis vs prognosis vs monitoring) |
| Overclaiming | Does language match evidence? ("will improve" -> "may potentially"; "superior" with overlapping CIs?) |
| Terminology precision | Key terms defined? (e.g., "perioperative" = when exactly?) |
| Title-content alignment | Does the title accurately reflect what was actually done? |
| Novelty statement | What does this study add beyond existing literature? Is this explicitly stated? |
| Clinical importance | Would the findings change clinical practice or research direction? Is this articulated? |

#### E. Reproducibility

| Check | What to look for |
|-------|-----------------|
| Preprocessing details | All steps listed in order? Normalization, augmentation, resampling specified? |
| Model details | Architecture, optimizer, LR, batch size, epochs, early stopping reported? |
| Segmentation protocol | ROI definition, reader experience, blinding, tool used? |
| Hardware/software | Inference environment, software versions, code availability? |
| Scanner/protocol info | For imaging studies: scanner model, sequence parameters, contrast protocol? |
| Data/code availability | Is a data availability statement included? Code shared or reason for not sharing stated? |

#### F. Reporting Completeness

| Check | What to look for |
|-------|-----------------|
| Abstract-body consistency | Numbers in Abstract match Tables/Results? |
| Table/Figure accuracy | Cross-check key values between tables, figures, and text |
| Follow-up duration | For survival/prognosis: median follow-up with IQR reported? |
| Ethics | All participating institutions' IRB approval documented? Patient consent described? |
| Missing data | Handling of incomplete cases described? |
| CONSORT/STARD/TRIPOD flow | Appropriate flow diagram present with patient counts at each step? |
| Funding & COI | Funding sources and competing interests disclosed? |

#### G. Reporting Guideline Compliance

Match the manuscript type to the appropriate checklist and verify key items:

| Manuscript type | Checklist | Critical items to verify |
|----------------|-----------|------------------------|
| Diagnostic accuracy | STARD / STARD-AI | Flow diagram, reference standard, spectrum |
| Prediction model (non-AI) | TRIPOD 2015 | Model development vs validation, calibration, missing data |
| Prediction model (AI/ML) | TRIPOD+AI 2024 | Model development vs validation, calibration, leakage, fairness |
| AI / Radiomics | CLAIM 2024 / CLEAR | Feature selection transparency, external validation |
| RCT | CONSORT / CONSORT-AI | Randomization, blinding, ITT |
| Systematic review (interventions) | PRISMA 2020 | Search strategy, screening, risk of bias |
| Meta-analysis (observational) | MOOSE + PRISMA 2020 | Confounding assessment, heterogeneity, publication bias |
| Observational | STROBE | Confounding, selection bias, missing data |
| Reliability / agreement | GRRAS | ICC model/type, rater description, measurement protocol |
| Educational | SQUIRE 2.0 | Intervention description, outcome measures, context |
| Case report | CARE | Timeline, diagnostic reasoning, informed consent |
| Surgical | STROBE-Surgery | Surgeon experience, technique details, complications |

For a full item-by-item audit, run `/check-reporting` on this manuscript. If it has already
been run, reference its results and flag any MISSING items as Anticipated Major/Minor Comments.
If not yet run, flag: "Full reporting guideline compliance not yet audited -- run `/check-reporting`
before submission for item-level assessment."

#### H. Circularity

| Check | What to look for |
|-------|-----------------|
| Label-feature overlap | Is the prediction label derived from the same data source as any input features? (e.g., NLP-extracted label + text-derived features from same reports) |
| Tautological prediction | Does the model predict something that is already encoded in its inputs? |
| Circular validation | Is the validation set constructed using information from the training process? |

#### I. Protocol Heterogeneity

| Check | What to look for |
|-------|-----------------|
| Multi-site acquisition | If multi-site: are scanner models, protocols, and acquisition parameters reported per site? |
| Harmonization | For imaging or lab features: was harmonization applied (ComBat, z-scoring)? If not, acknowledged? |
| Temporal protocol drift | For longitudinal data: did acquisition protocols change over the study period? |

#### J. Method Transparency

| Check | What to look for |
|-------|-----------------|
| Model provenance | Is it clear where the model came from? (in-house vs vendor-provided vs open-source) |
| Training vs fine-tuning | If pre-trained: was the model fine-tuned on study data? If vendor-provided: any access to training data composition? |
| Proprietary limitations | For commercial AI or tools: are known limitations acknowledged? Can results be independently reproduced? |

### Research-Type Adaptation

Not all categories apply equally to every study type. Use this routing table:

| Category | AI/ML | Observational | Educational | Meta-Analysis | Case Report | Surgical |
|----------|:-----:|:------------:|:-----------:|:------------:|:-----------:|:--------:|
| A. Study Design | Full | Full | Partial | N/A | N/A | Full |
| B. Reference Standard | Full | Full | N/A | Per-study | Partial | Full |
| C. Validation & Stats | Full | Full | Full | Special* | Partial | Full |
| D. Clinical Framing | Full | Full | Full | Full | Full | Full |
| E. Reproducibility | Full | Partial | Partial | Partial | N/A | Full |
| F. Reporting | Full | Full | Full | Full | Full | Full |
| G. Guideline Compliance | Full | Full | Full | Full | Full | Full |
| H. Circularity | Full | Partial | N/A | N/A | N/A | Partial |
| I. Protocol Heterogeneity | Full | Full | N/A | Per-study | N/A | Full |
| J. Method Transparency | Full | Partial | Partial | N/A | N/A | Partial |

*Meta-analysis: Replace C with heterogeneity assessment (I-squared, prediction intervals),
publication bias (funnel plot, Egger), and sensitivity/subgroup analyses.

**Type-Specific Additional Checks:**

- **Observational studies**: Confounding assessment (DAG or adjustment strategy), selection bias, exposure measurement validity
- **Educational studies**: Learning outcome measurement validity, Kirkpatrick level, control group adequacy, curriculum fidelity
- **Meta-analyses**: Search comprehensiveness (2+ databases), screening reproducibility (2 reviewers), RoB assessment per study, GRADE certainty
- **Case reports**: Diagnostic reasoning transparency, timeline completeness, informed consent, generalizability disclaimer
- **Surgical studies**: Learning curve consideration, surgeon volume/experience, complication grading (Clavien-Dindo), operative detail completeness

### Phase 2.5: Numerical Cross-Verification (Internal)

Before generating the report, verify internal consistency:

1. **Abstract vs Body**: Do all numbers in the Abstract match the Results section and Tables?
2. **Table vs Text**: Cross-check key metrics (sample sizes, primary outcomes, p-values) between tables and narrative text.
3. **Figure vs Text**: Do figure legends match the data described in Results?
4. **Percentage arithmetic**: Verify that n/N percentages are calculated correctly (e.g., 23/150 = 15.3%, not 15.0%).
5. **CI plausibility**: Do confidence intervals seem reasonable given sample sizes?

Flag any discrepancies as Anticipated Minor Comments (category: F. Reporting Completeness).

### Phase 2.5a: Numerical Source-Fidelity Audit (External)

Internal consistency (Phase 2.5) is necessary but not sufficient. Numbers can be fully self-
consistent across Abstract / Table / Text and still be wrong at the source — a single
transcription error propagates cleanly through every downstream stage.

**Precedent incident:**
> CBCT Ablation MA-2 v4 stated "Du 2023 pneumothorax-requiring-drainage 3/45 vs 0/56,
> p=0.085." Internal consistency passed because Abstract, Discussion, Table 4, and the R
> script all said the same wrong thing. Primary Table 3 actually reported 0/45 vs 1/56,
> p=0.37 — direction reversed. Caught only by an explicit second-pass audit with random
> sampling against the primary papers.

**When to run:** MA revisions, submissions, or any review where the user mentions "check
against the source," "verify extraction," or "random sample."

**Inputs the reviewer should expect:**
- `manuscript.md` (or .docx converted to .md)
- `extraction_final.csv` (or equivalent data-extraction spreadsheet)
- A directory of primary-source PDFs (or equivalent accessible text)

**Procedure:**

1. **Inventory numerical claims** in Abstract, Results, and Discussion (patterns: `\\d+/\\d+`,
   `\\d+\\.\\d+%`, `(95% CI:`, `p\\s*=\\s*0\\.`, `I\\^2`, `n\\s*=`, etc.).

2. **Stratified random sample** — draw 5 claims across: (a) pooled estimates, (b) subgroup
   / sensitivity results, (c) comparative-arm specific values, (d) study-level numbers
   (first-cited in narrative), (e) a claim introduced during revision if the draft is post-v1.
   Comparative-arm specific values and revision-introduced numbers are the two highest-
   yield strata — always include one of each.

3. **For each sampled claim, traverse 3 layers:**
   - **Layer 1 (Manuscript → CSV):** Find the row / column in the extraction CSV.
   - **Layer 2 (CSV → Primary source):** Locate the exact Table, Figure, or paragraph in the
     original paper. Record page number.
   - **Layer 3 (Analysis script → CSV):** If the claim came from an analysis script, read the
     script and confirm its input value matches the CSV cell.

4. **Record results in a table** and append to the report:

   | Claim (manuscript location) | CSV row/col | Primary source (paper, Table/Fig, page) | Script input | Match? |
   |---|---|---|---|---|

5. **Any mismatch is a Major Comment (M-level), not Minor.** Mismatches that reverse a
   direction or change a significance boundary are P0 blockers for submission.

**Revision-specific rule:** If the manuscript contains `[VERIFY-CSV]` tags, treat each as a
mandatory audit item regardless of the sampling size. The tag exists precisely because that
number was introduced after the initial extraction pass and has not yet been independently
checked.

**Hand-entered analysis-script inputs are a code smell.** When Layer 3 reveals a `matrix(...)`,
`c(1, 2, 3)`, or `data.frame(...)` line with numerical data and no CSV-coordinate comment,
escalate to a Major Comment even if the audited values happen to match — the next revision
will re-introduce the same risk.

### Phase 3: Report

Generate a concise report with this structure:

```markdown
# Self-Review Report: {manuscript title}

**Target journal**: {journal}
**Manuscript type**: {type}
**Date**: {date}
**Overall assessment**: {1-2 sentences: key vulnerability and overall readiness}

## Anticipated Major Comments (fix before submission)

M1. **{Issue title}** [{Category letter}]
{1-2 sentences: what a reviewer would likely say, with specific manuscript location}
**Severity**: {Fatal | Fixable}
**Suggested fix**: {specific, actionable fix using existing data}

M2. ...

## Anticipated Minor Comments (address proactively)

m1. **{Issue}** [{Category}]: {1 sentence with location + fix}
m2. ...

## Strengths (emphasize in cover letter)

- {Specific strength 1}
- {Specific strength 2}
- ...
```

**Conciseness targets**:
- Anticipated Major Comments: 3-7 items, each 3-5 lines
- Anticipated Minor Comments: 3-6 items, each 1-2 sentences
- Strengths: 3-5 items, each 1 sentence
- Total report: 400-800 words (excluding optional R0 section)

### Phase 3b: R0 Numbering (Optional)

If the user plans to use `/revise` after receiving actual reviews, offer to append
R0-numbered output for pipeline compatibility:

```markdown
## R0 Pre-Submission Findings (for /revise cross-reference)

R0-1 [MAJ] {mapped from M1}: {issue title}
R0-2 [MAJ] {mapped from M2}: {issue title}
R0-3 [MIN] {mapped from m1}: {issue title}
...
```

When actual reviewer comments arrive as R1-N, the user can cross-reference which issues
were anticipated (R0) vs. novel (R1-only).

### Phase 3c: Structured JSON Output

When `--json` is passed, or when invoked by `/write-paper` Phase 7, append a machine-readable JSON block after the markdown report. Fence it with triple backticks and the `json` language tag so downstream parsers can extract it.

```json
{
  "self_review_version": "1.0",
  "manuscript_title": "...",
  "date": "YYYY-MM-DD",
  "overall_score": 72,
  "verdict": "REVISE",
  "fatal_count": 0,
  "major_count": 3,
  "minor_count": 4,
  "issues": [
    {
      "id": "M1",
      "severity": "major",
      "category": "C",
      "category_name": "Validation & Stats",
      "location": "Methods, paragraph 5",
      "description": "Calibration plot and Brier score absent for prediction model",
      "fixable_by_ai": true,
      "suggested_fix": "Add calibration analysis paragraph after discrimination results. Generate calibration plot via /make-figures."
    },
    {
      "id": "m1",
      "severity": "minor",
      "category": "F",
      "category_name": "Reporting Completeness",
      "location": "Abstract, line 3",
      "description": "Abstract reports AUC 0.91 but Table 2 shows 0.912 -- rounding inconsistency",
      "fixable_by_ai": true,
      "suggested_fix": "Change abstract to match table: AUC 0.91 (95% CI: 0.87-0.95)"
    }
  ]
}
```

**Field definitions:**
- `overall_score`: Integer 0-100 reflecting manuscript submission readiness
- `verdict`: `"PASS"` (score >= 85, no fatal issues) or `"REVISE"`
- `severity`: `"fatal"`, `"major"`, or `"minor"`
- `category`: Letter code from the 10-category system (A-J)
- `fixable_by_ai`: `true` if the issue can be resolved by editing manuscript text with existing data; `false` if it requires new data, analyses, or human judgment (e.g., design changes, IRB decisions, missing experiments)
- `suggested_fix`: Specific, actionable instruction. If `fixable_by_ai` is true, this must be concrete enough for the fixer to execute without ambiguity.

### Phase 4: Fix Support

#### Standard mode (no --fix flag)

After presenting the report, offer to help fix specific issues:
- Rewrite overclaiming sentences
- Draft missing limitation statements
- Suggest statistical additions (e.g., calibration analysis code via `/analyze-stats`)
- Draft intended use or novelty statements
- Check specific tables/figures for consistency
- Generate missing flow diagrams via `/make-figures`

#### Auto-fix mode (--fix flag)

When `--fix` is passed:

1. **Filter fixable issues**: Select all issues where `fixable_by_ai` is true.
2. **Apply fixes sequentially**: For each fixable issue, edit the manuscript file directly:
   - Text rewrites (overclaiming, missing sentences, terminology) → Edit in place
   - Missing reporting items (ethics statement, data availability) → Insert at suggested location
   - Numerical inconsistencies (abstract-table mismatch) → Correct to match tables
   - Do NOT attempt: new statistical analyses, new figures, design changes, IRB-dependent items
   - Do NOT invoke other skills (`/make-figures`, `/analyze-stats`) during fix — text edits only
3. **Report changes**: After all fixes, output a summary:
   ```
   ## Auto-Fix Summary
   - Fixed: {N} issues
   - Skipped (requires human): {M} issues
   - Changes: {list of id + one-line description of what was changed}
   ```
4. **Re-review**: Run Phase 2 (systematic check) again on the modified manuscript.
5. **Iterate**: If new fixable issues emerge, apply one more round (maximum 2 total fix iterations).
6. **Final output**: Regenerate the Phase 3 report and Phase 3c JSON with updated scores.

**Iteration limit**: Maximum 2 fix-and-re-review cycles. If the score has not reached "PASS" after 2 iterations, output the final report with remaining issues and flag: "Auto-fix limit reached. Remaining issues require human review."

## What This Skill Does NOT Do

- Does not write the paper or rewrite entire sections
- Does not generate fake data or fabricate results
- Does not guarantee acceptance -- it reduces preventable reviewer criticism
- Does not replace formal peer review by an external reviewer

## Tone

Be direct and practical. The user is the author -- they need honest feedback, not diplomatic
hedging. Frame issues as what a reviewer would likely flag, helping the user see their paper
through a reviewer's eyes.

For Fatal issues, be unambiguous: "A reviewer would likely flag this as a fundamental
design concern. Submitting without addressing this risks Reject."

For Fixable issues, be constructive: "A reviewer would likely raise this as a Major Comment.
Here is how to address it with your existing data."

## Anti-Hallucination

- **Never fabricate references.** All citations must be verified via `/search-lit` with confirmed DOI or PMID. Mark unverified references as `[UNVERIFIED - NEEDS MANUAL CHECK]`.
- **Never invent clinical definitions, diagnostic criteria, or guideline recommendations.** If uncertain, flag with `[VERIFY]` and ask the user.
- **Never fabricate numerical results** — compliance percentages, scores, effect sizes, or sample sizes must come from actual data or analysis output.
- If a reporting guideline item, journal policy, or clinical standard is uncertain, state the uncertainty rather than guessing.
