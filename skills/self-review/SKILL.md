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
- `--panel`: Run the multi-agent panel review (Phase 2.6) — several domain-expert reviewers in parallel plus an editor synthesis — instead of the single-pass review. Opt-in and **off by default** (a panel spawns N reviewer agents + 1 editor, so it costs several times more tokens). Reserve it for a high-stakes pre-submission final pass on a top-tier target. Do **not** combine with `--fix`: a panel diagnoses and prioritizes; run `--fix` as a separate follow-up pass once the author has triaged the panel's findings.

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
   - **Review depth?** The default is a single-pass review. For a high-stakes pre-submission final pass, a multi-agent **panel** (`--panel`, Phase 2.6) is available — several domain-expert reviewers run independently, then an editor consolidates them (more thorough, but it spawns several agents so it costs several times more tokens). On an interactive run, surface this option **once** in one line and offer it; then proceed with the single-pass review unless the user opts in. Do **not** surface or auto-apply the panel when invoked with `--json` or from `/write-paper` — those stay single-pass.
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
| Effect-size meaningfulness | Scored separately from significance: is each primary effect (OR, HR, beta, Cohen's d, correlation) translated to a real-world unit shift and compared to a minimal clinically important difference? Is significance driven by magnitude rather than sample size? |
| Power-aware null interpretation | Scored separately from significance, for any **non-significant primary result** (p > 0.05, 95% CI crossing the null): is the analysis powered to *exclude* a clinically meaningful effect? An underpowered null is "not yet established," not "no effect" -- if the upper CI bound still includes a meaningful effect size, a flat "X was not associated with Y" claim overreads the data. Look for reported observed power or a minimum detectable effect that justifies a negative conclusion, and watch for **bilateral over-correction** (a prior "independently associated" overclaim swinging to an equally unsupported "not associated" claim during revision). Undocumented null = Minor; a null that drives a clinical recommendation or a headline negative conclusion without power/CI-compatibility justification = Major. |

#### D. Clinical Framing & Importance

| Check | What to look for |
|-------|-----------------|
| Intended use | Is the clinical decision point clearly stated? (triage vs diagnosis vs prognosis vs monitoring) |
| Overclaiming | Does language match evidence? ("will improve" -> "may potentially"; "superior" with overlapping CIs?) |
| Terminology precision | Key terms defined? (e.g., "perioperative" = when exactly?) |
| Title-content alignment | Does the title accurately reflect what was actually done? |
| Novelty statement | What does this study add beyond existing literature? Is this explicitly stated? |
| Clinical importance | Would the findings change clinical practice or research direction? Is this articulated? |
| Added value / actionability | Scored separately from novelty: does the finding add value over a measure already in routine use, or is it "real but redundant" (restates a standard test)? At the typical effect size, would a clinician act on it for an individual? |

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

#### K. Reviewer-team consistency (SR/MA-only; fabrication-grade)

| Check | What to look for |
|-------|-----------------|
| DUAL vs SINGLE conjunction **[CRITICAL]** | Methods or PROSPERO claims dual independent reviewers AND Discussion/Limitations admits single primary reviewer + 20% sample (or "deferred to before submission")? Mark as **MAJOR**, fabrication-grade. |

Run the deterministic check at Phase 2 entry:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/check_reviewer_team_consistency.py" \
    --manuscript manuscript.md \
    --prospero prospero/record.md \
    --out _audit_self/reviewer_team_consistency.md
```

Exit 1 = MAJOR red flag. Either claim alone is fine; the conjunction is
read by reviewers as fabrication. Resolution path:
1. Honest Methods/PROSPERO update (single-reviewer execution disclosed), OR
2. Limitations confession rewritten if dual review was actually completed.

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
| K. Reviewer-team consistency | N/A | N/A | N/A | Full | N/A | N/A |

*Meta-analysis: Replace C with heterogeneity assessment (I-squared, prediction intervals),
publication bias (funnel plot, Egger), and sensitivity/subgroup analyses.

**Type-Specific Additional Checks:**

- **Observational studies**: Confounding assessment (DAG or adjustment strategy), selection bias, exposure measurement validity. Run **Phase 2.5e (Confounding Completeness)** and apply the O1–O6 probes in `references/domain-probes/observational_confounding.md`.
- **Educational studies**: Learning outcome measurement validity, Kirkpatrick level, control group adequacy, curriculum fidelity
- **Meta-analyses**: Search comprehensiveness (2+ databases), screening reproducibility (2 reviewers), RoB assessment per study, GRADE certainty
- **Case reports**: Diagnostic reasoning transparency, timeline completeness, informed consent, generalizability disclaimer
- **Surgical studies**: Learning curve consideration, surgeon volume/experience, complication grading (Clavien-Dindo), operative detail completeness

**Domain probe modules (load when the manuscript type matches):**

These four modules carry the same domain-specific critique probes used by `/peer-review`, vendored here so self-review reaches the same depth (in particular, survival/time-to-event manuscripts now get a dedicated probe set that the routing table above does not otherwise cover).

| Manuscript type / signal | Probe module |
|---|---|
| Systematic Review / Meta-Analysis | `references/domain-probes/sr_ma.md` (P0–P10) |
| Time-to-event / survival / prognostic model (Cox, Fine-Gray, DeepSurv, nomogram, risk-stratification cutoff) | `references/domain-probes/survival_prognostic.md` (S1–S7) |
| Radiomic feature reproducibility / acquisition-parameter sweep / reliability-based feature filtering | `references/domain-probes/radiomics.md` (R1–R4) |
| Narrative / review article / primer / state-of-the-art | `references/domain-probes/narrative_review.md` (RV1–RV8) |

When the manuscript matches a row, read `${CLAUDE_SKILL_DIR}/references/domain-probes/<module>.md` and apply each probe as an additional source of Anticipated Major / Minor Comments. The module severity words (MAJOR / MINOR) map to this skill's framing as follows: a conclusion-threatening or design-level finding becomes a **Fatal** Anticipated Major Comment, a reporting-level finding becomes a **Fixable** Anticipated Minor Comment, and each is tagged with the closest category letter (A–K). These probes **complement** categories A–K above; they do not replace them. (The modules are vendored byte-identical from `/peer-review`; do not edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`.)

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

