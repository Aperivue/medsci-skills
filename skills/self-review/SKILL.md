---
name: self-review
description: Use when checking your own manuscript before submission from a reviewer's perspective. Returns anticipated Major/Minor comments with fixes, including numerical, citation and leakage checks, with an optional multi-reviewer panel. Someone else's paper is /peer-review.
metadata:
  triggers: "self-review, pre-submission check, check my paper, reviewer perspective, manuscript self-check"
---

# Self-Review Skill

Check the user's own manuscript before submission and produce an actionable list of anticipated
reviewer comments, each with a specific fix — not a written review.

## Optional Flags

- `--fix`: after the report, apply fixes for every issue with `fixable_by_ai: true`, editing the manuscript in place, then report a diff summary. Never fix `fixable_by_ai: false` issues (missing data, design flaws). Maximum 2 fix-and-re-review iterations; if the score is still below threshold after the second, stop and report what remains as structural (inside `/write-paper` this routes to Phase 7.4a Audit Recovery).
- `--json`: also emit the structured JSON block (Phase 3c). Default when called from `/write-paper` Phase 7.
- `--panel`: run the multi-agent panel review (Phase 2.6) — domain-expert reviewers in parallel plus an editor synthesis — instead of the single-pass review. Opt-in and **off by default**, because it spawns N reviewer agents + 1 editor and costs several times more tokens; reserve it for a high-stakes final pass on a top-tier target. Do **not** combine with `--fix`: a panel diagnoses and prioritizes; run `--fix` as a separate pass once the author has triaged the panel's findings.

## Severity Framing

- **Fatal**: a design flaw existing data cannot fix (data leakage that invalidates all results, no reference standard, label–feature circularity). Submission would likely be rejected. Reserve Fatal for true design-level problems.
- **Fixable**: significant but addressable with existing data (missing calibration, unclear exclusion criteria, absent CIs, incomplete reporting). Most issues are Fixable.

## Two Objectives: the Floor and the Ceiling

The **floor** (categories A–K and the gates of Phases 2.5–2.5f) minimizes rejection-for-cause —
fabricated citations, numbers that do not reconcile, overclaims, missing checklist items, leakage —
and much of it works by **adding** a hedge, caveat, disclosure or audit trail. Iterated, that
over-hardens a manuscript: every finding is correct, yet the whole reads as a defensive audit
(over-hedged, audit trail in the body, Abstract buried under caveats, the strongest robustness
result hidden in Limitations). The **ceiling** pass (category L / Phase 2.5g) runs **after** the
floor gates, reads the accurate manuscript as a whole, and recommends only SUBTRACTION — REMOVE,
MOVE, or TIGHTEN. It is advisory, never blocks, and cannot relax a floor gate. Report its findings
as their own block (Phase 3), not folded into the "add this" comments. Phase 2.5i then reads the
floor + ceiling state to declare the loop done, including a zero-edit PASS.

## Workflow

### Phase 1: Intake

1. Get the manuscript — PDF, Word doc, or pasted text.
2. Ask the user: target journal (sets reporting standards and scope); manuscript type (original research / review / perspective / technical note / letter / meta-analysis / case report); anything they are already worried about. On an interactive run, offer the `--panel` review (Phase 2.6) **once**, in one line, then proceed single-pass unless the user opts in. Never offer or apply the panel under `--json` or when called from `/write-paper`.
3. Read the full manuscript.
4. **SSOT gate — confirm there is one manuscript, not several.** Self-review reads a single file,
   so drift between a legacy working copy and the live submission copy is invisible to it. Before
   a `--panel` run or any pre-submission pass, check for multiple copies:

   ```bash
   find . \( -path '*manuscript*' -o -path '*main_document*' \) -name '*.md' | grep -v node_modules
   ```

   If more than one manuscript-like file exists, confirm which is the SSOT and run
   `/sync-submission`'s divergence gate — a `STALE_COPY` (an SSOT numeric claim or heading that did
   not propagate to the other copy) is a P0 that must clear first:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/../sync-submission/scripts/detect_copy_divergence.py" \
     --ssot <ssot>.md --copy <other-copy>.md
   ```

   Review the SSOT copy, never a stale one. **Under `--panel` this is blocking:** if `find` returns
   more than one file and the SSOT is not pinned (no `SSOT.yaml` with `truth.manuscript_md`, no
   explicit `--ssot <path>`), STOP before spawning any reviewer and have the user name the SSOT
   (and clear any `STALE_COPY`), because a panel on a stale copy wastes the whole pass. Do not
   auto-pick the longest/newest file. A single-pass review may proceed on the one file it was given.

### Phase 2: Systematic Check

Work every category the Research-Type Adaptation table (below) marks as applicable, and for each
item decide whether a reviewer would raise it as a Major or Minor comment. The per-item check
tables are in `references/phases/phase2_systematic_check.md` — read it once you have the
manuscript and know its type.

| | Category | What it asks |
|---|---|---|
| **A** | Study Design & Data Integrity | patient-level splits, leakage, input-text contamination, analysis unit |
| **B** | Reference Standard & Ground Truth | definition specificity, timing, annotator independence |
| **C** | Validation & Statistical Reporting | CIs, **calibration**, comparator, effect size, power-aware nulls, equivalence margins, interaction anchoring |
| **D** | Clinical Framing & Importance | intended use, overclaiming, novelty, **endpoint↔conclusion scope** |
| **E** | Reproducibility | preprocessing, model detail, hardware/software, data & code availability |
| **F** | Reporting Completeness | abstract↔body consistency, flow diagram, ethics, missing data, word cap |
| **G** | Reporting Guideline Compliance | match the type to its checklist; `/check-reporting` does the item-level audit |
| **H** | Circularity | label–feature overlap, tautological prediction, circular validation |
| **I** | Protocol Heterogeneity | multi-site acquisition, harmonization, temporal protocol drift |
| **J** | Method Transparency | model provenance, fine-tuning, classical-style body conventions |
| **K** | Reviewer-team consistency | *SR/MA only* — dual-vs-single conjunction, LLM-as-reviewer (both fabrication-grade) |
| **L** | Editorial impression & defensiveness | *advisory, never blocking* — the ceiling category: REMOVE / MOVE / TIGHTEN |

**Run the deterministic gates at Phase 2 entry, on every path:**

```bash
# D. endpoint↔conclusion scope
python3 "${CLAUDE_SKILL_DIR}/scripts/check_scope_coherence.py" \
  --manuscript manuscript.md --out qc/scope_coherence.json --strict

