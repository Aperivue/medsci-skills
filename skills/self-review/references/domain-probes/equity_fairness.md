<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; a task- or
         design-level flaw is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# Fairness / Equity / Subgroup-performance probes (EQ0–EQ6)

A 7-probe checklist for **AI/ML, prediction, or diagnostic studies that make (or imply) a claim about
performance across a heterogeneous population** — generalizable / deployment-ready / "works for
patients" claims, or studies that present **subgroup analyses as evidence of fairness or equity**.
These probes complement (do not replace) the generic Phase 2 issue checklist, the AI-overclaiming
probes (`ai_overclaiming.md`, with which EQ co-applies), the prediction-model probes
(`clinical_prediction_model.md`, whose EPV logic EQ5 reuses), and the reporting items in TRIPOD+AI,
DECIDE-AI, and CONSORT-AI. They target one recurring failure: an aggregate performance number, or an
eyeballed "similar across groups" statement, presented as evidence that a model is *equitable* or
*broadly deployable*.

**EQ0 — Applicability gate (apply only when a cross-population claim is made)**:
- Apply EQ1–EQ6 when the manuscript claims (or its framing implies) that the model/score/test
  performs adequately across a heterogeneous population, **or** reports subgroup analyses as a
  fairness/equity argument.
- Do **not** fire these probes on a study that explicitly **scopes its claim to a single,
  well-defined population** and does not generalise beyond it — there, the right probe is scope
  coherence (the conclusion must stay within the evaluated population), not a fairness audit.

**EQ1 — Disaggregated subgroup performance, not aggregate-only**:
- An overall AUC / sensitivity / specificity / calibration is **not** evidence of per-subgroup
  performance — it can hide large, offsetting subgroup gaps. A broad-applicability or deployment
  claim requires **disaggregated** metrics, with confidence intervals, for **pre-specified**
  subgroups defined by clinically and (where collected and appropriate) socially relevant attributes
  (e.g. age band, sex, acquisition site / scanner / vendor, and protected attributes when available).
- Reporting only the pooled metric while claiming the model works "across patients" / "in practice"
  → MAJOR. Reporting per-subgroup point estimates **without CIs**, so the reader cannot tell a real
  gap from noise → MINOR.

**EQ2 — Error-rate parity ≠ discrimination parity; base-rate dependence**:
- Equal **AUC** across groups does not imply equal **sensitivity/specificity** at the operating
  threshold, nor equal **PPV/NPV** — and a *single* threshold applied across subgroups with different
  outcome prevalence yields different error trade-offs by construction. "Discrimination is similar,
  therefore the model is fair" conflates two different fairness criteria.
- The probe asks for the metric that drives the **deployment harm** (often the subgroup
  false-negative rate, or PPV at the decision threshold), not just AUC parity. A fairness claim
  resting on AUC parity alone, with the threshold-dependent error rates unreported or unequal →
  MAJOR.

**EQ3 — A fairness claim needs a named estimand + a gap test, not eyeballed point estimates**:
- "Performance was similar across groups" is an estimand-free assertion. If fairness is claimed, the
  manuscript must (a) **name the fairness criterion** — error-rate parity / calibration-within-groups
  / equalized odds — recognising that these can **mathematically conflict** and cannot all hold at
  once when base rates differ; (b) report the **between-group gap with a confidence interval** and a
  test, not overlapping point estimates; and (c) ideally pre-specify it.
- A parity conclusion read off non-overlapping-looking point estimates with no gap CI / test →
  MAJOR (eyeballed/data-mined parity). A reported gap that was **not pre-specified** and is selected
  post hoc among several metrics → MINOR (disclose as exploratory).

**EQ4 — Development-cohort representativeness vs the deployment population**:
- Report the demographic / site composition of the **derivation (training) data**. A subgroup that
  is **small or absent** in development cannot be claimed to generalise to it, regardless of the
  pooled test metric; and **including an attribute as a covariate is not the same as validating
  performance within that stratum**.
- A deployment / "generalisable to [population]" claim for a subgroup that is unrepresented or
  trivially small in the development data → MAJOR. Composition simply not reported → MINOR (it is a
  required disclosure under TRIPOD+AI).

**EQ5 — Subgroup power / events-per-variable for the fairness comparison**:
- A "**no disparity**" conclusion drawn from subgroups with **few events** is underpowered — the same
  separation/instability problem the prediction-model EPV probe (CP3) raises. A fairness **null**
  needs the between-group gap CI to **exclude a clinically relevant difference**; a wide CI that still
  admits a meaningful gap is "we could not detect a disparity," not "the model is equitable."
- Subgroup comparisons with EPV in the low single digits, presented as evidence of fairness → MAJOR
  (overclaim); the comparison should be **descriptive-only**. EPV / event counts per subgroup not
  reported → MINOR.

**EQ6 — Equity-aware framing + guideline alignment; a limitation is not an endorsement**:
- Scope the conclusion to the **populations actually evaluated**, and align reporting to **TRIPOD+AI**
  (fairness / subgroup-performance and training-data composition items), **DECIDE-AI**, and
  **CONSORT-AI** (pre-specified subgroup analyses). A known fairness **limitation** (untested
  subgroup, unequal error rate, unrepresentative training data) must **not** be converted into a
  deployment endorsement or a recommendation-grade equity claim.
- Recommendation-grade equity language ("equitable", "fair across groups", "ready for diverse
  populations") that the evidence does not support, or a conclusion that silently generalises past
  the evaluated subgroups → MAJOR. Cross-link `~/.claude/rules/scope-coherence-gate.md`: an aggregate
  or single-population claim cannot stand on subgroup-silent data.

---

**Output mapping.** In **peer-review**, map each finding to a Major / Minor comment; EQ1
(aggregate-only performance behind a deployment claim), EQ2 (AUC-parity-only fairness claim), and EQ4
(deployment claim for an unrepresented subgroup) are **design-level** — surface them in the
Confidential Comments to the Editor and place the strongest as the Major #1 candidate. EQ4 and an
EQ5 underpowered-null overclaim are frequently **unfixable in the current data** (the missing
subgroup or events cannot be added in revision) and govern the recommendation per Phase 2F. In
**self-review**, a design-level EQ finding becomes a **Fatal** Anticipated Major Comment and a
reporting-level one a **Fixable** Anticipated Minor Comment, tagged with the closest category letter.
EQ co-applies with `ai_overclaiming.md` (a fairness gap is one route to an over-broad clinical claim)
and reuses the EPV logic of `clinical_prediction_model.md` (CP3) at the subgroup level.
