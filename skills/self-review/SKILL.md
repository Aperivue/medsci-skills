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
**Phase 2.5i (the loop controller)** then reads the floor + ceiling state to declare when
the loop is *done* — including a zero-edit PASS — so an accurate draft is not over-hardened
by a pass it does not need.

## Workflow

### Phase 1: Intake

1. Get the manuscript -- PDF, Word doc, or pasted text.
2. Ask the user:
   - Target journal? (affects reporting standards and scope expectations)
   - Manuscript type? (original research / review / perspective / technical note / letter / meta-analysis / case report)
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

# J/D. Perspective structure (genre-gated: silent unless article_type is a Perspective).
# Pass the known type via --type; it also self-detects from the front-matter article_type.
python3 "${CLAUDE_SKILL_DIR}/scripts/check_perspective_structure.py" \
  --manuscript manuscript.md --type "${TYPE:-}" --out qc/perspective_structure.json
```

Verdict mapping: `CROSS_SECTIONAL_PROGNOSTIC`, `SURROGATE_CARE_DIRECTIVE`, `SECTION_SYMBOL`,
`INBODY_AI_DISCLOSURE`, and any reviewer-team hit (exit 1) are Anticipated **Major** Comments.
`CROSS_SECTIONAL_YIELD_LANGUAGE`, `ELIGIBILITY_PROSE`, `DECIMAL_INCONSISTENCY`,
`EM_DASH_OVERUSE`, `PERSPECTIVE_HEADING_NOT_ASSERTION`, `PERSPECTIVE_ABSTRACT_NO_AUTHORIAL_MOVE`,
and every `check_editorial_impression` verdict are **Minor**. The
per-verdict rationale and the resolution paths are in the reference file.

**Read on demand:**


**Then check that every analysis you report was ever defined.** The detectors in this skill ask whether a number is *correct*. None asks whether the analysis that produced it was *defined* — and that is the gap a reviewer walks straight into:

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

- **Observational studies**: Confounding assessment (DAG or adjustment strategy), selection bias, exposure measurement validity. Run **Phase 2.5e (Confounding Completeness)**, then apply the O-probes in `references/domain-probes/observational_confounding.md` — the two deterministic ones are O1 (a covariate imbalanced by exposure in Table 1 yet absent from the adjustment set) and O8 (records > subjects with the analysis unit undisclosed; `check_cohort_arithmetic.py --id-col`), and O7 is their opposite-direction twin (adjusting for a consequence/mediator of the outcome). If the manuscript develops or compares a **clinical prediction model** (TRIPOD / TRIPOD+AI, nested predictor-set comparison), also apply the CP-probes in `references/domain-probes/clinical_prediction_model.md`. The module is the single source for the probe list and its numbering; do not re-enumerate it here.
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
| Perspective / opinion / viewpoint (argumentative essay — npj DM long-essay, Lancet Comment, NEJM AI / RYAI short-structured) | `references/domain-probes/narrative_review.md` (RV1–RV9) + the deterministic `check_perspective_structure.py` gate above (IMRAD-heading + abstract authorial-move tells) |
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
### Phase 2.5a-2: Design & Power Statistic Provenance

A design or power statistic is **computed**, not copied from a source, so the source-fidelity audit of Phase 2.5a cannot check it — it has to be re-derived from the manuscript's own inputs. This applies only when the manuscript states a sample-size calculation, a power figure, or a detectable-effect claim.

**Read on demand:**

| File | Read it when | Cost if read blindly |
|---|---|---|
| `references/phases/phase2_5a2_design_power.md` | the manuscript reports a sample-size / power / MDE calculation | ~1,050 tokens; a manuscript with no power statement needs none of it |

**Load-on-demand**: read `${CLAUDE_SKILL_DIR}/references/phases/phase2_5a2_design_power.md` when the manuscript reports a sample-size / power / MDE calculation.

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

**A. SR/MA — recount from the ID sets.** Derive every study count from the screening TSV and the
consensus sheet rather than from prose, and **list the narrative-only IDs explicitly** — the
highest-yield cross-check, the one that turns "10 narrative-only studies" into "2 (IDs 120, 474)".
Any derived total that disagrees with Abstract, Methods, Results, the Figure 1 caption or
Limitations is a **P0 Major, blocking submission**, and any `N → M` transition claim not backed by
an enumerable ID addition/subtraction set is itself a **Major** — it is unverifiable by downstream
audit. The set definitions, the derivation formulas and the reconciliation-block template are in
the reference file.

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
### Phase 2.5c: Reference Scans (hallucination + adequacy)

Two scans run on the bibliography: **2.5c** catches a citation that does not exist or whose first author is invented, and **2.5c-2** catches a claim that carries no citation at all. Both need a bibliography — a draft with no `refs.bib` and no reference list skips them entirely. Run `/verify-refs --strict` first; these scans read its audit rather than re-deriving it, then run the adequacy checker:

```bash
python3 "${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}/skills/self-review/scripts/check_reference_adequacy.py" \
  --manuscript manuscript/manuscript.md --bib "$BIB" \
  --article-type "$TYPE" ${CAP:+--journal-cap "$CAP"} \
  --out qc/reference_adequacy.json --strict