# J. classical-style body conventions
python3 "${CLAUDE_SKILL_DIR}/scripts/check_classical_style.py" \
  --manuscript manuscript.md --out qc/classical_style.json --strict

# K. reviewer-team consistency (SR/MA only; pass the extraction JSON file or directory)
python "${CLAUDE_SKILL_DIR}/scripts/check_reviewer_team_consistency.py" \
    --manuscript manuscript.md --prospero prospero/record.md \
    --extraction-json extraction/ --out _audit_self/reviewer_team_consistency.md

# J/D. Perspective structure (genre-gated: silent unless article_type is a Perspective).
# Pass the known type via --type; it also self-detects from the front-matter article_type.
python3 "${CLAUDE_SKILL_DIR}/scripts/check_perspective_structure.py" \
  --manuscript manuscript.md --type "${TYPE:-}" --out qc/perspective_structure.json

# Was every reported analysis ever defined (outcome, reference standard)?
python3 "${CLAUDE_SKILL_DIR}/scripts/check_analysis_definitions.py" \
  --manuscript manuscript.md --json --strict > qc/analysis_definitions.json
```

Verdict mapping: `CROSS_SECTIONAL_PROGNOSTIC`, `SURROGATE_CARE_DIRECTIVE`, `SECTION_SYMBOL`,
`INBODY_AI_DISCLOSURE`, any reviewer-team hit (exit 1), `MODEL_OUTCOME_UNDEFINED` (a Cox /
Fine–Gray / logistic model with no outcome named), `MODEL_NOT_IN_METHODS`, and
`REFERENCE_STANDARD_UNDEFINED` (discrimination or calibration with nothing to score against) are
Anticipated **Major** Comments. `CROSS_SECTIONAL_YIELD_LANGUAGE`, `ELIGIBILITY_PROSE`,
`DECIMAL_INCONSISTENCY`, `EM_DASH_OVERUSE`, `PERSPECTIVE_HEADING_NOT_ASSERTION`,
`PERSPECTIVE_ABSTRACT_NO_AUTHORIAL_MOVE`, and `TIER_LABEL_UNDEFINED` are **Minor**. The
per-verdict rationale and resolution paths are in the Phase 2 reference file.

`ANALYSIS_LOAD` is **informational, never a verdict**: many analyses are the cause of omitted
definitions, not the defect. Do not cut analyses to satisfy it; restore the definitions they
crowded out, and if load is genuinely high, move the defensive analyses to the supplement.

### Research-Type Adaptation

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
| L. Editorial impression | Full | Full | Full | Full | Full | Full |

*Meta-analysis: replace C with heterogeneity (I², prediction intervals), publication bias (funnel
plot, Egger), and sensitivity/subgroup analyses.

**Type-specific additional checks:**

- **Observational**: confounding (DAG or adjustment strategy), selection bias, exposure measurement validity. Run **Phase 2.5e (Confounding Completeness)**, then apply the O-probes in `references/domain-probes/observational_confounding.md` — O1 (covariate imbalanced by exposure in Table 1 yet absent from the adjustment set) and O8 (records > subjects with the analysis unit undisclosed; `check_cohort_arithmetic.py --id-col`) are the deterministic ones, and O7 (adjusting for a mediator/consequence of the outcome) is their opposite-direction twin. For a **clinical prediction model** (TRIPOD / TRIPOD+AI, nested predictor-set comparison), also apply the CP-probes in `references/domain-probes/clinical_prediction_model.md`.
- **Educational**: learning-outcome measurement validity, Kirkpatrick level, control-group adequacy, curriculum fidelity.
- **Meta-analyses**: search comprehensiveness (2+ databases), screening reproducibility (2 reviewers), per-study RoB, GRADE certainty.
- **Case reports**: diagnostic-reasoning transparency, timeline completeness, informed consent, generalizability disclaimer.
- **Surgical**: learning curve, surgeon volume/experience, complication grading (Clavien-Dindo), operative detail.

**Domain probe modules** — the same probes `/peer-review` uses, vendored here. Load every module
whose row matches:

| Manuscript type / signal | Probe module |
|---|---|
| Systematic Review / Meta-Analysis | `references/domain-probes/sr_ma.md` (P0–P19) |
| Time-to-event / survival / prognostic model (Cox, Fine-Gray, DeepSurv, nomogram, risk-stratification cutoff) | `references/domain-probes/survival_prognostic.md` (S1–S9) |
| Radiomic feature reproducibility / acquisition-parameter sweep / reliability-based feature filtering | `references/domain-probes/radiomics.md` (R1–R4) |
| Cross-modality image synthesis (MRI→PET / MRI→CT / non-contrast→contrast / low-dose→full-dose) claiming functional/molecular information or target-modality substitution | `references/domain-probes/image_synthesis.md` (IS1–IS4) |
| Narrative / review article / primer / state-of-the-art | `references/domain-probes/narrative_review.md` (RV1–RV9) |
| Perspective / opinion / viewpoint (npj DM long-essay, Lancet Comment, NEJM AI / RYAI short-structured) | `references/domain-probes/narrative_review.md` (RV1–RV9) + the `check_perspective_structure.py` gate above |
| AI/ML primary study with a clinical claim (generalizable / outperforms clinicians / deployment-ready / can replace a reader) | `references/domain-probes/ai_overclaiming.md` (AO0–AO7) |
| Engineer-built medical-imaging model (segmentation / classification / detection) being validated — partition/leakage, seed & run variance, metric selection, reproducibility, reference-standard quality; plus saliency faithfulness, uncertainty/OOD/abstention and deployment feasibility when a clinical-use claim is made | `references/domain-probes/model_development.md` (MD0–MD11) |
| LLM / MLLM evaluated on a clinical task (report generation, VQA, clinical text extraction/classification; closed API or open weights) | `references/domain-probes/mllm_evaluation.md` (ME0–ME8) |
| Randomised controlled trial (parallel / crossover / cluster / stepped-wedge) | `references/domain-probes/rct_trial.md` (RC0–RC7) |
| Diagnostic test accuracy (DTA) primary study / multi-reader multi-case (MRMC) reader study (AI-vs-reader, AI-assisted reading, modality comparison) | `references/domain-probes/diagnostic_accuracy.md` (D1–D12) |
| Case report / case series (incl. adverse-event/pharmacovigilance and imaging-led radiology/nuclear-medicine/IR reports) | `references/domain-probes/case_report.md` (CR1–CR9) |
| AI/ML, prediction, or diagnostic study claiming cross-population performance, or presenting subgroup analyses as a fairness/equity argument | `references/domain-probes/equity_fairness.md` (EQ0–EQ6) |
| Mendelian randomization (two-sample, one-sample, multivariable, drug-target / cis-MR, non-linear MR) | `references/domain-probes/mendelian_randomization.md` (MR1–MR8) |
| Polygenic risk score (PRS / PGS) developed, validated, or applied as a predictor or risk-stratifier | `references/domain-probes/polygenic_risk_score.md` (PG1–PG8) |
| Network meta-analysis (≥3 interventions via direct + indirect evidence, treatment ranking, incl. component NMA) | `references/domain-probes/network_meta_analysis.md` (NM1–NM8) |
| Health economic evaluation (cost-effectiveness / cost-utility / cost-benefit / budget-impact; trial- or model-based — decision tree, Markov, DES) | `references/domain-probes/health_economic_evaluation.md` (HE1–HE8) |
| Observational study using routinely-collected health data (claims / EHR / registry / health-checkup DB, linked or not) | `references/domain-probes/record_routinely_collected_data.md` (RD1–RD8) |
| Self-report survey / questionnaire study (KAP, physician/patient survey, web/e-survey) | `references/domain-probes/survey_research.md` (SV1–SV8) |
| Scoping review (maps breadth of evidence; PCC framing, charting — not a focused effectiveness/accuracy question) | `references/domain-probes/scoping_review.md` (SC1–SC8) |
| Qualitative study (interviews, focus groups, ethnography, grounded theory, phenomenology, document analysis) | `references/domain-probes/qualitative_research.md` (QL1–QL8) |
| **Self-improving / self-evaluating system** (an agent that critiques and rewrites its own output; training on model-generated data; an LLM judge scoring the training signal; "self-evolving" clinical agents) | `references/domain-probes/self_improving_system.md` (SI1–SI7) + `skills/peer-review/scripts/check_self_improvement_claims.py` |

Apply each probe as an additional source of comments, complementing (not replacing) categories
A–K: a conclusion-threatening or design-level finding becomes a **Fatal** Anticipated Major
Comment, a reporting-level finding a **Fixable** Anticipated Minor Comment, each tagged with the
closest category letter (A–K).

For a **classifier / NLP / tabular ML** manuscript, also run the feature-selection-leakage gate — a
data-driven selection (feature selection, univariate filtering, vocabulary, a threshold) fit on the
FULL dataset before cross-validation inflates the CV metric:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_cv_leakage.py" \
  --manuscript manuscript.md --out qc/cv_leakage.json
```

