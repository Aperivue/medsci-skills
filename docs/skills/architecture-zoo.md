<!-- AUTO-GENERATED from skills/architecture-zoo/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# architecture-zoo

> Choose a model architecture for a medical-imaging research question before scaffolding. Maps the task (classification, segmentation, detection, transfer), modality and dimensionality, labelled-data scale, and class imbalance to a shortlist of architectures, each grounded in its source paper with a when-to-use, a medical-imaging use, a reference implementation, the typical validation setup, and the matching model-scaffold template. Covers the foundational curriculum (ResNet, DenseNet, EfficientNet, ViT, Swin; U-Net, 3-D U-Net, Attention/Residual U-Net, nnU-Net, Mask R-CNN; SAM/MedSAM, TotalSegmentator, BiomedCLIP, DINO/MAE/SimCLR). It teaches archetypes and the task-to-architecture logic, not a live SOTA leaderboard.

**Invoke:** `/architecture-zoo` · **Tools:** Read, Write, Edit, Grep, Glob · **Model:** inherit

## When to use

`architecture-zoo` activates on requests such as: architecture zoo, which architecture, choose a model, model selection, ResNet vs ViT, U-Net vs nnU-Net, what backbone, foundation model for, transfer learning choice, MedSAM, TotalSegmentator, DINO, MAE, self-supervised, paper to architecture, reference implementation, when to use ViT, segmentation architecture, classification backbone.

## Quality Card

**Purpose** — Turn a medical-imaging research question into a paper-grounded architecture choice — so the build starts from the right archetype (and a known validation setup) rather than from what is fashionable, and the choice carries its source citation into the manuscript.

**Safety boundaries**

- Advisory only: it writes a decision note, never code or weights; the build is /model-scaffold.
- Every recommendation names its source paper; benchmark numbers are cited, never invented; the zoo describes archetypes, not a live leaderboard.

**Known limitations**

- The literature moves fast; this is a curated archetype map (classification, segmentation, detection, synthesis, foundation/SSL families), not an exhaustive or current SOTA ranking.
- A sound architecture choice is necessary, not sufficient; validity still depends on the split, validation design, and metrics (/model-validation, /model-evaluation).

**Validation**

- `carry the decision note into /model-scaffold to instantiate the chosen template, then /model-validation`

**Evidence** — `manual_workflow`

## Bundled resources

**References** (`skills/architecture-zoo/references/`):

- `classification.md`
- `detection.md`
- `foundation_models.md`
- `index.md`
- `segmentation.md`
- `synthesis.md`

## Source

Canonical definition: [`skills/architecture-zoo/SKILL.md`](../../skills/architecture-zoo/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
