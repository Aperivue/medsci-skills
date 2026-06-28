---
name: model-card
description: >
  Generate the documentation an engineer-built medical-imaging model must carry — a Model Card
  (Mitchell et al. 2019), a Datasheet for its dataset (Gebru et al. 2021), and a METRIC-informed
  data-quality pass — filled from user-supplied facts, then verify every required section is present
  and non-empty before the card ships to a repo, Hugging Face card, or manuscript supplement. Never
  fabricates numbers, provenance, consent, or licence; unfilled fields stay flagged. Ships a
  deterministic completeness gate. Model Card and Datasheet are documentation standards vendored here as
  templates, not counted reporting checklists.
triggers: model card, model cards, datasheet, datasheet for datasets, dataset documentation, model documentation, hugging face card, model metadata, intended use, out-of-scope, data quality, METRIC framework, model reporting, document a model
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Model-Card Skill

## Purpose

This skill produces the **documentation an engineer-built medical-imaging model must carry**: a
**Model Card** (intended use, out-of-scope use, training data, per-subgroup performance, caveats), a
**Datasheet** for its dataset (provenance, composition, collection, labelling, consent), and a
**METRIC-informed data-quality pass**. It fills the templates **from facts the user supplies** — it
never invents a number, a provenance detail, a consent status, or a licence — and ships a deterministic
gate that no required section is missing or left as an unfilled `[NEEDS INPUT]` placeholder.

It is the **reporting** seam of the model-engineering lane: after `/model-validation` audits the design
and `/model-evaluation` produces the numbers, this skill records them in a portable, auditable card that
`/write-paper` and `/check-reporting` consume. It mirrors `/version-dataset` structurally (generate +
deterministic verify).

## When to use
- A trained model needs a Model Card / Datasheet for a repo, Hugging Face card, or manuscript supplement.

## When NOT to use
- Auditing the validation design / metrics → `/model-validation`, `/model-evaluation`.
- Versioning the dataset bytes → `/version-dataset`; tabular variable docs → `/generate-codebook`.
- Item-by-item reporting-guideline compliance of the manuscript → `/check-reporting`.
- Building / training the model → `/model-scaffold`.

## Workflow

### Phase 1 — Collect the facts
Gather, from the user / the model's developers: task + architecture + provenance + licence; intended use
and out-of-scope use; training and evaluation cohorts; the reference standard and inter-reader agreement;
overall and **per-subgroup** performance; data collection, consent, and de-identification. Anything not
supplied stays `[NEEDS INPUT]` — never guess.

### Phase 2 — Fill the Model Card
Copy `${CLAUDE_SKILL_DIR}/references/model_card_template.md` to `MODEL_CARD.md` and fill each section
from the facts. Keep the headings. Numbers come only from `/model-evaluation` / executed results.

### Phase 3 — Fill the Datasheet
Copy `${CLAUDE_SKILL_DIR}/references/datasheet_template.md` to `DATASHEET.md` and fill the seven
question groups (Motivation, Composition, Collection, Preprocessing/Labeling, Uses, Distribution,
Maintenance).

### Phase 4 — METRIC data-quality pass
Walk `${CLAUDE_SKILL_DIR}/references/metric_dimensions.md` (completeness, correctness, consistency,
representativeness, timeliness, provenance, label provenance, fairness/coverage, leakage safety) and
record each finding in the Datasheet. Anything that affects the headline metric's validity is also a
`/model-validation` finding — cross-check there.

### Phase 5 — Verify completeness (deterministic gate)
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_model_card_complete.py \
  --card MODEL_CARD.md --datasheet DATASHEET.md --strict
```
`MISSING_SECTION` / `EMPTY_REQUIRED_SECTION` must be zero before the card ships.

### Phase 6 — Hand off
Carry the card into `/write-paper` (the Methods / supplement reference it), `/check-reporting`
(CLAIM 2024 / TRIPOD+AI item audit of the manuscript), and `/self-review`.

## Anti-Hallucination

- **Never invent evaluation numbers, subgroup results, or dataset provenance.** Every figure comes from
  `/model-evaluation` or the user's executed results; every provenance / consent / licence statement is
  user-confirmed. Unknown → `[NEEDS INPUT]`, which the gate flags.
- **Never mark a section complete without user-supplied content**, and never auto-fill a placeholder to
  pass the gate.
- **Never assert a licence or consent status the user did not confirm.**
- The gate checks **presence**, not truth — a complete card can still contain a wrong number; validity
  is `/model-validation` and the human's responsibility.

## Deterministic gate
`scripts/check_model_card_complete.py` — verifies every required Model Card / Datasheet section is
present and non-empty (stdlib, network-free). Reproducible challenge:
`bash ${CLAUDE_SKILL_DIR}/scripts/check_model_card_complete_challenge/verify.sh`.

## Note on classification
Model Cards (Mitchell et al. 2019) and Datasheets (Gebru et al. 2021) are **documentation standards**,
not clinical reporting guidelines, so they live here as `references/` **templates** (uncounted), not in
`/check-reporting`'s counted checklist set — the same way `appraisal_tools/METRICS.md` is kept separate.
`/check-reporting` still owns the manuscript-level CLAIM 2024 / TRIPOD+AI item audit.

## Boundaries

```
model-validation (audit design) + model-evaluation (metrics)
  └─ model-card (this skill: Model Card + Datasheet + METRIC pass, completeness-gated)
       └─ write-paper + check-reporting (manuscript) ; version-dataset (dataset bytes)
```
