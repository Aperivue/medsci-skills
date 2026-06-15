# Exemplar — a causal mediation chain claimed from cross-sectional data

**Fired:** `observational_confounding.md` probe **O13** (cross-sectional mediation: temporal order
& sequential ignorability), with **O3** (the cross-sectional design signal) nearby. Surfaced by
reading the mediation claim against the design, not an automated gate. **Severity:** Fatal →
Anticipated **Major**. **Category:** D. Clinical Framing & Importance (with C. Validation for the
missing sensitivity analysis).

## Anticipated Major Comment (how a reviewer will put it)

> The analysis reports a bootstrapped indirect effect and concludes that the exposure influences
> the outcome "through" the mediator. But exposure, mediator, and outcome are all measured at a
> single visit, so the design cannot establish the X → M → Y temporal sequence — the same data are
> equally consistent with the mediator preceding the exposure, with reverse causation, or with a
> shared common cause. The 5,000-sample bootstrap quantifies the sampling variability of the a×b
> product; it does not address whether the mediated effect is identified. Mediation additionally
> assumes no unmeasured mediator–outcome confounding, which is not plausible here and is not probed.
> Please reframe the indirect effect as association-level ("consistent with mediation"), state that
> a single-timepoint design cannot order the three variables, add a sensitivity analysis for
> unmeasured mediator–outcome confounding (e.g. an E-value for the indirect effect), and reserve the
> causal-mediation claim for a longitudinal design that measures the mediator before the outcome.

## Severity / category rationale

**Fatal** because the headline contribution *is* the causal chain, and the design cannot support it;
a reader could act on a mediation pathway that the data do not establish. The bootstrap CI is a
true result but answers the wrong question (precision, not identification). The fix is reframing +
a sensitivity analysis, not a new dataset — but the claim cannot stand as written.

## Fix

Down-scope every claim site (Abstract, Results, Discussion, Title) from "X affects Y through M" to
"the cross-sectional pattern is consistent with mediation by M." Add an unmeasured M–Y confounding
sensitivity analysis and report proportion-mediated with uncertainty (and only when the total effect
is well-estimated). Report against AGReMA. `fixable_by_ai: true` for the wording; the sensitivity
analysis is `requires_reanalysis` (route to `/analyze-stats`).

## R0-ready line

> R0-D1 (Major, Fatal): cross-sectional design but a causal mediation chain (X→M→Y) is claimed from
> a bootstrapped indirect effect — reframe to association-level, add an unmeasured M–Y-confounding
> sensitivity analysis, defer the causal claim to a longitudinal design. [probe: O13]
