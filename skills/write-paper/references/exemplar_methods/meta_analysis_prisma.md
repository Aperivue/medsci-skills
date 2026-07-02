# Methods structure — systematic review / meta-analysis (PRISMA 2020)

A structure model for a systematic review with quantitative synthesis. Each heading is a
paragraph; each bullet is *what it must establish*. Fill the `[brackets]`; do not copy this
text. Pairs with `paper_types/meta_analysis.md` (which carries the fuller prose templates) —
this file is the paragraph-order skeleton and the reviewer-critical checklist.

## Protocol and registration
- Prospective registration (PROSPERO `CRD[number]`) or an OSF/protocol reference, **lodged
  before data extraction began** — state the registration date relative to the search.
- Adherence to PRISMA 2020 (name the base guideline *and* the extension used, e.g. PRISMA
  base + **PRISMA-DTA** for diagnostic accuracy, PRISMA-NMA for network — never just the
  extension acronym).
- Any protocol amendments as dated entries (what changed, when, why), not a silent deviation.

## Eligibility criteria
- PICO(S) as a numbered inclusion list and a **separate** explicit exclusion list (not "did
  not meet inclusion") — Population, Intervention/Index test, Comparator, Outcome, Study
  design, and any language/date limits.
- The effect measure the review is built around (OR / RR / HR / MD / SMD / sensitivity &
  specificity / AUC) named here, so eligibility and synthesis agree.

## Information sources and search strategy
- Every database with its coverage dates and the last-search date; grey literature and
  register searches (ClinicalTrials.gov, conference abstracts) if used.
- The **full search string for ≥1 database, verbatim** (in-text or as a supplement) — a
  PRISMA-critical, first-line reviewer item; a paraphrased strategy is not reproducible.

## Study selection and data extraction
- Dual independent screening (title/abstract then full text) with the agreement metric
  (Cohen's κ or % agreement) at each stage and how disagreements were resolved; the operational
  reviewer count here must match what Limitations later concedes (no "dual" here / "single
  reviewer" there).
- Standardized dual extraction; the variables extracted; how the reference-standard / outcome
  cells (e.g. 2×2 TP/FP/FN/TN) were obtained and reconciled against the source (cell-level
  audit for hand-entered accuracy data).

## Risk of bias / quality assessment
- The tool matched to the design (**QUADAS-2** for DTA, **RoB 2** for RCTs, ROBINS-I / NOS /
  MINORS for non-randomized), applied in duplicate; how domain judgements were reached.
- Whether risk of bias fed a sensitivity analysis (low-RoB-only pool), not just a figure.

## Statistical synthesis
- The model and estimand: **random-effects a priori** (state the estimator, e.g.
  DerSimonian–Laird or REML; bivariate / HSROC for DTA) with the pooled effect and **95% CIs**.
- Heterogeneity: I² **with τ² and a 95% prediction interval** (I² is a proportion, not a
  magnitude — the PI shows the range of true effects); Cochran's Q threshold.
- **Pre-specified** subgroup / meta-regression covariates (post-hoc ones labeled exploratory);
  sensitivity analyses (leave-one-out, prospective-only, low-RoB-only); overlapping-population /
  shared-benchmark non-independence check.
- Publication bias (Egger / Deeks funnel asymmetry) **only when ≥10 studies**; certainty of
  evidence (**GRADE**) if claimed. Software + version + seed.

## Reporting-guideline fit
- PRISMA 2020 (+ the relevant extension). Critical items: verbatim search strategy for ≥1
  database, a flow diagram that reconciles, per-study risk of bias, and the protocol/registration
  reference (see `peer-review/references/reviewer_calibration/compliance_floor.md`).

## Common omission
- A **pre-specified subgroup set + an overlapping-population / shared-dataset non-independence
  check**, and naming **base + extension** guideline correctly — the Methods elements MA drafts
  most often skip, and among the first a synthesis reviewer checks. Cross-reference
  `section_guides/methods.md`, `paper_types/meta_analysis.md`, and the
  `peer-review/references/domain-probes/sr_ma.md` probes (P1 comparator existence, P2
  non-independence, P4 k=1 subgroup).
