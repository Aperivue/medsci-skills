# Exemplar — the reported "primary" differs from the registered one

**Fired:** `check_claim_artifact.py` — `PRIMARY_REASSIGNED` / `ESTIMAND_DRIFT` (the
manuscript's stated primary analysis or estimand does not match the pre-registration /
protocol), or an E-value attached to a non-primary or non-reproducing estimate.
**Severity:** Fatal → Anticipated **Major**. **Category:** C. Validation & Statistical
Reporting.

## Anticipated Major Comment (how a reviewer will put it)

> The registered protocol names the complete-case model as the primary analysis, but the
> manuscript presents the multiple-imputation model as primary (Methods, *Primary analysis*
> vs the registration). Selecting the primary after seeing results is outcome-dependent and
> can bias inference. Please either (a) restore the pre-registered primary and present the
> other model as a pre-specified sensitivity analysis, or (b) if the change was unavoidable,
> report both models coequally, disclose the change in the Abstract and a Limitations
> paragraph, and lodge the corresponding registration amendment.
>
> The reported E-value of 2.79 should also be recomputed from, and attached to, the primary
> estimate (it currently appears to derive from a different model).

## Severity / category rationale

**Fatal** because *which* result is primary determines the paper's headline; choosing it
post hoc is a credibility issue a methods reviewer catches deterministically. **Category C**
(estimand provenance). This is the estimand-provenance-lock principle: primary contrast and
derived statistics trace to the pre-registration, not to the data.

## Fix

Restore the registered primary (or present both coequally with disclosure + amendment),
recompute the E-value from the declared primary estimate, and propagate the framing to every
claim site (Abstract, Highlights, any plain-language summary). `fixable_by_ai: false` —
requires the registered protocol as the source of truth and a re-run.

## R0-ready line

> R0-C1 (Major, Fatal): reported primary ≠ registered primary; restore or report coequally +
> disclose + amend; recompute E-value from the primary. [gate: check_claim_artifact]
