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

## Two Objectives: the Floor and the Ceiling

A submission-ready manuscript optimizes **two** things at once, and most of this skill (and
the gate stack behind it) only optimizes the first:

- **Floor — minimize rejection-for-cause.** Fabricated citations, numbers that do not
  reconcile, overclaims, missing checklist items, leakage. Categories A–K and the
  deterministic gates (Phases 2.5–2.5f) do this, and they are right to. Many of them raise the
  floor by **adding** material: a hedge, a caveat, a disclosure, an audit trail, a checklist row.
- **Ceiling — maximize editorial-championing.** Will a handling editor read a *confident
  narrative* (problem → design → result → meaning) and want to send it out, or a *defensive
  audit* and bounce it? Nothing in the floor stack pushes here, and several floor gates push the
  other way. Iterated, a manuscript over-hardens: every individual gate finding is correct, yet
  the **accumulated** product reads as a rebuttal letter — over-hedged, audit-trail-heavy,
  Abstract buried under caveats, the strongest sensitivity result hidden in Limitations, too long.

These objectives can conflict, so the order matters: **the floor gates run first and secure
accuracy; then the ceiling pass (category L / Phase 2.5g) reads the accurate manuscript as a
whole and recommends SUBTRACTION — REMOVE, MOVE, or TIGHTEN — so the same content is read
confidently.** The ceiling pass is advisory and never blocks; it cannot relax a floor gate.
Without it, repeated self-review monotonically over-defends. Surface the ceiling findings as
their own first-class output (Phase 3), not folded silently into the "add this" comments.

## Workflow

### Phase 1: Intake

1. Get the manuscript -- PDF, Word doc, or pasted text.
2. Ask the user:
   - Target journal? (affects reporting standards and scope expectations)
   - Manuscript type? (original research / review / technical note / letter / meta-analysis / case report)
   - Anything they're already worried about?
   - **Review depth?** The default is a single-pass review. For a high-stakes pre-submission final pass, a multi-agent **panel** (`--panel`, Phase 2.6) is available — several domain-expert reviewers run independently, then an editor consolidates them (more thorough, but it spawns several agents so it costs several times more tokens). On an interactive run, surface this option **once** in one line and offer it; then proceed with the single-pass review unless the user opts in. Do **not** surface or auto-apply the panel when invoked with `--json` or from `/write-paper` — those stay single-pass.
3. Read the full manuscript.
4. **SSOT gate — confirm there is one manuscript, not several.** Self-review reads a single
   input file, so a divergence between a legacy working copy and the live submission copy is
   structurally invisible to it. Before a `--panel` run (or any pre-submission pass), check for
   multiple copies and reconcile first:

   ```bash
   find . \( -path '*manuscript*' -o -path '*main_document*' \) -name '*.md' | grep -v node_modules
   ```

   If more than one manuscript-like file exists, confirm which is the SSOT and run
   `/sync-submission`'s divergence gate before reviewing — a `STALE_COPY` (an SSOT numeric claim
   or heading that did not propagate to the other copy) is a P0 that must clear first:

   ```bash
   python3 "${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}/skills/sync-submission/scripts/detect_copy_divergence.py" \
     --ssot <ssot>.md --copy <other-copy>.md
   ```

   Review the SSOT copy; do not review a stale copy and pass it.

   **In `--panel` mode this is a blocking precondition, not advice.** A panel spawns N reviewer
   agents + an editor, so reviewing a stale copy wastes the whole pass (a prior panel's top
   finding was literally "you reviewed the wrong file"). If the `find` above returns **more than
   one** manuscript-like `.md` and the SSOT is not pinned — no `SSOT.yaml` with `truth.manuscript_md`
   and no explicit `--ssot <path>` argument — **STOP before spawning any reviewer** and have the
   user name the SSOT (and clear any `STALE_COPY`). Do not auto-pick the longest/newest file. The
   single-pass review may proceed on the one file it was given, but the panel must not.

### Phase 2: Systematic Check

Run the manuscript through each applicable category below. For each item, assess whether
a reviewer would raise it as a Major or Minor comment. Use the Research-Type Adaptation
table (below) to determine which categories apply fully, partially, or not at all.

**The categories (A–L).** The per-item check tables — what to look for under each — live
in `references/phases/phase2_systematic_check.md`; read it once you have the manuscript
and know its type, and work the categories the adaptation table marks as applicable.

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

**Run the deterministic gates.** These are greps and counts, so they belong in a gate rather
than in eyeballing. Run them at Phase 2 entry, on every path:

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

# L. editorial impression (advisory; exits 0 even under --strict)
python3 "${CLAUDE_SKILL_DIR}/scripts/check_editorial_impression.py" \
  --manuscript manuscript.md --out qc/editorial_impression.json
```

Verdict mapping: `CROSS_SECTIONAL_PROGNOSTIC`, `SURROGATE_CARE_DIRECTIVE`, `SECTION_SYMBOL`,
`INBODY_AI_DISCLOSURE`, and any reviewer-team hit (exit 1) are Anticipated **Major** Comments.
`CROSS_SECTIONAL_YIELD_LANGUAGE`, `ELIGIBILITY_PROSE`, `DECIMAL_INCONSISTENCY`,
`EM_DASH_OVERUSE`, and every `check_editorial_impression` verdict are **Minor**. The
per-verdict rationale and the resolution paths are in the reference file.

**Read on demand:**


**Then check that every analysis you report was ever defined.** Twenty-four detectors in this skill ask whether a number is *correct*. None asks whether the analysis that produced it was *defined* — and that is the gap a reviewer walks straight into:

> "The outcome (dependent variable) for the multivariable Cox model is not specified." … "The ground truth (reference standard) against which discrimination and calibration were assessed is not defined." … "This section is largely incomprehensible in its current form."

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_analysis_definitions.py" \
  --manuscript manuscript.md --out qc/analysis_definitions.json --strict
```

`MODEL_OUTCOME_UNDEFINED` (a Cox / Fine–Gray / logistic model with no outcome named), `MODEL_NOT_IN_METHODS`, and `REFERENCE_STANDARD_UNDEFINED` (discrimination or calibration with nothing to score against) are Anticipated **Major** Comments. `TIER_LABEL_UNDEFINED` is Minor.

`ANALYSIS_LOAD` is **informational and never a verdict.** The reviewer who wrote *"too many analyses have been performed and reported"* also named the mechanism — *"this appears to have contributed to omissions of critical information in the Materials and Methods section"* — while a second reviewer of the same manuscript listed its sensitivity analyses as a **strength**. **Load is the cause, not the crime.** Do not cut analyses to satisfy this gate; restore the definitions the analyses crowded out. If load is genuinely high, move the defensive analyses to the supplement — same defence, far less reader burden and far less attack surface.

| File | Read it when | Cost if read blindly |
|---|---|---|
| `references/phases/phase2_systematic_check.md` | you are working the A–L manual pass and know the manuscript type | ~5,600 tokens — and a run that halts at Phase 1, or a panel-mode review, never reaches it |
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
| L. Editorial impression | Full | Full | Full | Full | Full | Full |

