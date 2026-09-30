<!-- AUTO-GENERATED from skills/model-selection/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# model-selection

> Use when choosing the model for a medical-imaging study. Picks a paper-grounded architecture family (CNN/ViT, U-Net/nnU-Net, detection, SAM/foundation, GNN), then vets the concrete repo or checkpoint for licence, version pin, weight provenance and benchmark overlap.

**Invoke:** `/model-selection`

## When to use

`model-selection` activates on requests such as: architecture zoo, model sourcing, which architecture, choose a model, model selection, ResNet vs ViT, U-Net vs nnU-Net, what backbone, foundation model for, transfer learning choice, MedSAM, TotalSegmentator, DINO, MAE, self-supervised, graph neural network, GNN, brain connectome, GCN, GAT, GraphSAGE, BrainGNN, population graph, paper to architecture, reference implementation, when to use ViT, segmentation architecture, classification backbone, nnU-Net ResEnc, MedNeXt, STU-Net, nnInteractive, VISTA3D, SAM-Med3D, Mamba, U-Mamba, interactive segmentation, labelling acceleration, promptable segmentation, nnDetection, lesion detection, ConvNeXt, YOLO, YOLOv8, RT-DETR, DETR, RetinaNet, detection architecture, RETFound, UNI, CONCH, RAD-DINO, Merlin, medical foundation model, pathology foundation model, domain transfer, diffusion model, latent diffusion, ControlNet, MAISI, image synthesis, GAN, CycleGAN, Pix2Pix, source a model, vet a model, pick a model, model provenance, model dossier, pretrained weights, checkpoint, HuggingFace model, GitHub model, model licence, weight provenance, is this model independent, benchmark overlap, trained on my test set, data contamination, model version pin, third-party model, can I use this model.

## Quality Card

**Purpose** — Start a medical-imaging model study from a defensible, paper-grounded architecture archetype, then establish what the chosen third-party artifact's numbers are allowed to claim — by writing provenance facts that live in different documents into one record and auditing the relationships between them, chiefly whether an evaluation arm sits on the benchmark the model was developed against.

**Safety boundaries**

- Advisory plus deterministic-audit only: writes decision notes and a dossier; never downloads, executes, fine-tunes, or benchmarks a model, and never fetches a repository or resolves a licence over the network.
- Every architecture recommendation names its source paper; benchmark numbers are cited, never invented; the zoo describes archetypes, not a live leaderboard.
- Every provenance verdict is decided by set arithmetic over the dossier JSON (stdlib-only); an unstated fact yields a finding rather than an inferred value.

**Known limitations**

- The literature moves fast; the architecture cards are a curated archetype map (classification, segmentation, detection, synthesis, foundation/SSL, graph/GNN), not an exhaustive or current SOTA ranking.
- The dossier is taken at face value: the gate cannot tell that a stated licence is wrong or that `developed_on` is incomplete, so reading the artifact is the researcher's responsibility and the gate audits the consequences.
- Dataset matching is token-sequence based with a small family-alias table; two names for the same corpus that share no leading token (a private cohort renamed between papers) will not be matched.
- A sound choice and a clean dossier are necessary, not sufficient: preprocessing leakage (imaging-data), split disjointness and metric choice (model-assessment) are separate gates.

**Validation**

- `python3 scripts/check_model_provenance.py --dossier <dossier.json> --strict`
- `bash scripts/check_model_provenance_challenge/verify.sh  # deterministic, network-free`
- `bash tests/test_model_provenance.sh`

**Evidence** — `ci_validator`

## Bundled resources

**References** (`skills/model-selection/references/`):

- `classification.md`
- `detection.md`
- `foundation_models.md`
- `graph.md`
- `index.md`
- `segmentation.md`
- `synthesis.md`

**Scripts** (`skills/model-selection/scripts/`):

- `check_model_provenance.py`
- `check_model_provenance_challenge/` (8 files)

## Source

Canonical definition: [`skills/model-selection/SKILL.md`](../../skills/model-selection/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
