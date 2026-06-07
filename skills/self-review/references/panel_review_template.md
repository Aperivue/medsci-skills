# Panel Review Template (Phase 2.6)

Reusable scaffolding for the multi-agent panel: a reviewer output schema, a
generic reviewer prompt skeleton with per-domain focus checklists, and an
editor synthesis prompt skeleton. This is a template, not a runtime program —
it carries no manuscript-specific content. Fill the `{...}` placeholders from
the manuscript under review and from the reviewer-set mapping in Phase 2.6.

The per-domain focus checklists below name *categories of concern*; the precise
probes (and their output templates) live in the vendored domain-probe modules
(`references/domain-probes/*.md`), which each reviewer should load.

---

## Reviewer output schema

Each reviewer returns one object with these fields:

```json
{
  "reviewer_id": "R1",
  "expertise_area": "Biostatistics & Study Design",
  "overall_assessment": "3-5 sentences. State explicitly whether a fatal flaw exists and name the single biggest threat to the conclusions.",
  "strengths": ["...", "..."],
  "major": [
    {
      "number": 1,
      "heading": "Short title of the issue",
      "comment": "Detailed critique. Quote the manuscript where relevant. Explain why it threatens validity.",
      "location": "section / table / figure / specific claim",
      "severity": "Fatal | Fixable",
      "suggested_fix": "What the authors should do to address it"
    }
  ],
  "minor": [
    { "number": 1, "comment": "...", "location": "..." }
  ]
}
```

`severity` uses this skill's own scale: **Fatal** for a conclusion-threatening /
design-level finding, **Fixable** for a reporting-level finding.

---

## Reviewer prompt skeleton

> You are an expert peer reviewer for a competitive journal in {field}, performing a
> blinded pre-submission review of the author's own manuscript. Read the full
> manuscript (and any supplement) first.
>
> TONE: rigorous and skeptical, but fair and constructive. Hunt for the issues that
> threaten the manuscript's conclusions. Keep strengths to 2–3 genuine items. Every
> major comment must threaten an actual conclusion or a reporting requirement; quote
> the manuscript when you criticize a specific claim, and cite the location.
>
> Stay strictly within YOUR assigned area of expertise: {expertise_area}. Do not
> stray into the other reviewers' domains. Load and apply the probes in
> {domain_probe_module} where it applies. Produce 4–8 major comments and 4–10 minor
> comments, and return them in the reviewer output schema above. Set `reviewer_id`
> to "{reviewer_id}" and `expertise_area` to "{expertise_area}".
>
> YOUR FOCUS:
> {focus_checklist}

### Per-domain focus checklists (generic)

**Biostatistics & Study Design**
- Model specification: is the primary model pre-specified, or chosen post hoc in a results-favorable direction? Over-adjustment / conditioning on mediators on the causal pathway?
- Assumption checks appropriate to the model (e.g., proportional hazards for Cox), and adequacy of any corrections.
- Missing data: extent, plausibility of the missingness mechanism, whether the headline estimate survives a principled imputation, and whether imputation is primary or relegated to sensitivity.
- Competing risks / informative censoring where multiple event types exist.
- Sparse events: events-per-variable, penalization adequacy, CI stability.
- Multiplicity across multiple outcomes, subgroups, and exploratory analyses.
- Sensitivity / bias analyses (e.g., E-value) computed and interpreted correctly.
- Time-zero / immortal-time / left-truncation; power for any null finding.

**Clinical (domain)**
- Clinical actionability: do the stated recommendations follow from the actual (possibly attenuated) results, or do they overreach?
- Residual confounding by the dominant clinical driver of the outcome; can the exposure be disentangled from it?
- Screening vs symptomatic population framing; external validity to the target readership.
- Plausibility of the pattern of findings (e.g., a selective association without an expected concomitant one) — biology vs confounding vs chance.
- Whether the findings would change management for a real patient.
- Missing clinical variables and their interpretive cost.

**Imaging / Radiology**
- Exposure / measurement validity: how the imaging variable was defined and measured; visual/binary vs quantitative; threshold dependence.
- Interobserver reliability measured in THIS cohort vs cited from the literature; defensibility of any non-differential-misclassification "bias toward the null" claim.
- Protocol heterogeneity over time (scanner generation, slice thickness, reconstruction, dose) and its effect on the measurement.
- Unavailable / non-retrievable images and selection implications.
- Subtype/severity collapsed into a binary; loss of dose-response.
- Reliability of routine clinical reports used as a research-grade variable.

