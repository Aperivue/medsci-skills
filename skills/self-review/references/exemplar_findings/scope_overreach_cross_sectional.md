# Exemplar — a prognostic/surveillance claim from a cross-sectional design

**Fired:** `check_scope_coherence.py` — `CROSS_SECTIONAL_PROGNOSTIC` (a single-timepoint /
cross-sectional design signal co-occurs with a conclusion-region action verb such as
"predict", "progression", "rescreen", "surveillance").
**Severity:** Fatal → Anticipated **Major**. **Category:** D. Clinical Framing & Importance.

## Anticipated Major Comment (how a reviewer will put it)

> The study is cross-sectional — exposure and outcome are measured at a single visit
> (Methods, *Study design*) — but the Conclusion recommends a "surveillance interval" and
> describes "disease progression." A cross-sectional association cannot establish temporal
> order or progression, so these claims outrun the design. Please reframe the conclusion to
> the association actually estimated (e.g., "X was associated with Y at the index visit") and
> move any prognostic or surveillance language to a clearly-labeled hypothesis for future
> longitudinal work.

## Severity / category rationale

This is **Fatal** because the gap is between the *design* and the *clinical action the paper
recommends* — a reader could adopt a surveillance schedule that the data do not support. The
fix is reframing, not new analysis, but the claim cannot stand as written. **Category D**
(framing / endpoint↔conclusion scope).

## Fix

Rewrite the Abstract Conclusion and the Discussion's closing claim to the cross-sectional
estimand; demote prognostic/surveillance statements to "future directions." Check that the
Title does not imply prediction. `fixable_by_ai: true` (wording), but verify the author
agrees the longitudinal claim is genuinely unsupported before softening.

## R0-ready line

> R0-D1 (Major, Fatal): cross-sectional design but the Conclusion claims surveillance/
> progression; reframe to the index-visit association. [gate: check_scope_coherence]