**Precedent failure pattern:**
> A revision-era comparative meta-analysis reported a safety-outcome 2x2 with the
> arm-level events direction-reversed relative to the primary-source Table. Internal
> consistency passed because Abstract, Discussion, Table, and the R script all echoed
> the same wrong values. The reversal was caught only by an explicit second-pass audit
> that randomly sampled claims and traced each back to the primary paper.

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

### Phase 2.5a-2: Design & Power Statistic Provenance (computed, not extracted)

Phase 2.5a traces data-derived numbers back to a CSV and a primary source. **Design and power
statistics are a different class and a common blind spot**: the minimum detectable effect
(MDE), a-priori or post-hoc power, the required sample size for a future trial, and the
a-priori effect-size assumptions behind them are *computed*, not extracted, so they have no
CSV row or source-paper Table to trace to. They routinely escape both the internal-consistency
check and the source-fidelity audit above.

**Precedent failure pattern:**
> A pilot study reported a minimum detectable effect of d = 1.67. No standard two-sample method
> reproduces it (the correct value at the stated n, alpha, and power was about 1.24). It survived
> several review rounds because no committed script computed it — the value had been hand-entered —
> and one reviewer even cited the figure approvingly. In the same manuscript, a set of future-trial
> sample sizes was numerically correct but had been produced with an exact noncentral-t tool, while
> the committed script used a normal approximation and printed different numbers: right value, no
> reproducible provenance.

**Procedure:**

1. **Inventory design/power claims.** Search for: "minimum detectable", "detectable effect",
   "MDE", "power" (80% / 90% / "1 − beta"), "sample size", "n = N per arm/group", "to detect",
   "powered to", "a priori", and any a-priori planning effect size (Cohen's d / f / OR used for
   sizing).

