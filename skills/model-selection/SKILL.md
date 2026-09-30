---
name: model-selection
description: Use when choosing the model for a medical-imaging study. Picks a paper-grounded architecture family (CNN/ViT, U-Net/nnU-Net, detection, SAM/foundation, GNN), then vets the concrete repo or checkpoint for licence, version pin, weight provenance and benchmark overlap.
model: inherit
metadata:
  triggers: "architecture zoo, model sourcing, which architecture, choose a model, model selection, ResNet vs ViT, U-Net vs nnU-Net, what backbone, foundation model for, transfer learning choice, MedSAM, TotalSegmentator, DINO, MAE, self-supervised, graph neural network, GNN, brain connectome, GCN, GAT, GraphSAGE, BrainGNN, population graph, paper to architecture, reference implementation, when to use ViT, segmentation architecture, classification backbone, nnU-Net ResEnc, MedNeXt, STU-Net, nnInteractive, VISTA3D, SAM-Med3D, Mamba, U-Mamba, interactive segmentation, labelling acceleration, promptable segmentation, nnDetection, lesion detection, ConvNeXt, YOLO, YOLOv8, RT-DETR, DETR, RetinaNet, detection architecture, RETFound, UNI, CONCH, RAD-DINO, Merlin, medical foundation model, pathology foundation model, domain transfer, diffusion model, latent diffusion, ControlNet, MAISI, image synthesis, GAN, CycleGAN, Pix2Pix, source a model, vet a model, pick a model, model provenance, model dossier, pretrained weights, checkpoint, HuggingFace model, GitHub model, model licence, weight provenance, is this model independent, benchmark overlap, trained on my test set, data contamination, model version pin, third-party model, can I use this model"
---

# Model-Selection Skill

Two questions, in this order. Phases 1–3 answer a literature question with a stable answer: which
architecture **family** suits the task. Phases 4–6 answer a provenance question: which concrete
**artifact** — repository, revision, checkpoint — will be run, and what its numbers may claim.
The skill writes decision notes and runs one stdlib gate; it never downloads, runs, trains or
benchmarks a model, and it describes archetypes, not a live SOTA leaderboard.

Elsewhere: building the repo → `/model-scaffold`; profiling data and planning preprocessing →
`/imaging-data`; validation design, metrics, uncertainty, explainability → `/model-assessment`;
documenting a model you built → `/model-card`; an LLM/MLLM, including benchmark contamination in
that setting → `/mllm-eval`; AI-vs-expert reader study → `/design-ai-benchmarking`.

## Workflow

### Phase 1 — Frame the question
State the **task** (classification / segmentation / detection / synthesis / transfer), the
**modality and dimensionality** (2-D vs 3-D volume), the **labelled-data scale** (events /
structures, not just images), **label availability** (lots / few / unlabelled pool), and the
constraints (class imbalance, small structures, interpretability, deployment compute).

### Phase 2 — Walk the decision tree, read the family card
Follow `${CLAUDE_SKILL_DIR}/references/index.md` (task → constraints → default pick). It routes to
one card; each gives the source paper, core idea, when-to-use, medical-imaging use, reference
implementation, and the typical validation setup for that class.

| Card | Families |
|---|---|
| `${CLAUDE_SKILL_DIR}/references/classification.md` | ResNet / DenseNet / EfficientNet / Inception / ConvNeXt / ViT / Swin / DeiT |
| `${CLAUDE_SKILL_DIR}/references/segmentation.md` | U-Net / 3-D U-Net / V-Net / Attention & Residual U-Net / nnU-Net (+ ResEnc, MedNeXt, STU-Net) / SegResNet / Swin-UNETR / Mask R-CNN |
| `${CLAUDE_SKILL_DIR}/references/detection.md` | nnDetection / Faster R-CNN + FPN / Mask R-CNN / RetinaNet / YOLO / DETR |
| `${CLAUDE_SKILL_DIR}/references/synthesis.md` | Pix2Pix / CycleGAN / SPADE / diffusion (DDPM, latent) / VAE / fastMRI reconstruction |
| `${CLAUDE_SKILL_DIR}/references/foundation_models.md` | SAM / MedSAM / MedSAM2 / nnInteractive / VISTA3D / TotalSegmentator / SegVol / BiomedCLIP / DINO / MAE / SimCLR / MoCo |
| `${CLAUDE_SKILL_DIR}/references/graph.md` | GCN / GraphSAGE / GAT / GIN / BrainGNN for connectomes and population graphs (PyTorch Geometric / DGL; not scaffolded by `/model-scaffold`) |

Never recommend an architecture for a modality or data scale it does not suit (a from-scratch ViT
on a few hundred images, 2-D slices for a volumetric structure) — the decision-tree constraints
exist to prevent exactly that. If asked for "the best" model, say the zoo is a curated archetype
map, not a current SOTA ranking.