`CV_SELECTION_LEAKAGE` (Major) fires when a selection token co-occurs with cross-validation and no
fold-nesting is disclosed ("within each fold" / "nested CV" suppresses it). Patient-vs-image split
leakage is a different check (`model-assessment/check_split_leakage.py`).

### Phase 2.5: Numerical Cross-Verification (Internal)

Before the report, verify internal consistency:

1. **Abstract vs Body**: every Abstract number matches Results and Tables.
2. **Table vs Text**: sample sizes, primary outcomes and p-values agree between tables and narrative.
3. **Figure vs Text**: figure legends match the data described in Results.
4. **Percentage arithmetic**: n/N percentages are correct (23/150 = 15.3%, not 15.0%). The gate
   holds each cell to its printed precision (half a unit in the last printed place).
5. **CI plausibility**: confidence intervals are reasonable for the sample sizes.
6. **Rate back-calculation**: every rate inverts to its own numerator/denominator (incidence rate ≈ events / person-years × scale, ±rounding). A rate that does not recompute, or implies more events than the cohort can supply, is a Major.
7. **Exclusion-cascade and complete-case arithmetic** (cohort/observational): start N − Σ(exclusions) == final analytic N, and total − missing == complete. A footnote N that does not equal the subtraction is a Major.

For cohort/observational manuscripts, run the gate instead of eyeballing it (it parses prose
equations + GFM tables, and recomputes from a committed CSV when given one):

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_cohort_arithmetic.py" \
  --manuscript manuscript.md --data analysis/cohort.csv --id-col mockid \
  --out qc/cohort_arithmetic.json --strict
