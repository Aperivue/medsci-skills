# Results structure — systematic review / meta-analysis (PRISMA 2020)

A structure model for the Results of a systematic review with quantitative synthesis. It
follows its Methods PRISMA sibling in Methods order. Each heading is a paragraph; each bullet
is *what it must establish*. Fill the `[brackets]`; do not copy this text. Report findings
only — no interpretation.

## Study selection (Figure 1 — PRISMA flow)
- The identification→screening→eligibility→inclusion cascade as the PRISMA 2020 flow diagram:
  records identified, duplicates removed, screened, full texts assessed, and excluded **with
  reasons and counts**.
- The cascade reconciles (identified − duplicates − excluded = included); state N studies in the
  review vs N in the meta-analysis (they can differ). These numbers match the Abstract, Methods,
  and Table 1 exactly (one locked count, re-derived — not re-typed per document).

## Study and patient characteristics (Table 1)
- Publication-year span, design mix (prospective / retrospective; RCT / observational), total
  and per-study N (median, IQR/range), countries, and the effect-relevant descriptors.
- A **data-provenance column** when studies may share an institution / public database / imaging
  benchmark — so overlapping-population non-independence is visible, not hidden.

## Risk of bias across studies (Figure 2)
- The RoB summary (QUADAS-2 / RoB 2 domain plot): how many studies were low risk overall and
  the domain that drove concern, with counts (N/N).

## Quantitative synthesis — primary outcome (Figure 3, forest plot)
- The pooled effect with **95% CI**, the study count **k** and pooled **N**, and heterogeneity
  reported as **I² with τ² and the 95% prediction interval** (state what the PI's bounds imply
  for a new setting).
- The forest plot cited; per-study weights visible. For DTA, the bivariate/HSROC summary point
  (pooled sensitivity & specificity with CIs) — check no sensitivity/specificity swap versus a
  source.

## Subgroups, meta-regression, and sensitivity
- Each **pre-specified** subgroup with its estimate + CI **and the test for subgroup interaction**
  (report the interaction p, not two bare stratum estimates); flag k=1 strata as descriptive, not
  pooled.
- Leave-one-out, prospective-only, and low-RoB-only sensitivity results, reported as results — not
  deferred to a supplement mention only.

## Publication bias / small-study effects
- Egger / Deeks asymmetry **only if ≥10 studies** (state the count gate); if trim-and-fill was
  run, the adjusted estimate. Do not over-read a non-significant test — its power is low; say so.

## Common omission
- The **prediction interval alongside I²**, a **subgroup interaction test** (rather than two
  separate stratum estimates), and the **overlapping-population/provenance** disclosure — the
  Results elements MA drafts most often skip. Cross-reference `section_guides/results.md`, the
  `peer-review/references/domain-probes/sr_ma.md` probes (P1, P2 non-independence, P3 subset-N
  transparency, P4 k=1), and the PRISMA critical items in
  `peer-review/references/reviewer_calibration/compliance_floor.md`.
