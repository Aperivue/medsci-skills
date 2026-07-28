# Pipeline & Architecture Diagrams — Medical AI / Engineering

> **Triggered from**: SKILL.md Step 1 (Specify) when the figure is a
> pipeline / architecture / workflow for a medical AI or imaging
> engineering paper. Read alongside `design_principles.md` (key-message)
> and `flow_diagram_lessons.md` (production lessons).

This file covers the four most common diagram types in medical-imaging AI
and engineering manuscripts that the standard reporting-guideline flows
(PRISMA / CONSORT / STARD / STROBE) do not address: DICOM workflow,
annotation pipeline, federated-learning topology, and model architecture.
For each, this file gives the canonical layout, common pitfalls, and a
preferred tool.

---

## 1. DICOM workflow diagram

**Use when**: the manuscript describes how DICOM images flow from scanner
→ PACS → research environment → preprocessing → model.

**Canonical layout** (left-to-right):

```
[Modality / scanner]  →  [PACS]  →  [Research VNA / mirror]
       ↓                                       ↓
  acquisition                       de-identification
  parameters                        + DICOM tag scrub
                                              ↓
                              [Preprocessed cohort store]
                                              ↓
                              [Train / tune / test split]
                                              ↓
                                     [Model input]
```

**Required annotations**:

- Modality (CT, MR, US, X-ray, OCT) and key acquisition parameters
  (kVp / mAs for CT, sequence and TE/TR for MR).
- De-identification step explicitly named — DICOM tag list (e.g., remove
  PatientName, PatientID, AccessionNumber, InstitutionName) or reference
  to a published profile (DICOM PS3.15 Annex E "Basic Profile").
- Whether pixel-data redaction (burned-in PHI) was performed.
- Cohort filtering criteria with counts at each step (this is also a
  STARD / TRIPOD requirement).

**Common pitfalls**:

- Drawing "PACS → model" with no de-identification box (privacy reviewers
  reject).
- Counts only at the final analytic cohort, not at each filter step
  (reproducibility reviewers reject).
- Using "DICOM" as a single block when the manuscript actually transforms
  to NIfTI / NRRD partway through — show the conversion explicitly.

**Preferred tool**: D2 with `--layout elk` for left-to-right; or Graphviz
`rankdir=LR`. Avoid matplotlib `FancyBboxPatch` (manual coordinates break
when text changes).

---

## 2. Annotation / labeling pipeline

**Use when**: the manuscript reports a labeled dataset built by human
annotators (segmentation, classification, bounding boxes).

**Canonical layout**:

```
[Raw image cohort]
       ↓
[Annotation tool / platform]  ←  [Annotator pool: N readers, expertise]
       ↓
[Round 1 labels]  →  [QC / consensus]  →  [Adjudication: senior reader]
                                                       ↓
                                        [Final reference standard]
                                                       ↓
                                        [Inter-rater agreement: κ / Dice]
```

**Required annotations**:

