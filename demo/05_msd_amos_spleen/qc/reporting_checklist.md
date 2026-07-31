# Reporting checklist — CLAIM 2024

**Manuscript**: `manuscript/writeup.md` (+ `manuscript/title_page.md`)
**Guideline**: CLAIM 2024 Update — Tejani AS, Klontzas ME, Gatti AA, Mongan JT, Moy L, Park SH,
Kahn CE Jr. *Radiol Artif Intell* 2024;6(4):e240300. doi:10.1148/ryai.240300
**Checklist source**: vendored `skills/check-reporting/references/checklists/CLAIM_2024.md`
(44 items; `check_checklist_exists.py --guideline "CLAIM 2024"` → OK)
**Assessed**: 2026-07-31

CLAIM was written for AI in medical imaging generally, and several of its items assume a
**classification** study with human annotators and patient-level clinical data. This is a
**segmentation** study on two public benchmarks, so a number of items are genuinely Not Applicable
and several others are unanswerable from the public data. Those are marked as such and counted
separately rather than being quietly scored as satisfied — a compliance percentage computed by
folding N/A items into the numerator is the standard way this artifact becomes worthless.

## Summary

| Status | Count | Meaning |
|---|---:|---|
| PRESENT | 23 | The item is reported, and the location is cited below. |
| PARTIAL | 10 | Reported somewhere in the demo (usually `pipeline/REPRODUCIBILITY.md`) but not in the manuscript body, or reported incompletely. |
| MISSING | 7 | Not reported. Each row says whether it *could* be, given the public data. |
| N/A | 4 | The item does not apply to this design. |

**Compliance among applicable items: 23 / 40 fully present (57.5 %), 33 / 40 at least partial
(82.5 %).** The denominator is 44 − 4 N/A. This is a demonstration write-up rather than a
submission, and the MISSING rows are left visible on purpose: four of the seven are unanswerable
from the source datasets, and the other three are real gaps a submitting author would have to close.

## Title and Abstract

| # | Item | Status | Location / note |
|---|---|---|---|
| 1 | Title | PRESENT | Title names "deep-learning study" and the task ("spleen segmentation"); the technology category (nnU-Net, a convolutional segmentation network) is named in the Abstract Methods. |
| 2 | Abstract | PRESENT | Structured Background/Methods/Results/Conclusion; states the datasets, the three partitions and their sizes, the retrospective use of public data, the statistical approach (bootstrap CIs, seed recorded), the outcomes, and code/data availability. |

## Introduction

| # | Item | Status | Location / note |
|---|---|---|---|
| 3 | Background | PRESENT | Introduction ¶1–2: the scientific gap (where the unaided path breaks), the contrast with the documented "what the model learned" failure modes, and the explicit statement that the intended use is a tooling demonstration with no clinical role. |
| 4 | Objectives | PRESENT | Introduction ¶1 states the question. The study additionally carries a **written, dated prediction** for the MRI rung in `EVALUATION_PLAN.md` §6, fixed before any prediction existed — which is stronger than the item requires, and is reported as partly wrong in the Discussion. |

## Methods — Study Design

| # | Item | Status | Location / note |
|---|---|---|---|
| 5 | Study design | PARTIAL | The design is retrospective secondary use of two public datasets, and this is evident from Methods–Data, but the word "retrospective" does not appear. **Fix**: one clause in Methods–Data. |
| 6 | Study goal | PRESENT | Title page "Article type"; Abstract; Introduction. Model creation plus internal and external testing, framed as tooling. |

## Methods — Data

| # | Item | Status | Location / note |
|---|---|---|---|
| 7 | Data sources | PRESENT | Methods–Data with licences and DOIs; both datasets are public and linked. Neither is vendored. |
| 8 | Eligibility | PRESENT | Methods–Data and Figure 5 (`figures/fig5_case_flow.*`): labelled cases only, with the reason each exclusion was made, and the three target-free cases separated from the metric denominators by a rule fixed in advance. |
| 9 | Preprocessing | PRESENT | Methods–Split and preprocessing; the declared manifest `manifests/preprocessing_manifest.json` and its leakage gate; the normalisation contract itself is analysed in Results and Table 4. |
| 10 | Subset selection | PARTIAL | Split construction and seed are reported (Methods; `splits/split_assignment.csv`). "Training of personnel involved" is N/A — no human performed selection or annotation in this study. |
| 11 | De-identification | MISSING | Not stated. Both source datasets are distributed de-identified under their licences, so this is closable in one sentence; the manuscript does not currently say so. |
| 12 | Missing data | PARTIAL | The one form of missing data that occurs — a reference containing no target — is handled by a pre-specified rule and reported (Methods–Evaluation, Table 2). No general missing-data statement is given because no other field is used. |
| 13 | Acquisition protocol | PARTIAL | Voxel spacing and slice thickness are reported per arm (Table 1) and used as a pre-specified subgroup axis. Manufacturer, kVp and MR sequence are **not available** in either public release, so they cannot be reported. |

