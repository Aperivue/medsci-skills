---
name: design-ai-benchmarking
description: Use when designing a study that benchmarks AI systems against a human-expert panel, before data collection. Plans the arms, decoupled rubrics with anchors, planted calibration probes, reviewer panel, inter-rater reliability targets and LLM-as-judge versus human adjudication.
metadata:
  triggers: "AI benchmarking, AI vs human expert, reader study design, expert panel evaluation, LLM-as-judge, AI evaluation rubric, model benchmark design, human baseline comparison, AI-output rating, evaluation rubric design"
---

# Design-AI-Benchmarking Skill

## Standard Output

```text
## AI-Benchmark Design Review
Evaluation question: ...
Arms / systems compared: ...
Reference (human-expert panel): ...
Unit of rating: (item / case / output)

### Rubric (decoupled dimensions)
- dimension -> construct -> anchors (1..k)

### Calibration probes (blinded, randomized)
- positive-control / known-bad / instability / mechanism-contradiction

### Reviewer panel
- n reviewers, metadata captured, per-reviewer randomized order

### Reliability plan
- IRR target on the anchor set of real items (ICC form + 95% CI) + control-item hit rate (a competence check, reported separately)

### Judge strategy
- human-as-judge / LLM-as-judge / both + adjudication rule

### Validity risks
1. ...

### Minimal fixes
- ...

### Decision
- Ready to collect / Needs rubric revision / Needs arm or judge redesign
```

Reviewer ratings, reference labels, probe outcomes and agreement statistics come only from collected
rating records. Never invent them: a reported ICC, kappa or score with no underlying rating record is
the failure this skill exists to prevent. Cite a reference only with a `/search-lit`-confirmed DOI or
PMID; mark any other `[UNVERIFIED - NEEDS MANUAL CHECK]`. Flag an unconfirmed clinical definition,
diagnostic criterion or guideline recommendation `[VERIFY]` and ask the user.

---

## Workflow

### Phase 1: Define the evaluation question and arms

