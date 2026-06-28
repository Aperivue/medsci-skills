<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; a transitivity /
         incoherence / ranking-over-interpretation flaw is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# Network meta-analysis probes (NM1–NM8)

An 8-probe checklist for **network meta-analysis (NMA)** — a synthesis that compares three or more interventions simultaneously by combining **direct** (head-to-head) and **indirect** evidence across a network, and usually produces a **ranking** of interventions. These probes complement (do not replace) the pairwise SR/MA probes in `sr_ma.md` (which cover the search/screening/pooling that an NMA also needs), the PRISMA-NMA reporting items, and the **RoB-NMA** risk-of-bias tool; they target what NMA *adds* — the transitivity assumption, consistency between direct and indirect evidence, network geometry, ranking interpretation, and network-level certainty. NM1 (transitivity) and NM4 (ranking over-interpretation) are the highest-yield; run them first. For the pairwise-pooling machinery (heterogeneity model, publication bias mechanics, study-count thresholds) also apply `sr_ma.md`.

**NM1 — Transitivity (the foundational assumption)**:
- An NMA combines A-vs-C and B-vs-C trials to learn about A-vs-B indirectly; this is valid only if the **effect modifiers are distributed similarly across the comparisons** (transitivity / exchangeability). Did the authors **assess** transitivity — comparing the distribution of plausible effect modifiers (e.g., baseline severity, age, sex, dose, follow-up, year) across comparisons (box plots / distribution tables / meta-regression) — or merely assert it?
- Intransitivity (an effect modifier concentrated in one comparison) **invalidates the indirect comparisons**, and no statistical test fully substitutes for the clinical/epidemiological transitivity judgment.
- No transitivity assessment, or evidence of an imbalanced effect modifier left undiscussed, where indirect evidence drives a conclusion → MAJOR (request the effect-modifier distribution and a discussion of its impact).

**NM2 — Consistency / incoherence (direct vs indirect agreement)**:
- Transitivity's statistical footprint is **consistency**: direct and indirect estimates for the same comparison should agree. Was incoherence assessed both **globally** (design-by-treatment interaction model) and **locally** (node-splitting / loop-specific / back-calculation)?
- **A star network (no closed loops / no head-to-head comparisons) cannot be checked for incoherence at all** — the entire result then rests on the untestable transitivity assumption and must be flagged as such, not presented as if consistency were confirmed.
- Local inconsistency is often **driven by a single trial or loop** (excluding it can remove or reveal incoherence) — was the source of any inconsistency investigated rather than only reported as a global p value?
- No consistency assessment in a network with closed loops, or an unacknowledged star network presented as a validated comparison, or unexplained significant incoherence underlying a headline → MAJOR.

**NM3 — Network geometry & connectivity**:
- Is a **network plot** presented (nodes = treatments with size ∝ sample size/number of studies; edges = direct comparisons with thickness ∝ number of trials), so the reader can see where the evidence is thin?
- **Sparse edges (single-trial comparisons), a dominant node, or a poorly connected / disconnected network** make the indirect estimates fragile and the ranking unstable; comparisons supported by one small trial should not carry a strong claim. Is the connectivity discussed?
- A headline comparison resting on a single-study edge or a poorly connected network, presented with the same confidence as well-connected ones → MAJOR (or a prominent limitation).

**NM4 — Ranking over-interpretation (SUCRA / P-score / rankograms)**:
- Ranking metrics (**SUCRA**, **P-score**, rank probabilities, "probability best") are **easy to over-read**: a treatment can top the ranking on sparse or low-certainty evidence, the top rank is **not** a test of statistically significant superiority, and rankings are **unstable when the effect estimates are imprecise**. A small absolute difference can reorder ranks.
- Is the ranking interpreted **together with the effect estimates, their uncertainty, and the certainty of evidence** (e.g., a league table + CINeMA grades), rather than "Treatment X was best" headlined from SUCRA alone? Is it noted that ranking does not imply a clinically meaningful or significant difference from the runner-up?
- A "best treatment" conclusion driven by a ranking statistic, without the paired effect size / CI / certainty, → MAJOR (reframe to the magnitude and certainty of the actual comparisons).