```

**Read on demand:**

| File | Read it when | Cost if read blindly |
|---|---|---|
| `references/phases/phase2_5c_reference_scans.md` | the manuscript has a bibliography and you are auditing citations | ~1,950 tokens; a draft with no reference list cannot use any of it |

**Load-on-demand**: read `${CLAUDE_SKILL_DIR}/references/phases/phase2_5c_reference_scans.md` when the manuscript has a bibliography and you are auditing citations.

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
| `MISSING_BODY` | **Major (P0)** — no body caption definition | **Major (P0)** when the float IS in the rendered DOCX (SSOT drift). **Minor** when no `--docx` was supplied — excused without evidence, and reported as such |
| `MISMATCH` | **Major (P0)** — caption text disagrees between body and rendered DOCX | **Major (P0)** (no change) |
| `UNCITED` | Minor — orphan caption; cite it or remove it | Minor (no change) |

`MISMATCH` stays P0 under every policy. So does `MISSING_BODY` **when the float is present in the
rendered DOCX** — the build pipeline is then the only place that knows the caption text, which is SSOT
drift and not a style choice. `MISSING_BODY` with **no `--docx` supplied** is different: nothing was
checked, so under `--allow-separate-attachments` it is excused on the author's declaration and the run
says so in those words. Treat those rows as unverified, not as verified — re-run with `--docx` before
submission and read `summary.downgraded_unchecked` in the audit JSON.

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

### Phase 2.5h: Baseline Drift (anchor to the last human-approved version)

Run this after the ceiling pass and **before** the loop controller (Phase 2.5i), so its
findings are counted when the terminal state is judged. The refine loop's hazard is the
*anchor*: each pass silently takes the previous **AI output** as its baseline, so a small
framing bias compounds across passes while every pass looks locally fine. This gate
compares the current manuscript against the **last human-approved version** — the frozen
`v_N` of manuscript-versioning (a senior/co-author-circulated draft), **not** the last AI
output — and reports lexical framing drift. Supply the baseline explicitly; with none
available (a first draft) skip it — the gate is a no-op without one.

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

Every finding is **Minor and advisory** — framing is the author's judgment and the gate
never blocks. Treat drift as *review against the approved anchor*, not an instruction to
revert: legitimate new analysis can justify a stronger claim, but the author should confirm
it rather than let it accrete unexamined across AI passes. Its `qc/baseline_drift.json`
feeds the loop controller, so a draft that has drifted does not read as a zero-edit PASS.

### Phase 2.5i: Refinement Terminal-State (the loop controller)

Run this **last**, after the floor gates (Phases 2.5–2.5f) and the ceiling pass (Phase
2.5g), because it reads their `qc/*.json` artifacts and classifies whether the
refine-and-review loop is *done*. Self-review is run iteratively (review → revise →
review); the floor gates converge to a fixed point of zero Major findings, but the
additive bias of the whole stack means a naive loop never stops — there is always one
more caveat to add. This step is the counterweight's controller: it turns the floor +
ceiling state into a reproducible STOP verdict and makes a **zero-edit result a valid
PASS**, so an accurate manuscript is not over-hardened by another pass it does not need.

It is **not a detector** (it finds no defect, carries no `check_` prefix, is uncounted in
the catalog) and it is **advisory — it never blocks**; it must not double-gate the floor
detectors, which already fail under `--strict` on their own Majors.

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
| `INDETERMINATE` | no gate artifacts yet | run the floor + ceiling gates first |

**Stopping principle.** Deterministic floor gates iterate to their fixed point (0 Major);
subjective refinement does **not** get an open loop. Once the verdict is any `STOP_*`,
stop the additive cycle — surface the terminal state in the Phase 3 report and do not
re-run self-review to find "one more thing". A `STOP_ZERO_EDIT` or `STOP_MINOR_OPTIONAL`
verdict is a legitimate terminal state; treating "found nothing required" as a failure to
try harder is exactly the over-hardening this phase exists to stop.

### Phase 2.5j: Refinement Regression (fixed vs broke, across runs)

Run this each round, after the loop controller, and record the run. Self-review is
stateless: a revision that resolves finding X can introduce finding Y, and the pass-rate
(how many old findings are gone) hides it. This step reads a small run-history ledger — one
line per run, the `verdict@where` fingerprints of that run's findings — and reports the
**regression axis next to the pass-rate axis**: what the revision *fixed* vs what it *broke*.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/refinement_regression.py" \
  --qc-dir qc --ledger qc/refinement_ledger.jsonl --append \
  --out qc/refinement_regression.json
```

Use `--append` on a real run so the current findings become the next entry; omit it to
classify without recording.

| Verdict | Meaning | What the harness must do |
|---|---|---|
| `PROGRESSING` | findings resolved, none new | continue |
| `REGRESSION` | the revision introduced new finding(s) | review the new findings before accepting the fix — the pass-rate went up but something broke |
| `CHURNING` | a resolved finding reappeared (Mirror Loop) | **stop revising and re-anchor** — more passes re-derive, they do not converge |
| `CONVERGED` | nothing new, nothing carried | the loop is done |
| `INDETERMINATE` | first run, no prior entry | re-run after a revision |

It is **not a detector** (no `check_` prefix, uncounted) and **advisory — it never blocks**.
Report both axes in Phase 3: a revision is an improvement only if it resolved findings **and**
the `new`/`churn` columns are empty. A `CHURNING` verdict is the deterministic form of the
same stop signal the loop controller raises — the loop is no longer making progress.

### Phase 2.6: Multi-Agent Panel Review (--panel, opt-in)

Run this phase **only when `--panel` is passed**. The default single-pass review (Phases 2–2.5d) stays the fast path; the panel is the high-cost, high-precision option for a pre-submission final pass on a top-tier target. Run it after the numerical audits (Phases 2.5–2.5d) so the reviewers see source-verified numbers, and before the Phase 3 report, which it feeds.

Two things bind before you spawn anything: the **SSOT must be singular** (the Phase 1 step 4 gate — halt and ask if more than one manuscript-like `.md` is unpinned), and the roster must not be a **substrate monoculture** (a panel that shares the drafter's model inherits its blind spots; route at least one lens to Codex or a human co-author). Both are enforced by `check_panel_diversity.py --strict`, which also fires `PANEL_UNDERRETURN` when fewer reviewers returned than were spawned — a panel with <2 returned reviews is a failed run, not a thin one.

**Read on demand:**

| File | Read it when | Cost if read blindly |
|---|---|---|
| `references/phases/phase2_6_panel.md` | `--panel` was passed and you are composing the reviewer set | ~2,600 tokens — the reviewer-set table, roster manifest, editor synthesis and lens-diversity gate; a default single-pass review reaches none of it |

**Load-on-demand**: read `${CLAUDE_SKILL_DIR}/references/phases/phase2_6_panel.md` when `--panel` is passed.

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

### Phase 3c: Structured JSON Output (--json)

Emit the review as machine-readable JSON **only when `--json` is passed** (or when another skill consumes this run). The schema, field semantics and worked example live in the reference; a human-facing review never serializes anything.

**Read on demand:**

| File | Read it when | Cost if read blindly |
|---|---|---|
| `references/phases/phase3c_json_output.md` | --json was passed, or a downstream skill consumes this run | ~790 tokens of schema a human-facing review never emits |

**Load-on-demand**: read `${CLAUDE_SKILL_DIR}/references/phases/phase3c_json_output.md` when --json was passed, or a downstream skill consumes this run.

### Phase 4: Fix Support (on request)

The review ends at Phase 3. Enter this phase **only when the user asks for help applying the findings** — a review that is read and acted on by the author never reaches it.

**Read on demand:**

| File | Read it when | Cost if read blindly |
|---|---|---|
| `references/phases/phase4_fix_support.md` | the user asks you to apply or draft fixes for the findings | ~850 tokens; a review that is only read never reaches this phase |

**Load-on-demand**: read `${CLAUDE_SKILL_DIR}/references/phases/phase4_fix_support.md` when the user asks you to apply or draft fixes for the findings.

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

## Global-rule references

Some passages in this skill cite a path of the form `~/.claude/rules/<name>.md`. Those are the
maintainer's personal global rules, kept outside this repository. They are **not shipped with
this skill** and will not exist on your machine; they appear only as provenance for where a
convention came from. If one of them looks like it is standing in for an instruction you actually
need, that is a bug — please open an issue, because the instruction belongs here.
