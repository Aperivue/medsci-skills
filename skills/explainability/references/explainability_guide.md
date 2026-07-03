# Medical-imaging explainability — method, sanity, localisation

Companion to `explainability`. This is *produce* knowledge: which XAI method fits which architecture,
the sanity checks a faithful map must pass, how to measure localisation quantitatively, and how to
frame the result honestly. It wires captum / pytorch-grad-cam by name; it does not reimplement them.

## 1. Method by architecture

| Model | Method | Library | Note |
|---|---|---|---|
| CNN (ResNet/DenseNet/EfficientNet) | **Grad-CAM / Grad-CAM++** | `pytorch-grad-cam`, `captum` (`LayerGradCam`) | Target the last conv block; Grad-CAM++ handles multiple instances |
| CNN, fine attribution | **Integrated Gradients**, **SHAP** | `captum` (`IntegratedGradients`), `shap` | Needs a baseline (black/blurred image, not zeros for CT) |
| Vision Transformer (ViT/Swin) | **Attention rollout**, **Grad-CAM on tokens** | `captum`, custom rollout | Raw attention ≠ explanation; rollout aggregates across layers |
| Segmentation (U-Net) | Region-level attribution; per-class Grad-CAM | `captum` `LayerGradCam` on the decoder | The mask *is* the localisation; explain the classification head if any |
| Any | **Occlusion / perturbation** | `captum` (`Occlusion`) | Model-agnostic sanity cross-check for a gradient method |

Pick one primary method and, where feasible, a second of a different family (gradient vs perturbation)
as a cross-check — agreement between families is stronger evidence than one pretty map.

## 2. Sanity checks (mandatory — Adebayo et al. 2018)

A saliency method can produce a convincing map that is **independent of the model and the labels**.
Before trusting any map, run both:

- **Model-parameter randomisation test** — progressively randomise the trained weights (top layer →
  all layers). A *faithful* map degrades toward noise; a map that is unchanged is an edge detector, not
  an explanation.
- **Data (label) randomisation test** — retrain on permuted labels. A faithful method's maps should
  differ from the correctly-trained model's; if identical, the map reflects the input, not the learned
  function.

Report the outcome (e.g. rank correlation of the map before/after randomisation). Declaring
`sanity_checks: ["model_randomization", "data_randomization"]` in the manifest is the gate's minimum;
one axis alone raises `INSUFFICIENT_SANITY`.

## 3. Quantitative localisation (don't eyeball)

If you claim the map "focuses on the lesion", measure it against ground-truth masks/boxes over the
cohort — not a few examples:

| Metric | What it measures | Range |
|---|---|---|
| **IoU / Dice** (thresholded map vs GT mask) | Overlap of the salient region with the finding | 0–1 |
| **Pointing game** | Does the map's peak fall inside the GT box? (hit rate over cohort) | 0–1 |
| **Energy-based pointing game** | Fraction of map energy inside the GT mask | 0–1 |

Report the metric **with a denominator** (n cases) and, ideally, a CI. A single annotated example is an
illustration, not evidence — the gate raises `CHERRY_PICKED_EXAMPLES` when `cohort_level` is not set.

## 4. Framing (attribution, not validation)

- **Say:** "Grad-CAM attributed the prediction to the perihilar region in X% of true positives (IoU
  0.6)." → `interpretation: localization` / `attribution`.
- **Do not say:** "The saliency map confirms the model is correct / uses clinically valid features /
  proves causation." A map shows *where signal is attributed under this method*, not that the decision
  is right or that the feature is causal. This framing raises `SALIENCY_AS_VALIDATION` (Major).
- A map that localises well can still accompany a wrong prediction, and a correct prediction can have a
  diffuse map — localisation and correctness are separate axes.

## 5. Common reviewer objections this pre-empts

1. "Did you sanity-check the saliency method?" → §2, both axes.
2. "Is the localisation quantified or just shown on one case?" → §3, cohort metric.
3. "You claim the map validates the model — it doesn't." → §4, reframe as attribution.
4. "Which layer / baseline / method version?" → declare `method` (and layer/baseline in notes);
   missing method raises `MISSING_METHOD`.