**NM5 — Heterogeneity (common-τ² assumption)**:
- Is **between-study heterogeneity** reported (global τ² / heterogeneity rating), and is the usual **common (shared) heterogeneity assumption** across the network examined rather than assumed? Substantial heterogeneity undermines both the pooled estimates and the transitivity premise.
- High global heterogeneity with no exploration (subgroup / meta-regression / sensitivity), where it could explain the findings → MAJOR; pairwise heterogeneity mechanics carry over from `sr_ma.md`.

**NM6 — Certainty of network estimates (CINeMA / GRADE-NMA)**:
- Network certainty is assessed **per estimate**, not as one overall grade: **CINeMA / GRADE for NMA** rates each comparison across within-study bias, reporting bias, indirectness, imprecision, heterogeneity, and **incoherence**. Were estimate-level certainty grades reported, and were **indirect-only** comparisons downgraded appropriately?
- Conclusions must be **scaled to certainty** — a low/very-low-certainty network estimate cannot support a definitive "X is superior" claim. A uniform or absent certainty assessment, or conclusions that ignore low certainty, → MAJOR.

**NM7 — Publication / small-study bias**:
- For small-study/publication bias in a network, the appropriate tool is a **comparison-adjusted funnel plot** (with a pre-specified comparison ordering); standard funnel/Egger tests are uninformative with **< 10 studies** per comparison and should be reported as "suspected/not assessable" rather than "absent." Was small-study bias addressed at the network level?
- A claim of "no publication bias" from an underpowered or comparison-naive funnel analysis → MINOR–MAJOR depending on how load-bearing the affected comparisons are.

**NM8 — Component NMA additivity & interpretation/estimand**:
- For a **component NMA (cNMA)** that decomposes multicomponent interventions into component effects, the analysis assumes **additivity** of component effects (and often no interaction between components) — is this assumption stated and, where possible, checked (an interaction/full-interaction model)? An unstated additivity assumption can manufacture component "effects."
- Is the **reference/comparator and the estimand** clearly defined (relative effects via a league table; the chosen reference), and are conclusions kept within what the network supports (indirect, ranking-based, certainty-bounded) rather than translated into a definitive head-to-head clinical recommendation the trials never made?
- An unstated cNMA additivity assumption, an undefined reference/estimand, or a network-level result over-stated as direct comparative proof → MAJOR for the interpretation, MINOR for a reporting-only gap.

**Output template (NM1 example)**:
> "The conclusion that A is superior to B rests on indirect evidence (there are few or no head-to-head A-vs-B trials), so it depends on the transitivity assumption — that effect modifiers are distributed similarly across the A-vs-C and B-vs-C comparisons. I could not find an assessment of this: the distributions of likely effect modifiers (baseline severity, age, dose, follow-up) across comparisons are not shown. I'd suggest presenting those distributions (box plots or a table, and/or network meta-regression), assessing local and global incoherence where closed loops exist, and tempering the comparative claim if an effect modifier is imbalanced — because intransitivity, not sampling error, would then drive the indirect estimate."

**Output template (NM4 example)**:
> "The abstract leads with the SUCRA ranking ('Treatment X ranked best'). A SUCRA/P-score value is a summary of rank probabilities, not a test of superiority, and it is unstable when the underlying estimates are imprecise or based on sparse, low-certainty evidence; a treatment can rank first while its credible interval overlaps several others. I'd suggest reporting the ranking alongside the relative effect estimates and their intervals (a league table) and the CINeMA/GRADE certainty for the key comparisons, and reframing the conclusion around the magnitude and certainty of the X-vs-comparator difference rather than the rank position."
