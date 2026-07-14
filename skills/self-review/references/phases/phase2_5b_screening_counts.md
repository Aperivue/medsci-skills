# Phase 2.5b — Screening-Count Reconciliation from ID Sets

Load-on-demand companion to `/self-review` Phase 2.5b. SKILL.md keeps the entry
condition and the two deterministic gates; this file carries the ID-set recount
procedure, the reconciliation-block template, and the precedent failures.

Read it when the manuscript is an SR/MA (the ID-set recount), or when a cohort
manuscript presents an ordinal tier / mutually-exclusive stratum split whose Ns
must partition (the binning and composite-indicator branch).

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

**Observational tier/stratum branch.** The same set-recount logic applies when a cohort
manuscript presents an ordinal tier or mutually-exclusive stratum split. A partition that
is claimed to be disjoint must satisfy `Σ(stratum N) == unique total` and
`Σ(stratum events) == total events`; denominators that sum *above* the unique cohort
double-count subjects, and a table where every stratum n equals the grand total is a
stratum-total mis-entry rather than a partition. Run `check_cohort_arithmetic.py`
(Phase 2.5 above) with the stratum CSV — its `PARTITION_OVERLAP` verdict is the cohort
analogue of an ID-set mismatch and is a P0 Major:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_cohort_arithmetic.py" \
  --manuscript manuscript.md --data analysis/strata.csv --strict
```

Also confirm the reference (baseline) row of any stratified hazard/odds table is present
and labelled; a missing reference category makes the other strata uninterpretable.

**Cross-script cut-point consistency (root cause of stratum-N drift).** When the same cohort
is re-stratified in more than one analysis script — a primary table in one file, a sensitivity
or secondary analysis in another — the derived categorical (age band, BMI category, eGFR stage,
risk tier) must use one identical cut definition: same breaks, same interval closure
(`right=`), same labels. If two scripts bin the same variable differently, per-stratum Ns drift
between tables while the grand total still reconciles, and a stratum can spuriously cross a
threshold — a `PARTITION_OVERLAP`/stratum-N check on the manuscript alone will not localize the
cause. `check_binning_consistency.py` parses the analysis source (R/Python) and emits
`BINNING_DRIFT` (Major) when one variable is derived with ≥2 different `(breaks, right)`
signatures across files:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_binning_consistency.py" \
  --root analysis --root scripts --strict
```

Precedent: a screening cohort binned age with `breaks=c(-Inf,45,50,60,Inf), right=FALSE` in the
primary script and `breaks=c(-Inf,44,49,59,Inf), right=TRUE` in a threshold sensitivity script;
fractional ages fell into different bands, shifting hundreds of participants and producing a
spurious "reached" stratum in the sensitivity table that vanished once the binning was
harmonized. Fix at the source by defining each cut once in a shared helper that every script
sources.

The same gate also covers the **composite-indicator** sibling failure: a derived 0/1 component
(e.g. a metabolic-syndrome criterion built from `as.integer(a >= x | b == 1 | c == 1)`) that is
re-built in a second script with a clause dropped or added. It splits each definition into
comparison atoms on the top-level `|`, compares them as a SET (clause order, whitespace, outer
parentheses, dataframe `df$` qualifiers and commutative `&`-operands are normalized away), and
emits `DERIVED_DEF_DRIFT` (Major) when one variable carries ≥2 distinct atom sets across scripts.
Precedent: `mets_bp <- as.integer(bl_he_sbp>=130 | bl_he_dbp>=85 | bl_tx_hypertension_med==1 |
bl_hypertension==1)` in the benchmark script vs the same name without the final
`| bl_hypertension==1` in a re-analysis script — the metabolic-syndrome C-index then read 0.6704
in one table and 0.6712 in another.
