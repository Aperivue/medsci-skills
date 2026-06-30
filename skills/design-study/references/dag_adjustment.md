# DAG-based confounder adjustment-set selection

Pre-specify the adjustment set from a **causal DAG**, not from a Table-1 `p<0.05` screen.
A p-value screen adjusts for mediators and colliders (which *introduce* bias) and misses
confounders that happen to be balanced by chance — the single most common
confounding-completeness error reviewers reject.

## The backdoor criterion (what a sufficient set must do)

A set **Z** identifies the causal effect of X on Y if:
1. **Z blocks every backdoor path** (every path from X to Y that starts with an arrow into
   X), and
2. **Z contains no descendant of X** (adjusting for a descendant of the exposure is
   over-adjustment / collider-stratification).

Three roles drive every decision:

- **Confounder (common cause)** — has a path into X *and* an X-free path to Y. **Adjust.**
- **Mediator** — lies on a directed `X → … → Y` path. **Do not adjust** (it is part of the
  effect you want).
- **Collider** — a node with two arrows into it (`A → C ← B`). **Do not adjust** (and do
  not adjust its descendants): conditioning on a collider *opens* a non-causal path (M-bias).

Note: because `X → Y` makes every ancestor of X also an ancestor of Y, "common cause" is
**not** simply "ancestor of both." A node that affects Y *only through* X (an
instrument-like `A → X → Y`) is not a confounder — omitting it is not bias. A confounder
needs a path to Y that does **not** pass through X.

## Step 1 — draw the DAG, then sanity-check covariate roles deterministically

Write the DAG as parent→child edges and run the helper to classify each proposed covariate
and catch the four unambiguous errors before you write the Methods:

```bash
# dag.json: {"edges": [["age","statin"], ["age","CVD"], ["statin","LDL"], ["LDL","CVD"], ["statin","CVD"]]}
python3 scripts/adjustment_set_helper.py \
  --dag dag.json --exposure statin --outcome CVD \
  --adjust "age,LDL" --out qc/adjustment_set.json --strict
```

It flags `MEDIATOR_ADJUSTMENT` (here `LDL`, on `statin→LDL→CVD`),
`DESCENDANT_ADJUSTMENT`, `COLLIDER_ADJUSTMENT`, and `CONFOUNDER_OMITTED`, and prints a
**candidate** sufficient set (the open-backdoor common causes). The helper uses
reachability only and **does not claim minimality** — it catches the errors, not the
optimum.

## Step 2 — derive the minimal sufficient set with dagitty (the validated solver)

For the **minimal** adjustment set (and to verify sufficiency by d-separation), use
`dagitty` — do not hand-roll a d-separation solver. Generate and run:

```r
library(dagitty)
g <- dagitty('dag {
  age -> statin; age -> CVD
  statin -> LDL; LDL -> CVD
  statin -> CVD
}')
exposures(g) <- "statin"; outcomes(g) <- "CVD"
adjustmentSets(g, type = "minimal")     # the minimal sufficient set(s)
adjustmentSets(g, type = "canonical")   # the all-common-causes set
# Falsification: testable conditional independencies implied by the DAG
impliedConditionalIndependencies(g)
```

`ggdag::ggdag_adjustment_set(g)` renders the DAG with the adjustment set highlighted for a
supplement figure. Report the DAG (or its dagitty string) in the supplement so reviewers
can audit the identification assumptions.

## Step 3 — report

- State the adjustment set **and its DAG-based justification** in Methods (not "covariates
  with p<0.05").
- Pre-specify it before looking at outcome associations.
- Plan an **extended-adjustment sensitivity** model: if a measured covariate turns out
  imbalanced by exposure but sits outside the adjustment set, show the primary estimate is
  robust to adding it (`/self-review` Phase 2.5e + `observational_confounding.md` O1–O14
  check this at review time).
- Unmeasured confounding that remains → report an **E-value**.

## Handoff

- Target-trial / comparative design → `references/target_trial_emulation.md`.
- Estimation (IPTW, g-methods, standardization) + E-value → `/analyze-stats`.
- Review-time confounding completeness → `/self-review` Phase 2.5e, `observational_confounding.md`.

## References (cite the originals)

- Greenland S, Pearl J, Robins JM. Causal diagrams for epidemiologic research.
  *Epidemiology* 1999.
- Textor J, van der Zander B, Gilthorpe MS, et al. Robust causal inference using directed
  acyclic graphs: the R package 'dagitty'. *Int J Epidemiol* 2016.
- VanderWeele TJ. Principles of confounder selection. *Eur J Epidemiol* 2019.
