# Graph neural networks — brain connectomes & population graphs (architecture-zoo)

For when the data is a **graph, not an image grid**: a brain **connectome** (nodes = ROIs /
parcels, edges = structural connectivity from DTI tractography or functional connectivity
from fMRI correlation), or a **population graph** (nodes = subjects, edges = phenotypic /
imaging similarity). The task is usually **graph-level classification** (diagnose a subject
from their connectome), **node-level** (flag abnormal ROIs, or classify subjects on a
population graph), or **link prediction** (connectivity changes).

This is a distinct family because a CNN/U-Net assumes a regular pixel grid; a connectome has
no grid — permuting the ROI order must not change the prediction, which is exactly the
symmetry a GNN respects. Each card: **paper → core idea → when to use → medical use →
reference impl → validation/experiment setup.**

---

## The general-purpose message-passing GNNs

### GCN (graph convolutional network)
- **Paper**: Kipf & Welling, "Semi-Supervised Classification with Graph Convolutional
  Networks", *ICLR* 2017.
- **Core idea**: each layer averages a node's features with its neighbours' (a first-order
  spectral-graph approximation), stacking to widen the receptive field over the graph.
- **When to use**: the transparent baseline for any connectome / population-graph task — try
  it before anything fancier.
- **Medical use**: connectome classification; **Parisot et al.** (*Medical Image Analysis*
  2018) put subjects on a **population graph** (phenotypic-similarity edges) for autism
  (ABIDE) and Alzheimer's (ADNI) prediction — a semi-supervised node-classification framing.
- **Reference impl**: **PyTorch Geometric** (`GCNConv`) or **DGL**; do not reimplement.
- **Validation setup**: split at the **subject level** (a subject's graph — or, on a
  population graph, a subject node's label — never spans train/test); with a small cohort,
  report a **permutation test** and cross-validated CIs, not a single split.

### GraphSAGE (inductive aggregation)
- **Paper**: Hamilton, Ying & Leskovec, "Inductive Representation Learning on Large Graphs",
  *NeurIPS* 2017.
- **Core idea**: learn an **aggregator** over a sampled neighbourhood so the model generalises
  to **unseen** nodes/graphs (inductive), unlike transductive GCN.
- **When to use**: a **new subject** must be classified without retraining (the realistic
  clinical setting), or the graph is too large to process whole.
- **Medical use**: inductive connectome classification where test subjects are genuinely held
  out (the honest deployment framing for a population-graph model).
- **Reference impl**: PyTorch Geometric (`SAGEConv`) / DGL.
- **Validation setup**: exploit the inductive setup to keep the test subjects fully out of
  message passing during training (transductive leakage is a real trap on population graphs).

### GAT (graph attention)
- **Paper**: Veličković et al., "Graph Attention Networks", *ICLR* 2018.
- **Core idea**: learn **attention weights** over neighbours, so the model decides which
  connections matter instead of averaging uniformly.
- **When to use**: when *which edges/connections drive the prediction* is itself a finding
  (edge importance is a built-in interpretability signal).
- **Medical use**: connectome studies that report the most-attended edges/ROIs as candidate
  biomarkers.
- **Reference impl**: PyTorch Geometric (`GATConv` / `GATv2Conv`) / DGL.
- **Validation setup**: treat attention as a **hypothesis-generating** attribution, not proof
  — sanity-check it (does it survive label permutation?) as `/explainability` requires of any
  saliency.

### GIN (graph isomorphism network)
- **Paper**: Xu et al., "How Powerful are Graph Neural Networks?", *ICLR* 2019.
- **Core idea**: an aggregation as discriminative as the Weisfeiler-Lehman test — the most
  **expressive** simple GNN for **graph-level** classification.
- **When to use**: graph-level diagnosis where subtle topology differences separate classes
  and GCN/GAT underfit.
- **Reference impl**: PyTorch Geometric (`GINConv`).
- **Validation setup**: expressiveness raises overfitting risk on small connectome cohorts —
  pair with heavy regularisation and nested CV (as `/radiomics-ml` does for the p ≫ n regime).

---

## The brain-specific model

### BrainGNN (ROI-aware, interpretable)
- **Paper**: Li et al., "BrainGNN: Interpretable Brain Graph Neural Network for fMRI Analysis",
  *Medical Image Analysis* 2021.
- **Core idea**: ROI-aware convolution + a pooling layer that scores and selects the most
  informative ROIs, so the model is **interpretable at the region level** by construction.
- **When to use**: fMRI connectome classification where you must report **which ROIs** drove
  the decision (the usual neuroimaging reviewer demand).
- **Medical use**: task-fMRI / resting-state connectome diagnosis (ASD, disorders) with a
  salient-ROI readout.
- **Reference impl**: the authors' released BrainGNN repo (on PyTorch Geometric).
- **Validation setup**: report salient ROIs with **stability across folds** (not one split);
  keep site-harmonisation (**ComBat**) fit on the **training** fold only.

---

## Connectome-specific validation traps (read before publishing)
- **Subject-level split.** A subject's connectome must not appear in more than one split; on a
  population graph, hold test-subject **labels** out of training and (ideally, inductive)
  their **nodes** out of message passing. This is `/model-validation`'s split-leakage discipline
  at the subject level.
- **Site / scanner harmonisation leakage.** Multi-site connectome data (ABIDE, ADNI) is
  harmonised with **ComBat** — fit it on the **training** fold only, never the whole cohort
  (the graph analogue of `/preprocess-imaging`'s `NORMALIZATION_LEAKAGE`).
- **p ≫ n.** A connectome has thousands of edges on tens–hundreds of subjects; treat it like
  radiomics — nested CV, regularisation, a **permutation test** for tiny cohorts, and don't
  over-read a single fold (`/radiomics-ml`).
- **Interpretability ≠ proof.** Attention / ROI-saliency is hypothesis-generating; sanity-check
  it (`/explainability`).

## Boundary — this family is not scaffolded by `/model-scaffold`
`/model-scaffold` builds **image-grid** repos (CNN / U-Net / transformer); it has **no graph
task template**. For GNNs, **integrate PyTorch Geometric / DGL directly** — they own the graph
layers, loaders, and training loop; the lane does not reimplement them. The lane's
**subject-level** gates still apply: `/model-validation` (split leakage), `/radiomics-ml`
(nested-CV rigor for p ≫ n), `/explainability` (attribution sanity), `/uncertainty-imaging`
(deployment uncertainty), and `/check-reporting` (TRIPOD+AI). Record the choice + paper in the
decision note; validate the built model with `/model-validation`.