2. **Require a reproducible source for each.** Every such value must be produced by committed
   code (e.g. `statsmodels` `TTestIndPower`, a G*Power-equivalent, or an explicit noncentral-t
   computation), with the inputs stated in the manuscript: n per arm, alpha, power, allocation
   ratio, and one- vs two-sided. A value with no committed-code source is the highest-risk case.

3. **Recompute independently** with a standard tool, then classify:
   - **Not reproducible by any standard method** → likely a calculation error (Major; P0 if it
     is a headline claim). This is the d = 1.67-vs-1.24 case above.
   - **Reproducible only by a method the committed script does not implement** (e.g. the
     manuscript value is noncentral-t but the script is a normal approximation) → provenance /
     method drift. The number may be correct, but update the committed code so it reproduces the
     reported value (Major: reproducibility, not correctness).

4. **Method-consistency across the manuscript.** All power, sample-size, and MDE statistics in
   one paper should share a single method family (e.g. all noncentral-t). A mix of normal
   approximation and exact-t within one manuscript signals that some values were computed in an
   ad-hoc side tool.

5. **Any non-reproducible design/power value is a Major Comment;** a non-reproducible headline
   power or MDE claim is a P0 submission blocker.

**Hand-entered design/power statistics are a code smell even when correct.** If no committed
function emits the value, flag it: the next revision will re-introduce the risk, and a reviewer
who recomputes will not match the manuscript.

### Phase 2.5b: Screening-Count Reconciliation from ID Sets (SR/MA-only)

Internal consistency across Abstract/Methods/Results (Phase 2.5) + source fidelity of 2×2 and
effect-size numbers (Phase 2.5a) do **not** cover study-count arithmetic. The latter is a
separate failure mode: a prior-draft prose total ("30 → 32 after FLAG consensus") can survive
every downstream pass because Abstract, Methods, Results, Discussion, Figure 1 caption, and
even the supplementary consensus file all cite the same wrong number back to each other.

**Precedent failure pattern (a PRISMA-DTA meta-analysis revision):**
> A late-revision manuscript reported study counts of k_qualitative = 32, k_narrative-only = 10,
> k_FT-excluded = 46. An ID-level recount against the screening TSV and consensus sheet (with
> FLAG additions reconciled) yielded k_qualitative = 24 with only 2 narrative-only studies
> (k_FT-excluded = 54). The original 32/10/46 figures came from an early-draft assumption that
> was never reconciled against the ID-level artifacts; downstream files (consensus markdown,
> supplementary tables, edit plans) propagated the same wrong total. Caught only by an explicit
> ID-set recount against the screening TSV and consensus spreadsheet, verified independently
> by an adversarial audit.

**When to run:** any SR/MA manuscript revision, regardless of stage. Run before Phase 3.

**Inputs:**
- Screening TSV with one row per full-text-reviewed record and an include/exclude column
- Consensus spreadsheet (Excel/CSV) with one row per record requiring adjudication and a
  `Consensus` column (typical values: `Exclude`, `Include-qualitative`, `Include-bivariate`)
- Any FLAG-adjudicated inclusion log documenting records added to the qualitative pool
  outside the primary screening TSV
- The manuscript's Table 1 (or equivalent): the definitive list of studies contributing to
  the primary quantitative synthesis

**Procedure:**

1. **Enumerate the ID sets:**
   - A = set of IDs marked INCLUDE in the screening TSV
   - B = set of IDs marked Exclude in the consensus spreadsheet
   - C = set of IDs marked Include-qualitative in the consensus spreadsheet
   - T = set of IDs represented in Table 1 (via author/year cross-match)

2. **Derive canonical totals:**
   - k_qualitative = |A \ B| + |C|
   - k_bivariate = |T|
   - k_narrative-only = k_qualitative − k_bivariate = |(A ∪ C) \ B \ T|
   - k_FT-excluded = |screening TSV rows| − |A| + |B ∩ A| + |(B \ A) encountered at FT stage|