## Methods — Reference Standard

| # | Item | Status | Location / note |
|---|---|---|---|
| 14 | Reference standard definition | PRESENT | Methods–Data and Methods–Evaluation: the spleen label index is 1, read from each dataset's shipped `dataset.json` rather than assumed, binarised as `== 1`; the CT label set runs 0–15 and the MRI set 0–13. |
| 15 | Reference standard rationale | PARTIAL | The reference standard is each dataset's own expert annotation, used because it is the released ground truth. No argument is made for it against alternatives. |
| 16 | Annotators | MISSING | The annotator source, qualifications and training for the two public datasets are not restated here. Closable by citing the dataset papers' annotation sections. |
| 17 | Annotation procedures | MISSING | Same as item 16. No annotation was performed in this study. |
| 18 | Annotation variability | MISSING | Inter- and intra-rater variability are **not published** for the released label sets at case level, so this cannot be reported from the available data. |

## Methods — Data Partitions

| # | Item | Status | Location / note |
|---|---|---|---|
| 19 | Partition assignment | PRESENT | 32 training / 9 held-out from 41 labelled MSD cases, seed 42; nnU-Net's internal 5-fold cross-validation is the tuning partition. Class imbalance is addressed by refusing accuracy as a metric (target ≈0.2–0.4 % of the volume). |
| 20 | Partition disjointness | PRESENT | **Patient-level**, and proved by set arithmetic rather than asserted: `qc/split_leakage.json` (`check_split_leakage.py --strict`, 0 overlapping subjects). |

## Methods — Testing Data

| # | Item | Status | Location / note |
|---|---|---|---|
| 21 | Test set size | MISSING | No power or precision calculation was performed. The internal held-out set is 9 cases and the external arms are the full labelled releases (300 CT, 60 MRI); sizes were set by availability, not by design. The bootstrap intervals in Table 2 make the resulting imprecision visible, which is not a substitute. |

## Methods — Model

| # | Item | Status | Location / note |
|---|---|---|---|
| 22 | Model architecture | PARTIAL | nnU-Net v2 `3d_fullres` is named in the manuscript and cited; the concrete configuration it self-selected (target spacing 2.55 × 0.789 × 0.789 mm, patch 56 × 192 × 192, batch 2) is in `pipeline/REPRODUCIBILITY.md`, read back from the shipped `plans.json`, not in the manuscript body. |
| 23 | Software | PARTIAL | nnU-Net v2 in a CUDA container is named. **Exact package versions were not captured at run time**, and `pipeline/REPRODUCIBILITY.md` says so explicitly rather than inventing pins. This is a real reproducibility gap and is declared as one. |
| 24 | Initialization | MISSING | Training was from random initialisation with no transfer learning, but the manuscript does not state it. Closable in one clause. |

## Methods — Training

| # | Item | Status | Location / note |
|---|---|---|---|
| 25 | Training procedures | PRESENT | Methods–Training: five folds, 100 epochs, the measured epoch time and the arithmetic that forced the reduced schedule. Augmentation is declared in `manifests/preprocessing_manifest.json` (`fit_scope: none`, applied after the split). |
| 26 | Model selection | PARTIAL | The final checkpoint of each fold was used (`checkpoint_final.pth`); no best-checkpoint selection on a tuning metric was applied. Stated in `pipeline/REPRODUCIBILITY.md`, not in the manuscript body. |
| 27 | Ensembling | PRESENT | Methods–Training and inference: five-fold ensemble at nnU-Net's default settings with mirroring test-time augmentation, on all three arms, confirmed from the run logs rather than from intent. |

## Methods — Evaluation

