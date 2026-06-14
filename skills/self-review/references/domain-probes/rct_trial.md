<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; a design-level
         flaw (concealment, unblinding, non-ITT primary) is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# RCT / Intervention-Trial probes (RC0–RC7)

A checklist for **randomised controlled trials** (parallel-group, crossover, cluster, stepped-wedge) where the claim is that an intervention *causes* an outcome difference. These probes complement (do not replace) the generic Phase 2 issue checklist and the CONSORT reporting items; they target the threats randomisation is supposed to remove but reporting can hide. Run RC0 first.

**RC0 — Registration & pre-specified-primary gate (run before RC1–RC7)**:
- Find the trial registration (ClinicalTrials.gov / ISRCTN / registry ID) and the **pre-specified primary outcome + timepoint**. If absent, that is itself a MAJOR (prospective registration is a baseline expectation for a trial).
- Compare the registered primary to the **reported** primary. A switch (a registered secondary reported as primary, the registered primary demoted/dropped, the timepoint/metric changed) without a dated, justified amendment is a MAJOR — see `exemplar_reviews/selective_outcome_reporting.md`.

**RC1 — Randomisation sequence + allocation concealment**:
- Is the **sequence generation** described (computer random, blocked, stratified) and, separately, is **allocation concealment** described (central/pharmacy randomisation, sequentially-numbered opaque sealed envelopes)? These are different items; concealment prevents foreknowledge of the next assignment.
- Inadequate or unstated concealment → selection bias the analysis cannot fix → MAJOR (or a request to clarify if merely under-reported).

**RC2 — Blinding & functional unblinding**:
- State **who** was blinded (participants, providers, outcome assessors, analysts). For a **subjective primary outcome**, outcome-assessor (or self-report) blinding is critical.
- **Functional unblinding**: even a nominally blinded trial can be effectively unblinded when the active arm produces unmistakable effects (a drug with obvious side-effects, an arm with a different experience/intensity) — flag this when the design implies it, and ask for any blinding-success check (guess-the-arm). An open-label trial with a subjective outcome is a MAJOR interpretive limit, not a footnote.

**RC3 — ITT primary + missing-data handling**:
- Is the **primary analysis intention-to-treat** (all randomised, as randomised)? A per-protocol or completers-only primary breaks randomisation and is a MAJOR; per-protocol belongs as a **sensitivity** analysis.
- How were dropouts/missing data handled? Prefer a principled approach (mixed models under MAR, multiple imputation) over **LOCF/single-imputation**; the missing-data assumption should be stated and probed. High or differential attrition without this → MAJOR.

**RC4 — Multiplicity & outcome hierarchy**:
- One pre-specified primary; secondaries and subgroups handled for **multiplicity** (the analysis plan states the correction) — and a "significant" secondary that does not survive correction is reported as such, not spun as a headline.
- Unplanned subgroup claims, or a forest of secondary p-values mined for significance, → MAJOR when they drive the conclusion; otherwise a request to label them exploratory.

**RC5 — Baseline comparability (no baseline significance testing)**:
- Table 1 by arm should show the groups are comparable. **Do not run baseline significance tests** — randomisation guarantees exchangeability *in expectation*, so a baseline p-value tests a null the design already makes true and any imbalance is chance; the test is uninformative. Flag a manuscript that reports baseline p-values (MINOR) and, more importantly, one that uses "baseline p > 0.05" to *justify* not adjusting.
- A **notable imbalance** on a prognostic covariate (chance, in a small trial) warrants a **pre-specified adjusted** analysis as sensitivity — request it rather than reading the unadjusted estimate as definitive.

**RC6 — Early stopping & interim analyses**:
- If the trial **stopped early for benefit**, were there pre-specified stopping rules with an alpha-spending function? Trials stopped early for benefit **overestimate** the effect — the estimate needs that caveat. Unplanned interim looks that informed stopping → MAJOR.