### Phase 3 — Write the architecture decision note
Write `decisions/architecture_choice.md`: the task, the chosen architecture, its **source paper**
(mandatory — the Methods cite it), the reason against the constraints, the runner-up and why not,
and the matching `/model-scaffold` template. Never invent a benchmark number or paper claim: cite it
(verify via `/search-lit`), or write `[VERIFY]` and ask. A reference without a `/search-lit`-confirmed
DOI/PMID is marked `[UNVERIFIED - NEEDS MANUAL CHECK]`.

### Phase 4 — Write the model dossier for the concrete artifact
When a concrete candidate exists (a GitHub repo, a Hugging Face checkpoint, a paper's released
weights), write `model_dossier.json` recording what is **known**; leave unknowns unstated, never
guessed — the gate turns an absence into a finding.

```json
{
  "model": "OrganSeg-3D v2.5.1",
  "source": {"kind": "github", "url": "...", "version": "v2.5.1", "commit": "abc1234"},
  "licence": {"spdx": "Apache-2.0", "verified_from": "LICENSE at commit abc1234"},
  "intended_use": "research",
  "weights": {"pretrained": false},
  "task": {"model": "3d_ct_organ_segmentation", "study": "3d_ct_organ_segmentation"},
  "reported_validation": [{"dataset": "ExampleBench", "metric": "Dice", "source": "J Ex 2021"}],
  "developed_on": ["ExampleBench"],
  "evaluation_arms": [{"name": "external", "dataset": "OtherCohort-2026"}],
  "hardware": {"claimed": "any CUDA GPU", "verified_on": "GTX 1080 Ti", "verified": true}
}
```

Read each field from the artifact, not from memory:
- **Licence** — only from the licence file at the pinned revision, and record which file
  (`verified_from`). Never from a README badge, a model-card summary, or memory; an unstated
  licence is `LICENCE_UNSTATED`, never "probably MIT".
- **`developed_on`** — the paper's own account of where the method was built and tuned. It is the
  field people skip and the one the gate needs: a method that won a challenge was tuned on it.
- **`hardware.verified`** — true only after it actually ran. A support matrix is a different claim:
  a CUDA capability one compiler accepts may still be refused by another in the same stack.

### Phase 5 — Gate the dossier
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_model_provenance.py --dossier model_dossier.json \
    --out qc/model_provenance.json --strict
```
Stdlib-only and network-free: nothing is fetched and no licence resolved online.

| Verdict | Severity | Fires when |
|---|---|---|
| `BENCHMARK_PROVENANCE_CONFLICT` | Major | an evaluation arm uses a dataset the model was developed or tuned on |
| `EVAL_DATA_IN_TRAINING` | Major | an evaluation arm's dataset is inside the pretraining corpus |
| `LICENCE_UNSTATED` | Major | no licence recorded — not the same as a permissive one |
| `LICENCE_INCOMPATIBLE` | Major | non-commercial / research-only licence under commercial or deployment intent |
| `WEIGHTS_PROVENANCE_UNKNOWN` | Major | pretrained weights whose training corpus is not stated |
| `TASK_MISMATCH` | Minor | the model's task is not the study's task |
| `NO_VERSION_PIN` | Minor | no commit, tag or revision |
| `VALIDATION_UNREPORTED` | Minor | no reported validation (dataset + metric + source) |
| `HARDWARE_UNVERIFIED` | Minor | hardware support claimed but never executed |
| `LICENCE_UNVERIFIED` | Minor | a licence is named but not the file it was read from |

The gate flags a **relationship, not a reputation**: `developed_on: ExampleBench` passes cleanly as
long as no evaluation arm uses ExampleBench (the clean fixture proves this). Dataset names match as
**token sequences** with a small family-alias table — `MSD Task09 Spleen` matches `MSD`,
`MS Cohort 2026` does not — never by substring.

### Phase 6 — Turn a Major into a study decision
A `BENCHMARK_PROVENANCE_CONFLICT` rarely means abandoning the model (it is often the best-engineered
option precisely because it was tuned hard). It changes **what the arm may claim**:
1. Report that arm as a demonstration that the pipeline runs end to end, not as evidence the method works.
2. Put the evidential weight on an arm whose data **post-dates** the model, and say so with dates.
3. State the conflict in Methods and Limitations rather than leaving a reviewer to find it.

Never report a flagged arm as independent validation. An `EVAL_DATA_IN_TRAINING` arm is different in
kind: it produces a training-set score and cannot be reported as validation at all. Write this
arm-by-arm decision into the study record.

## Outputs and hand-off

- `decisions/architecture_choice.md` — the architecture decision note (Phase 3).
- `model_dossier.json` — the provenance record (Phase 4); `qc/model_provenance.json` — the audit (Phase 5).
- The arm-by-arm decision (Phase 6).

Carry them to `/model-scaffold` (instantiate the template), `/model-assessment` (arm and validation
design, what each arm may claim, metrics), `/model-card` (provenance section), and `/write-paper`
(Methods cite the source paper; Limitations state any conflict). Gate regression:
`bash ${CLAUDE_SKILL_DIR}/scripts/check_model_provenance_challenge/verify.sh` and
`bash ${CLAUDE_SKILL_DIR}/tests/test_model_provenance.sh`.
