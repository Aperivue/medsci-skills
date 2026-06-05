# Decoupled Elicitation Rubric Template (synthetic)

A starting rubric for an AI-vs-human-expert benchmark. Every dimension measures one construct, so a
candidate can score high on validity yet low on added value ("real but redundant"). All values below
are illustrative placeholders, not real data — replace them for your own evaluation.

## Per-item rating dimensions

| Dimension | Construct (one only) | Anchor 1 (low) | Anchor 3 (mid) | Anchor 5 (high) |
|-----------|----------------------|----------------|----------------|-----------------|
| Validity | Is the output correct against the reference? | Contradicted by reference | Partially supported | Fully supported |
| Novelty | Is it new vs prior work? | Restates known result | Incremental extension | Genuinely new |
| Feasibility | Can it be measured/obtained in practice? | Not measurable | Measurable with effort | Routinely measurable |
| Added value | Does it add over a measure already in use? | Redundant with a routine measure | Marginal gain | Clear gain over current tools |
| Actionability | Would a clinician act on it for an individual? | Would not change action | Might change action | Would change action |

Notes:
- Pilot the anchors with at least one reviewer before locking the scale.
- Pre-specify which dimensions are expected to correlate (e.g., validity and actionability) vs be
  orthogonal (e.g., novelty and feasibility); report the inter-dimension correlation matrix afterward.

## Planted calibration probes

`probe_arm` marks a control item; it is randomized across reviewers and excluded from the primary
estimate but reported separately for scale validity.

| probe_arm | Flavor | What it tests | Expected behavior |
|-----------|--------|---------------|-------------------|
| pos_control | Positive / "too-good" (near-tautological) | Whether raters equate "largest effect" with "best"; whether the construct-independence gate fires | High validity, low added value |
| neg_control | Known-bad (engineered defect) | Whether obvious defects are caught | Low validity |
| instability | Reverses on holdout | Caveat-handling for unstable estimates | Lower confidence ratings |
| mechanism_contra | Direction opposes mechanism | Whether raters notice mechanism conflict | Flagged in free-text |

## Per-item free-text fields

- justification (required): one or two sentences, judged standalone (no cross-item references)
- follow_up (optional): what additional evidence would change the rating