3. **List the narrative-only IDs explicitly** — this is the highest-yield cross-check. A
   manuscript claiming "10 narrative-only studies" while the (A ∪ C) \ B \ T set contains
   only 2 IDs is an immediate P0 finding.

4. **Compare each derived total against the manuscript's prose claim** in Abstract, Methods
   §Study Selection, Results §Study Selection, Figure 1 caption, Discussion §Limitations,
   and any References §Narrative-Only heading. Any mismatch between derived total and
   manuscript prose = P0 Major Comment, blocking submission.

5. **Record results in a short reconciliation block** and append to the report:

   ```
   | Quantity | Manuscript claim | ID-derived value | Status |
   |---|---|---|---|
   | k_full-text | 78 | 78 | ✓ |
   | k_qualitative | 32 | 24 | ✗ P0 |
   | k_bivariate | 22 | 22 | ✓ |
   | k_narrative-only | 10 | 2 (IDs 120, 474) | ✗ P0 |
   | k_FT-excluded | 46 | 54 | ✗ P0 |
   ```

**Any "N → M" transition claim in a consensus summary (e.g., "30 → 32 after FLAG
consensus") that is not backed by an enumerable ID addition/subtraction set is itself a
Major Comment**, because the transition is unverifiable by downstream audit. Require
conversion of every such claim to explicit ID lists before closing the report.

### Phase 2.5c: Reference Hallucination Scan

Numerical audits (2.5/2.5a/2.5b) cover in-text numbers; they do **not** cover reference-list integrity. LLM-drafted or co-author-handed-in bibliographies frequently contain fabricated DOIs, wrong author/year combinations for a real DOI, or plausible-looking references that never existed. These slip past human proofreading because the surface form looks canonical.

**When to run:** every manuscript at self-review, regardless of stage. Mandatory before submission and before any revision circulation to co-authors or the editor.

**Procedure:**

1. **Locate the bibliography.** From `SSOT.yaml` → `truth.refs_bib` (fallback `manuscript/_src/refs.bib` for legacy projects). If `SSOT.yaml` is absent, scan `references/library.bib` as a last resort.

2. **Invoke `/verify-refs`** on the resolved bib. The skill writes `qc/reference_audit.json` with a per-entry verdict (`VERIFIED` / `FABRICATED` / `UNVERIFIED`) and a top-level `submission_safe` boolean.

   ```bash
   # equivalent CLI form (same result as invoking the skill).
   # verify_refs.py takes a positional input (the .bib path) and writes its audit
   # to <project-root>/qc/reference_audit.json (path derived from --project-root).
   BIB="$(python3 -c "import yaml; print(yaml.safe_load(open('SSOT.yaml'))['truth']['refs_bib'])")"
   python3 skills/verify-refs/scripts/verify_refs.py "$BIB" --project-root . --strict
   ```

   When both reference QC and cross-reference QC are needed in one pass, prefer
   the master orchestration entry point in `/manage-refs` — it chains
   `check_citation_keys.py` → `verify_refs.py --strict` → `render_pandoc.sh`
   (optional) → `check_xref.py --strict` and writes
   `qc/pre_submission_gate.json` as the single submission-readiness artifact:

   ```bash
   bash "${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}/skills/manage-refs/scripts/pre_submission_gate.sh" \
       --md manuscript/manuscript.md \
       --bib manuscript/_src/refs.bib \
       --docx submission/<journal>/manuscript.docx \
       --allow-separate-attachments  # see Phase 2.5d for when this is appropriate
   ```

3. **Read `qc/reference_audit.json`.** For each entry not marked `VERIFIED`, add a row to the reconciliation block below. `FABRICATED` entries are P0 Major Comments (block submission). `UNVERIFIED` entries are Minor Comments unless the manuscript is at a circulation/submission gate, in which case they escalate to Major. For each `duplicate_findings[]` entry (category `duplicate_pmid` / `duplicate_doi`), add a Major Comment row noting the duplicated `ref_ids` pair and recommend cite renumbering — duplicates block submission (P0 Major) regardless of per-record `VERIFIED` status.

4. **Cross-check placeholder drift.** `grep -n '\[@NEW:' manuscript/` — any remaining `[@NEW:topic]` placeholder at self-review stage is a P0: the citation was queued but never resolved. Include in the reconciliation block.

5. **Record results in a short reconciliation block** and append to the Phase 3 report:

   ```
   | Citekey | Verdict | Source check | Status |
   |---|---|---|---|
   | Kim_2024_Validation | VERIFIED | DOI + PubMed match | ✓ |
   | Park_2023_Radiomics | FABRICATED | DOI resolves to unrelated paper | ✗ P0 |
   | Lee_2022_DeepLearning | UNVERIFIED | No DOI/PMID, title not found | △ Major before submission |
   | [@NEW:segmentation_review] | PLACEHOLDER | unresolved citation queue | ✗ P0 |
   ```

**Short-circuit rule:** if `qc/reference_audit.json` already exists with a bib-hash match within 60s (P9 cache TTL, pending), the scan MAY reuse it; otherwise re-run. Never consume a stale audit from a prior manuscript revision.

**Do NOT fabricate replacement references** if any entry fails. Fix-forward belongs to `/search-lit` and `/lit-sync`, not to this skill. Self-review only reports the failure and blocks submission.

### Phase 2.5d: Cross-Reference QC (Manuscript ↔ rendered DOCX)

Reference-list integrity (Phase 2.5c) does **not** cover Table/Figure
cross-references. This is a separate failure mode where in-text citations
("Supplementary Table S4 reports a sensitivity analysis") resolve to a different
caption in the rendered DOCX ("Supp Table S4 = a diagnostics table") because the
build script carries its own legacy SSOT. Internal consistency (Phase 2.5)
cannot detect it — both the prose and the build artifact echo their own
divergent truths cleanly.

**Precedent failure pattern (an STROBE cohort manuscript revision):**
> Body prose cited Supp Table S4 as a sensitivity analysis; the rendered DOCX
> S4 instead contained a diagnostics table. S1, S6, S7 also mismatched. S8 and S9
> were cited in the manuscript but absent from the rendered DOCX entirely.
> Caught only on co-author circulation review.

**When to run:** every manuscript at self-review when a rendered DOCX exists
(e.g., circulation drafts, post-build pre-submission checks). Skip only if no
DOCX build has occurred yet (early drafts).

**Procedure:**

1. **Locate inputs.** `manuscript/manuscript.md` (or the SSOT `truth.manuscript_md`)
   and the rendered DOCX (typically `manuscript/manuscript_final.docx` or the
   most recent circulation `.docx`).

2. **Invoke the shared script** (lives in `/manage-refs`):

   ```bash
   python3 "${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}/skills/manage-refs/scripts/check_xref.py" \
     --md manuscript/manuscript.md \
     --docx manuscript/manuscript_final.docx \
     --out qc/xref_audit.json \
     [--allow-separate-attachments]
   ```

   The script writes `qc/xref_audit.json` with per-label rows tagged
   `OK | MISSING_DOCX | MISSING_BODY | MISMATCH | UNCITED | NOT_CITED_NO_BODY`,
   a top-level `submission_safe` boolean, and a `policy.allow_separate_attachments`
   field that records which severity policy applied.

3. **Translate findings to anticipated comments.** Severity mapping depends on
   the journal's figure/table submission policy. Many radiology and medical
   journals (e.g., European Radiology, Radiology, AJR) accept figures and tables
   as separate attachment files rather than inline in the manuscript DOCX; for
   those workflows pass `--allow-separate-attachments` so MISSING_DOCX is not
   treated as a P0 blocker. `MISSING_BODY` and `MISMATCH` remain P0 regardless,
   because they indicate SSOT drift between body markdown and rendered DOCX
   rather than a legitimate attachment style.

   | Status | Default policy | With `--allow-separate-attachments` |
   |---|---|---|
   | `MISSING_DOCX` | **Major (P0)** — cited Table/Figure absent from rendered output | **Minor** — figure/table is separately attached per journal policy |
   | `MISSING_BODY` | **Major (P0)** — build SSOT drift; rendered caption has no body definition | **Major (P0)** (no change) |
   | `MISMATCH` | **Major (P0)** — caption text disagrees between body and rendered DOCX | **Major (P0)** (no change) |
   | `UNCITED` | Minor — orphan caption that should be cited or removed | Minor (no change) |

4. **Append a reconciliation block to the Phase 3 report:**

   ```
   | Label | Status | Body caption | DOCX caption | Verdict |
   |---|---|---|---|---|
   | Supplementary Table S4 | MISMATCH | Sensitivity analysis | Diagnostics table | ✗ P0 |
   | Supplementary Table S8 | MISSING_DOCX | (defined in body) | — | ✗ P0 |
   | Figure 2 | UNCITED | Forest plot of subgroups | Forest plot of subgroups | △ Minor |
   ```

5. **Emit each P0 row as a separate `M`-numbered Major Comment** with
   `category: "F"` (Reporting Completeness) and `fixable_by_ai: false`
   (build script changes are out of scope for the auto-fix loop — they
   require pipeline-side fixes per `/write-paper` Step 7.6a routing).

**Do NOT auto-fix cross-reference defects in `--fix` mode.** Caption rewrites
in the body without re-running the DOCX build will simply move the mismatch.
Surface as Major Comments and let the user route to `/write-paper` Step 7.6a.

### Phase 2.5e: Confounding Completeness (observational only)

For an observational study, the highest-yield reviewer finding is also the most
mechanical, and a prose pass misses it because the manuscript text is internally
consistent: a covariate that was **measured**, is **imbalanced across exposure
groups** in the baseline table, and is **absent from the adjustment set** is
residual confounding by a measured variable. Only a join of the exposure-
stratified Table 1 against the Methods adjustment set exposes it. This is probe
O1 of `references/domain-probes/observational_confounding.md`, run here as a
deterministic gate so the finding lands without the `--panel` cost.

**When to run:** manuscript type is observational (cohort, case-control,
cross-sectional, health-screening registry) and the central claim is an
adjusted exposure–outcome association. Skip for RCTs and descriptive studies.

**Precedent failure pattern:**
> A cross-sectional screening-cohort manuscript reported an adjusted association
> while Table 1 showed uric acid, smoking pack-years, HDL, total cholesterol, and
> HbA1c all significantly imbalanced across the exposure groups — none of which
> were in the age/sex/BMI/hypertension/diabetes adjustment set. The single-pass
> review passed it; only an epidemiology panel reviewer who read the Table 1 CSV
> against the Methods caught the gap. After refitting with extended adjustment the
> primary estimate held, but the manuscript had claimed robustness it had not shown.

**Procedure:**

1. **Locate the exposure-stratified baseline table** as a CSV (e.g.
   `table1_by_<exposure>.csv` from `/analyze-stats`) and the Methods adjustment
   set (the variables after "adjusted for ...").

2. **Run the deterministic gate:**

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/check_confounding_completeness.py" \
     --table1 table1_by_<exposure>.csv \
     --adjusted-list "age, sex, BMI, hypertension, diabetes" \
     --out qc/confounding_completeness.json --strict
   ```

   It emits a reconciliation table (covariate | imbalance p | SMD | in adjustment
   set? | verdict) and flags each **measured-but-unadjusted imbalanced** covariate
   as an `UNADJUSTED_IMBALANCED` Major candidate. When the CSV is unavailable,
   apply probe O1 by hand from the published Table 1.

3. **Each `UNADJUSTED_IMBALANCED` covariate is an Anticipated Major Comment**
   (category: A. Study Design & Data Integrity), with the suggested fix: report an
   **extended-adjustment sensitivity model** that adds the omitted covariates and
   states whether the primary estimate is materially unchanged; the original model
   stays primary only if the extended model agrees.

4. **Then apply the rest of the observational probe set** (O2 adjustment-set
   provenance, O3 selection/collider bias, O4 exposure measurement validity, O5
   missing-data mechanism & complete-case collapse, O6 residual-confounding
   E-value) from `references/domain-probes/observational_confounding.md` — these
   are prose probes, not data-checkable, and complement the generic Phase 2
   categories rather than replacing them.

**Adjustment-set matching is fuzzy** (a table row "Smoking, pack-years" vs an
adjustment token "smoking"): read the reconciliation table rather than trusting
the count, and confirm each flagged covariate is a plausible cause of the outcome
(not a mediator or collider, which O2 covers) before raising it.

### Phase 2.6: Multi-Agent Panel Review (--panel, opt-in)

Run this phase **only when `--panel` is passed**. The default single-pass review (Phases 2–2.5d) stays the fast path; the panel is the high-cost, high-precision option for a pre-submission final pass on a top-tier target. Run it after the numerical audits (Phases 2.5–2.5d) so the reviewers see source-verified numbers, and before the Phase 3 report, which it feeds.

The panel simulates independent peer reviewers who do not see each other's comments, then an editor who consolidates them — the same structure a journal uses. It reuses the vendored domain-probe modules so every reviewer applies the same criteria.

**Step 1 — Compose the reviewer set by research type.** Auto-detect the manuscript type (Phase 1 input + the Research-Type Adaptation table). Each reviewer loads the matching domain-probe module so the panel's criteria are single-sourced.

| Research type | Reviewer set (each is one reviewer) | Domain-probe module each loads |
|---|---|---|
| Survival / prognostic cohort | R1 Biostatistics & Study Design · R2 Clinical (domain) · R3 Imaging/Radiology (if an imaging exposure) | `references/domain-probes/survival_prognostic.md` |
| Systematic review / meta-analysis | R1 Methodology (search/screening/PRISMA) · R2 Clinical · R3 Statistics (pooling/heterogeneity) | `references/domain-probes/sr_ma.md` |
| Radiomics / feature reproducibility | R1 Imaging physics & acquisition · R2 ML / Statistics · R3 Clinical translation | `references/domain-probes/radiomics.md` |
| Diagnostic-accuracy / AI model | R1 Study design & leakage · R2 Statistics (DeLong, calibration) · R3 Clinical / reference standard | `references/domain-probes/sr_ma.md` (P1 DTA cells) + categories A–C |
| Observational (STROBE) | R1 Epidemiology / confounding · R2 Clinical · R3 Statistics | `references/domain-probes/observational_confounding.md` (O1 run as the Phase 2.5e deterministic gate) + categories A–J + the effect-size / added-value axes |
| Narrative / review article | R1 Domain-content expert · R2 Methodology / SANRA · R3 Technical accuracy | `references/domain-probes/narrative_review.md` |

If the type is ambiguous, ask the user before composing the set.

**Step 2 — Run the reviewers (portable execution).** When the host provides a parallel subagent / Task capability (Claude Code, or any harness exposing an Agent tool), spawn the reviewer set as independent parallel subagents, each blinded to the others, then run the editor as a final synthesis agent. **Fallback (no subagent capability — e.g. a minimal Codex/Cursor harness):** a single agent role-plays each reviewer sequentially and in isolation — it completes and writes out reviewer R1's full structured review before reading the manuscript "fresh" as R2, so a later reviewer never sees an earlier reviewer's comments. The panel is defined by these instructions; it does **not** depend on the `Workflow` tool or any Claude-Code-only orchestration.

A reusable reviewer schema, a generic harsh-but-fair reviewer prompt skeleton with per-domain focus checklists, and the editor synthesis prompt skeleton live in `${CLAUDE_SKILL_DIR}/references/panel_review_template.md`.

Each reviewer returns: `reviewer_id`, `expertise_area`, an `overall_assessment` (name the single biggest threat to the conclusions), `strengths` (2–3), `major[]` (each with `heading`, `comment`, `location`, `severity`, `suggested_fix`), and `minor[]`. Map `severity` onto this skill's own scale — a conclusion-threatening / design-level finding is **Fatal**, a reporting-level finding is **Fixable** — rather than introducing a separate vocabulary.

**Step 3 — Editor synthesis.** One editor pass (a final agent, or the main agent in the fallback) consolidates the reviews:
1. **Dedupe** findings by theme across reviewers.
2. **Flag CONSENSUS** for any theme raised by ≥2 reviewers, with R1/R2/R3 attribution (e.g., `[CONSENSUS: R1+R3]`); single-reviewer findings are attributed to the one reviewer.
3. **Decide** an internal readiness verdict (this sets the Phase 3c `verdict` / `overall_score`; it is not printed as a journal recommendation).
4. **Rank** the concrete pre-submission actions the author should complete first.
5. State a one-line **readiness verdict** (ready for the target tier now / fix specific items first / consider a different tier).

**Step 4 — Feed Phase 3.** The consolidated panel output flows into the Phase 3 report, Phase 3b R0 numbering (**preserved**, so `/revise` still consumes it), and Phase 3c JSON. CONSENSUS flags and reviewer attribution are additive annotations on the existing `M`/`m` comments (and the optional `consensus` JSON field); they do not change the report or JSON structure.

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
- `consensus` *(optional, panel mode only)*: array of reviewer ids that raised the issue, e.g. `["R1","R3"]`. Additive and backwards-compatible — present only when Phase 2.6 ran; parsers that do not expect it must ignore it.

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

- **Never fabricate references.** All citations must be verified via `/search-lit` with confirmed DOI or PMID. Mark unverified references as `[UNVERIFIED - NEEDS MANUAL CHECK]`. Self-review enforces this through **Phase 2.5c: Reference Hallucination Scan** (runs `/verify-refs` against the SSOT bib); any `FABRICATED` verdict blocks submission as a P0 Major Comment.
- **Never invent clinical definitions, diagnostic criteria, or guideline recommendations.** If uncertain, flag with `[VERIFY]` and ask the user.
- **Never fabricate numerical results** — compliance percentages, scores, effect sizes, or sample sizes must come from actual data or analysis output.
- If a reporting guideline item, journal policy, or clinical standard is uncertain, state the uncertainty rather than guessing.

---

## Gates

| Gate | Severity | Trigger | Action on fail |
|---|---|---|---|
| Phase 2.5b cross-reference QC (delegate `/manage-refs scripts/check_xref.py`) | ENFORCED | MISSING_DOCX / MISSING_BODY / MISMATCH > 0 | P0 Major Comment, blocks submission |
| Phase 2.5c reference hallucination scan (delegate `/verify-refs`) | ENFORCED | `FABRICATED` in `records[]` OR nonempty `duplicate_findings[]` | P0 Major Comment, blocks submission |
| Phase 2.5a-2 design/power statistic provenance | ENFORCED | a reported MDE / power / sample-size value is not reproduced by committed code, or is reproducible only by a method the committed script does not implement | Major Comment (P0 if a headline claim); recompute and either correct the value or update the committed code to reproduce it |
| `--fix` auto-fix loop (max 2 iterations) | ENFORCED in `/write-paper` Phase 7.4 chain | score still below threshold after 2 iterations | Route to write-paper Phase 7.4a Audit Recovery |
| R0 numbering output | OPT-IN | `--r0-numbering` flag or downstream `/revise` consumer | Emits structured Anticipated Major/Minor Comments — consumable by `/revise` |
| `--json` machine-readable output | OPT-IN | `--json` flag | Emits parseable JSON block consumed by `/orchestrate` post-skill validation |
