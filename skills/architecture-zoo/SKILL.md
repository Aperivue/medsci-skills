---
name: architecture-zoo
description: >
  Choose a model architecture for a medical-imaging research question before scaffolding. Maps the task
  (classification, segmentation, detection, transfer), modality and dimensionality, labelled-data scale,
  and class imbalance to a shortlist of architectures, each grounded in its source paper with a
  when-to-use, a medical-imaging use, a reference implementation, the typical validation setup, and the
  matching model-scaffold template. Covers the foundational curriculum (ResNet, DenseNet, EfficientNet,
  ViT, Swin; U-Net, 3-D U-Net, Attention/Residual U-Net, nnU-Net, Mask R-CNN; SAM/MedSAM,
  TotalSegmentator, BiomedCLIP, DINO/MAE/SimCLR). It teaches archetypes and the task-to-architecture
  logic, not a live SOTA leaderboard.
triggers: architecture zoo, which architecture, choose a model, model selection, ResNet vs ViT, U-Net vs nnU-Net, what backbone, foundation model for, transfer learning choice, MedSAM, TotalSegmentator, DINO, MAE, self-supervised, paper to architecture, reference implementation, when to use ViT, segmentation architecture, classification backbone
tools: Read, Write, Edit, Grep, Glob
model: inherit
---

# Architecture-Zoo Skill

## Purpose

This skill turns a **medical-imaging research question into a paper-grounded architecture choice** —
so the build starts from the right archetype (and a known validation setup) rather than from whatever is
fashionable, and the choice carries its source citation into the Methods. It is the **front end** of the
model-engineering lane: `architecture-zoo (choose)` → `/model-scaffold (build)` → `/model-validation
(validate)`.

It is **advisory** (Layer D): it writes a short decision note, never code or weights. The actual repo is
`/model-scaffold`. It describes **archetypes and the task → family → constraint logic**, not a live SOTA
leaderboard (SOTA churns; the logic does not).

## When to use
- You need to pick an architecture/backbone for a classification, segmentation, detection, or
  transfer-learning question and want it grounded in the literature with a sensible default.

## When NOT to use
- Generating the runnable repo → `/model-scaffold`.
- Auditing a trained model's validation design → `/model-validation`.
- Metrics / calibration → `/model-evaluation` + `/analyze-stats`.
- General study/validity design → `/design-study`; AI-vs-expert benchmark → `/design-ai-benchmarking`.
- LLM / MLLM → `/mllm-eval`.

## Workflow

### Phase 1 — Frame the question
State the **task** (classification / segmentation / detection / transfer), the **modality +
dimensionality** (2-D vs 3-D volume), the **labelled-data scale** (events / structures, not just
images), **label availability** (lots / few / unlabelled pool), and constraints (class imbalance,
small structures, interpretability, deployment compute).

### Phase 2 — Walk the decision tree
Open `${CLAUDE_SKILL_DIR}/references/index.md` and follow task → constraints → default pick. It routes to
a family card.

### Phase 3 — Read the family card
- `${CLAUDE_SKILL_DIR}/references/classification.md` — ResNet / DenseNet / EfficientNet / Inception /
  ViT / Swin / DeiT.
- `${CLAUDE_SKILL_DIR}/references/segmentation.md` — U-Net / 3-D U-Net / V-Net / Attention & Residual
  U-Net / nnU-Net / SegResNet / Swin-UNETR / Mask R-CNN.
- `${CLAUDE_SKILL_DIR}/references/foundation_models.md` — SAM / MedSAM / MedSAM2 / TotalSegmentator /
  SegVol / BiomedCLIP / DINO / MAE / SimCLR / MoCo.
Each card gives the paper, core idea, when-to-use, medical-imaging use, reference implementation, and the
**typical validation/experiment setup** for that architecture class.

### Phase 4 — Write the decision note
Record `decisions/architecture_choice.md`: the **task**, the **chosen architecture**, its **source
paper**, the **reason** against the constraints, the **runner-up + why not**, and the matching
**`/model-scaffold` template**. Naming the source paper is mandatory; cite, never invent, any benchmark
number.

### Phase 5 — Hand off
Carry the decision note to `/model-scaffold` (instantiate the template), then `/model-validation`
(split / validation design), `/model-evaluation` + `/analyze-stats` (metrics), and `/write-paper`
(the Methods cite the architecture's source paper).

## Anti-Hallucination

- **Never recommend an architecture without naming its source paper.** Every card cites the paper; the
  decision note must carry that citation.
- **Never invent benchmark numbers or paper claims.** If a number matters, cite it (verify via
  `/search-lit`); if uncertain, write `[VERIFY]` and ask.
- **Never recommend an architecture for a modality or data scale it does not suit** (e.g. a from-scratch
  ViT on a few hundred images, or 2-D slices for a volumetric structure) — the constraints in the
  decision tree exist to prevent exactly that.
- The zoo is a curated **archetype** map, not a current SOTA ranking — say so rather than implying a
  recommendation is the latest best.

## Boundaries

```
architecture-zoo (this skill: choose, paper-grounded)
  └─ model-scaffold (build the reproducible repo from the chosen template)
       └─ model-validation -> model-evaluation -> write-paper (cite the source paper)
```

It does not build, train, evaluate, or rank live SOTA — it maps the research question to a defensible,
paper-grounded archetype and hands the choice to `/model-scaffold`.