**Methodology (SR/MA)**
- Search comprehensiveness and reproducibility; screening reviewer count.
- Extraction fidelity vs source; comparator existence and consistent definition.
- Non-independence (overlapping cohorts / shared public benchmarks).
- Risk-of-bias instrument and per-study application; supplementary completeness.
- Registration (PROSPERO) format and amendment discipline.

**ML / Statistics (radiomics, AI)**
- Design-grid circularity: is an outcome predicted from the very axes used to construct the dataset?
- Construct validity: reliability ≠ predictiveness; orthogonality of proxy and target.
- Transportability: cross-domain failure framed as success; negative R² read as a weak metric.
- Multiplicity across model × threshold / cohort grids; small-cohort bootstrap intervals.
- Leakage (patient-level vs image-level splits); calibration beyond discrimination.

**Clinical translation / reference standard**
- Reference-standard validity and verification bias.
- Whether reported performance reflects the intended-use population and decision point.
- Incremental value over the comparator already in routine use.

**Methodology / SANRA (narrative review)**
- Novelty / value-add against recent reviews; scope and aims clarity.
- Evidence-gathering transparency (suggestion-level; not PRISMA).
- Taxonomy / synthesis coherence; balance, currency, citation accuracy.
- Load-bearing figures/tables; proportionate gap-filling ("consider adding", never "must cite").

**Technical accuracy (narrative review)**
- Engineering and domain correctness of specific claims; itemize errors with location.
- Verify-your-own-criticism: cross-check each asserted inaccuracy against a current authoritative source before raising it.

---

## Editor synthesis prompt skeleton

> You are the handling editor. {N} expert reviewers (areas: {areas}) have returned
> independent blinded reviews of this pre-submission manuscript. Here are their
> structured reviews as JSON:
>
> {reviews_json}
>
> Read enough of the manuscript to adjudicate conflicts and weigh severity yourself.
> Then:
> 1. Reach an internal readiness decision and state the rationale honestly. (This sets
>    the Phase 3c verdict / score; it is not a journal recommendation to print.)
> 2. De-duplicate and consolidate the major comments by theme. For each consolidated
>    point, flag CONSENSUS (raised by ≥2 reviewers) or single-reviewer, and attribute
>    (R1/R2/R3).
> 3. List the top priority pre-submission actions, ranked and concrete.
> 4. Give an honest readiness verdict: ready for the target tier now, fix specific
>    items first, or consider a different tier.
>
> Map every finding onto the self-review framing (Fatal / Fixable, category letters
> A–K) and emit it through the Phase 3 report, Phase 3b R0 numbering, and Phase 3c
> JSON, adding the optional `consensus` field where ≥2 reviewers agreed. Follow the
> manuscript-style rules: no "§" symbols, minimal em-dashes, full prose, cite specific
> locations.

---

## Lens-diversity gate (Step 3.5)

Before finalizing, the editor runs `scripts/check_panel_diversity.py` on the collected
reviewer JSON. The gate classifies each major finding into a concern family and checks
that the panel spans the axes its research type is expected to probe — the deterministic
backstop against a panel converging on one easy theme while a high-risk axis goes unprobed.

**Expected high-risk axes per research type** (each should yield ≥1 major; mirrors the
Phase 2.6 reviewer-set table). Optional axes — for example imaging when the exposure is
non-imaging — are not required:

| Research type | Expected axes (families) |
|---|---|
| Survival / prognostic | statistics, clinical |
| Systematic review / meta-analysis | search_screening, clinical, statistics |
| Radiomics | imaging, statistics, clinical |
| Diagnostic-accuracy / AI model | design_leakage, statistics, clinical |
| Observational (STROBE) | confounding, clinical, statistics |
| Narrative / review article | clinical, reporting |

Concern families the classifier recognizes: `search_screening`, `design_leakage`,
`confounding`, `imaging`, `reporting`, `reproducibility`, `statistics`, `clinical`
(everything else falls to `other` and does not count toward coverage). When the research
type is unknown, the axis-coverage check is skipped (the monoculture and lens-collapse
checks still run). The gate never penalizes genuine consensus — only full reviewer
redundancy (`LENS_COLLAPSE`) or panel-level concentration (`FAMILY_MONOCULTURE`).