Pin down, in writing:
- the exact claim the benchmark must support (e.g., "system A's outputs are perceptually
  indistinguishable from expert outputs", not "system A is deployment-ready")
- every arm/system and what each receives as input (same items, same information access, same output
  format), so no arm has a hidden advantage
- the human-expert reference: who they are, and whether they set ground truth, form a comparison arm,
  or both
- the unit of rating (item, case, output) and how many units each reviewer sees

**Gate:** Present the reconstructed evaluation question, arms, and reference to the user and confirm
before designing the rubric. A wrong reconstruction misdirects the entire benchmark.

### Phase 2: Design a decoupled multi-dimensional rubric

- **Decouple the axes.** Each rated dimension measures one construct. Keep "is the output
  valid/correct" separate from "is it novel", "is it feasible/measurable", "does it add value over
  current tools", and "would it change action". A candidate can be high-validity yet low-added-value
  ("real but redundant"); a single blended score hides this.
- **Anchor every scale point** with a short verbal descriptor; pilot the anchors with at least one
  reviewer before locking.
- **Pre-specify discriminant validity**: hypothesize which dimensions should correlate vs be
  orthogonal, then report the full inter-dimension correlation matrix.
- Start from `${CLAUDE_SKILL_DIR}/references/elicitation_rubric_template.md` (dimensions, anchors,
  probe flavors).

### Phase 3: Insert and randomize calibration probes

Plant a few deliberate control items, blinded and randomized across raters (record who received which
via a `probe_arm` flag), to anchor the scale, measure rater drift/fatigue, and audit the rubric and
pipeline. Four flavors:
- **Positive control / "too-good" item** — near-tautological; tests whether raters equate "largest
  effect" with "best", and whether the construct-independence gate (Phase 7) works.
- **Known-bad negative control** — an engineered defect (fabricated reference, missing key statistic).
- **Instability item** — an estimate that reverses or fails to replicate on a holdout.
- **Mechanism-contradiction item** — an empirical direction that opposes the proposed mechanism.

Probes are *planted or adjudicated*, never fabricated to fit a hypothesis.

### Phase 4: Construct the reviewer panel

- Recruit reviewers spanning the intended expertise gradient; pre-specify any stratification.
- Capture reviewer metadata (years of experience, prior AI-evaluation experience, subspecialty).
- Randomize item order **per reviewer** (not one global seed), record the order, and plan to analyze
  order and fatigue effects.
- Require each item to be judged standalone; cross-item references in free text signal
  non-independent rating.

**Gate:** Present the panel composition, stratification, and randomization plan for user review before
recruitment is finalized.

### Phase 5: Set inter-rater reliability targets

- Pre-specify the reliability statistic **and its form** — for several raters, an ICC with the
  model stated (e.g. ICC(2,1): two-way random, absolute agreement, single rater) or Krippendorff's α
  (ordinal); weighted (Cohen's) kappa is a two-rater statistic — and a justified target. Size the
  number of **items** for the CI width you need: ICC precision is driven mainly by the item count
  (Koo & Li, *J Chiropr Med* 2016).
- **Planted control items are a rater-competence check, not reliability evidence.** Report the hit
  rate on known-good vs known-bad controls. Do not present an ICC computed on the controls as
  evidence of rubric or scale validity: ICC scales with the spread between items, controls are
  extreme by construction, so their ICC is high whatever the raters' reliability on real items (same
  five raters, same noise: ICC(2,1) 0.89 on four planted controls, 0.16 on 40 real items), and it
  rests on a handful of items.
- **Report reliability on the representative anchor set of real items** — ICC with its 95% CI and
  stated form — with an agreement measure alongside (exact agreement, SEM), since reliability
  depends on how heterogeneous the rated items are (de Vet et al., *J Clin Epidemiol* 2006). A low
  ICC on real items with a good control hit rate points to little true spread among the items or a
  rubric that does not separate them, not to careless raters.
- Plan the minimum ratings-per-item for a stable agreement estimate (the math goes to
  `/analyze-stats`).

### Phase 5b: Reader allocation under burden constraints (anchor-and-rotate)

When the item pool exceeds what one reader can rate in a session, do **not** make every reader rate
every item (that caps the pool at the per-reader limit). Use **anchor-and-rotate** (an anchor set
plus rotating incomplete blocks — not a balanced incomplete block design, since reader pairs are
not co-rated equally often): all readers rate a shared **anchor set** of real items (which carries
the inter-rater reliability; the planted controls carry only the competence check) plus a
**rotating unique block** each. The binding
constraint is usually the number of available expert readers, so solve the reverse problem (largest
pool for R readers) to size the must-rate set. Pre-specify anchor membership, raters-per-item, and the
rotation seed before rating. Read `${CLAUDE_SKILL_DIR}/references/anchor_rotate_reader_allocation.md`
for the formulas, trade-offs, and a stdlib implementation.

### Phase 6: Choose the judge strategy and adjudication

- Decide human-as-judge, LLM-as-judge, or both. An LLM judge is one more arm whose ratings must be
  validated against the human panel on the anchor set of real items, not only on the extreme
  control items.
- Pre-specify the **adjudication rule** for disagreement (majority, a third senior reviewer, consensus
  discussion) and who adjudicates.
- Blind judges to arm identity wherever feasible; record any unavoidable unblinding.

### Phase 7: Construct-independence and leakage guards

- Exclude any predictor or input that is a definitional component of the outcome, and flag
  near-tautological composites built from the outcome's defining components — they produce an
  inflated, near-circular result and belong as labeled probes, not discoveries.
- Verify no arm sees post-decision or outcome-derived information the others do not.
- Confirm the reference labels were not derived from the same model output being evaluated.

### Phase 8: Lock a structured export schema

Write the machine-readable rating record as a JSON schema, starting from
`${CLAUDE_SKILL_DIR}/references/benchmark_export_schema.json`: per-item ratings on every rubric
dimension, free-text justifications, follow-up flags, the `probe_arm` flag, reviewer id and metadata,
item order, and timing.

**Gate:** Present the final rubric, probe set, panel plan, judge strategy, and export schema together;
collect explicit user approval before any rating begins, because changes after collection starts
compromise the comparison.

---

## Handoff Rules

- route to `/analyze-stats` for ICC (stated form) / Krippendorff's α / kappa (two raters) / DeLong, agreement sample size, and effect-size real-world
  translation of the benchmark results
- route to `/check-reporting` for STARD-AI, CLAIM, or TRIPOD+AI item-level reporting once the design is locked
- route to `/design-study` when the broader study around the benchmark (cohort logic, analysis unit,
  comparator) also needs review
- route to `/peer-review` or `/self-review` only after ratings exist and a manuscript is being assessed