| # | Item | Status | Location / note |
|---|---|---|---|
| 28 | Performance metrics | PARTIAL | Metric selection is reported and justified against Metrics Reloaded (Dice with HD95; accuracy never reported). **No comparison to published models on these benchmarks** is made — deliberately, because the reduced schedule and single configuration make this run a poor proxy for nnU-Net's published performance, but the item is not satisfied. |
| 29 | Uncertainty | PRESENT | Bootstrap 95 % confidence intervals on every reported median (10,000 resamples, seed 20260725), Table 2 and Table 3, Figure 2. No significance test between arms — the Results say why, and say it is not one. |
| 30 | Robustness | PRESENT | Three cohorts of increasing distributional distance; pre-specified subgroups on two axes with identical cut-points (Table 3, Figure 4); the normalisation contract replayed case-by-case over both external arms (Table 4, Figure 3). |
| 31 | Explainability | N/A | No explainability method was applied, and none is claimed. |
| 32 | Internal testing | PRESENT | Rung 1 (Table 2). Consistency with training performance is reportable: nnU-Net's own 5-fold cross-validation over the 32 training cases gave 0.8437–0.9696, against a held-out median of 0.9595. |
| 33 | External testing | PRESENT | Two external arms, the first of which (AMOS CT) postdates the model's development benchmark and is therefore genuinely independent — a point made explicitly in the Introduction. |
| 34 | Trial registration | N/A | Not a clinical trial. |

## Results — Data

| # | Item | Status | Location / note |
|---|---|---|---|
| 35 | Inclusion/exclusion numbers | PRESENT | Figure 5 is a STARD-style flowchart covering both source datasets, every exclusion with its reason, and the three cases removed from the metric distributions. |
| 36 | Demographics | MISSING | **Not available.** Neither public release distributes age, sex or clinical characteristics, so no demographic table can be produced. Table 1 reports the imaging characteristics that *are* available (spleen volume, slice thickness, in-plane spacing) per arm, and the Limitations note that patient-level bias sources therefore cannot be assessed. |

## Results — Model Performance

| # | Item | Status | Location / note |
|---|---|---|---|
| 37 | Performance reporting | PRESENT | Table 2 across all three partitions; Table 3 across the pre-specified subgroups; every value benchmarked against the reference standard per case. |
| 38 | Accuracy estimates | PARTIAL | 95 % confidence intervals are reported throughout. ROC analysis is **N/A for a segmentation task** (there is no operating-point sweep here). Class imbalance is addressed by the refusal to report accuracy, which is stated in Methods. |
| 39 | Failure analysis | PARTIAL | Quantitative failure analysis is present and unusually explicit: 28 of 300 external CT predictions empty, 20 of 60 on MRI, both spleen-free CT cases receiving a false positive, and the full per-case distribution in Figure 1. A confusion matrix is N/A for segmentation. **What is missing is qualitative**: no example images of incorrect segmentations are shown. |

## Discussion

| # | Item | Status | Location / note |
|---|---|---|---|
| 40 | Limitations | PRESENT | A dedicated Limitations paragraph: cohort size and single institution, the tenth-of-default schedule, single configuration, external-only subgroups, the undetermined nature of the spleen-free cases, and the internal rung's provenance conflict. |
| 41 | Implications | PRESENT | Discussion and Conclusion. The implication drawn is about tooling (routing and severity of an existing finding), and clinical use is explicitly disclaimed in the title page and Abstract. |

## Other Information

| # | Item | Status | Location / note |
|---|---|---|---|
| 42 | Full protocol | PRESENT | `EVALUATION_PLAN.md` is the pre-specified protocol, dated before any prediction existed and shipped unedited; `pipeline/REPRODUCIBILITY.md` carries the technical detail that exceeds the write-up. |
| 43 | Availability | PRESENT | Manuscript "Data and code availability"; both datasets public with licences; the pipeline, per-case results, gate outputs and friction log are in the demo directory; `reproduce.sh` re-runs the laptop-executable tier. |
| 44 | Funding | MISSING | No funding statement. Closable in one line by the submitting author. |

## What a submitting author would fix first

1. **Item 21 (test-set size)** and **item 28 (comparison to published models)** are the two that a
   reviewer of a real submission would press hardest, because both are about whether the reported
   numbers can bear weight.
2. **Items 11, 24, 44** are one-sentence closures (de-identification, initialisation, funding).
3. **Items 16, 17, 18, 36** cannot be closed from the public data. The honest response is to cite
   the dataset papers for annotation provenance and to state the demographic gap in Limitations,
   which is what a submission would do.

Nothing in this table was auto-scored. Each row was assessed against the manuscript text, and where
an item is satisfied outside the manuscript body the file that satisfies it is named so the claim
can be checked.