```

`RATE_BACKCALC` / `CASCADE_SUM` / `PARTITION_OVERLAP` are Anticipated Major Comments (category A).
On health-screening / EMR / registry data pass `--id-col` (or let it auto-detect a subject-ID
column) so it also checks the analysis unit: `records > unique subjects` with neither the unit nor a
one-record-per-subject sensitivity stated emits `ANALYSIS_UNIT_UNDISCLOSED` (Major — non-independent
observations give anti-conservative CIs; probe O8). Flag any remaining internal-consistency
discrepancies as Anticipated Minor Comments (category F).

Then recompute what a reviewer recomputes by hand:

```bash
# Every "n (%)" in a table, recomputed against its own denominator.
python3 "${CLAUDE_SKILL_DIR}/scripts/check_table_percentages.py" \
  --manuscript manuscript.md --out qc/table_percentages.json --strict

# Every reported P beside a 2×2 (or r×c) count, recomputed from the counts themselves.
python3 "${CLAUDE_SKILL_DIR}/scripts/check_reported_p_from_counts.py" \
  --manuscript manuscript.md --json --strict > qc/reported_p.json

# Diagnostic-accuracy only: sensitivity/specificity against the reference-standard denominators.
python3 "${CLAUDE_SKILL_DIR}/scripts/check_dta_denominators.py" \
  --manuscript manuscript.md --json --strict > qc/dta_denominators.json
```

`PERCENT_MISMATCH`, `P_NOT_REPRODUCIBLE`, and `DTA_DENOMINATOR_MISMATCH` / `STAGE_ROWSUM` are
**P0 Major** — not a rounding disagreement: one of the two numbers is wrong. Run the first two on
**every** manuscript with a table; the third only on diagnostic-accuracy work.

To check each P against its own test, declare the tests as `p_tests.json` (copy
`${CLAUDE_SKILL_DIR}/templates/p_tests.json`; schema in `references/p_tests_schema.md`) and add
`--tests p_tests.json`. The row's P is recomputed with the declared test (`fisher`, `chi2`,
`chi2_yates`). A reported P whose whole printed-precision interval lies on the other side of alpha
from the recomputed P is `P_ALPHA_CROSSING` (**Major**). An `adjusted`, `paired` or `other:` test,
a row whose printed percentage is not count/n (another denominator), or a table of 3+ groups (after dropping
a Total column) is `P_NOT_ASSESSED` (Minor).

Known limits: without `--tests`, `check_reported_p_from_counts.py` flags a row only when its reported
P differs from the crude 2x2 P by more than one order of magnitude under every test family, and only
in tables with at least two count rows. It does not flag a reported `<` bound (`<0.001`) that the
crude P exceeds, or a P on the other side of alpha, by less than that, nor a lone count row (open
finding SR-01 in prose-only mode): the table cannot show whether the P is adjusted, paired or on
another denominator. Check such P values against the stated test by hand, or declare them.
`check_table_percentages.py` reads one denominator per column. A cell that misses only at its printed
precision (within 0.5 pp) on a footnoted row (`Current smoker^a | 23 (15.4%)` under n = 150 with 149
known) is a Minor `PERCENT_PRECISION_NOTE`; an unfootnoted row, or a larger miss, is a
`PERCENT_MISMATCH`. Confirm footnoted rows against the footnote.

### Phase 2.5a: Numerical Source-Fidelity Audit (External)

Numbers can be self-consistent everywhere and still wrong at the source; only a traversal back to
the primary source catches that. First run the **displayed-arithmetic** gate — a stated difference
must equal the subtraction of its two displayed components at the same precision:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_rounded_delta.py" \
  --manuscript manuscript.md --out qc/rounded_delta.json
```

`ROUNDED_DELTA_MISMATCH` (Minor) fires when AUCs shown as `0.79` and `0.82` are reported with a
difference of `0.02`. A higher-precision pair (`0.794` vs `0.816`) with a 2-dp delta is legitimate
and not flagged.

**When to run the external audit:** MA revisions, submissions, or when the user says "check against
the source", "verify extraction", or "random sample". Skip otherwise.

**The audit:** draw a stratified sample of 5 numerical claims — always including one
comparative-arm value and one revision-introduced number — and trace each through three layers
(manuscript → extraction CSV → primary-source page; plus analysis script → CSV where a script
produced it). **Any mismatch is a Major Comment**; one that reverses a direction or crosses a
significance boundary is a P0 blocker. Every `[VERIFY-CSV]` tag is a mandatory audit item regardless
of sample size.

Read `references/phases/phase2_5a_source_fidelity.md` when running the external audit — it has the
traversal procedure, recording table, sampling strata, and four prose-judgement rules (hand-entered
analysis-script inputs; prose↔table statistic-type mismatch, e.g. a median in the text against a
mean in Table 1; stale derived CSVs after a model/adjustment-set change; direction reversals
internal consistency cannot see).

### Phase 2.5a-2: Design & Power Statistic Provenance

Applies only when the manuscript states a sample-size calculation, a power figure, or a
detectable-effect claim. These are computed, not copied, so Phase 2.5a cannot check them: re-derive
each from the manuscript's own inputs. A value not reproduced by committed code, or reproducible
only by a method the committed script does not implement, is a Major Comment (P0 if a headline
claim). Read `references/phases/phase2_5a2_design_power.md` when the manuscript reports a
sample-size / power / MDE calculation.

### Phase 2.5b: Screening-Count Reconciliation from ID Sets (SR/MA + observational tier/stratum)

