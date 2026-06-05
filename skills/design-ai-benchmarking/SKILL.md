---
name: design-ai-benchmarking
description: >
  Design and validity review for studies that benchmark one or more AI systems against a human-expert
  panel as the reference. Covers the evaluation question and arm definition, decoupled multi-dimensional
  rubrics with anchors, planted calibration probes, reviewer-panel construction, inter-rater reliability
  targets, LLM-as-judge versus human-as-judge adjudication, construct-independence guards, and a
  structured rating-export schema. Use before data collection on an AI-vs-expert evaluation.
triggers: AI benchmarking, AI vs human expert, reader study design, expert panel evaluation, LLM-as-judge, AI evaluation rubric, model benchmark design, human baseline comparison, AI-output rating, evaluation rubric design
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Design-AI-Benchmarking Skill

## Purpose

This skill pressure-tests an AI-vs-human-expert benchmark **before any ratings are collected**, so that
the comparison is fair, the rubric measures distinct constructs, the scale is calibrated, and the
reported reliability is interpretable. It is the AI-evaluation specialization of `/design-study`: where
`/design-study` reviews a study in general, this skill owns the specific machinery of comparing AI
system(s) to a panel of human experts (or to each other) on rated outputs.

Use it when:
- one or more AI systems will be scored against a human-expert reference (reader study, annotation
  panel, AI-output evaluation, model-vs-model bench)
- a rubric and rating protocol must be locked before reviewers begin
- a benchmark feels vulnerable to "the highest score is just the most tautological item" or
  "low agreement, but we cannot tell why" criticism
- a reviewer or editor asks how the evaluation controlled for rater drift, leakage, or judge bias

Do **not** use it for: general study/validity review (use `/design-study`); statistical execution such
as ICC or DeLong (use `/analyze-stats`); reporting-guideline item audits (use `/check-reporting`);
or reviewing an already-written manuscript (use `/peer-review` or `/self-review`).

---

## Communication Rules

- Communicate with the user in their preferred language.
- Use English for statistical, machine-learning, and reporting-guideline terminology.
- Be direct about evaluation-validity risks, but always propose the smallest feasible fix first.
- Never invent reviewer ratings, reference labels, or agreement statistics; those come from collected
  data only.

---

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
- overall IRR target + control-item IRR (reported separately)

### Judge strategy
- human-as-judge / LLM-as-judge / both + adjudication rule

### Validity risks
1. ...

### Minimal fixes
- ...

