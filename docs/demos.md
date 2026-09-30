# Live demos

The code, outputs and QC reports for each demo are committed under [`demo/`](../demo/). The
[README](../README.md#skills) lists the skills these pipelines use.

Five public datasets. Five study types. Demos 1–3 each produce a complete manuscript, publication-ready figures, and a reporting-compliance audit; Demo 4 runs the medical-AI **model-engineering lane** end to end (scaffold → gates → training → evaluation → interpretability); Demo 5 takes that lane onto a GPU cluster and out to a **genuinely external cohort**, then reports where it broke.

| Demo | Dataset | Study Type | Compliance |
|------|---------|------------|------------|
| [Demo 1: Wisconsin BC](../demo/01_wisconsin_bc/) | `sklearn` built-in | Diagnostic accuracy | STARD 2015 |
| [Demo 2: BCG Vaccine](../demo/02_metafor_bcg/) | `metafor::dat.bcg` (13 RCTs) | Meta-analysis | PRISMA 2020 |
| [Demo 3: NHANES Obesity](../demo/03_nhanes_obesity/) | CDC NHANES 2017-18 | Epidemiology (survey) | STROBE |
| [Demo 4: PneumoniaMNIST CNN](../demo/04_pneumoniamnist_cnn/) | `medmnist` (CC BY 4.0) | Medical-AI model engineering (CNN) | CLAIM / TRIPOD+AI |
| [Demo 5: MSD → AMOS spleen](../demo/05_msd_amos_spleen/) | MSD Task09 + AMOS22 (CC BY 4.0) | 3-D segmentation, external validation + modality shift | CLAIM / Metrics Reloaded |

## Demo 1: Diagnostic Accuracy — Wisconsin Breast Cancer

```python
from sklearn.datasets import load_breast_cancer
data = load_breast_cancer()  # 569 samples, zero download
```

**Output from `orchestrate --e2e`** ([see full demo](../demo/01_wisconsin_bc/)):

<details>
<summary>Full output list — manuscript, figures, STARD flow, checklist (click to expand)</summary>

| Output | Description |
|--------|-------------|
| [Manuscript](../demo/01_wisconsin_bc/manuscript/manuscript.md) | IMRAD draft, ~1,800 words |
| [Title Page](../demo/01_wisconsin_bc/manuscript/title_page.md) | STARD title page with key points |
| [DOCX](../demo/01_wisconsin_bc/manuscript/manuscript_final.docx) | Submission-ready Word document |
| [ROC Curve](../demo/01_wisconsin_bc/analysis/figures/roc_curve.png) | 3-model comparison with DeLong 95% CIs |
| [Confusion Matrices](../demo/01_wisconsin_bc/analysis/figures/confusion_matrices.png) | Per-model confusion matrices at threshold 0.5 |
| [STARD Flow](../demo/01_wisconsin_bc/figures/stard_flow.svg) | D2-generated STARD 2015 flow diagram |
| [Reporting Checklist](../demo/01_wisconsin_bc/qc/reporting_checklist.md) | STARD 2015 — 60.9% compliance (14/23 applicable) |
| [Self-Review](../demo/01_wisconsin_bc/qc/self_review.md) | Initial 82 (REVISE) → 88 (PASS) after 1 fix iteration; final 0 major / 1 minor |
| [Pipeline Log](../demo/01_wisconsin_bc/qc/_pipeline_log.md) | 7-step E2E execution trace |

</details>

**Pipeline:** `analyze-stats` &rarr; `make-figures` &rarr; `write-paper` &rarr; AI pattern scan &rarr; `check-reporting` (STARD) &rarr; `self-review` &rarr; DOCX build &rarr; `present-paper`

## Demo 2: Meta-Analysis — BCG Vaccine Efficacy

```r
library(metafor)
data(dat.bcg)  # 13 RCTs, 357,347 participants (Colditz et al. 1994)
```

**Output from `orchestrate --e2e`** ([see full demo](../demo/02_metafor_bcg/)):

<details>
<summary>Full output list — manuscript, forest/funnel plots, PRISMA flow, checklist (click to expand)</summary>

| Output | Description |
|--------|-------------|
| [Manuscript](../demo/02_metafor_bcg/manuscript/manuscript.md) | Pooled RR = 0.489 (95% CI: 0.344–0.696), ~2,200 words |
| [Title Page](../demo/02_metafor_bcg/manuscript/title_page.md) | PRISMA title page with key points |
| [DOCX](../demo/02_metafor_bcg/manuscript/manuscript_final.docx) | Submission-ready Word document |
| [Forest Plot](../demo/02_metafor_bcg/analysis/figures/forest.png) | 13 studies, RE model (REML), 300 dpi |
| [Funnel Plot](../demo/02_metafor_bcg/analysis/figures/funnel.png) | Small-study / publication-bias visual |
| [PRISMA Flow](../demo/02_metafor_bcg/analysis/figures/prisma_flow.svg) | D2-generated PRISMA 2020 flow diagram |
| [Reporting Checklist](../demo/02_metafor_bcg/qc/reporting_checklist.md) | PRISMA 2020 — 57.1% (24/42) at check-reporting → 61.9% (26/42) after self-review fix |
| [Self-Review](../demo/02_metafor_bcg/qc/self_review.md) | Initial 78 → 82 (REVISE) after 1 fix iteration; 3 major / 4 minor (majors are out-of-scope RoB/GRADE/references) |
| [Pipeline Log](../demo/02_metafor_bcg/qc/_pipeline_log.md) | 7-step E2E execution trace |

</details>

**Pipeline:** `analyze-stats` (R metafor) &rarr; `make-figures` &rarr; `write-paper` &rarr; AI pattern scan &rarr; `check-reporting` (PRISMA 2020) &rarr; `self-review` &rarr; DOCX build &rarr; `present-paper`

## Demo 3: Epidemiology — NHANES Obesity & Diabetes

```python
# Pre-processed NHANES 2017-2018 CSV included
# 5,010 US adults after exclusions
```

**Output from `orchestrate --e2e`** ([see full demo](../demo/03_nhanes_obesity/)):

<details>
<summary>Full output list — manuscript, OR forest plot, STROBE flow, checklist (click to expand)</summary>

| Output | Description |
|--------|-------------|
| [Manuscript](../demo/03_nhanes_obesity/manuscript/manuscript.md) | Adjusted OR = 3.03 (95% CI: 2.29–4.02), ~1,850 words |
| [Title Page](../demo/03_nhanes_obesity/manuscript/title_page.md) | STROBE title page with key points |
| [DOCX](../demo/03_nhanes_obesity/manuscript/manuscript_final.docx) | Submission-ready Word document |
| [OR Forest Plot](../demo/03_nhanes_obesity/analysis/figures/forest_or.png) | Adjusted odds ratios for 7 variables |
| [Study Flow](../demo/03_nhanes_obesity/analysis/figures/strobe_flow.svg) | D2-generated participant flow diagram |
| [Reporting Checklist](../demo/03_nhanes_obesity/qc/reporting_checklist.md) | STROBE — 83.3% compliance (25/30 applicable) |
| [Self-Review](../demo/03_nhanes_obesity/qc/self_review.md) | ACCEPT-WITH-NOTES after 1 fix iteration; 0 genuine majors remaining |
| [Pipeline Log](../demo/03_nhanes_obesity/qc/_pipeline_log.md) | 7-step E2E execution trace |

</details>

**Pipeline:** `analyze-stats` &rarr; `make-figures` &rarr; `write-paper` &rarr; AI pattern scan &rarr; `check-reporting` (STROBE) &rarr; `self-review` &rarr; DOCX build &rarr; `present-paper`

## Demo 4: Medical-AI model engineering — PneumoniaMNIST CNN

The model-engineering lane end to end on a public benchmark: architecture choice, scaffold, data-stage,
split and hygiene gates, 3-seed training, held-out evaluation, calibration, Grad-CAM interpretability
and a write-up. Results, layout and the reproduce command are in
[the demo's README](../demo/04_pneumoniamnist_cnn/README.md).

## Demo 5: External Validation — MSD &rarr; AMOS spleen segmentation

The only demo that leaves the laptop, and the only one that reports a **failure**. It asks whether a
clinician can carry a deep-learning study to a defensible result without an engineer, then answers by
running a three-rung external-validation ladder on a GPU cluster and logging every point where the
answer was no.

| Rung | Cohort | n scored | Dice median [95% CI] |
|---|---|---:|---|
| 1 internal | MSD held-out | 9 | **0.9595** [0.9367–0.9734] |
| 2 genuine external | AMOS **CT** | 298 / 300 | **0.8932** [0.8633–0.9108] |
| 3 modality shift | AMOS **MRI** | 59 / 60 | **0.0152** [0.0000–0.0626] |
| 3b counterfactual | AMOS MRI, **rescaled** | 59 / 60 | **0.3016** [0.1744–0.4048] |

Rung 3 is a **constructed** test, and the demo says so: the evaluation plan named the normalisation
contract and predicted the collapse *before* inference ran. The trained plan carries `CTNormalization`
into inference and there is no flag that says "this is MRI", so a Hounsfield-unit clip is applied to
arbitrary-unit images: **0 of 60 MRI cases contain a negative voxel** (against 300 of 300 on CT), and a
median **23.2 %** of voxels are flattened at the clip ceiling (against 2.7 %). The run exits 0 and
returns a file for all 60 cases, 20 of them empty. Only ground truth made it loud.

A fourth arm changes **only the input intensity scale** — same checkpoint, no retraining — and
recovers median Dice to **0.3016** (+0.2864 [+0.1204, +0.4048]) while staying **−0.5916** below the
CT arm. So both mechanisms are real and differently sized: roughly **0.29 Dice is the preprocessing
contract, 0.59 a representation that does not transfer**. The arm and its prediction were written
down before it ran.

And `/imaging-data` (its profiling phase) **had already flagged the mixed intensity scale before training — as a
Minor**, where it sat in `qc/` for nine days. So the gap this demo found is not detection; it is
**routing and severity**. A gate that fires correctly into a directory no later step reads is,
operationally, a gate that did not fire. See [the full demo](../demo/05_msd_amos_spleen/) — including
[`FRICTION.md`](../demo/05_msd_amos_spleen/FRICTION.md), which lists every point that needed engineering
knowledge, because the headline question is not answerable honestly without it.

**Pipeline:** `imaging-data` (profile) &rarr; `model-selection` (sourcing) &rarr; `imaging-data` (preprocessing: leakage gate, plus the
counterfactual that must fail) &rarr; `model-assessment` (split gate) &rarr; nnU-Net training &rarr;
`model-assessment` (metrics) &rarr; `make-figures` &rarr; write-up. `bash reproduce.sh` re-runs the gates and the whole
across-cohort analysis on a laptop; training needs ~50 GPU-hours and says so.

## Project Folder Structure

Each demo (and real project) follows this role-based folder layout:

```
project/
├── data/                          # Input data
│   └── raw_data.csv
├── analysis/                      # /analyze-stats + /make-figures outputs
│   ├── tables/
│   ├── figures/
│   │   └── _figure_manifest.md
│   ├── _analysis_outputs.md
│   └── analyze.py
├── manuscript/                    # /write-paper outputs
│   ├── manuscript.md
│   ├── manuscript_final.docx
│   └── title_page.md
├── qc/                            # Quality verification
│   ├── reporting_checklist.md     # /check-reporting
│   ├── self_review.md             # /self-review
│   └── _pipeline_log.md
├── submission/                    # Post-journal-selection (manual trigger)
│   └── {journal_short}/
│       ├── cover_letter.md
│       ├── checklist.md
│       └── peer_review.md
└── presentation/
    └── presentation.pptx
```

The E2E pipeline (`orchestrate --e2e`) produces everything up to `qc/`. The `submission/` directory is created after journal selection via `/find-journal`.