- Number and expertise level of annotators (e.g., "3 board-certified
  radiologists, 5–18 years of post-board experience").
- Annotation tool (e.g., 3D Slicer, ITK-SNAP, MD.ai, RIL-Contour, custom).
- Consensus rule (majority vote / unanimous / senior arbitration).
- Inter-rater agreement metric and value reported separately.
- Whether annotators were blinded to model output / clinical history.

**Common pitfalls**:

- Drawing "labeled by experts" with no count / qualification (reviewers
  ask for quantification).
- Omitting the QC arrow (looks like single-pass labeling, low quality).
- Conflating "reference standard" with "ground truth" — reference
  standard is the imperfect human label; ground truth is what we wish
  we had.

**Preferred tool**: D2; nodes shaped as rectangles for steps, dashed
border for human-in-the-loop steps to distinguish from automated.

---

## 3. Federated-learning topology

**Use when**: the manuscript trains a model across multiple sites without
centralizing raw data.

**Canonical layout** (radial, central server in middle):

```
              [Site A: cohort A_n, scanner type]
                              ↑↓
                       (model weights only,
                        not images)
                              ↑↓
              [Central aggregator / parameter server]
                              ↑↓
   [Site B: cohort B_n] ←→ [Site C: cohort C_n] ←→ [Site D: cohort D_n]
```

**Required annotations**:

- Per-site cohort size, scanner / vendor, demographic summary.
- What is exchanged (gradients / weights / encrypted updates) — and
  what is **not** (raw images, intermediate features).
- Aggregation algorithm (FedAvg / FedProx / FedBN / etc.).
- Number of communication rounds and local epochs per round.
- Privacy / security mechanism (differential privacy noise, secure
  aggregation) if claimed.

**Common pitfalls**:

- Bidirectional arrows without labeling what flows each way.
- No site-level demographic table — federated claims fall flat without
  evidence of distribution shift across sites.
- Labeling raw images crossing site boundaries — if that happens it is
  not federated learning, it is centralized.

**Preferred tool**: D2 with explicit `near: center` for the aggregator
node, then sites at compass points. Or matplotlib polar layout for
manuscripts that want radial symmetry.

---

## 4. Model architecture diagram

**Use when**: the manuscript proposes or modifies a neural-network
architecture and the message depends on the structural change.

**Canonical layout** (left-to-right block diagram):

```
[Input: 3D volume H×W×D, 1 channel]
                ↓
[Backbone: ResNet-50 / ViT-B / nnU-Net]   (cite + checkpoint)
                ↓
[Neck / feature pyramid / skip connections]
                ↓
[Head: classification / segmentation / detection]
                ↓
[Output: class probability / mask / bounding boxes]
```

**Required annotations**:

- Input shape (H × W × D × C) and modality.
- Backbone family + variant + initialization (random / ImageNet /
  domain-pretrained — cite the pretraining work).
- Output shape and post-processing (softmax / argmax / non-max
  suppression).
- Loss function (cross-entropy / Dice / focal / compound).
- Trainable parameter count.

**Style conventions** (medical-AI / engineering):

- Convolutional / linear blocks: rectangles with channel count below.
- Feature maps: trapezoids that shrink/grow to convey resolution change
  (optional but well-recognized).
- Skip connections: dashed arrows.
- Attention or transformer blocks: rectangles with internal split into
  Q / K / V annotation only when the message depends on attention.

**Common pitfalls**:

- "We used ResNet-50" with no diagram — fine for a methods paper, not
  for an architecture-contribution paper.
- 3-D rendered "Convolution" pictograms with no dimension info — looks
  decorative, says nothing.
- Drawing every layer when only the modified blocks matter — the eye
  cannot tell what changed. Show the modification, abstract the rest as
  "ResNet-50 backbone (frozen)".

**Preferred tools**:

- **Diagrams.net (drawio)** — fastest for one-off architecture figures.
- **NN-SVG** (https://alexlenail.me/NN-SVG/) — generates clean SVG for
  fully-connected, LeNet, AlexNet variants.
- **PlotNeuralNet** (LaTeX/TikZ) — used in the academic CV/ML community
  for publication-quality 3-D block diagrams.
- D2 with `shape: hexagon` / `shape: cylinder` if the architecture is
  unusual enough that custom blocks are needed.

For medical-AI papers targeting *Radiology AI*, *npj Digital Medicine*,
or *Nature Medicine*, prefer NN-SVG or PlotNeuralNet output over
hand-drawn blocks — reviewers in this venue are sensitive to alignment
quality.

---

## When to use which (quick selector)

| The figure is showing… | Use this section |
|---|---|
| How images move from scanner to model input | DICOM workflow |
| How a labeled dataset was built | Annotation pipeline |
| Multi-site training without raw-data sharing | Federated topology |
| The structure of the proposed neural network | Model architecture |
| Cohort filtering with counts at each stage | `flow_diagram_lessons.md` (PRISMA / STARD style) |
| Training / tuning / test data splits | dataset-flow (see `reporting_guideline_figure_map.md` §AI-specific) |

If the figure tries to do two of the above at once, split into two panels
or two figures — combining DICOM workflow + architecture in one panel
violates the cognitive-load budget (`design_principles.md` §4).

---

## Cross-references

- `design_principles.md` — communication-first checks
- `flow_diagram_lessons.md` — production lessons (template fidelity, PDF
  export, version freeze)
- `reporting_guideline_figure_map.md` — which figures CLAIM / TRIPOD+AI
  / STARD-AI mandate
- `critic_rubrics/data_plot.md` — calibration / fairness / colorblind
  checks
- `exemplar_diagrams/pipeline/*_why.md` — design notes (the rendered figures were cropped from published papers and were removed; an MIT-licensed package cannot redistribute them) —
  worked exemplars (multimodal MLLM, contrastive learning, VQA, report
  generation)
