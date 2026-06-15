# Exemplar Anticipated Comments — gate result → self-review finding

`/self-review` runs deterministic Phase 2.5 gates (cohort arithmetic, confounding
completeness, scope coherence, claim-vs-artifact) and a systematic A–K check, then writes
**Anticipated Major / Minor Comments** the author can fix before a reviewer sees them. This
directory models how a *gate hit* becomes a well-formed Anticipated Comment — the missing
worked-example layer between "the gate fired" and "here is the comment + fix."

Each file shows the same shape `/self-review` Phase 3 produces:

1. **What fired** — the deterministic gate (or category) and the specific signal.
2. **Anticipated Major/Minor Comment** — phrased the way the *reviewer* will phrase it, so
   the author reads it as the warning it is.
3. **Severity** — Fatal (conclusion-threatening / design-level → Anticipated **Major**) vs
   Fixable (reporting-level → Anticipated **Minor**).
4. **Category** — the closest letter (A–K).
5. **Fix** — the concrete change to make now, and whether it is `fixable_by_ai`.
6. **R0-ready** — a one-line form suitable for Phase 3b numbering into the `/revise`
   pipeline.

These differ from `/peer-review`'s `exemplar_reviews/`: those model a *reviewer's*
partner-voice comment to authors; these model the *author's* anticipation-and-fix entry.

## Contents

- `cohort_arithmetic_mismatch.md` — STROBE cascade / rate back-calc fails (gate:
  `check_cohort_arithmetic.py`) → category A.
- `unadjusted_confounder.md` — an imbalanced measured covariate left out of the model
  (gate: `check_confounding_completeness.py`) → category C/E.
- `over_adjustment_collider.md` — the opposite failure: a consequence/mediator of the outcome
  wrongly inside the model (probe: O7) → category C, `requires_reanalysis`.
- `prediction_two_null_conflation.md` — a "negative" prediction study merging a well-powered
  incremental-value null with an underpowered marginal-effect null, plus apparent (uncorrected)
  calibration/DCA (probes: CP1/CP2) → category C/D.
- `scope_overreach_cross_sectional.md` — a prognostic/surveillance claim from a
  cross-sectional design (gate: `check_scope_coherence.py`) → category D.
- `estimand_drift_posthoc_primary.md` — the reported "primary" differs from the registered
  one (gate: `check_claim_artifact.py`) → category C.

## Curator guidelines

- **Synthetic only.** Author the example with placeholder numbers; never paste a real
  manuscript's text or data. No PII, no real citations, English only.
- **One gate/finding per file**, end to end (fired → comment → severity → category → fix →
  R0 line).
- **Tie severity to the same Fatal/Fixable rule** the skill uses, and name the gate/script
  that surfaces it (do not re-document the gate — link by name).
- Keep each file ~40–70 lines.