*Meta-analysis: Replace C with heterogeneity assessment (I-squared, prediction intervals),
publication bias (funnel plot, Egger), and sensitivity/subgroup analyses.

**Type-Specific Additional Checks:**

- **Observational studies**: Confounding assessment (DAG or adjustment strategy), selection bias, exposure measurement validity. Run **Phase 2.5e (Confounding Completeness)** and apply the O1–O18 probes in `references/domain-probes/observational_confounding.md` — including O7 (over-adjustment: do not adjust for a consequence/mediator of the outcome, e.g. serum uric acid in an eGFR model — the opposite-direction failure to O1), O8 (analysis unit & clustering — run `check_cohort_arithmetic.py --id-col` for records-vs-subjects), O9 (construct validity of a report-/registry-derived outcome), O10 (an inferential effect-size gradient across overlapping/nested subsets needs a difference/interaction test, not descriptive refinement alone), and — for complex-survey data (NHANES/KNHANES/CHNS) — O11 (design-based weighting: the right weight + strata + PSU, subpopulation-not-subset) and O12 (data-driven inflection-point/'saturation' threshold mining needs a breakpoint CI + pre-specification, not a quoted cutoff), O13 (a cross-sectional mediation claim cannot establish X→M→Y order and needs an unmeasured-M–Y-confounding sensitivity), and O14 (a synergy/joint-effect/effect-modification claim needs the additive scale — RERI/AP/S with CIs — not a multiplicative-only interaction or joint-category ORs), O15 (an analytic cohort selected on an optional modality/procedure's availability is a spectrum/selection bias, not a generalizability caveat — ask for consecutive enrollment + a selected-vs-source comparison), and O16 (a serial-imaging size/growth endpoint needs a stated lesion-tracking rule + multiplicity prevalence + a solitary-lesion sensitivity), O17 (a many-exposure agnostic scan — ExWAS/EWAS/MWAS — needs multiplicity control against the true denominator + independent replication, not a raw p<0.05 top hit), and O18 (a multi-rater agreement / reader test run on pooled pairwise distances rather than independent subjects is pseudoreplication — re-run per-subject). If the manuscript develops or compares a **clinical prediction model** (TRIPOD / TRIPOD+AI, nested predictor-set comparison), also apply the CP1–CP4 probes in `references/domain-probes/clinical_prediction_model.md` (apparent-vs-optimism-corrected calibration/DCA, the incremental-value-vs-marginal-effect two-null distinction, EPV per nested model, net benefit as model comparison not policy).
- **Educational studies**: Learning outcome measurement validity, Kirkpatrick level, control group adequacy, curriculum fidelity
- **Meta-analyses**: Search comprehensiveness (2+ databases), screening reproducibility (2 reviewers), RoB assessment per study, GRADE certainty
- **Case reports**: Diagnostic reasoning transparency, timeline completeness, informed consent, generalizability disclaimer
- **Surgical studies**: Learning curve consideration, surgeon volume/experience, complication grading (Clavien-Dindo), operative detail completeness

**Domain probe modules (load when the manuscript type matches):**

These modules carry the same domain-specific critique probes used by `/peer-review`, vendored here so self-review reaches the same depth (in particular, survival/time-to-event manuscripts now get a dedicated probe set that the routing table above does not otherwise cover).

| Manuscript type / signal | Probe module |
|---|---|
| Systematic Review / Meta-Analysis | `references/domain-probes/sr_ma.md` (P0–P19) |
| Time-to-event / survival / prognostic model (Cox, Fine-Gray, DeepSurv, nomogram, risk-stratification cutoff) | `references/domain-probes/survival_prognostic.md` (S1–S9) |
| Radiomic feature reproducibility / acquisition-parameter sweep / reliability-based feature filtering | `references/domain-probes/radiomics.md` (R1–R4) |
| Cross-modality image synthesis (MRI→PET / MRI→CT / non-contrast→contrast / low-dose→full-dose) claiming functional/molecular information or target-modality substitution | `references/domain-probes/image_synthesis.md` (IS1–IS4) |
| Narrative / review article / primer / state-of-the-art | `references/domain-probes/narrative_review.md` (RV1–RV9) |
| AI/ML primary study with a clinical claim (generalizable / outperforms clinicians / deployment-ready / can replace a reader) | `references/domain-probes/ai_overclaiming.md` (AO0–AO7) |
| Engineer-built medical-imaging model (segmentation / classification / detection; CNN / U-Net / nnU-Net / transformer) being validated — partition/leakage, seed & run variance, metric selection, reproducibility, reference-standard quality | `references/domain-probes/model_development.md` (MD0–MD8) |
| LLM / MLLM evaluated on a clinical task (radiology report generation, visual question answering, clinical text extraction/classification; closed API or open weights) | `references/domain-probes/mllm_evaluation.md` (ME0–ME8) |
| Randomised controlled trial (parallel / crossover / cluster / stepped-wedge) | `references/domain-probes/rct_trial.md` (RC0–RC7) |
| Diagnostic test accuracy (DTA) primary study / multi-reader multi-case (MRMC) reader study (index test vs reference standard, AI-vs-reader, modality comparison) | `references/domain-probes/diagnostic_accuracy.md` (D1–D11) |
| Case report / case series / single-patient clinical narrative (incl. adverse-event/pharmacovigilance and imaging-led radiology/nuclear-medicine/IR reports) | `references/domain-probes/case_report.md` (CR1–CR9) |
| AI/ML, prediction, or diagnostic study claiming cross-population performance (generalizable / deployment-ready / "works for patients"), or presenting subgroup analyses as a fairness/equity argument | `references/domain-probes/equity_fairness.md` (EQ0–EQ6) |
| Mendelian randomization (genetic variants as instrumental variables: two-sample summary-data, one-sample, multivariable MR, drug-target / cis-MR, non-linear MR) | `references/domain-probes/mendelian_randomization.md` (MR1–MR8) |
| Polygenic risk score / polygenic score (PRS / PGS) developed, validated, or applied as a predictor or risk-stratifier | `references/domain-probes/polygenic_risk_score.md` (PG1–PG8) |
| Network meta-analysis (≥3 interventions via direct + indirect evidence, treatment ranking, incl. component NMA) | `references/domain-probes/network_meta_analysis.md` (NM1–NM8) |
| Health economic evaluation (cost-effectiveness / cost-utility / cost-benefit / budget-impact; trial-based or decision-model-based — decision tree, Markov, DES) | `references/domain-probes/health_economic_evaluation.md` (HE1–HE8) |
| Observational study using routinely-collected health data (administrative claims / EHR / disease or population registry / health-checkup DB, linked or not) | `references/domain-probes/record_routinely_collected_data.md` (RD1–RD8) |
| Self-report survey / questionnaire study (KAP, physician/patient survey, cross-sectional questionnaire, web/e-survey) | `references/domain-probes/survey_research.md` (SV1–SV8) |
| Scoping review (maps the breadth/nature of evidence, clarifies concepts, identifies gaps; PCC framing, charting, optional appraisal — not a focused effectiveness/accuracy question) | `references/domain-probes/scoping_review.md` (SC1–SC8) |
| Qualitative study (interviews, focus groups, ethnography, grounded theory, phenomenology, document analysis; reflexivity, trustworthiness, thematic analysis — not quantitative validity) | `references/domain-probes/qualitative_research.md` (QL1–QL8) |
| **Self-improving / self-evaluating system** (an agent that critiques and rewrites its own output; training on model-generated data; an LLM used as the judge that scores the training signal; "self-evolving" clinical agents) | `references/domain-probes/self_improving_system.md` (SI1–SI7) + `skills/peer-review/scripts/check_self_improvement_claims.py` |

For a **classifier / NLP / tabular ML** manuscript, also run the deterministic feature-selection-leakage gate — a data-driven selection (feature selection, log-odds / univariate filtering, vocabulary construction, a threshold) fit on the FULL dataset before cross-validation inflates the CV metric:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_cv_leakage.py" \
  --manuscript manuscript.md --out qc/cv_leakage.json
```

`CV_SELECTION_LEAKAGE` (Major) fires when a selection token co-occurs with cross-validation and no fold-nesting is disclosed ("within each fold" / "nested CV" suppresses it). This is distinct from patient-vs-image split leakage (`model-validation/check_split_leakage.py`).

When the manuscript matches a row, read `${CLAUDE_SKILL_DIR}/references/domain-probes/<module>.md` and apply each probe as an additional source of Anticipated Major / Minor Comments. The module severity words (MAJOR / MINOR) map to this skill's framing as follows: a conclusion-threatening or design-level finding becomes a **Fatal** Anticipated Major Comment, a reporting-level finding becomes a **Fixable** Anticipated Minor Comment, and each is tagged with the closest category letter (A–K). These probes **complement** categories A–K above; they do not replace them. (The modules are vendored byte-identical from `/peer-review`; do not edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`.)

