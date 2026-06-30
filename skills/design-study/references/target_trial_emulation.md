# Target-trial emulation — design module

A target trial is the hypothetical randomized trial you would run if you could. Emulating
it with observational data is the discipline that turns an **association** into a
**defensible causal contrast** — the jump from a specialty paper to a high-impact one, and
the design that high-impact journals now expect for comparative observational questions
(treatment vs treatment, screening vs no screening, drug A vs drug B).

Use this when the question is causal/comparative on routinely-collected data (NHIS,
KNHANES, EHR, registry, health-checkup DB). It is **not** needed for a purely descriptive,
prevalence, or diagnostic-accuracy study.

## Protocol component table (fill every row before data extraction)

Specify all seven, then state how each is **emulated** in the data. Leaving a row blank is
where immortal-time, prevalent-user, and selection bias enter.

| # | Target-trial component | Specify | Emulation in the data |
|---|------------------------|---------|------------------------|
| 1 | **Eligibility criteria** | who could enroll (assessed using only information available at time zero) | the cohort filter; no criterion may use post-baseline information |
| 2 | **Treatment strategies** | the well-defined interventions being compared (dose, duration, start/stop rules) | how each strategy is identified from codes/prescriptions |
| 3 | **Assignment / treatment groups** | randomized in the target trial; here, assigned by observed strategy at time zero | new-user / active-comparator definition (below) |
| 4 | **Time zero (start of follow-up)** | the instant eligibility, treatment assignment, and follow-up **coincide** | the index date — must be identical for all three; misalignment ⇒ immortal-time bias |
| 5 | **Outcome** | the event, its ascertainment, and validation | code algorithm + (ideally) a validation reference |
| 6 | **Causal contrast** | ITT (assignment), per-protocol (sustained adherence), or as-treated | the estimand you report |
| 7 | **Analysis plan** | the model + confounding control + censoring weights | IPTW / g-methods / standardization; pre-specified covariates from a DAG |

## The three alignment errors this prevents

1. **Immortal-time bias.** Time zero must be the moment eligibility, strategy assignment,
   and follow-up start *coincide*. If a strategy is defined by something that can only
   happen after baseline (e.g., "patients who received ≥2 doses"), the period before that
   is immortal — survivors are guaranteed event-free. Fix: assign strategy using only
   information available at time zero; if a strategy needs a window to be met, use a
   **grace period** with cloning + censoring + weighting (below).
2. **Prevalent-user bias.** Including patients already on treatment at baseline conditions
   on having survived/tolerated it. Fix: **new-user (incident-user) design** — time zero =
   treatment initiation.
3. **Confounding by indication.** The reason a treatment was chosen also affects the
   outcome. Fix: **active comparator** (compare two treatments for the same indication, not
   treatment vs nothing) + a DAG-derived adjustment set (`dag_adjustment.md`), with IPTW
   or g-methods rather than a single outcome-regression adjustment.

## Grace period + clone-censor-weight (when a strategy needs a window)

When a strategy is "initiate within N days," a patient's data are consistent with *both*
strategies during the grace window. The standard emulation:
1. **Clone** each eligible person into both strategy arms at time zero.
2. **Censor** a clone when its data diverge from its assigned strategy (e.g., did not
   initiate within the grace period).
3. **Weight** by inverse probability of censoring to remove the selection introduced by
   artificial censoring.
This removes immortal-time bias without discarding the grace window. Report the grace
period and the censoring/weighting model explicitly.

## Estimand: ITT vs per-protocol

- **ITT (assignment) effect** — robust (assignment is as-randomized-as-emulated) but
  diluted by non-adherence; the conservative primary for most emulations.
- **Per-protocol effect** — the effect of *sustained* adherence; needs IP-weighting for
  adherence-related time-varying confounding (a naive per-protocol analysis re-introduces
  selection bias). State which is primary and why.

## Negative controls (falsification)

Pre-specify at least one **negative-control outcome** (an outcome the exposure cannot
plausibly cause through the hypothesized mechanism) and, where possible, a **negative-control
exposure**. A non-null association on a negative control flags residual confounding /
design bias and bounds the credibility of the primary estimate. Report them alongside the
primary result, not only when convenient.

## Reporting + registration

- Report against **STROBE** (+ RECORD for routinely-collected data); state the target-trial
  protocol table in the Methods or a supplement.
- For comparative-effectiveness emulations, pre-register the protocol (the seven components
  above) — a registered target-trial protocol is the strongest defense against post-hoc
  design choices.

## Handoff

- Adjustment set → `references/dag_adjustment.md` + `scripts/adjustment_set_helper.py`.
- Time-origin / survivorship structural checks → design-study Phase 2 §F.
- Analysis (IPTW, g-methods, marginal structural models) → `/analyze-stats`.
- Sample size for the emulated trial → `/calc-sample-size`.

## References (canonical — cite the originals, do not paraphrase as your own)

- Hernán MA, Robins JM. Using big data to emulate a target trial when a randomized trial
  is not available. *Am J Epidemiol* 2016.
- Hernán MA, Sauer BC, Robins JM, et al. Specifying a target trial prevents immortal time
  bias and other self-inflicted injuries in observational analyses. *J Clin Epidemiol* 2016.
- Hernán MA, Wang W, Leaf DE. Target trial emulation: a framework for causal inference from
  observational data. *JAMA* 2022.
