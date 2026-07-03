# ML / DL method coverage map

Which machine-learning and deep-learning method families the toolkit covers, and **how** — by
*selecting*, *producing*, *validating*, *interpreting*, and *reporting* each, integrating the standard
frameworks (timm / MONAI / nnU-Net / TorchIO / scikit-learn / xgboost / pyradiomics) rather than
reimplementing them. The target user **fine-tunes existing models and builds classical-ML on collected
clinical data to derive clinical results and write papers** — not novel architecture development
(that stays [out of scope](../ROADMAP.md)).

Two facts make "all methods" tractable without a skill per algorithm:

1. **Produce paths integrate whole libraries.** `model-scaffold` wires **timm** (hundreds of pretrained
   backbones) + MONAI / nnU-Net / torchvision; `radiomics-ml` wires **scikit-learn** + xgboost /
   lightgbm / catboost + pyradiomics. Any learner in those libraries is in scope.
2. **The rigor gates are learner-agnostic.** `check_radiomics_ml`, `check_split_leakage`,
   `check_preprocessing_leakage`, `check_metric_reporting`, and `check_explainability_report` audit the
   *pipeline* (leakage, nested CV, calibration, metric choice, saliency rigor) — not the specific
   algorithm — so they apply to every method in the same family.

## Deep learning (imaging)

| Family | Examples | Select | Produce / fine-tune | Validate | Interpret | Report / evaluate |
|---|---|---|---|---|---|---|
| Classification CNN / transformer | ResNet, DenseNet, EfficientNet, ViT, Swin (timm) | `architecture-zoo` | `model-scaffold --task classification` (+ fine-tune, Item 4) | `model-validation`, `preprocess-imaging` | `explainability` | `model-evaluation`, `check-reporting` (CLAIM / TRIPOD+AI) |
| Segmentation | U-Net, 3D U-Net, Attention/Residual U-Net, **nnU-Net** | `architecture-zoo` | `model-scaffold --task segmentation` | `model-validation` | `explainability` | `model-evaluation` |
| Detection | Faster R-CNN, RetinaNet, YOLO, Mask R-CNN | `architecture-zoo` | `model-scaffold --task detection` | `model-validation` | — | `model-evaluation` (FROC / mAP) |
| Promptable / foundation segmentation | **SAM, MedSAM**, TotalSegmentator | `architecture-zoo` | fine-tune / adapt (Item 4) | `model-validation` | `explainability` | `model-evaluation` |
| Self-supervised pretraining | DINO, MAE, SimCLR | `architecture-zoo` | `model-scaffold --task ssl` | `model-validation` | — | — |
| Generative / synthesis | GAN, **diffusion** | `architecture-zoo` | `model-scaffold --task synthesis`; diffusion augmentation (Item 4) | `model-validation` | — | `check-reporting` |
| Vision-language / multimodal | CLIP, BiomedCLIP | `architecture-zoo` | fine-tune (Item 4) | `model-validation` | — | `model-evaluation` |
| Graph neural nets (connectomes) | GCN, GAT | *candidate* (`architecture-zoo` graph entry) | *candidate* | `model-validation`; tabular graph features → `radiomics-ml` | — | — |

## Classical / statistical ML (radiomics & tabular)

All of the below are produced and gated by **`radiomics-ml`** (learner-agnostic `check_radiomics_ml`
+ nested-CV recipe), with calibration / clinical-utility from `analyze-stats` and CLEAR / TRIPOD+AI /
PROBAST-AI reporting from `check-reporting`.

| Family | Examples |
|---|---|
| Penalised regression | LASSO, ridge, **elastic-net** logistic |
| Margin / kernel | linear & RBF **SVM** |
| Instance-based | **k-NN** |
| Probabilistic / discriminant | **naive Bayes**, LDA, QDA |
| Single tree | decision tree, CART |
| Bagging | **random forest**, extra-trees |
| Boosting | **XGBoost**, **LightGBM**, **CatBoost**, HistGBM, AdaBoost |
| Shallow neural | **MLP** |
| Meta / ensemble | **stacking**, voting, blending |
| Dimensionality reduction | PCA, UMAP, t-SNE, LASSO-selection |
| Unsupervised / clustering | k-means, hierarchical, GMM |
| Survival ML | random survival forest, Cox-net, DeepSurv (+ `analyze-stats` survival) |
| Probability calibration | Platt, isotonic (+ `analyze-stats` calibration) |

## LLM / MLLM

| Family | Select / produce | Evaluate | Report |
|---|---|---|---|
| Clinical LLM / multimodal LLM (API or open weights) | prompt-driven; `design-ai-benchmarking` for reader panels | **`mllm-eval`** (faithfulness, hallucination, contamination, clinical-efficacy metrics) | `check-reporting` (TRIPOD-LLM / MI-CLEAR-LLM / CLAIM) |

## What is deliberately NOT here

- **Novel architecture development / a new training framework.** We wire and report MONAI / nnU-Net /
  timm / scikit-learn; we do not reimplement them or invent architectures.
- **Autonomous training / experiment tracking (MLOps).** Left to the frameworks + W&B / MLflow; a thin
  integration reference is roadmap Item 6.
- **Anything that runs a model on real patient data or fabricates a metric.** Every number comes from
  the researcher's executed code.

*Candidate gaps (open):* a `architecture-zoo` graph-neural-net entry for brain-connectome studies, and
the Item 4 fine-tuning / SAM-adaptation / diffusion-augmentation produce path. See
[`roadmap_model_engineering_depth.md`](roadmap_model_engineering_depth.md).