### Phase 2.5: Numerical Cross-Verification (Internal)

Before generating the report, verify internal consistency:

1. **Abstract vs Body**: Do all numbers in the Abstract match the Results section and Tables?
2. **Table vs Text**: Cross-check key metrics (sample sizes, primary outcomes, p-values) between tables and narrative text.
3. **Figure vs Text**: Do figure legends match the data described in Results?
4. **Percentage arithmetic**: Verify that n/N percentages are calculated correctly (e.g., 23/150 = 15.3%, not 15.0%).
5. **CI plausibility**: Do confidence intervals seem reasonable given sample sizes?
6. **Rate back-calculation**: every reported rate must invert to its own numerator/denominator — an incidence rate ≈ events / person-years × scale (±rounding). A rate that does not recompute from the stated events and person-time (or that implies more events than the cohort can supply) is a Major, not a Minor.
7. **Exclusion-cascade and complete-case arithmetic** (cohort/observational): the STROBE flow must balance — start N − Σ(exclusions) == final analytic N — and any complete-case statement must balance — total − missing == complete. A footnote N that does not equal the subtraction is a Major.

For cohort/observational manuscripts, run the deterministic gate instead of eyeballing it (it parses prose equations + GFM tables, and recomputes from a committed CSV when given one):

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_cohort_arithmetic.py" \
  --manuscript manuscript.md --data analysis/cohort.csv --id-col mockid \
  --out qc/cohort_arithmetic.json --strict
```

`RATE_BACKCALC` / `CASCADE_SUM` / `PARTITION_OVERLAP` rows are Anticipated Major Comments (category: A. Study Design & Data Integrity); the partition check is the Phase 2.5b cohort branch below. Pass `--id-col` (or let it auto-detect a subject-ID column) on health-screening / EMR / registry data so the gate also runs the **analysis-unit** check: when `records > unique subjects` and the manuscript states neither the analysis unit nor a one-record-per-subject sensitivity, it emits `ANALYSIS_UNIT_UNDISCLOSED` (Major — non-independent observations give anti-conservative CIs; probe O8). Flag any remaining internal-consistency discrepancies as Anticipated Minor Comments (category: F. Reporting Completeness).

**Then recompute the three things a reviewer recomputes by hand.** These are the arithmetic checks a
careful reviewer does with a calculator on the train home, and the ones that end a submission when
they fail:

```bash
# Every "n (%)" in a table, recomputed against its own denominator.
python3 "${CLAUDE_SKILL_DIR}/scripts/check_table_percentages.py" \
  --manuscript manuscript.md --out qc/table_percentages.json --strict

# Every reported P beside a 2×2 (or r×c) count, recomputed from the counts themselves.
python3 "${CLAUDE_SKILL_DIR}/scripts/check_reported_p_from_counts.py" \
  --manuscript manuscript.md --out qc/reported_p.json --strict

# Diagnostic-accuracy only: sensitivity/specificity against the reference-standard denominators.
python3 "${CLAUDE_SKILL_DIR}/scripts/check_dta_denominators.py" \
  --manuscript manuscript.md --out qc/dta_denominators.json --strict
```

`PCT_MISMATCH`, `P_MISMATCH` / `P_IMPOSSIBLE`, and `DENOM_MISMATCH` are **P0 Major** — a percentage
that does not follow from its own denominator, or a P value that does not follow from its own counts,
is not a rounding disagreement. It means one of the two numbers is wrong, and the reviewer who checks
will find it. Run the first two on **every** manuscript with a table; the third only on
diagnostic-accuracy work.

### Phase 2.5a: Numerical Source-Fidelity Audit (External)

Internal consistency (Phase 2.5) is necessary but not sufficient. Numbers can be fully
self-consistent across Abstract / Table / Text and still be wrong **at the source** — a single
transcription error propagates cleanly through every downstream stage, and every internal check
then confirms it. Only a traversal back to the primary source catches it.

Run the **displayed-arithmetic** gate first — a stated difference must equal the subtraction of
its two displayed component values at the *same* precision:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_rounded_delta.py" \
  --manuscript manuscript.md --out qc/rounded_delta.json
```

`ROUNDED_DELTA_MISMATCH` (Minor) fires when AUCs shown as `0.70` and `0.73` (a displayed gap of
0.03) are reported with a between-arm difference of `0.02` — self-consistent only on the
unrounded values. A higher-precision component pair (`0.703` vs `0.726`) with a 2-dp delta is
the legitimate unrounded case and is not flagged.

**When to run the external audit:** MA revisions, submissions, or any review where the user says
"check against the source", "verify extraction", or "random sample". Skip otherwise.

**The audit, in one line:** draw a stratified sample of 5 numerical claims — always including one
comparative-arm value and one revision-introduced number, the two highest-yield strata — and
trace each through three layers (manuscript → extraction CSV → primary-source page; plus analysis
script → CSV where a script produced it). **Any mismatch is a Major Comment**, and one that
reverses a direction or crosses a significance boundary is a P0 blocker. Every `[VERIFY-CSV]` tag
is a mandatory audit item regardless of sample size.