**RC7 — Power, pilot framing & estimand**:
- Is there an a-priori **sample-size / power** calculation tied to the primary, or is the trial an explicit **pilot/feasibility** study? A small pilot must be framed as hypothesis-generating, not confirmatory — a definitive efficacy claim from an underpowered trial is a MAJOR over-reach.
- Is the **estimand** clear (the contrast, population, and handling of intercurrent events — treatment discontinuation, rescue medication)?

## AI-trial reporting-flow probes (CONSORT-AI / SPIRIT-AI, A1–A5)

Co-apply when the trial's intervention **includes an AI/ML component** — the reporting axis is then CONSORT-AI (completed-trial report) or SPIRIT-AI (protocol), on top of base CONSORT/SPIRIT. These probe what randomisation cannot protect: whether the AI was specified, used, and monitored as it would be in practice. Name the base instrument and the AI extension, and cite each.

**A1 — Algorithm version + lock**:
- Is the exact **AI algorithm version** stated, and was it **locked** for the trial (no mid-trial retraining/updating)? A trial result tied to an unspecified or silently-updated model is not interpretable or reproducible. Undefined/changed version → MAJOR.

**A2 — Input-data eligibility + poor-input handling**:
- Are the **input-data** inclusion/exclusion criteria stated **separately** from participant eligibility (a trial can enrol eligible patients yet feed the AI out-of-distribution inputs)? Is the handling of **poor-quality or unavailable inputs** specified? Missing input-data eligibility or undefined poor-input handling → MAJOR (the evaluated population is undefined, and silent failures bias the result).

**A3 — Human–AI interaction + decision pathway**:
- Is the **human–AI interaction** described (autonomous vs assistive), with the **expertise required of the user**, and is it explained **how the AI output fed the clinical decision** (5(vi)/11a(vi))? This determines whether the trial evaluated the AI *as used in practice*. A bare "the model assisted clinicians" with no interaction/decision detail → MAJOR interpretive gap.

**A4 — Performance-error analysis + safety monitoring**:
- Are **performance errors** analysed (CONSORT-AI item 19) — or, for a protocol, is there a **plan to identify and analyse them** (SPIRIT-AI item 22)? AI-specific harms (systematic failure on a subgroup, distribution shift during the trial) live here. Absent error analysis/plan where the design permits → MAJOR.

**A5 — Setting integration + code/intervention accessibility**:
- Are the **onsite/offsite integration** requirements described (how the AI was embedded in the trial setting), and is the **intervention/code accessibility** stated (with restrictions)? Opaque integration or undisclosed accessibility limits reproducibility and external validity → minor–MAJOR depending on the claim.

**Output template (RC2 / RC3 example)**:
> "The trial is described as blinded, but the active intervention produces [obvious effects] and the comparator arm undergoes [a different experience], so participants were likely **functionally unblinded** ([Methods]); with a self-reported primary outcome this is a real interpretive limit. I'd suggest reporting any blinding-success assessment and tempering the causal language accordingly. Relatedly, the primary analysis appears to be [per-protocol / completers]; because that breaks the randomisation, I'd suggest making the **intention-to-treat** analysis (all randomised) the primary, with per-protocol as a sensitivity analysis, and stating the missing-data assumption and method (e.g., a mixed model under MAR rather than LOCF)."

**Discipline — leads vs findings (applies to RC0–RC7)**:
- A concealment/blinding/ITT concern surfaced by a quick scan is a **lead until the Methods and the CONSORT flow are read together** — distinguish under-reporting (ask to clarify) from a true design flaw (MAJOR).
- Anchor every comment to the exact item (sequence vs concealment; ITT vs per-protocol; registered vs reported primary) and the location. "The trial is biased" is not actionable; "the primary analysis is per-protocol, which breaks randomisation (Methods, Statistical analysis)" is.
- Keep severity tied to what the flaw *does*: a broken-randomisation primary, unconcealed allocation, or an open-label subjective outcome is design-level (MAJOR, often Major #1); a reported baseline p-value is MINOR.
