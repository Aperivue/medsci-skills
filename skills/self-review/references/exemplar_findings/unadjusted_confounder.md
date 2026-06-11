# Exemplar — an imbalanced measured covariate is left out of the model

**Fired:** `check_confounding_completeness.py` — `UNADJUSTED_IMBALANCED` (a covariate that
is measured and imbalanced across exposure groups in Table 1 is not in the Methods
adjustment set).
**Severity:** usually Fixable → Anticipated **Minor**; Fatal → Anticipated **Major** when
the covariate plausibly explains the primary association. **Category:** C. Validation &
Statistical Reporting (with E. Reproducibility for the model spec).

## Anticipated Major/Minor Comment (how a reviewer will put it)

> Baseline smoking differs between the exposed and unexposed groups (Table 1: 41% vs 23%,
> standardized mean difference 0.39), and smoking is a plausible confounder of the
> exposure–outcome relationship, but it does not appear in the adjustment set (Methods,
> *Statistical analysis*). Please either add it to the multivariable model or explain why it
> was excluded, and report whether the primary estimate changes when it is included.

## Severity / category rationale

It is **Minor/Fixable** when the covariate is one of several already-adjusted and the result
is robust; it escalates to **Major/Fatal** when it is imbalanced *and* on the causal path to
the outcome *and* the primary estimate is near the significance boundary — then an
unadjusted confounder could flip the conclusion. Tag **category C** (the estimate's
validity), noting the model spec under E.

## Fix

Add the covariate to the model (or pre-specified sensitivity model), report the adjusted
estimate with its CI, and state the change from the unadjusted estimate. If exclusion was
deliberate (e.g., collider/mediator), say so and cite the DAG rationale. `fixable_by_ai:
false` — requires re-running the model on the data.

## R0-ready line

> R0-C2 (Major, Fatal-if-flips): smoking is imbalanced (SMD 0.39) but unadjusted; add to the
> model and report the change in the primary estimate. [gate: check_confounding_completeness]
