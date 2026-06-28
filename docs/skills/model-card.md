<!-- AUTO-GENERATED from skills/model-card/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# model-card

> Generate the documentation an engineer-built medical-imaging model must carry — a Model Card (Mitchell et al. 2019), a Datasheet for its dataset (Gebru et al. 2021), and a METRIC-informed data-quality pass — filled from user-supplied facts, then verify every required section is present and non-empty before the card ships to a repo, Hugging Face card, or manuscript supplement. Never fabricates numbers, provenance, consent, or licence; unfilled fields stay flagged. Ships a deterministic completeness gate. Model Card and Datasheet are documentation standards vendored here as templates, not counted reporting checklists.

**Invoke:** `/model-card` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`model-card` activates on requests such as: model card, model cards, datasheet, datasheet for datasets, dataset documentation, model documentation, hugging face card, model metadata, intended use, out-of-scope, data quality, METRIC framework, model reporting, document a model.

## Quality Card

**Purpose** — Produce an auditable Model Card + Datasheet so an engineer-built model carries its intended-use, out-of-scope, training-data, per-subgroup-performance, and limitations record into clinical evaluation and publication — with a deterministic gate that no required section is missing or left as an unfilled placeholder.

**Safety boundaries**

- Templates are filled only from user-supplied facts; an empty required field stays [NEEDS INPUT] and is flagged, never auto-filled or guessed.
- Completeness is reproduced by a stdlib script; it checks presence, not the truth of a stated fact (that is model-validation / check-reporting).

**Known limitations**

- Documents what is supplied; it cannot verify that a stated performance number or provenance claim is real.
- Model Card / Datasheet are documentation standards, not clinical reporting guidelines — they are vendored as templates here, not counted reporting checklists.

**Validation**

- `python3 scripts/check_model_card_complete.py --card MODEL_CARD.md --datasheet DATASHEET.md --strict`
- `bash scripts/check_model_card_complete_challenge/verify.sh  # deterministic, network-free`

**Evidence** — `ci_validator`

## Bundled resources

**References** (`skills/model-card/references/`):

- `datasheet_template.md`
- `metric_dimensions.md`
- `model_card_template.md`

**Scripts** (`skills/model-card/scripts/`):

- `check_model_card_complete.py`
- `check_model_card_complete_challenge/` (5 files)

## Source

Canonical definition: [`skills/model-card/SKILL.md`](../../skills/model-card/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