**When to run:** any SR/MA manuscript revision, at any stage (before Phase 3); or any observational
manuscript presenting an ordinal tier / mutually-exclusive stratum split. Skip otherwise. A wrong
prose total survives every other pass because Abstract, Methods, Results, captions and supplement
all cite it back to each other; only a recount from the **ID sets** catches it.

**A. SR/MA — recount from the ID sets.** Derive every study count from the screening TSV and the
consensus sheet, never from prose, and **list the narrative-only IDs explicitly** (turning "10
narrative-only studies" into "2 (IDs 120, 474)"). A derived total that disagrees with the Abstract,
Methods, Results, Figure 1 caption or Limitations is a **P0 Major, blocking submission**; an `N → M`
transition claim not backed by an enumerable ID addition/subtraction set is a **Major**.

**B. Observational tier/stratum.** A disjoint partition must satisfy `Σ(stratum N) == unique total`
and `Σ(stratum events) == total events`. Denominators summing *above* the unique cohort double-count
subjects; every stratum n equal to the grand total is a mis-entry. Confirm the reference (baseline)
row of any stratified hazard/odds table is present and labelled.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_cohort_arithmetic.py" \
  --manuscript manuscript.md --data analysis/strata.csv --strict
```

**C. Cross-script cut-point consistency.** When one cohort is re-stratified in more than one
script, the derived categorical must use one cut definition (same breaks, same `right=` closure,
same labels) — otherwise per-stratum Ns drift while the grand total still reconciles. The same gate
covers a derived 0/1 composite rebuilt in a second script with a clause dropped.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_binning_consistency.py" \
  --root analysis --root scripts --strict
```

`PARTITION_OVERLAP`, `BINNING_DRIFT`, and `DERIVED_DEF_DRIFT` are all **P0 Major**. Read
`references/phases/phase2_5b_screening_counts.md` when doing the SR/MA ID-set recount or a
stratified-cohort recount (set definitions, derivation formulas, reconciliation-block template).

### Phase 2.5c: Reference Scans (hallucination + adequacy)

**2.5c** catches a citation that does not exist or has an invented first author; **2.5c-2** catches a
claim with no citation. Both need a bibliography — skip them if there is no `refs.bib` and no
reference list. Run `/verify-refs --strict` first (these scans read its audit), then the adequacy
checker:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_reference_adequacy.py" \
  --manuscript manuscript/manuscript.md --bib "$BIB" \
  --article-type "$TYPE" ${CAP:+--journal-cap "$CAP"} \
  --out qc/reference_adequacy.json --strict
```

A `FABRICATED` record or any `duplicate_findings[]` entry in `qc/reference_audit.json` is a P0 Major
Comment that blocks submission. Read `references/phases/phase2_5c_reference_scans.md` when the
manuscript has a bibliography and you are auditing citations.

### Phase 2.5d: Cross-Reference QC (Manuscript ↔ rendered DOCX)

In-text Table/Figure citations can resolve to a *different* caption in the rendered DOCX when the
build script carries its own legacy SSOT; no other phase sees this.

**Markdown stage (always).** Every captioned `Figure N.` / `Table N.` must be cited elsewhere in the
body:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_figure_citation.py" \
  --manuscript manuscript.md --out qc/figure_citation.json
```

`FIGURE_ORPHAN` / `TABLE_ORPHAN` (Minor): a float with a legend but no in-text citation.

**DOCX stage (only when a rendered DOCX exists** — circulation drafts, post-build checks):

```bash
python3 "${CLAUDE_SKILL_DIR}/../manage-refs/scripts/check_xref.py" \
  --md manuscript/manuscript.md --docx manuscript/manuscript_final.docx \
  --out qc/xref_audit.json [--allow-separate-attachments]
```

`MISMATCH` is always **Major (P0)**. `MISSING_DOCX` and `MISSING_BODY` are **Major (P0)** by default.
For journals that take figures/tables as separate attachments (European Radiology, Radiology, AJR),
pass `--allow-separate-attachments`: it downgrades `MISSING_DOCX` to Minor, and `MISSING_BODY` to
Minor only when no `--docx` was supplied — nothing was checked, so treat those rows as unverified
(`summary.downgraded_unchecked`) and re-run with `--docx` before submission. `MISSING_BODY` for a
float that IS in the rendered DOCX stays P0 (SSOT drift). `UNCITED` is Minor.

**Do NOT auto-fix cross-reference defects in `--fix` mode**, because rewriting a body caption
without re-running the DOCX build only moves the mismatch. Emit each P0 row as its own `M`-numbered
Major Comment with `category: "F"` and `fixable_by_ai: false`, and route the user to `/write-paper`
Step 7.6a. Read `references/phases/phase2_5d_xref_qc.md` when the xref gate fired and you are writing
up the reconciliation.

### Phase 2.5e: Confounding Completeness (observational only)

**When to run:** observational manuscripts (cohort, case-control, cross-sectional,
health-screening registry) whose central claim is an adjusted exposure–outcome association. **Skip
for RCTs, diagnostic-accuracy, SR/MA, and descriptive studies.**

A covariate that is measured, imbalanced across exposure groups in Table 1, and absent from the
adjustment set (probe O1) is invisible to a prose pass. Run the gate and treat each
`UNADJUSTED_IMBALANCED` covariate as an Anticipated Major Comment (category A):

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_confounding_completeness.py" \
  --table1 table1_by_<exposure>.csv \
  --adjusted-list "age, sex, BMI, hypertension, diabetes" \
  --exposure-defining-list "body mass index, waist, fasting glucose, triglycerides, HDL cholesterol" \
  --out qc/confounding_completeness.json --strict
```

For observational manuscripts, **read `references/phases/confounding_completeness.md`** for the full
procedure: the `--exposure-defining-list` over-adjustment exemption for guideline-defined exposures
(MASLD / metabolic syndrome / CKM / sarcopenia / frailty), the SMD-from-`mean ± SD` fallback, the
extended-adjustment sensitivity model (refit the unadjusted estimate on the reduced complete-case
frame, not the full frame), and probes O2–O10 of `references/domain-probes/observational_confounding.md`.

### Phase 2.5f: Claim-vs-Artifact Cross-Check

This phase checks claims against the artifacts they should trace to — the pre-registration, the
protocol, the analysis outputs — where the prose is internally consistent yet disagrees with them.
Run the gates (pass the supplement so the corpus is complete):

```bash
# 1. claims ↔ pre-registration/protocol: estimand provenance + E-value arithmetic
python3 "${CLAUDE_SKILL_DIR}/scripts/check_claim_artifact.py" \
  --manuscript manuscript.md --prereg prereg.md \
  --out qc/claim_artifact.json --strict   # + --evalues evalues.json (templates/) to recompute declared E-values

# 2. Methods ↔ Results ↔ disk coverage (both directions: promised-absent AND run-but-unreported)
python3 "${CLAUDE_SKILL_DIR}/scripts/check_artifact_coverage.py" \
  --manuscript manuscript.md --supplement supplement.md --analysis-dir output/analysis \
  --out qc/artifact_coverage.json --strict

# 3. reader-facing residue in EVERY rendered artifact, not just the body
python3 "${CLAUDE_SKILL_DIR}/scripts/check_supplement_hygiene.py" \
  --supplement supplement.md --supplement tables.md --supplement captions.md \
  --manuscript manuscript.md --out qc/supplement_hygiene.json --strict

# 4. float AND in-text reference-number ([N]) citation order — a desk-reject item the hygiene gate does not cover
python3 "${CLAUDE_SKILL_DIR}/scripts/check_citation_order.py" \
  --manuscript manuscript.md --out qc/citation_order.json --strict

# 5. a headline null is uninterpretable without a precision statement
python3 "${CLAUDE_SKILL_DIR}/scripts/check_null_calibration.py" \
  --manuscript manuscript.md --out qc/null_calibration.json --strict

# 5b. a headline OR/HR/RR whose 95% CI spans an order of magnitude (a direction, not a magnitude), or events/covariates < 10 (EPV)
python3 "${CLAUDE_SKILL_DIR}/scripts/check_effect_stability.py" \
  --manuscript manuscript.md --out qc/effect_stability.json --strict

# 5c. incorporation bias — a trajectory-defined reference standard with a trajectory predictor (growth) reported as associated with the outcome
python3 "${CLAUDE_SKILL_DIR}/scripts/check_incorporation_bias.py" \
  --manuscript manuscript.md --out qc/incorporation_bias.json --strict

# 6. reader/observer study only — prove the (call × confidence) → score encoding is strictly
#    monotonic; a folded score silently mis-estimates the AUC and no prose review can see it
python3 "${CLAUDE_SKILL_DIR}/../analyze-stats/scripts/rating_monotonicity.py" \
  --encoding score_def.json
```

| Verdict | Severity |
|---|---|
| `PRIMARY_REASSIGNED` | **Major** — the primary was re-designated after results were known |
| `EVALUE_ARITHMETIC` | **Major** — recompute for the *declared primary* estimate; `EVALUE_NON_PRIMARY` is an advisory flag (check which estimate the E-value bounds) |
| `PROMISED_ABSENT`, `DISK_UNREPORTED`, `PROMISED_STAT_NO_VALUE` | **Major** |
| `SUPP_INTERNAL_LABEL`, `SUPP_PLACEHOLDER`, `SUPP_BUILD_MARKER`, `SUPP_RESPONSE_FRAMING`, `SUPP_PLANNING_RESIDUE`, `SUPP_XREF_UNRESOLVED` | **Major** — a slip in a supplement is as fatal at a technical check as one in the body |
| `CITATION_ORDER` | **Major**; `CITATION_GAP` **Minor** |
| `CONFIRM_NULL_NO_MDE` | **Major** |
| `ESTIMAND_DRIFT`, `PRIMARY_DISCLOSURE_NOTE` | **Advisory Minor — never a blocker.** The provenance match is fuzzy (token overlap); confirm against the actual registration first. `PRIMARY_DISCLOSURE_NOTE` flags an honest disclosure the guidance recommends — do not penalise it. |

With `--evalues` (schema `references/evalues_schema.md`), each declared E-value is recomputed from
its declared RR and CI (VanderWeele–Ding; the CI E-value from the limit nearest 1) over the printed
precision of every number: `EVALUE_DECLARED_MISMATCH` is **Major**, `EVALUE_DECLARED_NOT_IN_TEXT`
Minor; an OR/HR must be converted to an RR or declared `other:` (Minor, not recomputed).
Known limits: in prose-only mode the E-value check splits sentences at every '.', so the decimal in
"HR 1.52" can cut the estimate out of its window (`EVALUE_UNVERIFIABLE`); "E-value = 3.10",
"(E-value 3.10)" and the plural are not read, and a CI-limit E-value is not recognised (open
finding SR-02 without `--evalues`). Check by hand, or declare them.

**Checks no script makes** (prose judgement):

1. **Primary-change guard** — two models for one contrast, one significant and one null, the
   significant one foregrounded: confirm which was pre-specified.
2. **Headline vs own-sensitivity direction** — a headline claim pointing the opposite way from the
   authors' own sensitivity estimate means the paper contradicts its own robustness check (Major).
3. **Figure-embedded numbers are grep-blind** — every numeric audit above misses numbers *inside* a
   rasterised figure. Read each figure page visually before submission.

Re-run `/sync-submission`'s `check_cross_artifact_stale.py` **after** any reframe, not just once at
the start. For time-to-event manuscripts, apply probe **S8 (estimand provenance)** of
`references/domain-probes/survival_prognostic.md`. Read `references/phases/phase2_5f_claim_artifact.md`
when a gate above fired and you need the rationale and resolution path, or there is a
pre-registration to reconcile.

### Phase 2.5g: Editorial-Impression / Defensiveness Scan (the ceiling pass)

Run this **after** the floor gates (Phases 2.5–2.5f): it reads the accurate manuscript and recommends
what to take back out. It is advisory and **non-blocking** — it never produces a Major and never
gates submission.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_editorial_impression.py" \
  --manuscript manuscript.md --out qc/editorial_impression.json
```

It exits 0 even under `--strict` and emits up to six verdicts, each tagged with a SUBTRACTION
`action`:

| Verdict | Reads as | Action |
|---|---|---|
| `HEDGE_DENSITY` | defensive-caveat tokens per 1,000 narrative words over threshold | TIGHTEN |
| `HEDGE_REPEAT` | one caveat motif repeated across body + Abstract | TIGHTEN |
| `AUDIT_IN_BODY` | SHA / commit / unit-test / post-lock / manifest / seed in the narrative | MOVE (→ Methods/supplement) |
| `LIMITATIONS_VOLUME` | a long enumerated Limitations list | TIGHTEN (consolidate) |
| `ABSTRACT_CAVEAT_LOAD` | several caveat clauses in the Abstract | TIGHTEN |
| `BURIED_DEFENSE` | strong numeric robustness result only in Limitations/supplement | MOVE (→ Results) |

Each finding becomes a Minor `issues[]` entry with `category: "L"`, `category_name: "Editorial
impression"`, `issue_type: "editorial_impression"`, `subtype: <verdict>`, and `action: "REMOVE" |
"MOVE" | "TIGHTEN"`, reported in the Phase 3 "Editorial-Impression Risks" block. Mark them
`fixable_by_ai: false` — tightening a hedge or moving a result is the author's voice-and-judgment
edit — except a clearly redundant `HEDGE_REPEAT`, which `--fix` may collapse to one statement.

When an earlier phase recommends adding a caveat or disclosure, weigh it against L: an
integrity-critical disclosure is a must, stated once and crisply; a defensive over-disclosure is a
cut or move. Place it once and point to the supplement rather than repeating it at every claim site.

### Phase 2.5h: Baseline Drift (anchor to the last human-approved version)

Run after the ceiling pass and **before** the loop controller (Phase 2.5i). Each refine pass takes
the previous AI output as its baseline, so framing bias compounds unseen; this gate compares the
manuscript against the **last human-approved version** (the frozen `v_N` circulated to senior
authors/co-authors — **not** the last AI output). With no baseline (a first draft), skip it.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_baseline_drift.py" \
  --manuscript manuscript.md --baseline "$BASELINE_MD" \
  --out qc/baseline_drift.json
```

| Verdict | Signal (baseline → current) | Fold into report as |
|---|---|---|
| `STRENGTH_INFLATION` | certainty markers up while hedges fall | Minor — tone back to the approved strength |
| `SIGNIFICANCE_INFLATION_DRIFT` | novel/pivotal/unprecedented tokens added | Minor — remove the inflation |
| `SCOPE_INFLATION_DRIFT` | new generalization phrases ("in clinical practice") | Minor — the estimand did not widen; re-scope |
| `HEDGE_ACCRETION` | hedge/caveat density up | Minor — cumulative over-hardening; TIGHTEN |

Every finding is **Minor and advisory**; the gate never blocks. Treat drift as a prompt to review
against the approved anchor, not an instruction to revert — new analysis can justify a stronger
claim, but the author should confirm it. `qc/baseline_drift.json` feeds the loop controller, so a
drifted draft does not read as a zero-edit PASS.

### Phase 2.5i: Refinement Terminal-State (the loop controller)

Run this **last**, after the floor gates and the ceiling pass: it reads their `qc/*.json` artifacts
and classifies whether the review → revise → review loop is done, so an accurate manuscript is not
over-hardened by a pass it does not need. It is advisory and **never blocks**; do not treat it as a
second gate on the floor detectors, which already fail under `--strict` on their own Majors.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/refinement_stop.py" \
  --qc-dir qc --out qc/refinement_stop.json
```

| Verdict | Meaning | What the harness must do |
|---|---|---|
| `CONTINUE` | a floor gate still reports a Major | genuine work remains — keep going |
| `STOP_OVERHARDENING` | floor clean, ceiling flags accumulation | STOP adding; only optional SUBTRACTION (REMOVE/MOVE/TIGHTEN) remains — do **not** run another additive pass |
| `STOP_MINOR_OPTIONAL` | floor clean, only optional Minor polish left | stop the required-work loop; present the Minor items as an optional menu, do not loop for them |
| `STOP_ZERO_EDIT` | floor at fixed point, ceiling clean | the manuscript is submission-ready as-is — **NO EDITS REQUIRED. Do not manufacture changes.** Report the zero-edit PASS as a first-class outcome |
| `INDETERMINATE` | no gate artifacts yet, no floor gate parsed (e.g. only the ceiling ran), or an empty / invalid `qc/*.json` (a gate that crashed under `--json > file`) | run, or re-run, the floor + ceiling gates first |

Known limits: a detector-keyed artifact whose findings are not under `claims` / `findings`
(for example `/verify-refs`' `qc/reference_audit.json`) is listed as *Unparsed* with a WARNING but
does not by itself block a `STOP_*`; read its own verdict before acting on the stop signal.

Once the verdict is any `STOP_*`, stop the additive cycle: surface the terminal state in the Phase 3
report and do not re-run self-review to find "one more thing". A zero-edit or minor-optional result
is a legitimate outcome, not a failure to try harder.

### Phase 2.5j: Refinement Regression (fixed vs broke, across runs)

Run each round, after the loop controller. A revision that resolves finding X can introduce finding
Y, and the pass-rate hides it; this step reads a run-history ledger (one line per run, the
`verdict@where` fingerprints of its findings) and reports what the revision *fixed* vs what it
*broke*.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/refinement_regression.py" \
  --qc-dir qc --ledger qc/refinement_ledger.jsonl --append \
  --out qc/refinement_regression.json
```

Use `--append` on a real run so the current findings become the next entry; omit it to classify
without recording.

| Verdict | Meaning | What the harness must do |
|---|---|---|
| `PROGRESSING` | findings resolved, none new | continue |
| `REGRESSION` | the revision introduced new finding(s) | review the new findings before accepting the fix — the pass-rate went up but something broke |
| `CHURNING` | a resolved finding reappeared (Mirror Loop) | **stop revising and re-anchor** — more passes re-derive, they do not converge |
| `CONVERGED` | nothing new, nothing carried | the loop is done |
| `INDETERMINATE` | first run, no prior entry | re-run after a revision |

It is advisory and **never blocks**. Report both axes in Phase 3: a revision is an improvement only
if it resolved findings **and** the `new`/`churn` columns are empty.

### Phase 2.6: Multi-Agent Panel Review (--panel, opt-in)

Run this phase **only when `--panel` is passed**, after the numerical audits (Phases 2.5–2.5d) so the
reviewers see source-verified numbers, and before the Phase 3 report, which it feeds. Two things bind
before you spawn anything: the **SSOT must be singular** (the Phase 1 step 4 gate — halt and ask if
more than one manuscript-like `.md` is unpinned), and the roster must not be a **substrate
monoculture** (a panel sharing the drafter's model inherits its blind spots; route at least one lens
to Codex or a human co-author). `check_panel_diversity.py --strict` enforces the second, and fires
`PANEL_UNDERRETURN` when fewer reviewers returned than were spawned — a panel with <2 returned reviews
is a failed run, not a thin one.

Read `${CLAUDE_SKILL_DIR}/references/phases/phase2_6_panel.md` when `--panel` is passed — it has the
reviewer-set table, roster manifest, editor synthesis and lens-diversity gate.

### Phase 3: Report

Before writing the comments, skim `references/exemplar_findings/` for the finding at hand
(cohort-arithmetic mismatch, unadjusted confounder, cross-sectional scope overreach, post-hoc
primary / estimand drift). Each models the full shape — gate fired, the comment in a reviewer's
words, Fatal/Fixable, category letter, fix, `fixable_by_ai`, R0-ready line. Match the structure, not
the wording; they are synthetic.

Write the report to `qc/self_review.md` with this structure:

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

## Editorial-Impression Risks (REMOVE / MOVE / TIGHTEN)

*The subtraction axis — what to take out, move, or tighten so the accurate manuscript reads
confidently. Advisory and non-blocking; from Phase 2.5g / category L. Omit this block only if the
scan returned nothing.*

L1. **{Issue}** [{REMOVE | MOVE | TIGHTEN}]: {1 sentence — what reads as over-defensive and where, with the subtraction to make}
L2. ...

## Strengths (emphasize in cover letter)

- {Specific strength 1}
- {Specific strength 2}
- ...
```

Keep the ADD / FIX axis (Major / Minor Comments) and the SUBTRACTION axis (Editorial-Impression
Risks) visually separate; never fold L items into the Minor Comments.

In suggested fixes and in any text drafted in Phase 4:
- **References** only from `/search-lit` with a confirmed DOI or PMID; mark any other reference `[UNVERIFIED - NEEDS MANUAL CHECK]` (Phase 2.5c blocks a `FABRICATED` one).
- **Clinical definitions, diagnostic criteria and guideline recommendations** you cannot verify: flag with `[VERIFY]` and ask the user; never invent them.

**Conciseness targets**:
- Anticipated Major Comments: 3-7 items, each 3-5 lines
- Anticipated Minor Comments: 3-6 items, each 1-2 sentences
- Editorial-Impression Risks: 0-6 items, each 1 sentence (only what the Phase 2.5g gate flagged)
- Strengths: 3-5 items, each 1 sentence
- Total report: 400-800 words (excluding optional R0 section)

### Phase 3b: R0 Numbering (Optional)

If the user plans to use `/revise` once real reviews arrive, offer to append R0-numbered output so
they can later tell anticipated (R0) from novel (R1-only) comments:

```markdown
## R0 Pre-Submission Findings (for /revise cross-reference)

R0-1 [MAJ] {mapped from M1}: {issue title}
R0-2 [MAJ] {mapped from M2}: {issue title}
R0-3 [MIN] {mapped from m1}: {issue title}
...
```

### Phase 3c: Structured JSON Output (--json)

Emit machine-readable JSON **only when `--json` is passed** (or another skill consumes this run):
append the block to the report and also write it to `qc/self_review.json`. Read
`${CLAUDE_SKILL_DIR}/references/phases/phase3c_json_output.md` for the schema, field semantics and
worked example when --json was passed, or a downstream skill consumes this run.

### Phase 4: Fix Support (on request)

The review ends at Phase 3. Read `${CLAUDE_SKILL_DIR}/references/phases/phase4_fix_support.md` when
`--fix` was passed or the user asks you to apply or draft fixes for the findings.
