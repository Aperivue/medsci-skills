# Exemplar — over-adjustment: a consequence of the outcome in the adjustment set

**Fired:** `observational_confounding.md` probe **O7** (over-adjustment / conditioning on a
mediator or consequence of the outcome). This is the opposite-direction failure to O1
(measured-but-unadjusted, the `check_confounding_completeness.py` gate): here a covariate that
the outcome physiologically *drives* is wrongly **inside** the primary model. Not an automated
gate — surfaced by reading the adjustment set against the outcome's causal structure (a DAG).
**Severity:** Fatal → Anticipated **Major**. **Category:** C. Validation & Statistical Reporting
(with E. Reproducibility for the sensitivity model). `requires_reanalysis: true`.

## Anticipated Major Comment (how a reviewer will put it)

> The outcome is eGFR, and the multivariable model adjusts for serum uric acid. Because urate is
> renally excreted, a lower eGFR mechanically raises serum uric acid — uric acid is a *consequence*
> of the outcome, not a confounder of the exposure–eGFR relationship. Adjusting for it (and, if
> similarly downstream, blood pressure or HbA1c) is over-adjustment and can attenuate the very
> association the study reports. The adjustment set appears to have been chosen because these
> variables differ across exposure groups in Table 1, but baseline imbalance is not a
> confounder-selection criterion. Please justify the adjustment set with a DAG, report a primary
> model that excludes outcome-consequences, and show the current model as a sensitivity analysis
> with collinearity (VIF) disclosed.

## Severity / category rationale

**Fatal** because removing the over-adjusted covariate can move the headline estimate — the result
as reported may be biased toward or away from the null. The fix is not wording: it needs a re-fit
under a defensible adjustment set (`requires_reanalysis`), so `fixable_by_ai: false`. **Category C**
(model specification), with the parsimonious-vs-kitchen-sink comparison reported under E.

## Fix

Draw a DAG; classify each adjustment variable as confounder / mediator / outcome-consequence /
collider. Keep only confounders in the primary model. Report a parsimonious history-based model as
primary, the full model as a sensitivity analysis, and VIF for collinearity. Route the re-fit to
`/analyze-stats`. If the estimate changes materially, propagate to Abstract and Conclusions.

## R0-ready line

> R0-C1 (Major, Fatal, requires_reanalysis): eGFR model adjusts for serum uric acid (an outcome
> consequence) — over-adjustment; re-fit a DAG-justified primary model excluding outcome-
> consequences, report the current model as sensitivity + VIF. [probe: O7]