The traversal procedure, the recording table, the sampling strata, and the four prose-judgement
rules it also applies — hand-entered analysis-script inputs, prose↔table **statistic-type**
mismatches (a median in the text against a mean in Table 1), stale derived CSVs after a
model/adjustment-set change (the analytic `n` is the fastest tell, and the conflict can flip
significance), and the precedent direction-reversal that internal consistency could not see —
are in the reference file.

**Read on demand:**

| File | Read it when | Cost if read blindly |
|---|---|---|
| `references/phases/phase2_5a_source_fidelity.md` | you are running the external audit — tracing sampled claims back to primary sources | ~2,500 tokens; a first-draft review with no extraction CSV and no primary sources cannot use any of it |
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

**`POWER_MODEL_MISSPEC` — the power/MDE simulation's adjustment set must match the primary model.**
For cohort "negative findings," the whole conclusion leans on the MDE ("the literature effect of
1.2–1.5 cannot be excluded"), so the MDE must be computed under the **same covariate set as the
primary analysis**. When a committed power/MDE script exists, read its model formula: if it fits
`y ~ exposure + age` (2 covariates) while the primary model adjusts for 6, it **overstates power**
(omitted covariates inflate the apparent precision) — the MDE is too small and the negative claim
too strong. Re-running a parametric bootstrap under the full model is the fix (in one worked case
MDE moved from a 2-covariate "OR 1.67" to a full-model "OR ≈ 1.70"). A power/MDE whose script omits
primary-model covariates → Major (P0 when the MDE is a headline). This is `requires_reanalysis`
(re-simulate, not a prose edit). **`POWER_VALUE_INTERPOLATED`** — any `interpolat`/`approx`/`interp`
token in a power/MDE CSV's provenance column means the headline value was never simulated on the
grid; treat a non-reproducible headline power/MDE as Major.

### Phase 2.5b: Screening-Count Reconciliation from ID Sets (SR/MA + observational tier/stratum)

Internal consistency across Abstract/Methods/Results (Phase 2.5) and source fidelity of 2×2 and
effect-size numbers (Phase 2.5a) do **not** cover study-count arithmetic. That is a separate
failure mode: a prior-draft prose total ("30 → 32 after FLAG consensus") survives every
downstream pass because Abstract, Methods, Results, Discussion, the Figure 1 caption, and even
the supplementary consensus file all cite the same wrong number back to each other. The only
thing that catches it is a recount from the **ID sets**.

**When to run:** any SR/MA manuscript revision, regardless of stage (run before Phase 3); or any
observational manuscript presenting an ordinal tier / mutually-exclusive stratum split. Skip
otherwise.

**A. SR/MA — recount from the ID sets.** Enumerate A (INCLUDE in the screening TSV), B (Exclude
in the consensus sheet), C (Include-qualitative), T (studies in Table 1), then derive
`k_qualitative = |A \ B| + |C|`, `k_bivariate = |T|`, and `k_narrative-only = |(A ∪ C) \ B \ T|`.
**List the narrative-only IDs explicitly** — the highest-yield cross-check, and the one that
turns "10 narrative-only studies" into "2 (IDs 120, 474)". Compare every derived total against
the prose claim in Abstract, Methods, Results, the Figure 1 caption, and Limitations; any
mismatch is a **P0 Major, blocking submission**. Any `N → M` transition claim not backed by an
enumerable ID addition/subtraction set is itself a **Major** — it is unverifiable by downstream
audit. The full procedure and the reconciliation-block template are in the reference file.

**B. Observational tier/stratum — the same set logic, as arithmetic.** A partition claimed to be
disjoint must satisfy `Σ(stratum N) == unique total` and `Σ(stratum events) == total events`.
Denominators summing *above* the unique cohort double-count subjects; a table where every
stratum n equals the grand total is a mis-entry, not a partition. Confirm the reference
(baseline) row of any stratified hazard/odds table is present and labelled — without it the
other strata are uninterpretable.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_cohort_arithmetic.py" \
  --manuscript manuscript.md --data analysis/strata.csv --strict
```

**C. Cross-script cut-point consistency — the root cause of stratum-N drift.** When the same
cohort is re-stratified in more than one analysis script, the derived categorical must use one
identical cut definition (same breaks, same `right=` closure, same labels). Two scripts binning
one variable differently drift the per-stratum Ns while the grand total still reconciles — so a
manuscript-only check cannot localize it. The same gate covers the composite-indicator sibling
(a derived 0/1 criterion rebuilt in a second script with a clause dropped).

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_binning_consistency.py" \
  --root analysis --root scripts --strict
```

`PARTITION_OVERLAP`, `BINNING_DRIFT`, and `DERIVED_DEF_DRIFT` are all **P0 Major**.

**Read on demand:**

| File | Read it when | Cost if read blindly |
|---|---|---|
| `references/phases/phase2_5b_screening_counts.md` | this is an SR/MA (ID-set recount) or a stratified cohort, and you are doing the recount | ~3,300 tokens — nothing in it applies to a single-cohort manuscript with no strata |
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

4. **Cross-check placeholder + pagination drift.** Run, on every round:

   ```bash
   grep -nE '\[@NEW:|\[N\]|\[N–N\]|e0{3}.{0,5}e0{3}|in[ .]?press|\bTBD\b|forthcoming' manuscript/
   ```

   Two failure classes:
   - **Citation-queue placeholders** (`[@NEW:topic]`, `[N]`, `[N–N]`): a citation slot that was never resolved. Any remaining at self-review is a P0.
   - **Pagination placeholders** (`e000–e000`, `in press`, `TBD`, `forthcoming`): `/verify-refs` (Phase 2.5c step 2) marks these `UNVERIFIED` with `note = "pagination_placeholder"` but cannot judge centrality from the .bib alone. **Here, with the manuscript in hand, decide centrality:** if the unresolved reference supports a method choice or a headline claim (grep the citekey/marker against the Abstract, the Statistical Analysis subsection, and the first Results paragraph), escalate it to a **P0 Major** rather than a generic Minor. A method-load-bearing citation that is still "in press / e000" at submission is a blocker. Include each in the reconciliation block.

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

### Phase 2.5c-2: Reference Adequacy Scan

Phase 2.5c covers reference **integrity** — are the cited references real (fabricated / unverified / duplicate / placeholder)? It does **not** ask whether there are *enough* references, in the right sections, grounding every named method. That is reference **adequacy**, and it is the failure mode behind a draft with thirteen references where the Statistical Analysis subsection names a competing-risk model, multiple imputation, the E-value, and an eGFR equation with zero citations. Keep the two strictly separate: an integrity failure blocks because a citation is *wrong*; an adequacy failure flags because a citation is *missing*.

**When to run:** every manuscript at self-review, after the integrity scan. The two share the manuscript and the resolved bib path.

**Procedure:**

1. **Run the deterministic checker.** Resolve the article type from `project.yaml` (passed verbatim; the script's alias map handles repo paper-type names) and the journal cap from the target journal profile when known:

   ```bash
   python3 "${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}/skills/self-review/scripts/check_reference_adequacy.py" \
     --manuscript manuscript/manuscript.md --bib "$BIB" \
     --article-type "$TYPE" ${CAP:+--journal-cap "$CAP"} \
     --out qc/reference_adequacy.json --strict
   ```

   It reports the cited-reference count vs the article-type target, the section distribution (Introduction / Methods / Results / Discussion), every named method found in the Methods/Statistical-Analysis block, which of them lack a citation in their paragraph, and a `methods_zero_citations` flag.

2. **Fold `findings[]` into the review.** Each finding becomes a standard `issues[]` entry (so `/revise` and downstream consumers ingest adequacy and other comments uniformly), **additively** carrying the machine-readable `issue_type` + `subtype` alongside the usual fields, under `category: "F" / category_name: "Reporting Completeness"`:

   ```json
   {"id":"M2","severity":"major","category":"F","category_name":"Reporting Completeness",
    "issue_type":"reference_adequacy","subtype":"methods_named_method_uncited",
    "location":"Methods - Statistical Analysis",
    "description":"Fine-Gray competing-risk model is named without a canonical citation.",
    "fixable_by_ai":false,
    "suggested_fix":"Run /search-lit for the canonical Fine-Gray competing-risk source, sync via /lit-sync, then rerun /verify-refs --strict."}
   ```

   **Severity:** `methods_zero_citations` (original / AI-validation / meta-analysis) and each uncited statistical method → **Major** (a P0 candidate before submission when the method is central to the primary or a sensitivity analysis); each uncited reporting/diagnostic standard → **Minor**; a total count below the article-type target → **Major** when far below (under half the floor), otherwise **Minor**, scaled also by stage (escalate at a submission/circulation gate).

3. **Fix-forward, not fabricate.** As in Phase 2.5c, this skill never writes replacement references. Every adequacy finding carries `fixable_by_ai: false`; the remedy is `/search-lit` (Manuscript Paper Reference Pool mode) → `/lit-sync` → `/verify-refs --strict`, which the author runs.

### Phase 2.5d: Cross-Reference QC (Manuscript ↔ rendered DOCX)

Reference-list integrity (Phase 2.5c) does **not** cover Table/Figure cross-references. That is a
separate failure mode: an in-text citation ("Supplementary Table S4 reports a sensitivity
analysis") resolves to a *different* caption in the rendered DOCX ("Supp Table S4 = a diagnostics
table") because the build script carries its own legacy SSOT. Internal consistency (Phase 2.5)
cannot see it — the prose and the build artifact each echo their own divergent truth cleanly.

**Markdown stage (always).** Every captioned `Figure N.` / `Table N.` must be cited at least once
elsewhere in the body:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_figure_citation.py" \
  --manuscript manuscript.md --out qc/figure_citation.json
```

`FIGURE_ORPHAN` / `TABLE_ORPHAN` (Minor) catch a newly-added float that has a legend but no
in-text citation — the early, no-build counterpart to `check_xref`'s `UNCITED`.

**DOCX stage (when a rendered DOCX exists** — circulation drafts, post-build pre-submission
checks. Skip on early drafts with no build):

```bash
python3 "${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}/skills/manage-refs/scripts/check_xref.py" \
  --md manuscript/manuscript.md --docx manuscript/manuscript_final.docx \
  --out qc/xref_audit.json [--allow-separate-attachments]
```

Severity depends on the journal's figure/table submission policy. Many radiology and medical
journals (European Radiology, Radiology, AJR) accept figures and tables as **separate
attachments** rather than inline — pass `--allow-separate-attachments` there so a legitimate
attachment style is not read as a blocker.

| Status | Default policy | With `--allow-separate-attachments` |
|---|---|---|
| `MISSING_DOCX` | **Major (P0)** — cited Table/Figure absent from rendered output | **Minor** — separately attached per journal policy |
| `MISSING_BODY` | **Major (P0)** — build SSOT drift; rendered caption has no body definition | **Major (P0)** (no change) |
| `MISMATCH` | **Major (P0)** — caption text disagrees between body and rendered DOCX | **Major (P0)** (no change) |
| `UNCITED` | Minor — orphan caption; cite it or remove it | Minor (no change) |

`MISSING_BODY` and `MISMATCH` stay P0 under every policy: they are SSOT drift, not a style choice.

**Do NOT auto-fix cross-reference defects in `--fix` mode.** Rewriting a caption in the body
without re-running the DOCX build merely moves the mismatch. Emit each P0 row as its own
`M`-numbered Major Comment with `category: "F"` and `fixable_by_ai: false`, and route the user to
`/write-paper` Step 7.6a for the pipeline-side fix.

**Read on demand:**

| File | Read it when | Cost if read blindly |
|---|---|---|
| `references/phases/phase2_5d_xref_qc.md` | the xref gate fired and you are writing up the reconciliation | ~2,400 tokens; an early draft with no DOCX build never reaches this stage |
### Phase 2.5e: Confounding Completeness (observational only)

**When to run:** the manuscript is observational (cohort, case-control, cross-sectional,
health-screening registry) and the central claim is an adjusted exposure–outcome
association. **Skip for RCTs, diagnostic-accuracy, SR/MA, and descriptive studies** — which
is why the full procedure is loaded on demand rather than carried inline.

The highest-yield, most mechanical observational finding — a covariate that is **measured**,
**imbalanced across exposure groups** in Table 1, and **absent from the adjustment set**
(residual confounding by a measured variable) — is invisible to a prose pass and only
exposed by joining the exposure-stratified Table 1 against the Methods adjustment set
(probe O1). Run the deterministic gate and treat each `UNADJUSTED_IMBALANCED` covariate as
an Anticipated Major Comment (category A. Study Design & Data Integrity):

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_confounding_completeness.py" \
  --table1 table1_by_<exposure>.csv \
  --adjusted-list "age, sex, BMI, hypertension, diabetes" \
  --exposure-defining-list "body mass index, waist, fasting glucose, triglycerides, HDL cholesterol" \
  --out qc/confounding_completeness.json --strict
```

When the manuscript is observational, **load `references/phases/confounding_completeness.md`**
for the full procedure: the precedent failure pattern; the `--exposure-defining-list`
over-adjustment exemption for guideline-defined exposures (MASLD / metabolic syndrome / CKM
/ sarcopenia / frailty); the SMD-from-`mean ± SD` fallback; the extended-adjustment
sensitivity model and its frame discipline (refit the unadjusted estimate on the reduced
complete-case frame, not the full frame); and the rest of the observational probe set
(O2–O10) from `references/domain-probes/observational_confounding.md`.

### Phase 2.5f: Claim-vs-Artifact Cross-Check

Phases 2.5–2.5e check numbers and adjustment sets. This phase checks **claims against the
external artifacts they should trace to** — the pre-registration, the protocol, the analysis
outputs. These are the errors that survive a single-pass review because the manuscript prose
is internally consistent yet disagrees with the registration or the analysis it reports: a
primary re-designated after the results were known, an E-value that does not recompute from
the estimate it is quoted against, an analysis promised in Methods that never reaches Results.

**Run the gates** (all deterministic; pass the supplement so the corpus is complete):

```bash
# 1. claims ↔ pre-registration/protocol: estimand provenance + E-value arithmetic
python3 "${CLAUDE_SKILL_DIR}/scripts/check_claim_artifact.py" \
  --manuscript manuscript.md --prereg prereg.md \
  --out qc/claim_artifact.json --strict

# 2. Methods ↔ Results ↔ disk coverage (both directions: promised-absent AND run-but-unreported)
python3 "${CLAUDE_SKILL_DIR}/scripts/check_artifact_coverage.py" \
  --manuscript manuscript.md --supplement supplement.md --analysis-dir output/analysis \
  --out qc/artifact_coverage.json --strict

# 3. reader-facing residue in EVERY rendered artifact, not just the body
python3 "${CLAUDE_SKILL_DIR}/scripts/check_supplement_hygiene.py" \
  --supplement supplement.md --supplement tables.md --supplement captions.md \
  --manuscript manuscript.md --out qc/supplement_hygiene.json --strict

# 4. float citation order — a desk-reject item the hygiene gate does not cover
python3 "${CLAUDE_SKILL_DIR}/scripts/check_citation_order.py" \
  --manuscript manuscript.md --out qc/citation_order.json --strict

# 5. a headline null is uninterpretable without a precision statement
python3 "${CLAUDE_SKILL_DIR}/scripts/check_null_calibration.py" \
  --manuscript manuscript.md --out qc/null_calibration.json --strict

# 6. reader/observer study only — prove the (call × confidence) → score encoding is strictly
#    monotonic; a folded score silently mis-estimates the AUC and no prose review can see it
python3 "${MEDSCI_SKILLS_ROOT}/skills/analyze-stats/scripts/rating_monotonicity.py" \
  --encoding score_def.json
```

**Verdict → severity.** The rationale and the resolution path for each are in the reference file.

| Verdict | Severity |
|---|---|
| `PRIMARY_REASSIGNED` | **Major** — the primary was re-designated after results were known |
| `EVALUE_ARITHMETIC`, `EVALUE_NON_PRIMARY` | **Major** — recompute for the *declared primary* estimate |
| `PROMISED_ABSENT`, `DISK_UNREPORTED`, `PROMISED_STAT_NO_VALUE` | **Major** |
| `SUPP_INTERNAL_LABEL`, `SUPP_PLACEHOLDER`, `SUPP_BUILD_MARKER`, `SUPP_RESPONSE_FRAMING`, `SUPP_PLANNING_RESIDUE`, `SUPP_XREF_UNRESOLVED` | **Major** — a slip in a supplement is as fatal at a technical check as one in the body |
| `CITATION_ORDER` | **Major**; `CITATION_GAP` **Minor** |
| `CONFIRM_NULL_NO_MDE` | **Major** |
| `ESTIMAND_DRIFT`, `PRIMARY_DISCLOSURE_NOTE` | **Advisory Minor — never a blocker.** The provenance match is fuzzy (token overlap); confirm against the actual registration first. `PRIMARY_DISCLOSURE_NOTE` flags the honest disclosure the guidance *recommends writing* — do not penalise it. |

**Four checks no script makes** (prose judgement — the reference file has the full text):

1. **Primary-change guard** — two models for one contrast, one significant and one null, the
   significant one foregrounded: confirm which was pre-specified.
2. **Headline vs own-sensitivity direction** — if the headline claim points the opposite way
   from the authors' own sensitivity estimate, the paper contradicts its own robustness check.
3. **Rating → AUC monotonicity** — a *folded* (call × confidence) score silently mis-estimates
   the AUC, and prose review cannot see an estimator bug.
4. **Figure-embedded numbers are grep-blind** — every numeric audit above is blind to numbers
   *inside* a rasterised figure. Read each figure page visually before submission.

Also re-run `/sync-submission`'s `check_cross_artifact_stale.py` **after** any reframe, not just
once at the start. For time-to-event manuscripts, apply probe **S8 (estimand provenance)** of
`references/domain-probes/survival_prognostic.md`.

**Read on demand:**

| File | Read it when | Cost if read blindly |
|---|---|---|
| `references/phases/phase2_5f_claim_artifact.md` | a gate above fired and you need the rationale + resolution path, or there is a pre-registration to reconcile | ~4,800 tokens; a manuscript with no registration and no firing gate needs none of it |
### Phase 2.5g: Editorial-Impression / Defensiveness Scan (the ceiling pass)

Run this **after** the floor gates (Phases 2.5–2.5f), because it reads the *accurate* manuscript
and recommends what to take back out. It is the operational form of category L and the
counterweight to the additive bias of the rest of the stack: every other phase can only make the
manuscript longer and more defended; this one is the only phase that can make it shorter and more
confident. It is advisory and **non-blocking** — it never produces a Major and never gates
submission.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_editorial_impression.py" \
  --manuscript manuscript.md --out qc/editorial_impression.json
```

The gate reads the manuscript as a whole, segments it by IMRAD heading, and emits up to six
verdicts, each tagged with a SUBTRACTION `action`:

| Verdict | Reads as | Action |
|---|---|---|
| `HEDGE_DENSITY` | defensive-caveat tokens per 1,000 narrative words over threshold | TIGHTEN |
| `HEDGE_REPEAT` | one caveat motif repeated across body + Abstract | TIGHTEN |
| `AUDIT_IN_BODY` | SHA / commit / unit-test / post-lock / manifest / seed in the narrative | MOVE (→ Methods/supplement) |
| `LIMITATIONS_VOLUME` | a long enumerated Limitations list | TIGHTEN (consolidate) |
| `ABSTRACT_CAVEAT_LOAD` | several caveat clauses in the Abstract | TIGHTEN |
| `BURIED_DEFENSE` | strong numeric robustness result only in Limitations/supplement | MOVE (→ Results) |

**Fold the findings into the report as the SUBTRACTION axis, not the additive one.** Each
becomes a Minor `issues[]` entry under `category: "L" / category_name: "Editorial impression"`,
additively carrying `issue_type: "editorial_impression"`, `subtype: <verdict>`, and
`action: "REMOVE" | "MOVE" | "TIGHTEN"`. They are summarized in their own Phase 3 block
("Editorial-Impression Risks — REMOVE / MOVE / TIGHTEN"), kept visually separate from the
"Anticipated Major / Minor Comments (ADD / FIX)" so the author sees both forces. Mark them
`fixable_by_ai: false` by default — TIGHTEN-ing a hedge or MOVE-ing a robustness result is a
voice-and-judgment edit the author should own — except a clearly-redundant repeated caveat
(`HEDGE_REPEAT`), which `--fix` may collapse to a single statement.

**Net-impact note.** When an *earlier* phase recommends adding a caveat or disclosure, weigh it
against L: an integrity-critical disclosure is a **must (state it once, crisply)**, but a
defensive over-disclosure is a **cut / move**. The two are not symmetric — keep the disclosure,
but place it once and point to the supplement rather than repeating it at every claim site
(placement discipline: main text narrates, auditability lives in the supplement).

### Phase 2.6: Multi-Agent Panel Review (--panel, opt-in)

Run this phase **only when `--panel` is passed**. The default single-pass review (Phases 2–2.5d) stays the fast path; the panel is the high-cost, high-precision option for a pre-submission final pass on a top-tier target. Run it after the numerical audits (Phases 2.5–2.5d) so the reviewers see source-verified numbers, and before the Phase 3 report, which it feeds.

**Precondition (blocking): the SSOT must be singular.** Before spawning any reviewer, enforce the Phase 1 step 4 SSOT gate: if more than one manuscript-like `.md` exists and none is pinned (no `SSOT.yaml` `truth.manuscript_md`, no explicit `--ssot`), **halt and ask the user which file is the SSOT** — a panel is too expensive to spend on a stale copy. Clear any `STALE_COPY` from `detect_copy_divergence.py` first.

The panel simulates independent peer reviewers who do not see each other's comments, then an editor who consolidates them — the same structure a journal uses. It reuses the vendored domain-probe modules so every reviewer applies the same criteria.

**Step 1 — Compose the reviewer set by research type.** Auto-detect the manuscript type (Phase 1 input + the Research-Type Adaptation table). Each reviewer loads the matching domain-probe module so the panel's criteria are single-sourced.

| Research type | Reviewer set (each is one reviewer) | Domain-probe module each loads |
|---|---|---|
| Survival / prognostic cohort | R1 Biostatistics & Study Design · R2 Clinical (domain) · R3 Imaging/Radiology (if an imaging exposure) | `references/domain-probes/survival_prognostic.md` |
| Systematic review / meta-analysis | R1 Methodology (search/screening/PRISMA) · R2 Clinical · R3 Statistics (pooling/heterogeneity) | `references/domain-probes/sr_ma.md` |
| Radiomics / feature reproducibility | R1 Imaging physics & acquisition · R2 ML / Statistics · R3 Clinical translation | `references/domain-probes/radiomics.md` |
| Diagnostic-accuracy / AI model | R1 Study design & leakage · R2 Statistics (DeLong, calibration) · R3 Clinical / reference standard | `references/domain-probes/sr_ma.md` (P1 DTA cells) + `references/domain-probes/ai_overclaiming.md` (AO0–AO7, for AI clinical claims) + categories A–C |
| Observational (STROBE) | R1 Epidemiology / confounding · R2 Clinical · R3 Statistics | `references/domain-probes/observational_confounding.md` (O1/O8 run as the Phase 2.5e / `check_cohort_arithmetic.py --id-col` deterministic gates; O7 over-adjustment) + `references/domain-probes/clinical_prediction_model.md` (CP1–CP4, when it is a prediction-model paper) + categories A–J + the effect-size / added-value axes |
| Narrative / review article | R1 Domain-content expert · R2 Methodology / SANRA · R3 Technical accuracy · R4 Adversarial reject-hunter (structural: RV9 curated-base circularity, RV6 single-anchor overload, RV8 self-citation architecture) | `references/domain-probes/narrative_review.md` |
| Case report | R1 Clinical case-report reviewer · R2 Ethics / de-identification · R3 Literature-context reviewer | `references/domain-probes/case_report.md` + CARE items + categories D/F/G |

If the type is ambiguous, ask the user before composing the set.

Append the **handling-editor desk-impression** persona (the ceiling lens) to every reviewer set:
it loads no domain probe, reads only for narrative confidence vs over-defensiveness, and returns
Minor REMOVE / MOVE / TIGHTEN findings (category L) that the editor routes to the separate
Editorial-Impression Risks block. Its focus checklist is in `references/panel_review_template.md`.
It does not count toward the Step 3.5 lens-diversity axes.

**Step 2 — Run the reviewers (portable execution).** When the host provides a parallel subagent / Task capability (Claude Code, or any harness exposing an Agent tool), spawn the reviewer set as independent parallel subagents, each blinded to the others, then run the editor as a final synthesis agent. **Fallback (no subagent capability — e.g. a minimal Codex/Cursor harness):** a single agent role-plays each reviewer sequentially and in isolation — it completes and writes out reviewer R1's full structured review before reading the manuscript "fresh" as R2, so a later reviewer never sees an earlier reviewer's comments. The panel is defined by these instructions; it does **not** depend on the `Workflow` tool or any Claude-Code-only orchestration.

A reusable reviewer schema, a generic harsh-but-fair reviewer prompt skeleton with per-domain focus checklists, and the editor synthesis prompt skeleton live in `${CLAUDE_SKILL_DIR}/references/panel_review_template.md`.

Each reviewer returns: `reviewer_id`, `expertise_area`, an `overall_assessment` (name the single biggest threat to the conclusions), `strengths` (2–3), `major[]` (each with `heading`, `comment`, `location`, `severity`, `suggested_fix`), and `minor[]`. Map `severity` onto this skill's own scale — a conclusion-threatening / design-level finding is **Fatal**, a reporting-level finding is **Fixable** — rather than introducing a separate vocabulary.

**Step 3 — Editor synthesis.** One editor pass (a final agent, or the main agent in the fallback) consolidates the reviews:
1. **Dedupe** findings by theme across reviewers.
2. **Flag CONSENSUS** for any theme raised by ≥2 reviewers, with R1/R2/R3 attribution (e.g., `[CONSENSUS: R1+R3]`); single-reviewer findings are attributed to the one reviewer.
3. **Decide** an internal readiness verdict (this sets the Phase 3c `verdict` / `overall_score`; it is not printed as a journal recommendation).
4. **Rank** the concrete pre-submission actions the author should complete first.
5. State a one-line **readiness verdict** (ready for the target tier now / fix specific items first / consider a different tier).

**Step 3.5 — Lens-diversity gate (deterministic).** A panel only earns its cost if its reviewers span *distinct* axes rather than echo one theme louder. Before the editor finalizes, serialize the reviewers' structured outputs (the schema above) to a JSON file — either a top-level list or `{"reviewers": [...], "research_type": "..."}` — and run the gate:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_panel_diversity.py \
    --panel panel_reviews.json \
    --research-type {survival|sr_ma|radiomics|dta|observational|narrative} --strict
```

It reports three diversity failures, each mapped onto a concern family aligned to the focus checklists:
- **`UNCOVERED_AXIS`** (Major) — an axis the research type is expected to probe (e.g. heterogeneity/pooling for an SR/MA) drew **zero** major findings. The editor re-probes it with the owning reviewer before finalizing, or records in the synthesis why the gap is acceptable.
- **`FAMILY_MONOCULTURE`** (Major) — the majority of majors fall in one concern family; the lenses converged rather than spanned the manuscript.
- **`LENS_COLLAPSE`** (Flag) — a reviewer raised only families another reviewer already covered, adding no independent axis.

Healthy CONSENSUS is preserved — agreement on *some* themes is a strength (Step 3 flags it), and the gate fires `LENS_COLLAPSE` only on a *fully* redundant reviewer and the Major checks on panel-level coverage, never on agreement per se. Do not silently ship a monoculture: resolve every Major before the synthesis verdict.

**Step 4 — Feed Phase 3.** The consolidated panel output flows into the Phase 3 report, Phase 3b R0 numbering (**preserved**, so `/revise` still consumes it), and Phase 3c JSON. CONSENSUS flags and reviewer attribution are additive annotations on the existing `M`/`m` comments (and the optional `consensus` JSON field); they do not change the report or JSON structure.

**Re-run the panel after a large revision.** A panel is high-yield not only before the first submission but **again after any large edit** — a word-count compression, a primary-model or adjustment-set change, or resolving a batch of majors. Such edits introduce *new* drift (a compression drops a caveat; a re-fit leaves a derived CSV stale; a relocation orphans a cross-reference), and the second panel's findings shift character accordingly (method → compression-drift → residual). If the author has just compressed or re-modelled, recommend one more `--panel` pass rather than assuming the prior panel still holds; in practice each post-revision round surfaces real, distinct errors.

### Phase 3: Report

Before writing the Anticipated Comments, skim `references/exemplar_findings/` for the
finding at hand (cohort-arithmetic mismatch, unadjusted confounder, cross-sectional scope
overreach, post-hoc primary / estimand drift). Each models the full shape — which gate
fired, the comment in the reviewer's own words, Fatal/Fixable severity, the closest
category letter, the concrete fix, `fixable_by_ai`, and an R0-ready line for Phase 3b.
They are synthetic teaching models — match the structure, not the wording.

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

The report carries **two** axes, kept visually separate: the **ADD / FIX** axis (Anticipated
Major / Minor Comments — what is missing or wrong) and the **SUBTRACTION** axis
(Editorial-Impression Risks — what to remove, move, or tighten). Do not fold the L items into the
Minor Comments; an author who sees only "add this" will monotonically over-defend.

**Conciseness targets**:
- Anticipated Major Comments: 3-7 items, each 3-5 lines
- Anticipated Minor Comments: 3-6 items, each 1-2 sentences
- Editorial-Impression Risks: 0-6 items, each 1 sentence (only what the Phase 2.5g gate flagged)
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
- `requires_reanalysis` *(optional, default `false`)*: `true` when closing the finding needs a **committed analysis re-run against the real data**, not a prose edit — power/MDE re-simulation under the full model, first-visit/one-record-per-subject dedup, an extended- or reduced-adjustment sensitivity model, optimism correction of calibration. Always implies `fixable_by_ai: false`. Additive and backwards-compatible; parsers that do not expect it must ignore it. Route these to `/analyze-stats` (see Phase 4).
- `suggested_fix`: Specific, actionable instruction. If `fixable_by_ai` is true, this must be concrete enough for the fixer to execute without ambiguity.
- `consensus` *(optional, panel mode only)*: array of reviewer ids that raised the issue, e.g. `["R1","R3"]`. Additive and backwards-compatible — present only when Phase 2.6 ran; parsers that do not expect it must ignore it.
- `action` *(optional, editorial-impression findings only)*: `"REMOVE" | "MOVE" | "TIGHTEN"` — the SUBTRACTION direction for a category-L finding (Phase 2.5g). Present alongside `issue_type: "editorial_impression"` and `subtype: <verdict>` (e.g. `HEDGE_REPEAT`). Additive and backwards-compatible; these are always `severity: "minor"`, never block, and are `fixable_by_ai: false` by default (except a redundant `HEDGE_REPEAT`, which `--fix` may collapse). Parsers that do not expect it must ignore it.

### Phase 4: Fix Support

#### Standard mode (no --fix flag)

After presenting the report, offer to help fix specific issues:
- Rewrite overclaiming sentences
- Draft missing limitation statements
- Suggest statistical additions (e.g., calibration analysis code via `/analyze-stats`)
- Draft intended use, decision-impact, or novelty-delta statements
- Check specific tables/figures for consistency
- Generate missing flow diagrams via `/make-figures`

**`requires_reanalysis` findings route to `/analyze-stats`, not a prose edit (observational/cohort).**
For cohort and observational manuscripts, the highest-value fixes are usually *data-level*: a
power/MDE re-simulation under the full primary model, a first-visit / one-record-per-subject dedup
sensitivity, an extended- or reduced-adjustment (over-adjustment) sensitivity model, or optimism
correction of calibration. These are **not** `fixable_by_ai` text edits — `--fix` is text-only and
will silently skip them. Tag each such finding `requires_reanalysis: true` and route it to
`/analyze-stats` for a committed script + CSV, then feed the regenerated numbers back into the
manuscript and re-run the relevant Phase 2.5 gate. Surface these explicitly to the author rather
than letting an auto-fix pass appear to "resolve" them.

#### Auto-fix mode (--fix flag)

When `--fix` is passed:

1. **Filter fixable issues**: Select all issues where `fixable_by_ai` is true.
2. **Apply fixes sequentially**: For each fixable issue, edit the manuscript file directly:
   - Text rewrites (overclaiming, missing sentences, terminology) → Edit in place
   - Missing reporting items (ethics statement, data availability) → Insert at suggested location
   - Numerical inconsistencies (abstract-table mismatch) → Correct to match tables
   - Do NOT attempt: new statistical analyses, new figures, design changes, IRB-dependent items, or any issue tagged `requires_reanalysis` (route those to `/analyze-stats`)
   - Do NOT invoke other skills (`/make-figures`, `/analyze-stats`) during fix — text edits only
3. **Report changes**: After all fixes, output a summary:
   ```
   ## Auto-Fix Summary
   - Fixed: {N} issues
   - Skipped (requires human): {M} issues
   - Changes: {list of id + one-line description of what was changed}
   ```
4. **Post-edit paren-span safety scan**: if any fix reduced em-dashes (e.g. a `— X —` appositive → `(X)`), run the parenthesis-span gate before re-review — a bulk conversion can pair two unrelated dashes across a sentence boundary and wrap a whole sentence (or an ordinal "Sixth, …" limitation) inside one parenthesis (paren-balanced, so a balance check misses it):

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/check_paren_spans.py" \
     --manuscript manuscript.md --out qc/paren_spans.json --strict
   ```

   `PAREN_SPAN_ORDINAL` / `PAREN_SPAN_SENTENCE` is a Major — undo or repair that conversion before continuing.
5. **Re-review**: Run Phase 2 (systematic check) again on the modified manuscript.
6. **Iterate**: If new fixable issues emerge, apply one more round (maximum 2 total fix iterations).
7. **Final output**: Regenerate the Phase 3 report and Phase 3c JSON with updated scores.

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
| Phase 2.5g editorial-impression scan (`check_editorial_impression.py`) | ADVISORY (non-blocking) | HEDGE_DENSITY / HEDGE_REPEAT / AUDIT_IN_BODY / LIMITATIONS_VOLUME / ABSTRACT_CAVEAT_LOAD / BURIED_DEFENSE | Minor REMOVE/MOVE/TIGHTEN recommendation in the Editorial-Impression Risks block; never blocks submission |
| R0 numbering output | OPT-IN | `--r0-numbering` flag or downstream `/revise` consumer | Emits structured Anticipated Major/Minor Comments — consumable by `/revise` |
| `--json` machine-readable output | OPT-IN | `--json` flag | Emits parseable JSON block consumed by `/orchestrate` post-skill validation |
