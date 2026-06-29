# Health Economic Evaluation Analysis Guide

Comparing the **costs and consequences** of two or more interventions to inform a coverage,
adoption, or treatment decision. The headline — an **incremental cost-effectiveness ratio (ICER)**
— is arithmetically trivial; what fails review is **the structural choices behind it** (perspective,
time horizon, discounting, the effectiveness source, the cost basis, the model, and the propagation
of uncertainty). So the analysis is mostly the costing, the model, and the sensitivity suite, not the
ratio. This is the analysis-side companion to review probes **HE1–HE8** in
`health_economic_evaluation.md` and the **CHEERS 2022** reporting checklist.

---

## When to Use

- A comparative decision question (adopt / reimburse / treat) where both **cost** and **health
  outcome** differ between options: cost-effectiveness (CEA, natural units — life-years, events
  avoided), **cost-utility** (CUA, QALYs — the default for reimbursement), cost-benefit (CBA,
  monetised outcomes), cost-minimisation (only when outcomes are demonstrably equivalent), or
  **budget-impact** (affordability, distinct from cost-effectiveness).
- **Trial-based** (within-RCT patient-level costs and outcomes) or **decision-model-based** (decision
  tree for short horizons; **Markov / state-transition** or **discrete-event simulation** when timing
  and recurrence matter; lifetime horizons).
- NOT for: a costing/burden-of-illness description with no comparator (not an economic *evaluation*);
  asserting "cost-effective" from a point ICER with no uncertainty analysis; cost-minimisation when a
  non-inferiority outcome claim has not actually been established.

## Core quantities

- **Incremental cost** ΔC and **incremental effect** ΔE between an intervention and its comparator;
  the **ICER = ΔC / ΔE** (e.g. cost per QALY gained). With ≥3 options, rank by cost, remove
  **dominated** (more costly, less effective) and **extended-dominated** strategies, then compute
  ICERs sequentially along the efficient frontier.
- **Net benefit** at a willingness-to-pay threshold λ: **INMB = λ·ΔE − ΔC** (monetary) or
  **INHB = ΔE − ΔC/λ** (health). Net benefit is linear and avoids the ICER's quadrant ambiguity, so
  it is preferred for regression and for probabilistic summaries.
- **QALYs** = time × **utility** (preference-based, 0=dead, 1=full health) from a named instrument
  (EQ-5D-3L/5L, SF-6D, HUI) and a stated **value set/tariff** for the relevant country.

## The structural choices (state and justify each)

- **Perspective** — healthcare-system/payer vs **societal**; determines which costs count (societal
  adds productivity and informal-care costs). Apply it consistently.
- **Time horizon** — long enough to capture all differential costs and effects; **lifetime** for
  chronic disease or interventions with lasting effects. Extrapolation beyond trial data must be
  modelled explicitly (e.g. parametric survival extrapolation) and tested.
- **Discounting** — apply the jurisdiction's reference-case rate (commonly ~3% or 3.5%) to **both
  costs and outcomes**; sensitivity at alternative rates.
- **Costing** — report **resource quantities and unit costs separately**; state **currency, price
  year**, and inflation/currency conversion. Match cost categories to the perspective.
- **Model** — justify structure against natural history; state cycle length and half-cycle
  correction (Markov); validate (internal/face/external/predictive); test **structural** uncertainty
  via scenario analysis.

## Uncertainty (the analytic core)

- **Deterministic** — one-way and **tornado** diagrams to find the drivers; multi-way / scenario
  analyses for methodological and structural choices (discount rate, time horizon, alternative
  model structures).
- **Probabilistic (PSA)** — assign each uncertain parameter a **distribution** (beta for
  probabilities and utilities; gamma or log-normal for costs; Dirichlet for transition-probability
  sets), propagate by **Monte Carlo**, and report the **cost-effectiveness plane** (the cloud of ΔC,
  ΔE draws) and the **cost-effectiveness acceptability curve (CEAC)** — P(cost-effective) across a
  range of λ. Report results as net benefit at the relevant threshold with its uncertainty, not a
  bare point ICER.
- **Value of information** (EVPI/EVPPI) is an optional extension quantifying the expected cost of
  current decision uncertainty / the priority parameters for further research.

## Reporting & tools

- Report to **CHEERS 2022** (28 items): perspective, horizon, discount rate, currency/price year,
  model rationale, study parameters with distributions, disaggregated costs/outcomes, the ICER,
  and the uncertainty analysis (plane + CEAC). State the **willingness-to-pay threshold** and make
  the "cost-effective" conclusion conditional on it and on the CEAC probability.
- Tools: R — `heemod` / `dampack` / `hesim` (state-transition + PSA + CEAC), `BCEA` (Bayesian
  cost-effectiveness, CEAC/EVPI), `survival`/`flexsurv` (survival extrapolation); also TreeAge, or
  spreadsheet models with a documented PSA. Make the model or the health-economic analysis plan
  available for scrutiny.
- Companion review probes: **HE1–HE8** (`peer-review`/`self-review`
  `references/domain-probes/health_economic_evaluation.md`).
