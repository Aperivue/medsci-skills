# Discussion structure — observational cohort (STROBE)

A structure model for the Discussion of an exposure→outcome cohort study, completing the trio
with the `exemplar_methods/` and `exemplar_results/` siblings. Each heading is a paragraph;
each bullet is *what it must establish*. Fill the `[brackets]`; do not copy this text.
Follows `section_guides/discussion.md`. Introduces **no new results** and cites **no
tables/figures**.

## Paragraph 1 — Key finding and why it matters
- Restate the primary **association** (adjusted effect with its direction/magnitude) in 2–3
  sentences (only restate a comparison to conventional predictors if that comparison was
  pre-specified and reported in Results — introduce no new comparison here).
- One sentence on the clinical/public-health relevance — as risk stratification, not proven
  causation.
- **If the primary result is null, frame it by precision, not absence.** Do not write "X was
  not associated with Y" flatly; state what the confidence interval *excludes* — e.g. "the 95%
  CI excluded an eGFR difference larger than ~1.7" or cite the minimum detectable effect that
  the study was powered for. "No effect" and "could not exclude an effect of size X" are
  different claims; an underpowered null is "not yet established," and the MDE must be computed
  under the **full primary-model adjustment set** (a 2-covariate power calc overstates
  precision). Watch for **bilateral over-correction** — a prior "independently associated"
  overclaim swinging to an equally unsupported "not associated" claim during revision.

## Paragraphs 2–3 — Interpretation and comparison
- Compare to prior evidence (agree/differ and why: design, population, exposure measurement).
- **Causal caution is mandatory**: state plainly that the estimate is an association, not a
  demonstrated causal effect; discuss **reverse causation** and the limits a single-timepoint
  or cross-sectional exposure places on directionality.
- Offer a mechanism/biological plausibility as hypothesis, flagged as such.

## Limitations
- **Residual and unmeasured confounding** with the adjustment set named and its gaps stated
  (and, ideally, an E-value / tipping-point referenced from Results); selection bias; exposure
  misclassification; missing-data handling; outcome ascertainment completeness.
- **Adjustment-set choice both ways**: state that confounders were chosen by a causal rationale
  (DAG / prior literature), not because they differed in Table 1, and that no **mediator or
  consequence of the outcome** was adjusted (over-adjustment — e.g. a renally-excreted lab in an
  eGFR model); if a borderline covariate was included, reference the drop-it sensitivity model
  from Results.

## Generalizability
- The population the cohort represents and where the estimate may not transfer (single
  ancestry/region/registry), and how external validation mitigates but does not remove the
  concern.

## Conclusion
- Matched to the evidence — "associated with", "may identify higher-risk individuals", never a
  care directive (defer/withhold/initiate) or a prognostic/surveillance claim a cross-sectional
  or single-visit design cannot license.

## Common omission
- An explicit **causation caveat with reverse-causation/unmeasured-confounding** treatment —
  the Discussion element cohort drafts most often soften, and the one a methods reviewer checks
  first. Cross-reference `section_guides/discussion.md`, the
  `peer-review/references/domain-probes/observational_confounding.md` probe, and the STROBE
  critical items in
  `peer-review/references/reviewer_calibration/compliance_floor.md`.
