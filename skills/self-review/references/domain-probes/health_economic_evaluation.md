<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; a
         perspective/time-horizon/uncertainty/ICER-interpretation flaw is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# Health economic evaluation probes (HE1–HE8)

An 8-probe checklist for **health economic evaluations** — comparative analyses of the costs and consequences of two or more options: cost-effectiveness (CEA), cost-utility (CUA, QALY-based), cost-benefit (CBA), cost-minimisation, and budget-impact/HTA analyses, whether **trial-based** or **decision-model-based** (decision tree, Markov/state-transition, discrete-event simulation). These probes complement (do not replace) the generic Phase 2 checklist and the **CHEERS 2022** reporting items; they target the gap between a clean-looking incremental cost-effectiveness ratio (ICER) and whether the structural choices that produced it — perspective, time horizon, discounting, the effectiveness source, the cost basis, the model, and the handling of uncertainty — are defensible. Because the headline number is a single ratio that a reader cannot reproduce from the manuscript, the burden is on the study to *evidence* each structural choice, not assert it. HE2 (time horizon & discounting), HE5 (model structure), and HE6 (uncertainty / probabilistic sensitivity analysis) are the highest-yield; run them first.

**HE1 — Decision problem, comparators, and perspective**:
- Is the decision/policy question explicit, and are **all relevant comparators** included — the current standard of care and, where appropriate, a do-nothing/usual-care arm — rather than a convenient or obsolete comparator that flatters the new intervention? Omitting the true standard of care is the most common way to manufacture a favourable ICER.
- Is the **analytic perspective** stated (healthcare-system / payer vs **societal**) and justified, and is it applied consistently to what is counted (HE4)? A "societal" claim that omits productivity and informal-care costs — or a payer analysis that smuggles in societal costs — is an internal inconsistency.
- A missing/obsolete comparator, an unstated perspective, or a perspective inconsistent with the costs counted → MAJOR.

**HE2 — Time horizon and discounting**:
- Is the **time horizon** long enough to capture all material differential costs and health effects? For a chronic disease or a one-off intervention with lifelong consequences, a **lifetime horizon** is usually required; a horizon truncated to trial follow-up flatters whichever arm has earlier benefit and hides downstream costs.
- Are **both costs and outcomes discounted** at a stated, justified rate (with the jurisdiction's reference-case rate used and a sensitivity at alternative rates)? Discounting only costs, or not discounting a multi-year horizon at all, biases the ICER.
- A truncated horizon with no extrapolation justification, undiscounted long-horizon results, or asymmetric discounting → MAJOR.

**HE3 — Effectiveness source and outcome valuation**:
- Where do the **effectiveness/relative-effect estimates** come from — a head-to-head RCT or meta-analysis, or a weaker source (single-arm, naive indirect comparison, observational) — and is that source appropriate and its uncertainty carried into the model (HE6)? A model driven by an optimistic point estimate from a weak source is not rescued by elegant modelling.
- For a **cost-utility analysis**, are **QALYs** built from a **named preference-based instrument** (e.g. EQ-5D-5L) and a stated **value set / tariff** for the relevant population, rather than ad-hoc or mapped utilities with the mapping undisclosed?
- A weak/again-mismatched effectiveness source, or QALYs with no stated utility instrument/value set → MAJOR (or a prominent limitation if the source is the best available and is treated as uncertain).

**HE4 — Costs, resource use, currency, and price year**:
- Are **resource quantities and unit costs reported separately** (so a reader can re-value for another setting), and are the cost categories **consistent with the stated perspective** (HE1)?
- Are the **currency, price (cost) year, and any inflation/currency-conversion method** stated? Costs pooled across years or countries without a stated price year and conversion are not interpretable or transferable.
- Missing price year, perspective-inconsistent cost categories, or undisclosed resource-vs-unit-cost bundling → MAJOR.

**HE5 — Model structure, assumptions, and validation**:
- If **model-based**, is the model **type and structure** (states/events, cycle length, half-cycle correction for a Markov model) described and **justified** against the disease's natural history, rather than chosen for convenience? Is **structural uncertainty** acknowledged (alternative plausible structures), and was the model **validated** (internal consistency, and external/predictive validation where data exist)?
- Are key **structural assumptions and extrapolation** beyond the data (e.g. survival curve extrapolation, treatment-effect waning) declared and tested?
- An unjustified structure, undeclared extrapolation, or no validation/structural-sensitivity → MAJOR (the structure can drive the ICER more than any single parameter).

**HE6 — Uncertainty: deterministic AND probabilistic**:
- Is **parameter uncertainty** characterised by a **probabilistic sensitivity analysis (PSA)** — every uncertain input assigned a distribution and propagated by Monte Carlo — and reported as a **cost-effectiveness plane** and **cost-effectiveness acceptability curve (CEAC)**, not just a deterministic point ICER? Are **one-way / tornado** analyses used to identify the drivers, and **scenario analyses** for non-parametric (structural/methodological) uncertainty?
- Are the parameter **distributions justified** (beta for probabilities/utilities, gamma/log-normal for costs) rather than arbitrary ±20% ranges presented as if probabilistic?
- A single deterministic ICER with **no PSA**, or "sensitivity analysis" that is one-way only with no probabilistic component → MAJOR.

**HE7 — Results presentation and ICER interpretation**:
- Are **incremental costs and incremental effects reported separately** (and ideally a disaggregated cost/outcome table), not only the ratio? Are **dominance and extended dominance** correctly identified and dominated strategies excluded before computing ICERs?
- Is the ICER interpreted against a **stated, justified cost-effectiveness threshold (willingness-to-pay)** appropriate to the jurisdiction — not an arbitrary or post-hoc threshold — and is the conclusion ("cost-effective") conditional on that threshold and the uncertainty (CEAC probability), rather than asserted from the point estimate alone? Net monetary/health benefit (INMB/INHB) is a clearer alternative at a given threshold.
- An ICER reported without incrementals, mishandled dominance, or a "cost-effective" claim with no threshold context or ignoring the CEAC → MAJOR.

**HE8 — Equity, generalisability, funding/COI, and CHEERS reporting**:
- Are **distributional/equity effects** considered where relevant (who bears the costs and gains the health), and is **generalisability/transferability** to other settings or jurisdictions discussed (cost and epidemiology transfer, not just clinical effect)?
- Are **funding source and the funder's role** and **conflicts of interest** disclosed? An industry-funded evaluation whose ICER sits just below the threshold and is insensitive to plausible assumptions warrants heightened scrutiny of the structural choices (HE1–HE5).
- Is reporting mapped to **CHEERS 2022**, and is the model / health-economic analysis plan available for scrutiny?
- No generalisability discussion for a single-jurisdiction model presented as broadly applicable, or undisclosed funder role on a threshold-hugging result → MAJOR (funding/COI) / MINOR (generalisability), per centrality.
