# Arithmetic closure and acquisition completeness (original articles)

Supporting material for [`../SKILL.md`](../SKILL.md) Phase 2, steps 4 and 5. SR/MA manuscripts have
their own gate ([`domain-probes/sr_ma.md`](domain-probes/sr_ma.md) P0).

## 1. Arithmetic closure

Step 4 checks the manuscript's own numbers against each other before any criticism is drafted;
Phase 4 item 15 verifies a discrepancy before it becomes a comment. Start with the main PDF and
follow the supporting material it cites; an input you cannot find is unverified, not missing.

- **(a) Flow.** At each stage, the unique exclusions reconcile the count entering with the count
  leaving, down to the analytic N.
- **(b) Partitions.** Mutually exclusive, exhaustive categories on the same unit, including any
  unknown category, sum to their parent.
- **(c) Validation or audit samples.** When a sample's prevalence is compared with the full set,
  ask how the sample was drawn and whether the comparison accounts for that design.
- **(d) 2×2 tables.** For a single unweighted table at one threshold, cells sum to the margins, and sensitivity, specificity, PPV and NPV
  re-derive from the cells. When only metrics are printed, ask whether one table of non-negative
  whole-number cells at the stated margins reproduces all of them within rounding; if none does, ask the
  authors which denominator or averaging each metric used.
- **(e) Percentages and headline numbers.** Unweighted Table 1 percentages match their counts
  (averaged or weighted statistics follow their stated computation), and each Abstract number traces to the analysis, unit and denominator it came from.

`/self-review`'s `check_cohort_arithmetic.py` and `check_table_percentages.py` help with the
count and percentage checks in tables; tracing the Abstract is done by hand.

Record the result even when everything closes. A mismatch is a lead until Phase 4 item 15 has
tested it, and its severity follows its effect on the conclusions.

## 2. Acquisition parameters

Re-derivation never reaches a variable that was not reported. For an imaging study, check the
Methods, supplement and tables for the acquisition variables that plausibly affect the claim (MR:
vendor, field strength, sequences; CT: reconstruction kernel, slice thickness, contrast phase,
cone-beam versus multidetector), and ask whether performance differs across them where the strata
are large enough to say something. When a variable coincides with another (one scanner per site),
results by combination can still be described, but a separate effect cannot be attributed to
either.