### Decision
- Ready to collect / Needs rubric revision / Needs arm or judge redesign
```

---

## Workflow

### Phase 1: Define the evaluation question and arms

Pin down, in writing:
- the exact claim the benchmark must support (e.g., "system A's outputs are perceptually
  indistinguishable from expert outputs", not "system A is deployment-ready")
- every arm/system being compared, and what each arm receives as input (same items, same information
  access, same output format) so no arm has a hidden advantage
- the human-expert reference: who they are, and whether they set ground truth, provide a comparison
  arm, or both
- the unit of rating (item, case, output) and how many units each reviewer sees

**Gate:** Present the reconstructed evaluation question, arms, and reference to the user and confirm
before designing the rubric. A wrong reconstruction misdirects the entire benchmark.

### Phase 2: Design a decoupled multi-dimensional rubric

- **Decouple the axes.** Each rated dimension measures one construct. Keep "is the output valid/correct"
  separate from "is it novel", "is it feasible/measurable", "does it add value over current tools", and
  "would it change action". A candidate can be high-validity yet low-added-value ("real but redundant");
  a single blended score hides this divergence.
- **Anchor every scale point** with a short verbal descriptor; pilot the anchors with at least one
  reviewer before locking.
- **Pre-specify discriminant validity**: hypothesize which dimensions should correlate vs be orthogonal,
  then report the full inter-dimension correlation matrix to confirm the rubric measures distinct
  constructs.
- A worked rubric template lives in `${CLAUDE_SKILL_DIR}/references/elicitation_rubric_template.md`.

### Phase 3: Insert and randomize calibration probes

Plant a small number of deliberate control items, blinded and randomized across raters (record who
received which via a `probe_arm` flag), to (i) anchor the scale, (ii) measure rater drift/fatigue, and
(iii) audit the rubric and pipeline itself. Four useful flavors:
- **Positive control / "too-good" item** — a known-strong or near-tautological item; tests whether
  raters equate "largest effect" with "best", and whether the construct-independence gate (Phase 7) works.
- **Known-bad negative control** — an engineered defect (fabricated reference, missing key statistic);
  expected to score low.
- **Instability item** — an estimate that reverses or fails to replicate on a holdout; tests
  caveat-handling.
- **Mechanism-contradiction item** — an empirical direction that opposes the proposed mechanism.

Probes are *planted or adjudicated*, never fabricated to fit a hypothesis.

### Phase 4: Construct the reviewer panel

- Recruit reviewers spanning the intended expertise gradient; pre-specify any expertise stratification.
- Capture reviewer metadata (years of experience, prior AI-evaluation experience, subspecialty) for
  descriptive reporting and stratified analysis.
- Randomize item order **per reviewer** (not one global seed) and record the order; plan to analyze
  order and fatigue effects.
- Require each item to be judged standalone; discourage cross-item references in free-text, which signal
  non-independent rating.

**Gate:** Present the panel composition, stratification, and randomization plan for user review before
recruitment is finalized.

### Phase 5: Set inter-rater reliability targets

- Pre-specify the agreement statistic (e.g., ICC for continuous ratings, weighted kappa for ordinal)
  and a target with justification.
- **Report reliability on the planted control items separately** as primary evidence of rubric and
  scale validity. A low overall ICC is interpretable only if raters at least converge on the controls;
  surfacing both numbers prevents "low agreement => bad rubric" or "bad raters" misreads.
- Plan the minimum ratings-per-item needed for a stable agreement estimate (delegate the math to
  `/analyze-stats`).

### Phase 6: Choose the judge strategy and adjudication

- Decide human-as-judge, LLM-as-judge, or both. If an LLM is used as a judge, treat it as one more arm
  whose ratings must themselves be validated against the human panel on the control items.
- Pre-specify the **adjudication rule** for disagreement (e.g., majority, a third senior reviewer,
  consensus discussion) and who adjudicates.
- Blind judges to arm identity wherever feasible; record any unavoidable unblinding.

### Phase 7: Construct-independence and leakage guards

- Exclude any predictor or input that is a definitional component of the outcome (mathematical
  definition), and flag near-tautological composites built from the outcome's defining components — they
  produce an inflated, near-circular result and belong as labeled probes, not discoveries.
- Verify no arm sees post-decision or outcome-derived information the others do not.
- Confirm the reference labels were not derived from the same model output being evaluated.

### Phase 8: Lock a structured export schema

Define the machine-readable rating record up front: per-item ratings across every rubric dimension,
free-text justifications, follow-up flags, the `probe_arm` flag, reviewer id and metadata, item order,
and timing. A synthetic schema lives in `${CLAUDE_SKILL_DIR}/references/benchmark_export_schema.json`.

**Gate:** Present the final rubric, probe set, panel plan, judge strategy, and export schema together;
collect explicit user approval before any rating begins. Locking these before data collection is the
whole point — changes afterward compromise the comparison.

---

## Handoff Rules

- route to `/analyze-stats` for ICC / weighted kappa / DeLong, agreement sample size, and effect-size
  real-world translation of the benchmark results
- route to `/check-reporting` for STARD-AI, CLAIM, or TRIPOD+AI item-level reporting once the design is locked
- route to `/design-study` when the broader study around the benchmark (cohort logic, analysis unit,
  comparator) also needs review
- route to `/peer-review` or `/self-review` only after ratings exist and a manuscript is being assessed

---

## What This Skill Does NOT Do

- It does not compute agreement statistics or run analyses directly (that is `/analyze-stats`).
- It does not collect or fabricate ratings, reference labels, or probe outcomes.
- It does not draft manuscript prose or run a reporting-guideline audit.
- It does not replace a full peer review of a finished manuscript.

## Anti-Hallucination

- **Never fabricate references.** All citations must be verified via `/search-lit` with a confirmed DOI
  or PMID. Mark unverified references as `[UNVERIFIED - NEEDS MANUAL CHECK]`.
- **Never invent reviewer ratings, agreement statistics, reference labels, or probe outcomes** — these
  come from collected data only. A reported ICC, kappa, or score with no underlying rating record is the
  failure mode this skill exists to prevent.
- **Never invent clinical definitions, diagnostic criteria, or guideline recommendations.** If uncertain,
  flag with `[VERIFY]` and ask the user.
- If a reporting-guideline item, journal policy, or evaluation standard is uncertain, state the
  uncertainty rather than guessing.

## Reference Files

- `${CLAUDE_SKILL_DIR}/references/elicitation_rubric_template.md` -- a synthetic, decoupled
  multi-dimension rating rubric with anchors and a planted-probe column.
- `${CLAUDE_SKILL_DIR}/references/benchmark_export_schema.json` -- a synthetic JSON schema for the
  per-item rating export (ratings, justifications, probe_arm, reviewer metadata, order, timing).
