# Challenge card — DAG-based adjustment-set selection (design-study)

## Problem
design-study (and the confounding-completeness rule) tell authors to "pre-specify the
adjustment set from a DAG, not a Table-1 p<0.05 rule" — but shipped **no scaffold** to do
it, so the adjustment set stays ad-hoc and the recurrent reviewer-rejection errors slip
through: adjusting for a **mediator** (removes part of the causal effect), a **descendant**
of the exposure (over-adjustment), a **collider** (opens M-bias), or **omitting a common
cause** (leaves a backdoor open).

## What the helper does
`scripts/adjustment_set_helper.py` takes a causal DAG, an exposure, an outcome, and a
*proposed* adjustment set, and deterministically classifies each covariate by its DAG role
(reachability only — no fuzzy heuristics), flagging `MEDIATOR_ADJUSTMENT`,
`DESCENDANT_ADJUSTMENT`, `COLLIDER_ADJUSTMENT`, and `CONFOUNDER_OMITTED`. It proposes the
pre-exposure common-cause set as a *candidate* backdoor adjustment set and defers the
**minimal** sufficient set to dagitty (a validated tool) — it never claims minimality and
never implements a homegrown d-separation solver whose subtle errors would ship to users.

A confounder is defined soundly as a common cause with a path to the outcome **that does
not pass through the exposure** (an open backdoor); because `X→Y` makes every ancestor of
X an ancestor of Y, a naive `ancestors(X) ∩ ancestors(Y)` would mis-flag an instrument-like
`A→X→Y` ancestor as an omitted confounder. The instrument fixture locks that fix.

An omitted common cause is flagged only when its backdoor fork survives the adjustment set:
it still reaches X, and still reaches Y by an X-free directed path, once the adjusted nodes
are removed. Adjusting a measured node on the confounder→outcome path (`C→D→Y`, adjust `D`)
blocks it, and that set is valid by the backdoor criterion; the proxy fixture locks this.
An adjusted node with two or more unadjusted parents is not trusted as a blocker, because
conditioning on it joins its parents; the butterfly fixture locks that guard.

## Fixtures (synthetic canonical DAGs — no data)
- `confounder.json` — `C→X, C→Y, X→Y` (classic confounding).
- `mediator.json` — `X→M→Y, X→Y` (mediation).
- `mbias.json` — `Z1→X, Z1→C, Z2→C, Z2→Y, X→Y` (C is a collider; M-bias).
- `instrument.json` — `A→X→Y` (instrument-like ancestor; **not** a confounder).
- `proxy.json` — `C→X, C→D→Y, X→Y` (`{D}` is sufficient; dagitty `isAdjustmentSet` = TRUE).
- `butterfly.json` — `C→X, C→D, U→D, U→Y, D→Y, X→Y` (`{D}` opens `X←C→D←U→Y`;
  dagitty `isAdjustmentSet` = FALSE).

## Expected (`verify.sh`, network-free)
- confounder + adjust `C` → clean; confounder + adjust `∅` → `CONFOUNDER_OMITTED`.
- mediator + adjust `M` → `MEDIATOR_ADJUSTMENT`.
- mbias + adjust `C` → `COLLIDER_ADJUSTMENT`, and **no** `CONFOUNDER_OMITTED`.
- instrument + adjust `∅` → clean, and **no** `CONFOUNDER_OMITTED` (the soundness fix).
- proxy + adjust `D` → clean; proxy + adjust `∅` → `CONFOUNDER_OMITTED`.
- butterfly + adjust `D` → `CONFOUNDER_OMITTED` (`C` stays open through the collider at `D`).
